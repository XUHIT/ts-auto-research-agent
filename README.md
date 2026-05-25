# TS Auto Research Agent

`ts-auto-research-agent` is a clean-room time-series autonomous research agent for a server-backed research loop. It does not treat a demo as a collection of small examples. The main demo is a single locked benchmark study with a baseline, a strong reference, a literature-grounded innovation candidate, real metrics, review decisions, and recoverable run artifacts.

## At A Glance

Latest validated server benchmark on ETTh1, `seq_len=24`, `pred_len=24`, `subset_ratio=0.05`, `train_epochs=3`:

```text
1000 paper notes -> locked ETTh1 benchmark -> DLinear baseline -> literature-grounded candidate
DLinear   role=baseline_anchor       RMSE 0.59827763  MAE 0.38131171
PatchTST  role=strong_reference      RMSE 0.58627319  MAE 0.37807289
CalDLinear role=innovation_candidate RMSE 0.59605795  MAE 0.38774657
Result: CalDLinear improves RMSE over DLinear by 0.00221968, but PatchTST remains stronger.
Conclusion: bounded positive candidate, not a SOTA claim yet.
```

Run the one-screen benchmark interaction:

```bash
cd /home/xu/ts-auto-research-agent
ts-agent demo full-research
ts-agent showcase
```

## What Counts As The Demo

The project demo is the server-backed benchmark study above. It must include:

- A locked benchmark dataset and protocol: ETTh1, fixed horizon, fixed budget, fixed metric.
- DLinear as the baseline anchor.
- A strong reference arm, currently PatchTST, so the system cannot overclaim against DLinear only.
- A literature-grounded innovation candidate, currently CalDLinear.
- Pre-run taste review, experiment protocol files, metrics, post-run review, leaderboard, and trajectory.
- A bounded interpretation that states what the candidate proves and what it does not prove.

`ts-agent demo public-mini` is only a smoke check for the loop mechanics. It is not the project delivery demo.

## Target Server Quick Start

The primary delivery target is the A20CPolar server, not an arbitrary clean machine. The validated benchmark uses the server GPU, the server paper-note knowledge base, and the local Time-Series-Library_simple benchmark repository.

```bash
cd /home/xu/ts-auto-research-agent
/home/xu/anaconda3/bin/python -m pip install -e .
ts-agent demo full-research
ts-agent showcase
```

Default server inputs:

- Paper notes: `/home/xu/autoresearch-agent/knowledge-base/paper-notes`
- Benchmark repo: `/home/xu/pytorch_projects/my_time_series_lab/Time-Series-Library_simple`
- Dataset: `ETTh1.csv`
- Models: `DLinear`, `PatchTST`, `CalDLinear`
- Epochs: `3`
- Literature index limit: `1000`

## Core Commands

- `ts-agent init`: create `research_state/`, `runs/`, and `literature/` runtime files.
- `ts-agent literature build-index`: build a read-only paper-note index.
- `ts-agent vibe propose`: generate research-direction ideas from topic and literature context.
- `ts-agent taste review`: score an idea before experiment planning.
- `ts-agent demo full-research`: run the server benchmark study.
- `ts-agent showcase`: print a one-screen benchmark effect, novelty, usefulness, and next action.
- `ts-agent multiagent run/show`: run and inspect the role-based orchestration trace.
- `ts-agent leaderboard`: print the experiment leaderboard.
- `ts-agent demo public-mini`: run a bundled smoke check only.

## Runtime Protocol

Each benchmark run writes:

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
  review.json
```

Global trajectory files:

```text
research_state/leaderboard.csv
research_state/trajectory.jsonl
research_state/vibe_ideas.yaml
research_state/taste_reviews.yaml
research_state/multiagent_trace.json
research_state/showcase.md
```

## Current Method Card

The candidate implementation is included for review at `integrations/time_series_library_simple/models/CalDLinear.py`. The target server Time-Series-Library_simple working tree has the same model registered for the validated benchmark.

`CalDLinear` keeps DLinear as the raw forecasting anchor and adds a small future-calendar residual. The candidate is motivated by the paper-note library signals around timestamp/prototype affine structure, reversible and selective normalization, linear-model analysis, and PatchTST as a strong reference.

Acceptance rule:

- It may continue only if it beats DLinear under the locked protocol.
- It is not a SOTA claim unless it also beats the strong reference.
- Current status: positive against DLinear on RMSE, weaker than PatchTST, needs ablations and more datasets.

## Validation

```bash
/home/xu/anaconda3/bin/python -m compileall src tests
/home/xu/anaconda3/bin/python -m unittest discover -s tests -v
ts-agent demo full-research
ts-agent showcase
```

## Design Docs

- `docs/ARCHITECTURE.md`: system layers, state layout, and backend contract.
- `docs/PROTOCOL.md`: experiment protocol, taste gates, and reviewer outputs.
- `docs/ASSET_INTEGRATION.md`: how server-side papers, data, baselines, checkpoints, and environments enter the agent.
- `docs/MULTI_AGENT_ORCHESTRATION.md`: role-based agent orchestration and trace files.
- `docs/SERVER_ENVIRONMENT.md`: target GPU, conda, CUDA, paths, and active scope.
- `docs/SERVER_CLOSED_LOOP_DEMO.md`: validated server benchmark and latest metrics.
- `docs/SHOWCASE.md`: first-screen benchmark showcase.
- `docs/PUBLIC_DEMO.md`: optional smoke check.

## License

MIT.
