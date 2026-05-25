# Presentation Demo

## Public Mini Demo

The portable demo is the recommended first run for outside users:

```bash
python -m pip install -e .
ts-agent demo public-mini
```

It uses only bundled paper notes and `examples/sample_series.csv`, then writes `research_state/public_mini_demo_report.md` and `research_state/multiagent_trace.md`.

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

## Full Research Demo

The full demo exercises every major agent stage:

1. Build a paper-note index.
2. Propose a literature-grounded idea.
3. Run the pre-taste gate.
4. Generate recoverable experiment plans.
5. Execute real Time-Series-Library_simple runs.
6. Parse RMSE and MAE.
7. Generate post-taste review decisions.
8. Update leaderboard and trajectory.
9. Write a presentation report.

```bash
cd /home/xu/ts-auto-research-agent
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

Expected local report:

```text
research_state/full_research_demo_report.md
```

This is the recommended presentation artifact because it shows the agent as a complete research workflow, not just an experiment runner.

## Published Demo Result

A public-safe snapshot of the completed full research demo is committed under:

```text
docs/demo_results/full_research_demo_result.md
docs/demo_results/leaderboard_excerpt.csv
docs/demo_results/run_artifacts_tree.txt
```

The snapshot shows the final effect of the complete demo while keeping raw runtime state local.
