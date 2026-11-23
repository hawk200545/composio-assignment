import io
import json
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import httpx

import research
from providers import BudgetPaused, Docs, OpenRouter, ProviderError, SourceUnavailable, Spend
from research_models import (
    FIELDS, App, Claim, Profile, Review, Source, evidence_issues, normalize,
    repair_citations, unknown,
)

FIRST_URL = "https://docs.example.org/product/api"
SECOND_URL = "https://docs.example.org/product/access"
BAD_URL = "https://docs.example.org/product/browser-only"
FIRST_QUOTE = "The Workspace API exposes customers and tasks with a project API key."
SECOND_QUOTE = "Production access requires a paid plan."


class PilotTests(unittest.TestCase):
    def test_trial_access_does_not_establish_ongoing_production(self):
        profile = Profile(**{field: unknown() for field in FIELDS})
        trial = "The free trial allows API requests for 14 days."
        production = "After the trial, subscribe to a paid plan to continue calling the API."
        source = Source(id="S1", url=FIRST_URL, retrieved_at="2026-11-23", text=f"{trial} {production}")
        profile.developer_access = Claim(
            values=["free_trial"], conflict=False, evidence=[{"source_id": "S1", "quote": trial}],
        )
        profile.production_access = Claim(
            values=["free_trial", "paid_plan"], conflict=False,
            evidence=[{"source_id": "S1", "quote": production}],
        )
        issues = evidence_issues(profile, [source])
        self.assertNotIn("developer_access", issues)
        self.assertEqual(issues["production_access"], "trial access belongs in developer access")
        profile.production_access.values = ["paid_plan"]
        self.assertNotIn("production_access", evidence_issues(profile, [source]))
        profile.developer_access.values = ["free_trial", "paid_plan"]
        self.assertIn("choose one cost tier", evidence_issues(profile, [source])["developer_access"])

    def test_retry_route_excerpts_are_contiguous_and_cover_distinct_resources(self):
        raw = "Create a ticket\n/api/v2/tickets\nList tickets\n/api/v2/tickets\nCreate a contact\n/api/v2/contacts"
        source = Source(id="S1", url=FIRST_URL, retrieved_at="2026-11-23", text=raw)
        excerpts = research.api_route_excerpts([source])
        self.assertEqual(len(excerpts), 2)
        self.assertTrue(all(excerpt["quote"] in raw for excerpt in excerpts))
        self.assertIn("/api/v2/contacts", excerpts[1]["quote"])

    def test_joined_citation_splits_only_when_every_fragment_is_present(self):
        routes = ["Create a ticket /api/v2/tickets", "Create a contact /api/v2/contacts"]
        claim = Claim(values=["broad"], conflict=False,
                      evidence=[{"source_id": "S1", "quote": " ... ".join(routes)}])
        repaired = repair_citations(claim, {"S1": " and ".join(routes)})
        self.assertEqual([citation.quote for citation in repaired.evidence], routes)
        self.assertEqual(repair_citations(claim, {"S1": routes[0]}), claim)

    def test_overlong_exact_quote_splits_without_losing_text(self):
        quote = " ".join(f"Documented API operation number {n}." for n in range(15))
        claim = Claim(values=["rest"], conflict=False, evidence=[{"source_id": "S1", "quote": quote}])
        repaired = repair_citations(claim, {"S1": quote})
        parts = [citation.quote for citation in repaired.evidence]
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(part) <= 320 and part in quote for part in parts))
        self.assertEqual(" ".join(parts), quote)

    def test_quote_verification_accepts_punctuation_split_by_html(self):
        self.assertEqual(
            normalize("Authenticate with an\nOAuth app\n.\nThen select scopes."),
            normalize("Authenticate with an OAuth app. Then select scopes."),
        )
        self.assertNotIn(normalize("OAuth app... scopes"), normalize("OAuth app. Then select scopes."))

    def test_resume_keeps_first_pass_and_rechecks_claims(self):
        app = {
            "id": 1, "name": "Example Workspace", "category": "CRM",
            "hint": FIRST_URL, "sources": ["https://docs.example.org/product"],
        }
        initial = Profile(**{field: unknown() for field in FIELDS})
        for field, values in {
            "auth": ["api_key"],
            "api_interfaces": ["rest"],
            "api_breadth": ["broad"],
        }.items():
            setattr(initial, field, Claim(values=values, conflict=False,
                                          evidence=[{"source_id": "S1", "quote": FIRST_QUOTE}]))
        initial.production_access = Claim(values=["free"], conflict=False,
                                          evidence=[{"source_id": "S1", "quote": "Free for everyone."}])
        retry = Profile(**{field: unknown() for field in FIELDS})
        retry.production_access = Claim(values=["paid_plan"], conflict=False,
                                        evidence=[{"source_id": "S2", "quote": SECOND_QUOTE}])
        review = Review(**{field: "supported" for field in FIELDS})
        phases = []

        def model_response(schema, label, instructions, inputs):
            phases.append(label)
            if label.endswith(":review") and phases.count(label) == 1:
                raise ProviderError("simulated interruption after saving the first pass")
            return {"extract": initial, "recheck": retry}.get(label.split(":")[1], review)

        def discover(query, label):
            return [SECOND_URL, BAD_URL] if "current official docs" in query else [FIRST_URL]

        def fetch(app, url):
            if url == BAD_URL:
                raise SourceUnavailable("browser rendering required")
            quote = {FIRST_URL: FIRST_QUOTE, SECOND_URL: SECOND_QUOTE}[url]
            return Source(id="", url=url, retrieved_at="2026-11-23T00:00:00Z", text=quote)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed = root / "seed.json"
            seed.write_text(json.dumps([app]))
            args = Namespace(seed=seed, out=root / "run", workers=1, budget_usd=2.0)
            with (
                patch.object(research, "credentials", return_value=("stub", "stub")) as credentials,
                patch.object(research, "ComposioCatalog") as catalog,
                patch.object(research, "Docs") as docs,
                patch.object(research, "OpenRouter") as router,
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                router.return_value.search.side_effect = discover
                catalog.return_value.toolkit.return_value = {"status": "not_checked"}
                docs.return_value.fetch.side_effect = fetch
                router.return_value.ask.side_effect = model_response
                self.assertEqual(research.run(args), 1)
                baseline = (args.out / "first-pass.json").read_bytes()
                self.assertEqual(research.run(args), 0)
                self.assertEqual((args.out / "first-pass.json").read_bytes(), baseline)
                self.assertEqual(research.run(args), 0)
                self.assertEqual(credentials.call_count, 2)
                self.assertEqual(phases.count("1:extract"), 1)
                self.assertEqual(docs.return_value.fetch.call_count, 3)
            [result] = json.loads((args.out / "results.json").read_text())
            [log] = json.loads((args.out / "verification.json").read_text())
            self.assertEqual(result["verdict"], "Gated")
            self.assertEqual(result["claims"]["production_access"]["evidence"][0]["url"], SECOND_URL)
            self.assertEqual(result["claims"]["description"]["values"], [])
            self.assertIn("citation quote missing", log["first_pass_issues"]["production_access"])
            self.assertEqual(log["browser_review_candidates"][0]["url"], BAD_URL)

    def test_search_reads_citations_and_tracks_search_cost(self):
        def model(request):
            body = json.loads(request.content)
            self.assertEqual(body["tools"][0]["type"], "openrouter:web_search")
            return httpx.Response(200, json={
                "usage": {"cost": 0.007},
                "choices": [{"message": {
                    "content": f"{FIRST_URL}\n{SECOND_URL}",
                    "annotations": [{"url_citation": {"url": FIRST_URL}}],
                }}],
            })
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "spend.json"
            with httpx.Client(transport=httpx.MockTransport(model)) as client:
                router = OpenRouter(client, "stub", Spend(ledger, 2.0))
                self.assertEqual(router.search("example search", "1:search"), [FIRST_URL, SECOND_URL])
            self.assertEqual(json.loads(ledger.read_text())[0]["usd"], 0.007)

    def test_document_reader_does_not_follow_cross_product_redirects(self):
        app = App(id=1, name="Example", category="CRM", hint=FIRST_URL,
                  sources=["https://docs.example.org/product/"])

        def page(request):
            self.assertEqual(str(request.url), FIRST_URL)
            return httpx.Response(302, headers={"location": "/another-product"})

        with httpx.Client(transport=httpx.MockTransport(page)) as client:
            with self.assertRaisesRegex(SourceUnavailable, "outside the product") as error:
                Docs(client).fetch(app, FIRST_URL)
        self.assertEqual(error.exception.blocked_target, "https://docs.example.org/another-product")

    def test_bigcommerce_legacy_hint_can_redirect_to_scoped_docs(self):
        app = research.load_apps(research.ROOT / "apps.json")[42]
        destination = "https://docs.bigcommerce.com/"
        self.assertFalse(app.allows("https://docs.bigcommerce.com.example.org/"))
        visited = []

        def page(request):
            visited.append(str(request.url))
            if str(request.url) == app.hint:
                return httpx.Response(301, headers={"location": destination})
            return httpx.Response(200, text="Public developer documentation. " * 5)

        with httpx.Client(transport=httpx.MockTransport(page)) as client:
            self.assertEqual(Docs(client).fetch(app, app.hint).url, destination)
        self.assertEqual(visited, [app.hint, destination])

    def test_openrouter_budget_stops_new_requests_after_resume(self):
        review = Review(**{field: "unsupported" for field in FIELDS})

        def model(request):
            body = json.loads(request.content)
            self.assertTrue(body["response_format"]["json_schema"]["strict"])
            return httpx.Response(200, json={
                "usage": {"cost": 0.003},
                "choices": [{"message": {"content": review.model_dump_json()}}],
            })

        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "spend.json"
            with httpx.Client(transport=httpx.MockTransport(model)) as client:
                router = OpenRouter(client, "stub", Spend(ledger, 2.0))
                self.assertEqual(router.ask(Review, "1:review", "instructions", {}), review)
                resumed = OpenRouter(client, "stub", Spend(ledger, 0.004))
                with self.assertRaises(BudgetPaused):
                    resumed.ask(Review, "1:recheck-review", "instructions", {})
            self.assertEqual(json.loads(ledger.read_text()),
                             [{"request": "1:review", "usd": 0.003, "estimated": False}])
