# Server Closed-Loop Demo

The main project demo is the server-backed closed loop. It uses the current A20CPolar server configuration, the local paper-note knowledge base, and the local Time-Series-Library_simple benchmark repository.

## Command

```bash
cd /home/xu/ts-auto-research-agent
/home/xu/anaconda3/bin/python -m pip install -e .
ts-agent demo full-research
```

The defaults expand to:

```bash
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

## Closed-Loop Stages

1. Build a read-only literature index from the server paper notes.
2. Propose research ideas from the literature context.
3. Run the pre-experiment taste gate.
4. Build recoverable experiment plans.
5. Execute Time-Series-Library_simple runs on the RTX 3090 server.
6. Parse RMSE and MAE from real benchmark output.
7. Run post-result taste review.
8. Produce constrained reviewer decisions.
9. Update `research_state/leaderboard.csv` and `research_state/trajectory.jsonl`.
10. Write `research_state/full_research_demo_report.md`.

## Latest Validated Result

Validated on May 25, 2026 in `/home/xu/ts-auto-research-agent`:

| Run | Model | RMSE | MAE | Baseline | Delta | Decision |
|---|---|---:|---:|---:|---:|---|
| `run_0018` | `DLinear` | `0.60498005` | `0.38604552` | `0.60498005` | `0.0` | `continue` |
| `run_0019` | `PatchTST` | `0.59777755` | `0.38496944` | `0.60498005` | `0.0072025` | `continue` |
| `run_0020` | `MLP` | `0.77158123` | `0.56779635` | `0.60498005` | `-0.16660118` | `kill` |

## Generated Artifacts

```text
research_state/full_research_demo_report.md
research_state/leaderboard.csv
research_state/trajectory.jsonl
runs/run_0018/
runs/run_0019/
runs/run_0020/
```

Each run directory contains the recoverable protocol files: idea, pre-taste, experiment plan, command, stdout/stderr logs, metrics, post-taste, and review.

## Interpretation

This is not a final scientific claim. It is the validated delivery demo: the agent moves from server literature resources to a taste-gated idea, executes real time-series benchmark runs, parses metrics, updates a trajectory, and makes review decisions on the target GPU environment.

## One-Screen Showcase

After the server demo, run:

```bash
ts-agent showcase
```

This prints the effect, novelty, usefulness, latest metrics, reviewer decisions, and next action in one screen.
