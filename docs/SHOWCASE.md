# Showcase Interaction

The project should make its effect visible in one screen. The command below converts the current run state into a compact card that explains what happened, what is new, why it is useful, and what should happen next.

```bash
ts-agent showcase
```

## What The User Sees

```text
TS Auto Research Agent - Showcase
=================================
Effect: 50 paper notes -> taste-gated idea -> 3 real experiment runs -> PatchTST improved rmse by 0.0072025.

Novelty:
- Research taste gates before and after experiments, not just metric chasing.
- Role-based agent orchestration creates an inspectable research trajectory.
- Server paper notes guide ideas while real benchmark runs decide what survives.

Use:
- Shows which forecasting branch deserves continuation.
- Records every run as recoverable protocol files for audit and resume.
- Turns local papers, baselines, metrics, and decisions into one reviewable loop.
```

## Generated Files

```text
research_state/showcase.json
research_state/showcase.md
```

## Design Intent

The showcase is not another log dump. It is the first-screen story:

1. Evidence source: paper notes.
2. Research judgment: taste gate.
3. Real action: benchmark runs.
4. Outcome: metric delta and reviewer decision.
5. Next step: the branch to continue or kill.

This makes the agent understandable to someone who does not want to inspect every protocol file first.
