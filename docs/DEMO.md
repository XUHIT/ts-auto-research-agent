# Benchmark Demo

The project demo is a server-backed benchmark study, not a collection of small examples. The current delivery target is one ETTh1 forecasting study with DLinear as the baseline anchor, PatchTST as the strong reference, and CalDLinear as the literature-grounded innovation candidate.

## Recommended Command

```bash
cd /home/xu/ts-auto-research-agent
/home/xu/anaconda3/bin/python -m pip install -e .
ts-agent demo full-research
ts-agent showcase
```

Defaults:

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

## What It Shows

- The agent uses the local top-venue paper-note library to build method evidence before running.
- DLinear is locked as the baseline anchor.
- PatchTST is included as a strong reference to prevent overclaiming.
- CalDLinear is evaluated as the project innovation candidate.
- Every run writes the same recoverable protocol files.
- RMSE and MAE are parsed from real Time-Series-Library_simple output.
- The reviewer records bounded decisions instead of blindly celebrating metric gain.

## Latest Result

| Role | Model | RMSE | MAE | Delta vs DLinear | Decision |
|---|---|---:|---:|---:|---|
| baseline anchor | DLinear | 0.59827763 | 0.38131171 | 0.00000000 | continue |
| strong reference | PatchTST | 0.58627319 | 0.37807289 | +0.01200444 | continue |
| innovation candidate | CalDLinear | 0.59605795 | 0.38774657 | +0.00221968 | continue |

Interpretation: CalDLinear is a bounded positive candidate against DLinear on RMSE, but PatchTST remains stronger. The next step is ablation and broader validation, not a SOTA claim.

## Expected Artifacts

```text
research_state/full_research_demo_report.md
research_state/showcase.md
research_state/leaderboard.csv
research_state/trajectory.jsonl
runs/run_XXXX/experiment_plan.yaml
runs/run_XXXX/metrics.json
runs/run_XXXX/review.md
```

## Smoke Check

`ts-agent demo public-mini` remains useful for checking install and loop mechanics with bundled assets. It is not the delivery benchmark demo.
