# Benchmark Demo

The project demo is a server-backed benchmark study, not a collection of small examples. The current delivery target is one ETTh1 forecasting study with DLinear as the baseline anchor, PatchTST as the strong reference, and CalDLinear as the literature-grounded innovation candidate.

## Recommended Command

```bash
cd /home/xu/ts-auto-research-agent
/home/xu/anaconda3/bin/python -m pip install -e .
/home/xu/anaconda3/bin/python -m ts_auto_research.cli multiagent run   --topic forecasting   --paper-source /home/xu/autoresearch-agent/knowledge-base/paper-notes   --literature-limit 1000   --backend tsl-simple   --execute-demo
/home/xu/anaconda3/bin/python -m ts_auto_research.cli report
```

The benchmark command expands to:

```bash
ts-agent demo full-research   --paper-source /home/xu/autoresearch-agent/knowledge-base/paper-notes   --literature-limit 1000   --topic forecasting   --model DLinear   --model PatchTST   --model CalDLinear   --data ETTh1.csv   --seq-len 24   --pred-len 24   --subset-ratio 0.05   --train-epochs 3
```

## What It Shows

- The agent uses the local top-venue paper-note library to build method evidence before running.
- Planner, Engineer, Executor, Evaluator, and Reporter lanes are visible in the trace and cockpit.
- DLinear is locked as the baseline anchor.
- PatchTST is included as a strong reference to prevent overclaiming.
- CalDLinear is evaluated as the project innovation candidate.
- Every run writes protocol files, schema validation, command, stdout/stderr, metrics, taste, and review files.
- RMSE and MAE are parsed from real Time-Series-Library_simple output.
- The reviewer records bounded decisions instead of blindly celebrating metric gain.

## Latest Result

| Run | Role | Model | RMSE | MAE | Delta vs DLinear | Schema | Decision |
|---|---|---|---:|---:|---:|---|---|
| `run_0051` | baseline anchor | DLinear | 0.59827763 | 0.38131171 | 0.00000000 | valid | continue |
| `run_0052` | strong reference | PatchTST | 0.58627319 | 0.37807289 | +0.01200444 | valid | continue |
| `run_0053` | innovation candidate | CalDLinear | 0.59605795 | 0.38774657 | +0.00221968 | valid | continue |

Interpretation: CalDLinear is a bounded positive candidate against DLinear on RMSE, but PatchTST remains stronger. The next step is ablation and broader validation, not a SOTA claim.

## Visual Artifacts

```text
docs/demo_results/research_cockpit.html
docs/demo_results/dashboard.html
docs/demo_results/monitor.html
docs/demo_results/benchmark_report.pdf
docs/demo_results/figures/benchmark_metrics.svg
docs/demo_results/figures/delta_vs_dlinear.svg
docs/demo_results/demo_packet.json
```

`research_cockpit.html` is the main presentation surface. It shows the five role lanes, literature-to-method flow, schema checks, metrics, decisions, and claim strength in one page. The dashboard and monitor are compact metric views, and the PDF is the formal benchmark report.

## Expected Run Artifacts

```text
runs/run_XXXX/vibe_idea.yaml
runs/run_XXXX/taste_pre.yaml
runs/run_XXXX/experiment_plan.yaml
runs/run_XXXX/experiment_schema.json
runs/run_XXXX/schema_validation.json
runs/run_XXXX/protocol_audit.md
runs/run_XXXX/command.sh
runs/run_XXXX/stdout.log
runs/run_XXXX/stderr.log
runs/run_XXXX/metrics.json
runs/run_XXXX/taste_post.yaml
runs/run_XXXX/review.md
```

## Smoke Check

`ts-agent demo public-mini` remains useful for checking install and loop mechanics with bundled assets. It is not the delivery benchmark demo.
