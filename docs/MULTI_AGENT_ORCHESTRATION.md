# Multi-Agent Orchestration

The project includes a deterministic, dependency-free multi-agent orchestration layer for the full research loop. It is intentionally explicit: each role writes recoverable artifacts today, and each role can later be replaced by an LLM-backed worker without changing the external contract.

## Five Role Lanes

| Lane | Purpose | Backing agents |
|---|---|---|
| Planner | Convert literature signals and taste constraints into bounded hypotheses. | `literature_curator`, `idea_scout`, `taste_reviewer`, `experiment_planner` |
| Engineer | Bind hypotheses to model registry entries, schema checks, and code-change boundaries. | `scope_manager`, `code_engineer` |
| Executor | Launch the selected backend and preserve commands, stdout, stderr, and metrics. | `experiment_runner` |
| Evaluator | Check metrics, fairness, leakage risk, post-result taste, and reviewer decisions. | `result_reviewer` |
| Reporter | Convert the trace into a cockpit, dashboard, PDF, and demo packet. | `synthesis_agent`, `reporter_agent` |

## Agent Roles

| Agent | Responsibility | Primary outputs |
|---|---|---|
| `literature_curator` | Build or read the paper-note index and extract compact signals. | `paper_index.jsonl`, `selected_context.md` |
| `idea_scout` | Generate research-direction candidates from topic and literature context. | `vibe_ideas.json` |
| `taste_reviewer` | Score whether an idea deserves benchmark time. | `taste_reviews.json` |
| `scope_manager` | Bind the workflow to approved datasets, baselines, and execution adapters. | `experiment_scope.json`, `assets.json` |
| `code_engineer` | Register baselines/candidates and enforce experiment-schema boundaries. | `baseline_registry.json`, per-run schema files |
| `experiment_planner` | Produce a bounded experiment command and configuration. | `execution_plan` |
| `experiment_runner` | Stage or execute the benchmark path while preserving run artifacts. | `runs/run_XXXX/`, `leaderboard.csv`, `trajectory.jsonl` |
| `result_reviewer` | Convert metrics into constrained next-action decisions. | `review.md`, trajectory action |
| `synthesis_agent` | Summarize the trace and select the next research move. | `multiagent_trace.md` |
| `reporter_agent` | Define the public demo packet boundary. | `research_cockpit.html`, `benchmark_report.pdf`, `demo_packet.json` |

## Main Server Command

Execute the full server demo through the orchestration layer:

```bash
cd /home/xu/ts-auto-research-agent
/home/xu/anaconda3/bin/python -m ts_auto_research.cli multiagent run   --topic forecasting   --paper-source /home/xu/autoresearch-agent/knowledge-base/paper-notes   --literature-limit 1000   --backend tsl-simple   --execute-demo
```

Inspect the latest orchestration trace:

```bash
ts-agent multiagent show
```

Refresh the cockpit and report artifacts:

```bash
ts-agent report
```

## Trace Artifacts

Every orchestration run writes:

```text
research_state/multiagent_trace.json
research_state/multiagent_trace.md
```

The JSON trace contains agent specifications, five role lanes, ordered task results, artifact paths, next actions, and the staged or executed benchmark command.

## Execution Modes

- `dry-run`: builds literature context, proposes ideas, runs the taste gate, checks scope, prepares the experiment plan, and records the runner as ready.
- `execute-demo`: runs the same orchestration, then launches the real `full-research` benchmark study through the runner role.

The default is `dry-run` because planning should be inspectable before spending benchmark time.
