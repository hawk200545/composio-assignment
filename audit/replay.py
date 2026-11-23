import argparse
import fcntl
import json
import os
import sys
from itertools import zip_longest
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers import Docs, OpenRouter, ProviderError, Spend
from research import REVIEW_VERSION, collect, export, load_apps, run_app
from research_models import App, write_json

BASELINE = ROOT / "runs" / "full"
REPLAYS = ROOT / "runs" / "verification-replays"
CACHED_KEYS = (
    "first_pass", "first_pass_source_ids", "catalog", "fetches", "searches", "sources",
)


def checkpoint(app, path):
    original = json.loads((BASELINE / "state" / path.name).read_text(encoding="utf-8"))
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
        if state["app"] != app.model_dump() or state["review_version"] != REVIEW_VERSION:
            raise ValueError(f"Replay settings changed for {app.name}. Use a new replay name.")
    else:
        state = {key: original[key] for key in CACHED_KEYS}
        state.update(app=app.model_dump(), review_version=REVIEW_VERSION)
        write_json(path, state)
    if state["first_pass"] != original["first_pass"]:
        raise ValueError(f"The saved first pass changed for {app.name}.")
    return state


def refresh_sources(app, state, path, docs, model):
    if state.get("cached_source_refresh_complete"):
        return
    original = json.loads((BASELINE / "state" / path.name).read_text(encoding="utf-8"))
    old_app = App.model_validate(original["app"])
    groups = original["searches"].values()
    candidates = [app.hint]
    candidates.extend(
        url for group in zip_longest(*groups) for url in group
        if url and app.allows(url) and not old_app.allows(url)
    )
    for url in candidates:
        fetch = state["fetches"].get(url)
        if fetch and fetch["status"] in {"unreadable", "filtered"} and fetch["stage"] != "refresh":
            del state["fetches"][url]
    collect(app, state, path, [], model, docs, "refresh", 6, hints=candidates)
    state["cached_source_refresh_complete"] = True
    write_json(path, state)


def replay(name, ids, refresh):
    apps_by_id = {app.id: app for app in load_apps(ROOT / "apps.json")}
    if len(ids) != len(set(ids)) or not set(ids) <= apps_by_id.keys():
        raise ValueError("Supply unique assignment IDs from apps.json.")
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise ValueError("Set OPENROUTER_API_KEY in the environment or .env.")
    output = REPLAYS / name
    state_dir = output / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    original_spend = json.loads((BASELINE / "spend.json").read_text(encoding="utf-8"))
    remaining = 5 - sum(item["usd"] for item in original_spend)
    with (REPLAYS / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        spend = Spend(REPLAYS / "spend.json", remaining)
        states = {}
        failures = 0
        with httpx.Client(timeout=14, follow_redirects=False) as http:
            model = OpenRouter(http, key, spend)
            for app_id in ids:
                app = apps_by_id[app_id]
                path = state_dir / f"{app_id:03d}.json"
                state = checkpoint(app, path)
                states[app_id] = state
                try:
                    docs = Docs(http)
                    if refresh and "revised" not in state:
                        refresh_sources(app, state, path, docs, model)
                    run_app(app, state, path, None, docs, model, cached_only=True)
                except ProviderError as error:
                    failures += 1
                    print(f"{app.name}: {error}", file=sys.stderr, flush=True)
                else:
                    print(f"{app.name}: revised export saved", flush=True)
        done = export(output, states)
        print(f"Completed {done}/{len(ids)} replays in {output}", flush=True)
        return int(bool(failures))


def main():
    parser = argparse.ArgumentParser(description="Recheck saved claims with the current verifier.")
    parser.add_argument("--name", required=True, help="Name of the output directory")
    parser.add_argument("--refresh-cached-urls", action="store_true",
                        help="Fetch the hint and saved discovery URLs newly allowed by the seed")
    parser.add_argument("ids", nargs="+", type=int)
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in {"", ".", ".."}:
        parser.error("Use a single directory name.")
    try:
        return replay(args.name, args.ids, args.refresh_cached_urls)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
