# Full Research Demo Result

This is a public-safe snapshot of the completed end-to-end demo. The raw runtime files stay under `research_state/` and `runs/` on the experiment machine because they contain local paths and source-specific notes.

## Demo Command

```bash
ts-agent demo full-research \
  --paper-source /path/to/paper-notes \
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

## End-to-End Flow

```mermaid
flowchart LR
  A[Paper notes] --> B[Literature index]
  B --> C[Vibe idea]
  C --> D[Pre-taste gate]
  D --> E[Experiment plans]
  E --> F[Time-Series-Library_simple runs]
  F --> G[Metric parser]
  G --> H[Post-taste review]
  H --> I[Leaderboard and trajectory]
  I --> J[Demo report]
```

## Literature Stage

- Indexed paper notes: `50`
- Topic: `forecasting`
- Representative signals, paraphrased for the public snapshot:
  - Multivariate time-series analysis often needs interpretable diagnostics, not only scalar metrics.
  - Dynamic temporal relations and distribution shift are recurring concerns in forecasting papers.
  - Existing methods often improve benchmarks while leaving open questions about robustness, data regimes, and mechanism.
  - This motivates experiments that test whether model improvements reflect useful predictive compression rather than blind context expansion.

## Vibe Idea

- Idea id: `vibe_005`
- One-liner: Long-context forecasting should be treated as predictive compression, not raw lookback expansion.
- Core tension: More history can help, but raw supervised models often consume irrelevant context as noise.
- Risk: The idea can collapse into a pooling trick unless the predictive-state claim is tested.

## Pre-Taste Gate

| Dimension | Score |
|---|---:|
| interestingness | 4 |
| non_obviousness | 4 |
| importance | 4 |
| story_potential | 4 |
| experimentability | 4 |
| defensibility | 3 |
| trend_alignment | 4 |
| personal_fit | 4 |

- Total: `31`
- Status: `approved`
- Reason: passes taste gate

## Real Experiment Setup

- Backend: `tsl-simple`
- External benchmark: `Time-Series-Library_simple`
- Dataset: `ETTh1.csv`
- Sequence length: `24`
- Prediction length: `24`
- Training subset ratio: `0.05`
- Training epochs: `1`
- Compared models: `DLinear`, `PatchTST`, `MLP`

## Results

| Run | Model | RMSE | MAE | Baseline RMSE | Delta vs DLinear | Reviewer decision |
|---|---:|---:|---:|---:|---:|---|
| `run_0008` | DLinear | 0.60498005 | 0.38604552 | 0.60498005 | 0.00000000 | `continue` |
| `run_0009` | PatchTST | 0.59777755 | 0.38496944 | 0.60498005 | +0.00720250 | `continue` |
| `run_0010` | MLP | 0.77158123 | 0.56779635 | 0.60498005 | -0.16660118 | `kill` |

## Demo Takeaway

PatchTST produced the best RMSE in this tiny controlled run. The result is not a final scientific claim; it is a validated trajectory showing that the agent can move from literature-grounded ideation to real benchmark execution, metric parsing, taste review, and trajectory update.

## Generated Runtime Artifacts

Each real run generated the same recoverable protocol files:

```text
vibe_idea.yaml
taste_pre.yaml
experiment_plan.yaml
command.sh
stdout.log
stderr.log
metrics.json
taste_post.yaml
review.md
```

The local full report was generated at:

```text
research_state/full_research_demo_report.md
```
