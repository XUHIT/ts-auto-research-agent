# Public Mini Demo Result Snapshot

This is the public-safe expected effect of running:

```bash
ts-agent demo public-mini
```

## Completed Stages

| Agent | Expected status |
|---|---|
| `literature_curator` | `completed` |
| `idea_scout` | `completed` |
| `taste_reviewer` | `completed` |
| `scope_manager` | `completed` |
| `experiment_planner` | `completed` |
| `experiment_runner` | `completed` |
| `result_reviewer` | `completed` |
| `synthesis_agent` | `completed` |

## Example Metric Outcome

On the bundled `examples/sample_series.csv`, the `dlinear-mini` backend should complete a real CSV-based benchmark run and update the leaderboard. A representative server run produced:

| Backend | Metric | Value | Baseline | Delta | Decision |
|---|---|---:|---:|---:|---|
| `dlinear-mini` | `mse` | `0.08126356` | `0.235424` | `0.15416044` | `continue` |

Exact run ids may differ because they depend on the current workspace state.

## Main Artifacts

```text
research_state/public_mini_demo_report.md
research_state/multiagent_trace.md
research_state/leaderboard.csv
runs/run_XXXX/review.md
```
