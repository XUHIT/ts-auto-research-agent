# Public Smoke Check

`ts-agent demo public-mini` is a portable smoke check. It proves that a fresh clone can execute the research-loop mechanics with bundled paper notes and a bundled CSV, but it is not the project delivery demo.

## One Command

```bash
python -m pip install -e .
ts-agent demo public-mini
```

## What Runs

1. Builds a paper-note index from `examples/demo_paper_notes/`.
2. Proposes a research idea from the bundled context.
3. Runs the pre-experiment taste gate.
4. Runs the multi-agent orchestration protocol.
5. Executes the `dlinear-mini` backend on `examples/sample_series.csv`.
6. Writes protocol files, leaderboard, trajectory, and a local report.

## Why This Exists

The smoke check is for installation and workflow sanity. The real demo is the server-backed ETTh1 benchmark study documented in `docs/SERVER_CLOSED_LOOP_DEMO.md`.
