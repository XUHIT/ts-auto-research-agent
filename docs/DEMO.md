# Presentation Demo

This demo proves the full loop with real Time-Series-Library_simple executions rather than synthetic metrics.

## Command

```bash
cd /home/xu/ts-auto-research-agent
ts-agent demo tsl-simple \
  --model DLinear \
  --model PatchTST \
  --model MLP \
  --data ETTh1.csv \
  --seq-len 24 \
  --pred-len 24 \
  --subset-ratio 0.05 \
  --train-epochs 1
```

## What It Shows

- The agent calls an external time-series benchmark repository.
- Each model run gets the same recoverable protocol files.
- RMSE and MAE are parsed from real experiment output.
- The leaderboard and trajectory are updated with comparable metrics.
- The reviewer keeps promising runs and kills weak ones.

## Expected Artifacts

```text
runs/run_XXXX/
  vibe_idea.yaml
  taste_pre.yaml
  experiment_plan.yaml
  command.sh
  stdout.log
  stderr.log
  metrics.json
  taste_post.yaml
  review.md

research_state/
  leaderboard.csv
  trajectory.jsonl
  tsl_simple_demo_report.md
```

The local report is generated from actual run outputs and is not committed to git.
