# TS Auto Research Agent

`ts-auto-research-agent` is a clean-room time-series autonomous research agent. It combines:

- Metric-driven experiment trajectory loops.
- Recoverable file protocols, review checkpoints, and resumable artifacts.
- A read-only time-series literature substrate built from curated top-venue paper notes.
- Role-based multi-agent orchestration for literature, idea, taste, planning, execution, review, and synthesis roles.
- Vibe and taste gates before and after experiments, so the agent does research instead of blind benchmark sweeping.

The system is designed as a clean-room time-series research loop: ideas are proposed, scored, executed, reviewed, and carried forward only when results change the research trajectory.

## Quick Start

```bash
cd /home/xu/ts-auto-research-agent
/home/xu/anaconda3/bin/python -m pip install -e .
ts-agent init
ts-agent demo public-mini
ts-agent literature build-index --source /home/xu/autoresearch-agent/knowledge-base/paper-notes --limit 50
ts-agent assets scan --scan-root /path/to/time-series-assets --max-depth 4
ts-agent scope set --name general-ts-two-libs --asset-id <baseline_repo_id> --asset-id <baseline_repo_id>
ts-agent vibe propose --topic forecasting --count 3
ts-agent taste review --idea vibe_001
ts-agent loop --budget 2 --backend smoke
ts-agent demo tsl-simple --model DLinear --model PatchTST --model MLP
ts-agent multiagent run --topic forecasting --paper-source /home/xu/autoresearch-agent/knowledge-base/paper-notes
ts-agent demo full-research --paper-source /home/xu/autoresearch-agent/knowledge-base/paper-notes --model DLinear --model PatchTST --model MLP
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
- `ts-agent multiagent run/show`: run and inspect the role-based orchestration trace.
- `ts-agent demo public-mini`: run the complete clone-local demo with bundled notes and CSV data.
- `ts-agent demo tsl-simple`: run a small real Time-Series-Library_simple comparison demo.
- `ts-agent demo full-research`: run the full literature-to-experiment research agent demo.

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
research_state/multiagent_trace.json
research_state/multiagent_trace.md
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
- `docs/MULTI_AGENT_ORCHESTRATION.md`: role-based agent orchestration, trace files, and extension path.
- `docs/PUBLIC_DEMO.md`: one-command portable demo for first-time users.
- `IMPLEMENTATION_REPORT.md`: delivered scope, validation commands, and remaining product work.

## Public Mini Demo

For a fresh clone without private server paths, run:

```bash
python -m pip install -e .
ts-agent demo public-mini
```

This generates `research_state/public_mini_demo_report.md`, `research_state/multiagent_trace.md`, a leaderboard row, and a recoverable `runs/run_XXXX/` protocol directory using only `examples/demo_paper_notes/` and `examples/sample_series.csv`.

## Presentation Demo

Run a real Time-Series-Library_simple mini-suite:

```bash
cd /home/xu/ts-auto-research-agent
ts-agent demo tsl-simple --model DLinear --model PatchTST --model MLP --data ETTh1.csv --seq-len 24 --pred-len 24 --subset-ratio 0.05 --train-epochs 1
```

The demo writes standard run artifacts under `runs/run_XXXX/` and a local report at `research_state/tsl_simple_demo_report.md`. Runtime artifacts are intentionally ignored by git.

## Full Research Demo

Run the complete demo from paper notes to real benchmark results:

```bash
cd /home/xu/ts-auto-research-agent
ts-agent demo full-research \
  --paper-source /home/xu/autoresearch-agent/knowledge-base/paper-notes \
  --literature-limit 50 \
  --topic forecasting \
  --model DLinear \
  --model PatchTST \
  --model MLP \
  --data ETTh1.csv \
  --seq-len 24 \
  --pred-len 24 \
  --subset-ratio 0.05 \
  --train-epochs 1
```

The generated local report is `research_state/full_research_demo_report.md`. It includes literature signals, the selected idea, pre-taste scores, real model metrics, post-result review, and the next automated step.

## Demo Result Snapshot

The completed full research demo result is included for public review:

- `docs/demo_results/full_research_demo_result.md`: public-safe end-to-end demo report.
- `docs/demo_results/leaderboard_excerpt.csv`: metrics from the real demo runs.
- `docs/demo_results/run_artifacts_tree.txt`: generated runtime artifact layout.

These files summarize the final demo effect without committing local runtime paths, private data, or raw run logs.

## License

MIT.
