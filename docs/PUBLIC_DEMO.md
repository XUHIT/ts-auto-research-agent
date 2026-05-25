# Public Mini Demo

The public mini demo is the portable first-run experience. It does not require private server paths, external benchmark repositories, GPUs, API keys, or additional datasets.

## One Command

```bash
python -m pip install -e .
ts-agent demo public-mini
```

## What Runs

1. Builds a paper-note index from `examples/demo_paper_notes/`.
2. Proposes a research idea from the topic and literature context.
3. Runs the pre-experiment taste gate.
4. Runs the multi-agent orchestration protocol.
5. Executes the `dlinear-mini` backend on `examples/sample_series.csv`.
6. Writes protocol files under `runs/run_XXXX/`.
7. Updates `research_state/leaderboard.csv` and `research_state/trajectory.jsonl`.
8. Writes `research_state/multiagent_trace.md`.
9. Writes `research_state/public_mini_demo_report.md`.

## Expected Artifacts

```text
research_state/public_mini_demo_report.md
research_state/multiagent_trace.md
research_state/leaderboard.csv
research_state/trajectory.jsonl
runs/run_XXXX/metrics.json
runs/run_XXXX/review.md
```

## Why This Demo Exists

The larger `tsl-simple` demo proves integration with a real external time-series benchmark repository. The public mini demo proves that a fresh clone can run the full research-agent loop immediately.
