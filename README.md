# TS Auto Research Agent

`ts-auto-research-agent` is a clean-room time-series autonomous research agent. It combines:

- Metric-driven experiment trajectory loops.
- Recoverable file protocols, review checkpoints, and resumable artifacts.
- A read-only time-series literature substrate built from curated top-venue paper notes.
- Vibe and taste gates before and after experiments, so the agent does research instead of blind benchmark sweeping.

The system is designed as a clean-room time-series research loop: ideas are proposed, scored, executed, reviewed, and carried forward only when results change the research trajectory.

## Quick Start

```bash
cd /home/xu/ts-auto-research-agent
/home/xu/anaconda3/bin/python -m pip install -e .
ts-agent init
ts-agent literature build-index --source /home/xu/autoresearch-agent/knowledge-base/paper-notes --limit 50
ts-agent assets scan --scan-root /path/to/time-series-assets --max-depth 4
ts-agent scope set --name general-ts-two-libs --asset-id <baseline_repo_id> --asset-id <baseline_repo_id>
ts-agent vibe propose --topic forecasting --count 3
ts-agent taste review --idea vibe_001
ts-agent loop --budget 2 --backend smoke
ts-agent run-next --backend dlinear-mini --data-csv examples/sample_series.csv --column value
```

Inspect outputs:

```bash
ts-agent leaderboard
find runs -maxdepth 2 -type f | sort
```

## Core Commands

- `ts-agent init`: create `research_state/`, `runs/`, and `literature/` runtime files.
- `ts-agent literature build-index`: build a read-only paper-note index.
- `ts-agent assets scan/list`: discover external papers, datasets, baselines, checkpoints, and environments into a local runtime registry.
- `ts-agent scope set/show`: restrict the active experiment scope to approved assets before automation begins.
- `ts-agent vibe propose`: generate fast research-direction ideas from topic + literature context.
- `ts-agent taste review`: score a vibe idea before experiment planning.
- `ts-agent plan-experiment`: create a recoverable experiment plan.
- `ts-agent run-next`: run the next queued experiment.
- `ts-agent parse-last`: parse and register the latest run.
- `ts-agent review-last`: produce a strict action decision for the latest run.
- `ts-agent loop`: run the autonomous inner loop for a fixed budget.
- `ts-agent leaderboard`: print the experiment leaderboard.

## Runtime Protocol

Each run directory contains:

```text
runs/run_0001/
  vibe_idea.yaml
  taste_pre.yaml
  experiment_plan.yaml
  command.sh
  stdout.log
  metrics.json
  taste_post.yaml
  review.md
```

Global trajectory files:

```text
research_state/leaderboard.csv
research_state/trajectory.jsonl
research_state/vibe_ideas.yaml
research_state/taste_reviews.yaml
research_state/experiment_queue.yaml
research_state/claims.yaml
```

## Backends

- `smoke`: deterministic synthetic backend for validating the full loop.
- `dlinear-mini`: minimal CSV-based time-series backend. If no CSV is provided, it records a clear environment/data blocker instead of silently pretending success. Try it with `examples/sample_series.csv`.

## Tests

```bash
/home/xu/anaconda3/bin/python -m unittest discover -s tests
```

## Design Docs

- `docs/ARCHITECTURE.md`: system layers, state layout, and backend contract.
- `docs/PROTOCOL.md`: experiment protocol, taste gates, and reviewer outputs.
- `docs/ASSET_INTEGRATION.md`: how server-side papers, data, baselines, checkpoints, and environments enter the agent without being copied into the repo.
- `IMPLEMENTATION_REPORT.md`: implemented scope, validation results, and current GitHub publication blocker.
