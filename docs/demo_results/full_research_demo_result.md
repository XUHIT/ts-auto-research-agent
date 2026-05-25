# Server Benchmark Research Demo Report

## Demo Goal
Show one rigorous benchmark study: DLinear is the locked baseline, PatchTST is the strong reference, and only literature-grounded candidates can be treated as project innovation.

## Literature Substrate
- Source: `/home/xu/autoresearch-agent/knowledge-base/paper-notes`
- Indexed papers: `1000`

### Representative Literature Signals
- **APT: Affine Prototype-Timestamp For Time Series Forecasting Under Distribution Shift** (AAAI_2026): Prototype or timestamp-conditioned affine structure motivates using known horizon context instead of only local instance statistics.
- **Reversible Instance Normalization for Accurate Time-Series Forecasting Against Distribution Shift** (ICLR_2022): Reversible normalization can help distribution shift, but its lookback-to-horizon statistic assumption must be tested.
- **A Time Series is Worth 64 Words: Long-term Forecasting with Transformers (PatchTST)** (ICLR_2023): Patch-based strong references prevent overstating a DLinear-only improvement.
- **An Analysis of Linear Time Series Forecasting Models** (ICML_2024): Recent linear-model analysis suggests constraints, normalization, and simple residual structure may matter more than adding heavy backbones.
- **SIN: Selective and Interpretable Normalization for Long-Term Time Series Forecasting** (ICML_2024): Selective normalization argues against one fixed statistic for every series and motivates gated lightweight adapters.

## Active Scope
- Scope: `general-ts-two-libs`
- Asset count: `2`
- Note: Active experiment scope: only TSFM_EVAL and Time-Series-Library_simple general time-series benchmark libraries. Ignore domain-specific projects such as CUE-TS and Uniwind for the next automation phase.

## Proposed Vibe Idea
- Idea id: `vibe_065`
- One-liner: A publishable forecasting agent should test one literature-backed residual against a locked DLinear anchor before scaling the search.
- Core tension: DLinear is strong because simple structure matters; a candidate must add a precise mechanism, such as known-horizon calendar context, without hiding inside a large backbone.
- Risk: Could be only a DLinear improvement and not a SOTA claim if PatchTST remains stronger.

## Pre-Taste Gate
- Status: `approved`
- Reason: passes taste gate
- Total score: `31`

## Experiment Setup
- Backend: `tsl-simple`
- Dataset: `ETTh1.csv`
- Sequence length: `24`
- Prediction length: `24`
- Training subset ratio: `0.05`
- Training epochs: `3`
- Baseline rule: `DLinear` is the metric anchor; strong references and innovation candidates are labeled separately.

## Real Experiment Results

| Run | Role | Model | RMSE | MAE | Baseline | Delta | Decision |
|---|---|---|---:|---:|---:|---:|---|
| `run_0051` | `baseline_anchor` | DLinear | 0.59827763 | 0.38131171 | 0.59827763 | 0.0 | `continue` |
| `run_0052` | `strong_reference` | PatchTST | 0.58627319 | 0.37807289 | 0.59827763 | 0.01200444 | `continue` |
| `run_0053` | `innovation_candidate` | CalDLinear | 0.59605795 | 0.38774657 | 0.59827763 | 0.00221968 | `continue` |

## Research Interpretation
The best RMSE in this locked benchmark study is `PatchTST` with RMSE `0.58627319`.
`CalDLinear` is a bounded positive innovation candidate against DLinear: RMSE improves by `0.00221968` under the same protocol.
`PatchTST` remains the stronger reference, so `CalDLinear` is not a SOTA claim; it is a lightweight baseline-improvement signal.
The result is a bounded benchmark claim, not a final paper claim: an innovation candidate must beat DLinear first, then be checked against the strong reference before any larger claim is allowed.

## Next Automated Step
Deepen the accepted candidate with ablations, secondary metrics, and more datasets before turning it into a paper-level claim.
