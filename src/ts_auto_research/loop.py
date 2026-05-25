"""Metric-driven research loop plus recoverable file protocol."""

from __future__ import annotations

from typing import Any

from .io_utils import ensure_dir, read_json, write_json, write_yaml
from .paths import Workspace
from .planner import mark_plan_status, next_queued_plan, plan_experiment
from .registry import latest_metrics, latest_run_dir, leaderboard_text, register_run
from .reviewer import review_run, review_to_markdown
from .runners import run_backend
from .state import init_workspace, next_run_id, utc_now
from .taste import get_pre_taste, post_taste, review_idea
from .vibe import get_vibe, propose_vibes


def ensure_seed_plan(workspace: Workspace, topic: str = "forecasting", backend: str = "smoke") -> dict[str, Any]:
    init_workspace(workspace)
    queued = next_queued_plan(workspace, backend=backend)
    if queued is not None:
        return queued

    ideas = read_json(workspace.vibe_json, default=[])
    candidate_ids = [idea["id"] for idea in ideas if idea.get("status") == "proposed"]
    if not candidate_ids:
        candidate_ids = [idea["id"] for idea in propose_vibes(workspace, topic=topic, count=3)]

    for idea_id in candidate_ids:
        taste = get_pre_taste(workspace, idea_id) or review_idea(workspace, idea_id)
        plan = plan_experiment(workspace, idea_id, backend=backend)
        if taste.get("status") == "approved" and plan.get("status") == "queued":
            return plan
    raise RuntimeError("No approved idea is available for an experiment plan.")


def _command_for_backend(backend: str, data_csv: str | None, column: str | None) -> str:
    parts = ["ts-agent", "run-next", "--backend", backend]
    if data_csv:
        parts.extend(["--data-csv", data_csv])
    if column:
        parts.extend(["--column", column])
    return " ".join(parts)


def _queue_followup_if_needed(workspace: Workspace, plan: dict[str, Any], review: dict[str, Any], metrics: dict[str, Any]) -> None:
    if review.get("decision") != "continue" or metrics.get("status") != "completed":
        return
    queue = read_json(workspace.queue_json, default=[])
    root_id = plan.get("root_plan_id", plan.get("id"))
    next_sequence = int(plan.get("sequence", 0)) + 1
    followup = dict(plan)
    followup.update(
        {
            "id": f"{root_id}_step_{next_sequence:02d}",
            "root_plan_id": root_id,
            "sequence": next_sequence,
            "status": "queued",
            "changed_config_summary": (
                f"Follow up {plan.get('hypothesis_id')} after positive delta "
                f"{metrics.get('delta')}; keep hypothesis but vary the next diagnostic knob."
            ),
            "config": dict(plan.get("config", {}), followup_sequence=next_sequence),
        }
    )
    if not any(item.get("id") == followup["id"] for item in queue):
        queue.append(followup)
        write_json(workspace.queue_json, queue)
        write_yaml(workspace.queue_yaml, queue)


def run_next(
    workspace: Workspace,
    backend: str = "smoke",
    topic: str = "forecasting",
    data_csv: str | None = None,
    column: str | None = None,
) -> dict[str, Any]:
    plan = ensure_seed_plan(workspace, topic=topic, backend=backend)
    idea = get_vibe(workspace, plan["idea_id"])
    taste_pre = get_pre_taste(workspace, plan["idea_id"]) or review_idea(workspace, plan["idea_id"])
    run_id = next_run_id(workspace)
    run_dir = ensure_dir(workspace.run_dir(run_id))
    command = _command_for_backend(backend, data_csv=data_csv, column=column)
    run = {
        "run_id": run_id,
        "created_at": utc_now(),
        "plan_id": plan["id"],
        "idea_id": plan["idea_id"],
        "hypothesis_id": plan.get("hypothesis_id"),
        "backend": backend,
        "run_dir": str(run_dir),
    }

    write_yaml(run_dir / "vibe_idea.yaml", idea)
    write_json(run_dir / "vibe_idea.json", idea)
    write_yaml(run_dir / "taste_pre.yaml", taste_pre)
    write_json(run_dir / "taste_pre.json", taste_pre)
    write_yaml(run_dir / "experiment_plan.yaml", plan)
    write_json(run_dir / "experiment_plan.json", plan)
    write_json(run_dir / "run.json", run)
    command_path = run_dir / "command.sh"
    command_path.write_text(f"#!/usr/bin/env bash\nset -euo pipefail\n{command}\n", encoding="utf-8")
    command_path.chmod(command_path.stat().st_mode | 0o111)

    metrics, stdout = run_backend(backend, run_id, plan, data_csv=data_csv, column=column)
    (run_dir / "stdout.log").write_text(stdout, encoding="utf-8")
    write_json(run_dir / "metrics.json", metrics)
    taste_after = post_taste(run, metrics)
    write_yaml(run_dir / "taste_post.yaml", taste_after)
    write_json(run_dir / "taste_post.json", taste_after)
    review = review_run(run, metrics, taste_after)
    (run_dir / "review.md").write_text(review_to_markdown(review, metrics, taste_after), encoding="utf-8")
    write_json(run_dir / "review.json", review)

    plan_status = "completed" if metrics.get("status") == "completed" else "blocked"
    mark_plan_status(workspace, plan["id"], plan_status)
    trajectory = register_run(workspace, run, plan, metrics, review)
    _queue_followup_if_needed(workspace, plan, review, metrics)
    return {"run": run, "metrics": metrics, "review": review, "trajectory": trajectory}


def run_loop_budget(
    workspace: Workspace,
    budget: int,
    backend: str = "smoke",
    topic: str = "forecasting",
    data_csv: str | None = None,
    column: str | None = None,
) -> list[dict[str, Any]]:
    if budget < 1:
        return []
    results = []
    for _ in range(budget):
        result = run_next(workspace, backend=backend, topic=topic, data_csv=data_csv, column=column)
        results.append(result)
        if result["review"].get("decision") == "needs_human_confirmation":
            break
    return results


def parse_last(workspace: Workspace) -> dict[str, Any] | None:
    run_dir = latest_run_dir(workspace)
    if run_dir is None:
        return None
    metrics = latest_metrics(workspace)
    return {"run_dir": str(run_dir), "metrics": metrics}


def read_leaderboard(workspace: Workspace) -> str:
    return leaderboard_text(workspace)
