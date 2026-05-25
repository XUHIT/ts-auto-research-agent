# Server Closed-Loop Benchmark Demo

The main project demo is a single server-backed benchmark study. It uses the current A20CPolar server configuration, the local paper-note knowledge base, and the local Time-Series-Library_simple benchmark repository.

This is not a collection of small examples. The demo is a rigorous ETTh1 benchmark loop with a locked baseline, a strong reference, an innovation candidate, schema validation, constrained review, and presentation artifacts.

## Command

```bash
cd /home/xu/ts-auto-research-agent
/home/xu/anaconda3/bin/python -m pip install -e .
/home/xu/anaconda3/bin/python -m ts_auto_research.cli multiagent run   --topic forecasting   --paper-source /home/xu/autoresearch-agent/knowledge-base/paper-notes   --literature-limit 1000   --backend tsl-simple   --execute-demo
/home/xu/anaconda3/bin/python -m ts_auto_research.cli report
```

## Closed-Loop Stages

1. Build a read-only literature index from the server paper notes.
2. Extract method evidence for candidate design and risk control.
3. Propose a taste-gated research idea.
4. Register DLinear, PatchTST, candidates, and controls.
5. Build recoverable experiment plans and per-run schemas.
6. Validate dataset, horizon, metric, seed, baseline, budget, and leakage policy.
7. Execute Time-Series-Library_simple runs on the server GPU.
8. Parse RMSE and MAE from real benchmark output.
9. Run post-result taste review.
10. Produce constrained reviewer decisions.
11. Update `research_state/leaderboard.csv` and `research_state/trajectory.jsonl`.
12. Generate `research_cockpit.html`, dashboard, monitor, PDF report, and `demo_packet.json`.

## Latest Validated Result

Validated on May 25, 2026 in `/home/xu/ts-auto-research-agent`:

| Run | Role | Model | RMSE | MAE | Baseline | Delta | Schema | Decision |
|---|---|---|---:|---:|---:|---:|---|---|
| `run_0051` | `baseline_anchor` | `DLinear` | `0.59827763` | `0.38131171` | `0.59827763` | `0.0` | `valid` | `continue` |
| `run_0052` | `strong_reference` | `PatchTST` | `0.58627319` | `0.37807289` | `0.59827763` | `0.01200444` | `valid` | `continue` |
| `run_0053` | `innovation_candidate` | `CalDLinear` | `0.59605795` | `0.38774657` | `0.59827763` | `0.00221968` | `valid` | `continue` |

## Interpretation

`CalDLinear` is a bounded positive innovation candidate because it improves RMSE over DLinear under the same protocol. It is not a SOTA claim because PatchTST remains stronger on both RMSE and MAE. The next research step is ablation and broader validation, not paper-level overclaiming.

## Generated Artifacts

```text
research_state/full_research_demo_report.md
research_state/multiagent_trace.md
research_state/showcase.md
research_state/leaderboard.csv
research_state/trajectory.jsonl
research_state/demo_packet.json
runs/run_0051/
runs/run_0052/
runs/run_0053/
docs/demo_results/research_cockpit.html
docs/demo_results/dashboard.html
docs/demo_results/monitor.html
docs/demo_results/benchmark_report.pdf
```
