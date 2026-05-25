# Server Benchmark Showcase Snapshot

```text
TS Auto Research Agent - Benchmark Showcase
===========================================
Effect: 1000 paper notes -> locked ETTh1 benchmark -> DLinear baseline 0.59827763 -> CalDLinear improves rmse by 0.00221968. PatchTST remains the stronger reference, so the claim stays bounded.

Novelty:
- DLinear is locked as the baseline anchor; project innovation is labeled separately from baselines.
- Paper-note evidence is written into method cards before the benchmark runs.
- The reviewer can keep a bounded candidate while refusing to call it SOTA when a strong reference still wins.

Use:
- Shows the exact benchmark branch worth deepening and the branch that only clears a weak baseline.
- Records every run as recoverable protocol files for audit and resume.
- Turns local papers, baselines, metrics, and decisions into one reviewable research loop.

Latest benchmark rows:
Run      Role                  Model       Metric      Value       Delta       Decision
run_0048 baseline_anchor       DLinear     rmse       0.59827763 0          continue
run_0049 strong_reference      PatchTST    rmse       0.58627319 0.01200444 continue
run_0050 innovation_candidate  CalDLinear  rmse       0.59605795 0.00221968 continue

Next: Deepen `CalDLinear` with ablations and more datasets before making a paper-level claim.
```
