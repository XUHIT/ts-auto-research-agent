"""Lightweight multi-agent orchestration for the research workflow.

The first implementation is deliberately deterministic and dependency-free.
It gives the project a stable role/task protocol today, while leaving a clean
boundary for replacing individual roles with LLM-backed agents later.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import shlex
from typing import Any

from .io_utils import read_json, write_json
from .literature import build_index, read_index
from .methods import default_full_research_models
from .paths import Workspace
from .scope import get_scope, scoped_assets
from .state import init_workspace, utc_now
from .taste import get_pre_taste, review_idea
from .vibe import propose_vibes


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    role: str
    responsibility: str
    tools: tuple[str, ...]
    outputs: tuple[str, ...]


@dataclass(frozen=True)
class AgentTaskResult:
    agent_id: str
    role: str
    status: str
    summary: str
    artifacts: tuple[str, ...]
    next_actions: tuple[str, ...]
    started_at: str
    finished_at: str
    data: dict[str, Any]


AGENT_SPECS: tuple[AgentSpec, ...] = (
    AgentSpec(
        agent_id="literature_curator",
        role="Literature Curator",
        responsibility="Convert read-only paper notes into compact signals for ideas, baselines, novelty warnings, and venue taste.",
        tools=("literature.build-index", "literature.read-index"),
        outputs=("paper_index.jsonl", "selected_context.md"),
    ),
    AgentSpec(
        agent_id="idea_scout",
        role="Idea Scout",
        responsibility="Generate research-direction candidates before any benchmark execution is planned.",
        tools=("vibe.propose",),
        outputs=("vibe_ideas.json",),
    ),
    AgentSpec(
        agent_id="taste_reviewer",
        role="Taste Reviewer",
        responsibility="Score whether an idea is interesting, non-obvious, defensible, and experimentally meaningful.",
        tools=("taste.review",),
        outputs=("taste_reviews.json",),
    ),
    AgentSpec(
        agent_id="scope_manager",
        role="Scope Manager",
        responsibility="Bind the research loop to approved datasets, baselines, environments, and execution adapters.",
        tools=("scope.show", "assets.list"),
        outputs=("experiment_scope.json", "assets.json"),
    ),
    AgentSpec(
        agent_id="experiment_planner",
        role="Experiment Planner",
        responsibility="Translate the accepted idea into a bounded, reproducible experiment command.",
        tools=("demo.full-research", "loop.run-next"),
        outputs=("execution_plan",),
    ),
    AgentSpec(
        agent_id="experiment_runner",
        role="Experiment Runner",
        responsibility="Execute or stage the planned benchmark while preserving run artifacts and logs.",
        tools=("backend.tsl-simple", "backend.dlinear-mini", "backend.smoke"),
        outputs=("runs/run_XXXX", "leaderboard.csv", "trajectory.jsonl"),
    ),
    AgentSpec(
        agent_id="result_reviewer",
        role="Result Reviewer",
        responsibility="Constrain post-result decisions to continue, kill, pivot, or needs_human_confirmation.",
        tools=("review-last", "leaderboard"),
        outputs=("review.md", "trajectory action"),
    ),
    AgentSpec(
        agent_id="synthesis_agent",
        role="Synthesis Agent",
        responsibility="Turn the trace into the next concrete research move and demo narrative.",
        tools=("multiagent.trace",),
        outputs=("multiagent_trace.md",),
    ),
)


def _spec(agent_id: str) -> AgentSpec:
    for spec in AGENT_SPECS:
        if spec.agent_id == agent_id:
            return spec
    raise KeyError(f"Unknown agent id: {agent_id}")


def _result(
    agent_id: str,
    status: str,
    summary: str,
    artifacts: list[str] | None = None,
    next_actions: list[str] | None = None,
    data: dict[str, Any] | None = None,
) -> AgentTaskResult:
    spec = _spec(agent_id)
    started_at = utc_now()
    finished_at = utc_now()
    return AgentTaskResult(
        agent_id=spec.agent_id,
        role=spec.role,
        status=status,
        summary=summary,
        artifacts=tuple(artifacts or []),
        next_actions=tuple(next_actions or []),
        started_at=started_at,
        finished_at=finished_at,
        data=data or {},
    )


def _contains_tsl_simple(asset: dict[str, Any]) -> bool:
    hay = " ".join(str(asset.get(key, "")) for key in ["id", "name", "path"]).lower().replace("_", "-")
    return "time-series-library-simple" in hay or "time-series-library" in hay


def _artifact(path: Path) -> str:
    return str(path)


def _quote_command(parts: list[str | int | float]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def _execution_command(
    backend: str,
    paper_source: Path | None,
    topic: str,
    models: list[str],
    data: str,
    data_csv: str | None,
    column: str | None,
    seq_len: int,
    pred_len: int,
    subset_ratio: float,
    train_epochs: int,
    literature_limit: int,
    budget: int,
) -> str:
    if backend == "tsl-simple":
        parts: list[str | int | float] = [
            "ts-agent",
            "demo",
            "full-research",
            "--topic",
            topic,
            "--literature-limit",
            literature_limit,
            "--data",
            data,
            "--seq-len",
            seq_len,
            "--pred-len",
            pred_len,
            "--subset-ratio",
            subset_ratio,
            "--train-epochs",
            train_epochs,
        ]
        if paper_source is not None:
            parts.extend(["--paper-source", str(paper_source)])
        for model in models:
            parts.extend(["--model", model])
        return _quote_command(parts)

    parts = ["ts-agent", "loop", "--budget", budget, "--backend", backend, "--topic", topic]
    if data_csv:
        parts.extend(["--data-csv", data_csv])
    if column:
        parts.extend(["--column", column])
    return _quote_command(parts)


def _summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts: dict[str, int] = {}
    best: dict[str, Any] | None = None
    for item in results:
        metrics = item.get("metrics", {})
        review = item.get("review", {})
        decision = str(review.get("decision", "unknown"))
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        value = metrics.get("metric_value")
        if value is None:
            continue
        diagnostics = metrics.get("diagnostics", {})
        model = diagnostics.get("model") or metrics.get("backend", "unknown")
        candidate = {"model": model, "metric_value": float(value), "run_id": item.get("run", {}).get("run_id")}
        if best is None or candidate["metric_value"] < best["metric_value"]:
            best = candidate
    return {"decision_counts": decision_counts, "best": best}


def run_research_crew(
    workspace: Workspace,
    topic: str = "forecasting",
    paper_source: Path | None = None,
    literature_limit: int = 1000,
    models: list[str] | None = None,
    data: str = "ETTh1.csv",
    data_csv: str | None = None,
    column: str | None = None,
    seq_len: int = 24,
    pred_len: int = 24,
    subset_ratio: float = 0.05,
    train_epochs: int = 3,
    backend: str = "tsl-simple",
    budget: int = 1,
    execute_demo: bool = False,
) -> dict[str, Any]:
    """Run the role-based orchestration protocol and write a trace.

    By default this stages the full research demo without executing expensive
    benchmarks. Pass ``execute_demo=True`` to let the runner role execute the
    selected backend and register run artifacts.
    """
    init_workspace(workspace)
    models = models or default_full_research_models()
    task_results: list[AgentTaskResult] = []
    created_at = utc_now()
    run_id = "crew_" + created_at.replace(":", "").replace("-", "").split(".")[0]

    if paper_source is not None:
        literature_result = build_index(workspace, paper_source, limit=literature_limit)
        literature_summary = f"Indexed {literature_result['count']} paper notes for topic `{topic}`."
    else:
        records_before = read_index(workspace, limit=None)
        literature_result = {"source": "existing_index", "count": len(records_before), "output": str(workspace.paper_index)}
        literature_summary = f"Using existing paper index with {len(records_before)} records."
    literature_records = read_index(workspace, limit=1000)
    task_results.append(
        _result(
            "literature_curator",
            "completed",
            literature_summary,
            artifacts=[_artifact(workspace.paper_index), _artifact(workspace.selected_context)],
            next_actions=["Pass compact literature signals to the idea scout."],
            data={
                "source": literature_result.get("source"),
                "count": literature_result.get("count"),
                "representative_titles": [record.get("title", "untitled") for record in literature_records[:5]],
            },
        )
    )

    ideas = propose_vibes(workspace, topic=topic, count=3)
    selected_idea = ideas[0]
    task_results.append(
        _result(
            "idea_scout",
            "completed",
            f"Proposed {len(ideas)} research ideas and selected `{selected_idea['id']}` for the next gate.",
            artifacts=[_artifact(workspace.vibe_json), _artifact(workspace.vibe_yaml)],
            next_actions=["Score the selected idea before allocating benchmark time."],
            data={
                "selected_idea_id": selected_idea["id"],
                "selected_one_liner": selected_idea.get("one_liner"),
                "candidate_ids": [idea["id"] for idea in ideas],
            },
        )
    )

    taste = get_pre_taste(workspace, selected_idea["id"]) or review_idea(workspace, selected_idea["id"])
    taste_status = str(taste.get("status", "unknown"))
    task_results.append(
        _result(
            "taste_reviewer",
            "completed" if taste_status == "approved" else "attention_required",
            f"Pre-run taste gate returned `{taste_status}` with total score `{taste.get('total')}`.",
            artifacts=[_artifact(workspace.taste_json), _artifact(workspace.taste_yaml)],
            next_actions=["Plan a bounded experiment." if taste_status == "approved" else "Improve the defense before expensive execution."],
            data={"status": taste_status, "reason": taste.get("reason"), "scores": taste.get("scores", {})},
        )
    )

    scope = get_scope(workspace)
    assets = scoped_assets(workspace)
    tsl_assets = [asset for asset in assets if _contains_tsl_simple(asset)]
    if backend == "tsl-simple":
        scope_status = "completed" if tsl_assets else "attention_required"
        scope_summary = (
            f"Active scope `{scope.get('name', 'default')}` contains {len(assets)} assets; Time-Series-Library_simple adapter is available."
            if tsl_assets
            else f"Active scope `{scope.get('name', 'default')}` contains {len(assets)} assets; staged plan assumes the `tsl-simple` adapter is configured before execution."
        )
    else:
        scope_status = "completed"
        scope_summary = f"Backend `{backend}` uses bundled or user-provided inputs and does not require an external repository scope."
    task_results.append(
        _result(
            "scope_manager",
            scope_status,
            scope_summary,
            artifacts=[_artifact(workspace.scope_json), _artifact(workspace.assets_json)],
            next_actions=["Use the active scope to bind the experiment command."],
            data={
                "scope_name": scope.get("name", "default"),
                "asset_count": len(assets),
                "selected_backend": backend,
                "tsl_asset_ids": [asset.get("id") for asset in tsl_assets],
            },
        )
    )

    command = _execution_command(
        backend=backend,
        paper_source=paper_source,
        topic=topic,
        models=models,
        data=data,
        data_csv=data_csv,
        column=column,
        seq_len=seq_len,
        pred_len=pred_len,
        subset_ratio=subset_ratio,
        train_epochs=train_epochs,
        literature_limit=literature_limit,
        budget=budget,
    )
    execution_plan = {
        "backend": backend,
        "topic": topic,
        "idea_id": selected_idea["id"],
        "models": models,
        "data": data,
        "data_csv": data_csv,
        "column": column,
        "seq_len": seq_len,
        "pred_len": pred_len,
        "subset_ratio": subset_ratio,
        "train_epochs": train_epochs,
        "budget": budget,
        "command": command,
        "execute_demo": execute_demo,
    }
    task_results.append(
        _result(
            "experiment_planner",
            "completed",
            f"Prepared a bounded `{backend}` plan with budget `{budget}`.",
            artifacts=["execution_plan"],
            next_actions=["Run the staged command." if execute_demo else "Review the plan or rerun with --execute-demo."],
            data=execution_plan,
        )
    )

    demo_result: dict[str, Any] | None = None
    if execute_demo and backend == "tsl-simple":
        from .demo import run_full_research_demo

        demo_result = run_full_research_demo(
            workspace,
            paper_source=paper_source or Path("/home/xu/autoresearch-agent/knowledge-base/paper-notes"),
            topic=topic,
            models=models,
            data=data,
            seq_len=seq_len,
            pred_len=pred_len,
            subset_ratio=subset_ratio,
            train_epochs=train_epochs,
            literature_limit=literature_limit,
        )
    elif execute_demo:
        from .loop import run_loop_budget

        demo_result = {
            "results": run_loop_budget(
                workspace,
                budget=budget,
                backend=backend,
                topic=topic,
                data_csv=data_csv,
                column=column,
            ),
            "report_path": None,
        }

    if demo_result is not None:
        run_ids = [item["run"]["run_id"] for item in demo_result.get("results", [])]
        artifacts = [str(workspace.run_dir(run_id)) for run_id in run_ids]
        if demo_result.get("report_path"):
            artifacts.append(str(demo_result["report_path"]))
        task_results.append(
            _result(
                "experiment_runner",
                "completed",
                f"Executed the staged `{backend}` plan and produced {len(run_ids)} run directories.",
                artifacts=artifacts,
                next_actions=["Review metric trajectory and post-run decisions."],
                data={"run_ids": run_ids, "report_path": demo_result.get("report_path")},
            )
        )
    else:
        task_results.append(
            _result(
                "experiment_runner",
                "ready",
                "Execution was staged but not run; use --execute-demo to launch the selected backend.",
                artifacts=[_artifact(workspace.multiagent_trace_json), _artifact(workspace.multiagent_trace_md)],
                next_actions=[command],
                data={"dry_run": True, "command": command},
            )
        )

    if demo_result:
        result_summary = _summarize_results(demo_result.get("results", []))
        best = result_summary.get("best")
        best_text = f" Best metric: `{best['model']}` with value `{best['metric_value']}`." if best else ""
        task_results.append(
            _result(
                "result_reviewer",
                "completed",
                f"Reviewed executed runs with decision counts {result_summary['decision_counts']}.{best_text}",
                artifacts=[_artifact(workspace.leaderboard_csv), _artifact(workspace.trajectory_jsonl)],
                next_actions=["Continue the best trajectory or kill weak branches."],
                data=result_summary,
            )
        )
    else:
        task_results.append(
            _result(
                "result_reviewer",
                "pending",
                "No new metrics were generated in dry-run mode; review will run after execution.",
                artifacts=[_artifact(workspace.leaderboard_csv), _artifact(workspace.trajectory_jsonl)],
                next_actions=["Execute the plan to populate reviewer decisions."],
                data={"pending_execution": True},
            )
        )

    synthesis_next = "Execute the prepared demo command and publish the resulting public-safe demo snapshot."
    if demo_result:
        synthesis_next = f"Use the reviewed leaderboard to select the next bounded `{backend}` experiment branch."
    task_results.append(
        _result(
            "synthesis_agent",
            "completed",
            "Compiled the multi-agent trace into a recoverable orchestration artifact.",
            artifacts=[_artifact(workspace.multiagent_trace_json), _artifact(workspace.multiagent_trace_md)],
            next_actions=[synthesis_next],
            data={"next_research_move": synthesis_next},
        )
    )

    trace = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": created_at,
        "mode": "execute-demo" if execute_demo else "dry-run",
        "topic": topic,
        "selected_idea_id": selected_idea["id"],
        "agent_specs": [asdict(spec) for spec in AGENT_SPECS],
        "tasks": [asdict(result) for result in task_results],
        "execution_plan": execution_plan,
        "artifacts": {
            "trace_json": _artifact(workspace.multiagent_trace_json),
            "trace_md": _artifact(workspace.multiagent_trace_md),
            "leaderboard": _artifact(workspace.leaderboard_csv),
            "trajectory": _artifact(workspace.trajectory_jsonl),
        },
    }
    write_json(workspace.multiagent_trace_json, trace)
    workspace.multiagent_trace_md.write_text(render_multiagent_trace(trace), encoding="utf-8")
    return trace


def read_multiagent_trace(workspace: Workspace) -> dict[str, Any]:
    return read_json(workspace.multiagent_trace_json, default={})


def render_multiagent_trace(trace: dict[str, Any]) -> str:
    lines = [
        "# Multi-Agent Orchestration Trace",
        "",
        f"- Run id: `{trace.get('run_id')}`",
        f"- Mode: `{trace.get('mode')}`",
        f"- Topic: `{trace.get('topic')}`",
        f"- Selected idea: `{trace.get('selected_idea_id')}`",
        "",
        "## Agents",
    ]
    for spec in trace.get("agent_specs", []):
        lines.append(f"- `{spec.get('agent_id')}`: {spec.get('role')} - {spec.get('responsibility')}")

    lines.extend(["", "## Timeline"])
    for index, task in enumerate(trace.get("tasks", []), start=1):
        lines.extend(
            [
                f"{index}. `{task.get('agent_id')}` - `{task.get('status')}`",
                f"   - Summary: {task.get('summary')}",
            ]
        )
        next_actions = task.get("next_actions") or []
        if next_actions:
            lines.append(f"   - Next: {next_actions[0]}")

    plan = trace.get("execution_plan", {})
    lines.extend(
        [
            "",
            "## Execution Plan",
            f"- Backend: `{plan.get('backend')}`",
            f"- Models: `{', '.join(plan.get('models', []))}`",
            f"- Data: `{plan.get('data')}`",
            f"- Data CSV: `{plan.get('data_csv')}`",
            f"- Budget: `{plan.get('budget')}`",
            "",
            "```bash",
            str(plan.get("command", "")),
            "```",
            "",
            "## Recovery",
            "This trace is recoverable from `research_state/multiagent_trace.json`. Re-run with `--execute-demo` when the staged plan is approved for benchmark execution.",
        ]
    )
    return "\n".join(lines) + "\n"
