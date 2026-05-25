# Architecture

`ts-auto-research-agent` is built around one principle: an autonomous research agent should spend compute only when an experiment can change a research belief.

## Core Layers

1. Metric trajectory inner loop
   - Maintains metric-driven experiment trajectory.
   - Runs bounded experiment budgets.
   - Updates `research_state/leaderboard.csv` and `research_state/trajectory.jsonl` after every run.
   - Queues follow-up variants when a result is worth continuing.

2. Multi-agent orchestration layer
   - Splits the research loop into explicit roles: literature curator, idea scout, taste reviewer, scope manager, experiment planner, experiment runner, result reviewer, and synthesis agent.
   - Writes `research_state/multiagent_trace.json` and `research_state/multiagent_trace.md` so orchestration is inspectable and resumable.
   - Starts as a deterministic local protocol and can later swap individual roles for LLM-backed agents without changing the run artifacts.

3. Recoverable research protocol
   - Every run is recoverable from files under `runs/run_XXXX/`.
   - Required protocol files are generated every time: `vibe_idea.yaml`, `taste_pre.yaml`, `experiment_plan.yaml`, `command.sh`, `metrics.json`, `taste_post.yaml`, and `review.md`.
   - Reviewer decisions are constrained to `continue`, `kill`, `pivot`, or `needs_human_confirmation`.

4. Time-series literature substrate
   - The paper-note index is read-only input.
   - It provides idea context, baseline hints, novelty warnings, and venue/taste signals.
   - It does not import or reuse the old time-series agent workflow code.

5. Vibe/taste layer
   - Pre-run taste scores decide whether an idea deserves an experiment.
   - Post-run taste evaluates whether the result changes belief, contains surprise, or supports a claim.
   - This prevents the loop from becoming blind hyperparameter search.

6. External asset substrate
   - Server-side papers, datasets, baseline repositories, checkpoints, scripts, and environments are discovered into a local runtime registry.
   - The core agent stores asset IDs and adapters, not copied data or external code.

## Runtime State

```text
research_state/
  state.json
  state.yaml
  vibe_ideas.json
  vibe_ideas.yaml
  taste_reviews.json
  taste_reviews.yaml
  experiment_queue.json
  experiment_queue.yaml
  leaderboard.csv
  trajectory.jsonl
  multiagent_trace.json
  multiagent_trace.md
  claims.json
  claims.yaml

runs/run_0001/
  vibe_idea.yaml
  taste_pre.yaml
  experiment_plan.yaml
  command.sh
  stdout.log
  metrics.json
  taste_post.yaml
  review.md
```

## Backend Contract

A backend returns two artifacts:

- `metrics`: structured JSON with status, metric value, baseline, delta, wall time, and diagnostics.
- `stdout`: human-readable execution log stored as `stdout.log`.

Current backends:

- `smoke`: deterministic synthetic runner for loop validation.
- `dlinear-mini`: minimal CSV time-series benchmark using a last-value baseline and a lightweight trend/residual forecaster.

## Extension Points

- Add a backend in `src/ts_auto_research/runners.py`.
- Add CLI flags in `src/ts_auto_research/cli.py` if the backend needs data paths or model knobs.
- Keep backend output compatible with `metrics.json`; the loop, reviewer, leaderboard, and trajectory will continue working.
