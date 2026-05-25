# Multi-Agent Orchestration

The project includes a role-based orchestration layer for the full research loop. The first version is deterministic and dependency-free so it can be tested, versioned, and demonstrated without external services. Each role can later be replaced by an LLM-backed implementation while keeping the same artifacts and contracts.

## Agent Roles

| Agent | Responsibility | Primary outputs |
|---|---|---|
| `literature_curator` | Build or read the paper-note index and extract compact signals. | `paper_index.jsonl`, `selected_context.md` |
| `idea_scout` | Generate research-direction candidates from topic and literature context. | `vibe_ideas.json` |
| `taste_reviewer` | Score whether an idea deserves benchmark time. | `taste_reviews.json` |
| `scope_manager` | Bind the workflow to approved datasets, baselines, and execution adapters. | `experiment_scope.json`, `assets.json` |
| `experiment_planner` | Produce a bounded experiment command and configuration. | `execution_plan` |
| `experiment_runner` | Stage or execute the benchmark path while preserving run artifacts. | `runs/run_XXXX/`, `leaderboard.csv`, `trajectory.jsonl` |
| `result_reviewer` | Convert metrics into constrained next-action decisions. | `review.md`, trajectory action |
| `synthesis_agent` | Summarize the trace and select the next research move. | `multiagent_trace.md` |

## Command

Stage the complete orchestration without launching the real benchmark:

```bash
ts-agent multiagent run \
  --topic forecasting \
  --paper-source /home/xu/autoresearch-agent/knowledge-base/paper-notes \
  --literature-limit 50 \
  --model DLinear \
  --model PatchTST \
  --model MLP
```

Inspect the latest orchestration trace:

```bash
ts-agent multiagent show
```

Execute the real full-research demo through the runner role:

```bash
ts-agent multiagent run \
  --topic forecasting \
  --paper-source /home/xu/autoresearch-agent/knowledge-base/paper-notes \
  --model DLinear \
  --model PatchTST \
  --model MLP \
  --execute-demo
```

## Trace Artifacts

Every orchestration run writes:

```text
research_state/multiagent_trace.json
research_state/multiagent_trace.md
```

The JSON trace contains:

- Agent specifications.
- Ordered task results.
- Status for each role.
- Artifact paths.
- Next actions.
- The staged or executed benchmark command.

The Markdown trace is a public-readable recovery summary for demos and reviews.

## Execution Modes

- `dry-run`: builds literature context, proposes ideas, runs the taste gate, checks scope, prepares the experiment plan, and records the runner as ready.
- `execute-demo`: runs the same orchestration, then launches the real `full-research` demo through the runner role.

The default is `dry-run` because multi-agent planning should be inspectable before spending benchmark time.

## Extension Path

The orchestration module exposes a stable role boundary:

```python
from ts_auto_research.multiagent import run_research_crew
```

Future upgrades can replace a deterministic role with an LLM-backed worker as long as the worker returns the same task result shape:

- `agent_id`
- `status`
- `summary`
- `artifacts`
- `next_actions`
- `data`

This keeps the public protocol stable while allowing stronger reasoning, tool calling, memory, and delegation inside each role.
