"""Prepare the shareable evidence from the original batch and both audits."""

import json
import re
import sys
from collections import Counter
from pathlib import Path
from shutil import copyfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from research import write_results_csv

SLIDES = Path(__file__).resolve().parent
PUBLIC = SLIDES / "public" / "data"
RUN = PROJECT / "runs" / "full"
REPLAY = PROJECT / "runs" / "verification-replays" / "held-out" / "results.json"
VERDICTS = ("Ready", "Gated", "Limited", "Unresolved")
SOURCE_FILES = (
    ".env.example", ".gitignore", "README.md", "apps.json", "audit-sample.json", "pilot.json",
    "providers.py", "pyproject.toml", "research.py", "research_models.py", "uv.lock", "tests/test_pilot.py",
    "audit/replay.py", "audit/score.py", "audit/recheck-sample.json",
)
AUDIT_FILES = ("holdout-report.md", "holdout-labels.json", "recheck-report.md", "recheck-labels.json")
RESULT_FILES = {
    "first-pass.json": RUN / "first-pass.json",
    "results.json": RUN / "results.json",
    "recheck-results.json": REPLAY,
}


def audit_scores(filename):
    report = (PUBLIC / filename).read_text(encoding="utf-8")
    return [
        {"label": title, "correct": int(correct), "total": int(total)}
        for title, correct, total in re.findall(
            r"^\| (First pass|Revised|Original verifier|Patched verifier) \| (\d+)/(\d+) \(", report, re.MULTILINE
        )
    ]


def main():
    rows = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
    assert sorted(row["id"] for row in rows) == list(range(1, 101)), "Expected the original 100-app export"
    categories = list(dict.fromkeys(row["category"] for row in rows))
    assert len(categories) == 10 and all(sum(row["category"] == cat for row in rows) == 10 for cat in categories)
    counts = Counter(row["verdict"] for row in rows)
    assert set(counts) == set(VERDICTS), "Unexpected verdict labels"
    auth_counts = Counter(value for row in rows for value in row["claims"]["auth"]["values"])
    summary = {
        "apps": len(rows),
        "verdicts": {name: counts[name] for name in VERDICTS},
        "categories": [
            {"name": category, "counts": dict(Counter(row["verdict"] for row in rows if row["category"] == category))}
            for category in categories
        ],
        "paidPlans": sum("paid_plan" in row["claims"]["production_access"]["values"] for row in rows),
        "paidGates": sum(row["verdict"] == "Gated" and "paid plan" in row["blocker"] for row in rows),
        "authCounts": auth_counts,
        "authUnknown": sum(not row["claims"]["auth"]["values"] for row in rows),
        "rest": sum("rest" in row["claims"]["api_interfaces"]["values"] for row in rows),
        "officialMcp": sum("official" in row["claims"]["mcp"]["values"] for row in rows),
        "mcpUnknown": sum(not row["claims"]["mcp"]["values"] for row in rows),
        "catalogMatches": sum(row["composio_catalog"]["status"] == "found" for row in rows),
        "audits": [audit_scores("holdout-report.md"), audit_scores("recheck-report.md")],
    }
    assert list(map(len, summary["audits"])) == [2, 3], "Audit reports are missing a score row"
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for name, source in RESULT_FILES.items():
        copyfile(source, PUBLIC / name)
    write_results_csv(PUBLIC / "results.csv", rows)
    (SLIDES / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    # Only the listed files ship. Local credentials, model logs and checkpoints stay out of the archive.
    data_paths = tuple(f"slides/public/data/{filename}" for filename in (*AUDIT_FILES, *RESULT_FILES, "results.csv"))
    with ZipFile(PUBLIC / "research-source.zip", "w") as archive:
        for name in sorted((*SOURCE_FILES, *data_paths)):
            source = PROJECT / name
            contents = source.read_bytes()
            if name == "README.md":
                contents = contents.split(b"\n## Open the web case study", 1)[0].rstrip() + b"\n"
            info = ZipInfo(f"composio-toolkit-research/{name}")
            info.external_attr = 0o644 << 16
            archive.writestr(info, contents, compress_type=ZIP_DEFLATED)


if __name__ == "__main__":
    main()
