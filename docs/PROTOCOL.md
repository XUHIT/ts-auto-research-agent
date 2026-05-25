# Research Protocol

The project protocol is designed for a time-series forecasting research loop where an agent must move from literature context to idea, experiment design, code-bound execution, result review, and report artifacts without losing reproducibility.

## One Experiment Round

1. Build or read the paper-note index.
2. Propose or select a `vibe_idea`.
3. Run the pre-taste gate.
4. Build a structured experiment schema.
5. Validate dataset, horizon, metric, seed, baseline, ablation, and leakage policy.
6. Execute one backend run.
7. Parse metrics and update the leaderboard.
8. Run post-taste review.
9. Emit a strict reviewer decision.
10. Queue a follow-up only when the reviewer says `continue`.

## Experiment Schema

Every executable run now writes:

```text
runs/run_XXXX/experiment_schema.json
runs/run_XXXX/experiment_schema.yaml
runs/run_XXXX/schema_validation.json
runs/run_XXXX/schema_validation.yaml
runs/run_XXXX/protocol_audit.md
```

The schema records:

- `dataset`: dataset name, feature mode, target, `seq_len`, `label_len`, `pred_len`, subset ratio, split policy.
- `model`: model name, role, claim, and code/config change summary.
- `baseline`: DLinear anchor, resolved anchor metric, strong reference, and controls.
- `evaluation`: metric, optimization direction, seed, epochs, batch size, learning rate, patience, timeout.
- `ablation`: minimum ablation grid required for innovation candidates.
- `leakage_policy`: chronological split, known future covariate rules, and metric visibility rules.

## Fairness And Leakage Checks

The validator checks:

- Locked dataset and horizon.
- Locked metric and optimization direction.
- Recorded seed and execution budget.
- Declared baseline anchor.
- Chronological split policy.
- No future target values in known future covariates.
- Metrics are read only after command execution.

A run with missing required fields is marked `invalid`; a run with non-blocking caveats is marked `warning`; a clean run is marked `valid`.

## Pre-Taste Gate

Scores are 1-5:

- `interestingness`
- `non_obviousness`
- `importance`
- `story_potential`
- `experimentability`
- `defensibility`
- `trend_alignment`
- `personal_fit`

Default blocking rules:

- `interestingness < 3`: do not run.
- `non_obviousness < 3`: do not run.
- `experimentability < 3`: defer.
- `defensibility < 3`: strengthen the defense before running.

## Post-Taste Review

Post-taste asks:

- Did the result change belief?
- Was there surprise?
- Can this support a claim?
- Should the next step deepen, broaden, kill, pivot, or ask a human?

The final reviewer output is always one of:

- `continue`
- `kill`
- `pivot`
- `needs_human_confirmation`

## Scope Gate

Every automated experiment should use assets from the active scope. If a proposed run needs an asset outside the scope, the reviewer should return `needs_human_confirmation` before any command is executed.
