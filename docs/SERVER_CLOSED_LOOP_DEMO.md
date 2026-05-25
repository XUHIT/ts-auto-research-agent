# Server Closed-Loop Benchmark Demo

The main project demo is a single server-backed benchmark study. It uses the current A20CPolar server configuration, the local paper-note knowledge base, and the local Time-Series-Library_simple benchmark repository.

This is not a collection of small examples. The demo is a rigorous ETTh1 benchmark loop with a locked baseline, a strong reference, an innovation candidate, and constrained review.

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
  --literature-limit 1000 \
  --topic forecasting \
  --model DLinear \
  --model PatchTST \
  --model CalDLinear \
  --data ETTh1.csv \
  --seq-len 24 \
  --pred-len 24 \
  --subset-ratio 0.05 \
  --train-epochs 3
```

## Closed-Loop Stages

1. Build a read-only literature index from the server paper notes.
2. Extract method evidence for candidate design and risk control.
3. Propose a taste-gated research idea.
4. Build recoverable experiment plans with explicit method roles.
5. Execute Time-Series-Library_simple runs on the RTX 3090 server.
6. Parse RMSE and MAE from real benchmark output.
7. Run post-result taste review.
8. Produce constrained reviewer decisions.
9. Update `research_state/leaderboard.csv` and `research_state/trajectory.jsonl`.
10. Write `research_state/full_research_demo_report.md` and `research_state/showcase.md`.

## Latest Validated Result

Validated on May 25, 2026 in `/home/xu/ts-auto-research-agent`:

| Run | Role | Model | RMSE | MAE | Baseline | Delta | Decision |
|---|---|---|---:|---:|---:|---:|---|
| `run_0048` | `baseline_anchor` | `DLinear` | `0.59827763` | `0.38131171` | `0.59827763` | `0.0` | `continue` |
| `run_0049` | `strong_reference` | `PatchTST` | `0.58627319` | `0.37807289` | `0.59827763` | `0.01200444` | `continue` |
| `run_0050` | `innovation_candidate` | `CalDLinear` | `0.59605795` | `0.38774657` | `0.59827763` | `0.00221968` | `continue` |

## Interpretation

`CalDLinear` is a bounded positive innovation candidate because it improves RMSE over DLinear under the same protocol. It is not a SOTA claim because PatchTST remains stronger on both RMSE and MAE. The next research step is ablation and broader validation, not paper-level overclaiming.

## Generated Artifacts

```text
research_state/full_research_demo_report.md
research_state/showcase.md
research_state/leaderboard.csv
research_state/trajectory.jsonl
runs/run_0048/
runs/run_0049/
runs/run_0050/
```
