# Composio toolkit readiness research

This take-home project researches 100 apps across 10 categories to assess whether they can become agent toolkits. The Python agent collects public documentation, extracts claims with source excerpts, verifies the claims, and checks the Composio catalog. The Slidev case study presents the findings, audits, and a searchable app matrix.

## Results

The original 100-app batch classified **8 Ready, 42 Gated, 5 Limited, and 45 Unresolved**. These are documentation-based verdicts. An unresolved app needs more evidence before a build decision.

| File | Contents |
| --- | --- |
| [Results CSV](slides/public/data/results.csv) | All 100 apps, verdicts, blockers, and evidence URLs |
| [Results JSON](slides/public/data/results.json) | Revised claims with source excerpts and Composio catalog matches |
| [First-pass JSON](slides/public/data/first-pass.json) | The 100 original model extractions before verification |
| [Follow-up replay JSON](slides/public/data/recheck-results.json) | Patched verifier results for the separate ten-app holdout |

## Run the research agent

Install [uv](https://docs.astral.sh/uv/) and use Python 3.12. Get an [OpenRouter API key](https://openrouter.ai/settings/keys) and a [Composio project API key](https://dashboard.composio.dev/). From the repository root, copy the example and fill in both keys locally.

```sh
cp -n .env.example .env
uv sync --locked --python 3.12
```

Run the six-app pilot. It uses three workers and a $2 OpenRouter cap and writes to `runs/pilot/`.

```sh
uv run --locked --env-file .env python research.py
```

Run the complete [100-app seed](apps.json) with a $5 OpenRouter cap.

```sh
uv run --locked --env-file .env python research.py \
  --seed apps.json --out runs/research --workers 3 --budget-usd 5
```

Repeat the same command to resume. Each run writes its first-pass and revised exports, a verification log, a spend ledger, and resumable per-app checkpoints to its output directory. Use a fresh `--out` directory to start over or change the app seed.

### How verification works

1. Discover public documentation and fetch it from approved product domains.
2. Use Gemini 3.1 Flash Lite through OpenRouter to extract claims and verbatim excerpts.
3. Check excerpts against downloaded text, review their meaning in a separate model call, and retry flagged fields once.
4. Keep unsupported fields unresolved and record pages that need manual review. The Composio SDK checks the existing toolkit catalog.

## Reproduce the accuracy audits

The [original audit](slides/public/data/holdout-report.md) compares the first pass and original verifier on one app per category. The [follow-up audit](slides/public/data/recheck-report.md) uses ten different apps to compare those passes with the patched verifier. Both reports document mistakes against frozen, source-linked labels.

These commands score the checked-in exports without API keys or another research run.

```sh
python3 audit/score.py
python3 audit/score.py --labels slides/public/data/recheck-labels.json \
  --patched-results slides/public/data/recheck-results.json
```

Run the Python tests with `uv run --locked python -m unittest discover -s tests`.

## Open the web case study

Use [Bun](https://bun.com/docs/installation) 1.4 and run the following from the repository root. Open the local URL printed by Slidev.

```sh
bun install --cwd slides --frozen-lockfile
bun run --cwd slides dev
```

To build and preview the production site locally:

```sh
bun run --cwd slides build
bun run --cwd slides preview
```

### Deploy to Vercel

Import the repository into Vercel and leave **Root Directory** at the repository root (`.`). The root [vercel.json](vercel.json) installs from the Bun lockfile, builds the deck under `slides/`, and serves `slides/dist`. If an existing Vercel project already uses `slides` as its root, [slides/vercel.json](slides/vercel.json) supports that setup too.

The rewrite lets reviewers open or refresh slide URLs directly, such as `/5` for the audit and `/7` for the app matrix. The app matrix links to `/csv`, where reviewers can search, filter, sort, and download the full CSV export. The site builds from the checked-in results. You can set `VITE_RESEARCH_REPO_URL` to the published repository URL to display a source link on the research-agent slide.

The optional `uv run --locked python slides/snapshot.py` command refreshes the published data and source archive when the original full-run and holdout replay outputs are available locally. The local `runs/` directory is ignored by Git.
