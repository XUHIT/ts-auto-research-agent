# Server Benchmark Demo Result

This is the public-safe snapshot of the latest server-backed benchmark study. The raw runtime files stay under `research_state/` and `runs/` on the experiment machine.

## Command

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

## End-to-End Flow

```mermaid
flowchart LR
  A[Top-venue paper notes] --> B[Literature evidence]
  B --> C[Vibe idea]
  C --> D[Pre-taste gate]
  D --> E[Method-role experiment plans]
  E --> F[Time-Series-Library_simple runs]
  F --> G[Metric parser]
  G --> H[Post-taste review]
  H --> I[Leaderboard and trajectory]
  I --> J[Benchmark showcase]
```

## Literature Signals Used

- APT: timestamp/prototype affine structure motivates known-horizon context.
- RevIN: reversible normalization helps distribution shift but has assumptions.
- PatchTST: patch-based strong references prevent overclaiming.
- LinearAnalysis: simple linear constraints and residual structure can matter more than heavy backbones.
- SIN: selective normalization motivates adaptive lightweight adapters.

## Benchmark Setup

- Dataset: `ETTh1.csv`
- Sequence length: `24`
- Prediction length: `24`
- Training subset ratio: `0.05`
- Training epochs: `3`
- Primary metric: `RMSE`
- Secondary metric: `MAE`

## Results

| Run | Role | Model | RMSE | MAE | Baseline | Delta | Decision |
|---|---|---|---:|---:|---:|---:|---|
| `run_0048` | `baseline_anchor` | `DLinear` | `0.59827763` | `0.38131171` | `0.59827763` | `0.0` | `continue` |
| `run_0049` | `strong_reference` | `PatchTST` | `0.58627319` | `0.37807289` | `0.59827763` | `0.01200444` | `continue` |
| `run_0050` | `innovation_candidate` | `CalDLinear` | `0.59605795` | `0.38774657` | `0.59827763` | `0.00221968` | `continue` |

## Takeaway

CalDLinear improves RMSE over DLinear by `0.00221968`, so it is worth continuing as a bounded lightweight candidate. PatchTST remains stronger, so this is not a SOTA claim. The next agent step is ablation and broader validation.
