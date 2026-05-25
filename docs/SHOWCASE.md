# Benchmark Showcase Interaction

The project should show its value in one screen. The showcase is not a log dump and not a bundle of small examples. It summarizes the latest locked benchmark study: baseline, strong reference, innovation candidate, metric deltas, reviewer decisions, and next action.

```bash
ts-agent showcase
```

## What The User Sees

```text
TS Auto Research Agent - Benchmark Showcase
===========================================
Effect: 1000 paper notes -> locked ETTh1 benchmark -> DLinear baseline 0.59827763 -> CalDLinear improves rmse by 0.00221968. PatchTST remains the stronger reference, so the claim stays bounded.

Novelty:
- DLinear is locked as the baseline anchor; project innovation is labeled separately from baselines.
- Paper-note evidence is written into method cards before the benchmark runs.
- The reviewer can keep a bounded candidate while refusing to call it SOTA when a strong reference still wins.

Latest benchmark rows:
Run      Role                  Model       Metric      Value       Delta       Decision
run_0048 baseline_anchor       DLinear     rmse       0.59827763 0          continue
run_0049 strong_reference      PatchTST    rmse       0.58627319 0.01200444 continue
run_0050 innovation_candidate  CalDLinear  rmse       0.59605795 0.00221968 continue
```

## Design Intent

The first screen makes the research loop legible:

1. The paper library supplies evidence and constraints.
2. DLinear is the locked baseline anchor.
3. PatchTST prevents overclaiming against a weak baseline only.
4. CalDLinear is the current project innovation candidate.
5. The reviewer accepts a bounded signal but explicitly refuses a SOTA claim.

Generated files:

```text
research_state/showcase.json
research_state/showcase.md
```

## Visual Report Command

For the final presentation artifacts, run:

```bash
ts-agent report
```

This writes `dashboard.html`, `monitor.html`, `benchmark_report.pdf`, and SVG figures under `docs/demo_results/`.
