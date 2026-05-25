# External Asset Integration

The agent treats server-side research assets as external resources. It does not copy datasets, checkpoints, old workflows, or private experiment code into the public repository.

## Resource Layers

1. Asset registry
   - Discovers papers, datasets, benchmark repositories, checkpoints, experiment scripts, and conda-style environments.
   - Stores local paths in `research_state/assets.json` and `research_state/assets.yaml`.
   - Runtime asset files are ignored by git.

2. Dataset registry
   - Converts discovered dataset paths into named benchmark candidates.
   - Planner can choose a dataset by asset ID.
   - Backends receive concrete paths only at run time.

3. External backend adapter
   - Wraps an existing baseline repository or benchmark script as a backend.
   - Executes commands in that repository without importing its workflow into the agent core.
   - Captures stdout, stderr, return code, wall time, and produced metric files.

4. Metric parser
   - Normalizes external results into the same `metrics.json` contract used by `smoke` and `dlinear-mini`.
   - Keeps the leaderboard and trajectory format stable across all backends.

5. Checkpoint registry
   - Records available pretrained models and checkpoints.
   - Backends can use checkpoint asset IDs for evaluation or fine-tuning.

## Commands

Scan local assets:

```bash
ts-agent assets scan \
  --scan-root /path/to/paper-or-code-or-data \
  --scan-root /path/to/another-root \
  --max-depth 4 \
  --limit 1000
```

List discovered assets:

```bash
ts-agent assets list
ts-agent assets list --kind baseline_repo
ts-agent assets list --adapter dataset_registry
```

## Experiment Flow With External Assets

1. `assets scan` discovers resources and writes `research_state/assets.json`.
2. Vibe/taste proposes and filters research ideas.
3. Planner chooses asset IDs for dataset, baseline, checkpoint, and environment.
4. Backend adapter runs an external command in the external repo.
5. Metric parser converts raw results into `runs/run_XXXX/metrics.json`.
6. Leaderboard and trajectory update exactly like internal backends.

## Design Boundary

The agent owns orchestration, taste, planning, metric normalization, trajectory, and review.

External assets own raw data, baseline code, pretrained weights, and specialized benchmark scripts.

## Active Scope

Before running automated experiments, set an active scope. The current recommended first phase is to use only general-purpose time-series benchmark libraries and exclude domain-specific standalone projects.

Example:

```bash
ts-agent scope set \
  --name general-ts-two-libs \
  --asset-id <tsfm-eval-baseline-repo-id> \
  --asset-id <time-series-library-simple-baseline-repo-id>

ts-agent scope show
```

This keeps the research loop focused on common model/data/benchmark surfaces instead of drifting into specialized project code.
