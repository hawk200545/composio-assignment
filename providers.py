import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from composio import Composio
from composio_client import NotFoundError
from pydantic import BaseModel

from research_models import App, Source, split_https, write_json

MODEL = "google/gemini-3.1-flash-lite"
MAX_OUTPUT_TOKENS = 2600
PROMPT_PRICE = 0.30
COMPLETION_PRICE = 1.65
MAX_HTML_BYTES = 4_000_000
MAX_SOURCE_CHARS = 6500


class ProviderError(RuntimeError):
    pass


class BudgetPaused(ProviderError):
    pass


class SourceUnavailable(RuntimeError):
    def __init__(self, message: str, *, blocked_target: str | None = None):
        super().__init__(message)
        self.blocked_target = blocked_target


class ComposioCatalog:
    def __init__(self, key: str):
        self.client = Composio(api_key=key, timeout=25, max_retries=1)

    def toolkit(self, app: App) -> dict:
        checked_at = datetime.now(UTC).isoformat()
        if app.toolkit_slug:
            try:
                item = self.client.toolkits.get(app.toolkit_slug)
            except NotFoundError:
                pass
            else:
                return self.found(item, checked_at, "configured_slug")
        query = app.name.split(" (", 1)[0]
        candidates = self.client.toolkits.get(query={"search": query, "limit": 30})
        names = {self.normalize_name(name) for name in (app.name, query)}
        matches = [item for item in candidates if self.normalize_name(item.name) in names]
        if len(matches) == 1:
            return self.found(matches[0], checked_at, "catalog_name")
        return {
            "status": "ambiguous_name_match" if matches else "no_exact_name_match",
            "search_query": query,
            "candidate_slugs": [item.slug for item in matches],
            "checked_at": checked_at,
        }

    @staticmethod
    def normalize_name(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", name.lower())

    @staticmethod
    def found(item, checked_at: str, matched_by: str) -> dict:
        return {
            "status": "found",
            "slug": item.slug,
            "name": item.name,
            "catalog_url": f"https://docs.composio.dev/toolkits/{item.slug}",
            "checked_at": checked_at,
            "matched_by": matched_by,
        }


class Docs:
    def __init__(self, client: httpx.Client):
        self.client = client

    def fetch(self, app: App, url: str) -> Source:
        for _ in range(5):
            if not app.allows(url):
                parsed = split_https(url)
                target = parsed._replace(query="", fragment="").geturl() if parsed else None
                raise SourceUnavailable(
                    "redirect or URL is outside the product's source rules", blocked_target=target,
                )
            try:
                with self.client.stream("GET", url) as response:
                    if response.is_redirect and response.headers.get("location"):
                        url = urljoin(url, response.headers["location"])
                        continue
                    if response.status_code != 200:
                        raise SourceUnavailable(f"HTTP {response.status_code}")
                    kind = response.headers.get("content-type", "").partition(";")[0].lower()
                    if kind not in {"text/html", "application/xhtml+xml", "text/plain", "text/markdown"}:
                        raise SourceUnavailable(f"unsupported content type {kind or 'unknown'}")
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_HTML_BYTES:
                            raise SourceUnavailable("response exceeds the document size limit")
                    text = self.page_text(body.decode(response.encoding or "utf-8", errors="replace"), kind)
                    if len(text) < 100:
                        raise SourceUnavailable("page returned too little readable text")
                    return Source(
                        id="",
                        url=str(response.url).partition("#")[0],
                        retrieved_at=datetime.now(UTC).isoformat(),
                        text=text[:MAX_SOURCE_CHARS],
                    )
            except (httpx.HTTPError, LookupError) as error:
                raise SourceUnavailable(type(error).__name__) from error
        raise SourceUnavailable("too many redirects")

    @staticmethod
    def page_text(body: str, kind: str) -> str:
        if kind in {"text/plain", "text/markdown"}:
            return body.strip()
        soup = BeautifulSoup(body, "html.parser")
        title = " ".join(soup.title.stripped_strings) if soup.title else ""
        for node in soup.select("script, style, link, noscript, svg, nav, footer, aside"):
            node.decompose()
        root = soup.select_one("main, [role=main], [itemprop=text]") or soup.body or soup
        return "\n".join(part for part in (title, root.get_text("\n", strip=True)) if part)


class Spend:
    """Persist a conservative reservation before each request, including interrupted calls."""

    def __init__(self, path: Path, limit: float):
        self.path = path
        self.limit = limit
        self.lock = Lock()
        self.calls = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def reserve(self, label: str, amount: float) -> int:
        with self.lock:
            if sum(call["usd"] for call in self.calls) + amount > self.limit:
                raise BudgetPaused("Next OpenRouter request would exceed the configured budget.")
            self.calls.append({"request": label, "usd": amount, "estimated": True})
            write_json(self.path, self.calls)
            return len(self.calls) - 1

    def settle(self, index: int, amount: float) -> None:
        with self.lock:
            self.calls[index].update(usd=amount, estimated=False)
            write_json(self.path, self.calls)


class OpenRouter:
    def __init__(self, client: httpx.Client, key: str, spend: Spend):
        self.client = client
        self.key = key
        self.spend = spend

    def ask(self, output: type[BaseModel], label: str, instructions: str, input_data: dict):
        request = {
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)},
            ],
            "max_tokens": MAX_OUTPUT_TOKENS,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": output.__name__,
                    "strict": True,
                    "schema": output.model_json_schema(),
                },
            },
        }
        message = self.complete(request, label)
        try:
            return output.model_validate_json(message["content"])
        except (KeyError, TypeError, ValueError) as error:
            raise ProviderError(f"OpenRouter did not return a valid {output.__name__}.") from error

    def search(self, query: str, label: str) -> list[str]:
        request = {
            "messages": [
                {"role": "system", "content": (
                    "Use the web search tool to find official pages matching the query. "
                    "Use the query as written. Return only the verified result URLs, one per line. "
                    "Omit any URL that did not appear in a search result."
                )},
                {"role": "user", "content": query},
            ],
            "max_tokens": 700,
            "parallel_tool_calls": False,
            "stop_server_tools_when": [{"type": "step_count_is", "step_count": 1}],
            "tools": [{
                "type": "openrouter:web_search",
                "parameters": {"engine": "exa", "max_results": 6, "max_total_results": 6},
            }],
        }
        # Allow for search charges and retrieved context in the budget reservation.
        message = self.complete(request, label, extra_reservation=0.035)
        urls = []
        for annotation in message.get("annotations") or []:
            citation = annotation.get("url_citation") or {}
            if isinstance(citation.get("url"), str):
                urls.append(citation["url"])
        # Discovery URLs still have to pass the product rules and fetch successfully.
        urls.extend(re.findall(r"""https://[^\s<>"'\x60)\]]+""", message.get("content") or ""))
        return list(dict.fromkeys(urls))[:10]

    def complete(self, request: dict, label: str, extra_reservation: float = 0) -> dict:
        request = {
            **request,
            "model": MODEL,
            "reasoning": {"effort": "minimal"},
            "provider": {
                "require_parameters": "response_format" in request,
                "max_price": {"prompt": PROMPT_PRICE, "completion": COMPLETION_PRICE},
            },
            "plugins": [{"id": "web", "enabled": False}],
        }
        prompt_ceiling = len(json.dumps(request, ensure_ascii=False).encode("utf-8")) + 512
        reservation = (
            prompt_ceiling * PROMPT_PRICE + request["max_tokens"] * COMPLETION_PRICE
        ) / 1_000_000 + extra_reservation
        index = self.spend.reserve(label, reservation)
        try:
            response = self.client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.key}"},
                json=request,
                timeout=65,
            )
        except httpx.HTTPError as error:
            raise ProviderError(f"OpenRouter request failed ({type(error).__name__}).") from error
        if response.is_error:
            if response.status_code in {400, 401, 402, 403, 404, 422, 429}:
                self.spend.settle(index, 0)
            raise ProviderError(f"OpenRouter returned HTTP {response.status_code}.")
        try:
            data = response.json()
            cost = (data.get("usage") or {}).get("cost")
            if isinstance(cost, (float, int)) and math.isfinite(cost) and cost >= 0:
                self.spend.settle(index, cost)
            message = data["choices"][0]["message"]
            if isinstance(message, dict):
                return message
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise ProviderError("OpenRouter did not return a valid message.") from error
        raise ProviderError("OpenRouter did not return a valid message.")
