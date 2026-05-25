"""Experiment planning and queue management."""

from __future__ import annotations

from typing import Any

from .io_utils import read_json, write_json, write_yaml
from .paths import Workspace
from .taste import get_pre_taste, review_idea
from .vibe import get_vibe


def plan_experiment(workspace: Workspace, idea_id: str, backend: str = "smoke") -> dict[str, Any]:
    idea = get_vibe(workspace, idea_id)
    taste = get_pre_taste(workspace, idea_id) or review_idea(workspace, idea_id)
    hypothesis_id = f"hyp_{idea_id}"
    plan = {
        "id": f"plan_{idea_id}_{backend}",
        "idea_id": idea_id,
        "hypothesis_id": hypothesis_id,
        "backend": backend,
        "root_plan_id": f"plan_{idea_id}_{backend}",
        "sequence": 0,
        "status": "queued" if taste["status"] == "approved" else "blocked_by_taste",
        "hypothesis": idea["one_liner"],
        "metric_name": "mse",
        "optimize": "minimize",
        "success_criteria": "metric improves over baseline and post-taste paper potential >= 3",
        "kill_criteria": "no improvement and no surprising diagnostic signal",
        "changed_config_summary": f"Evaluate `{idea_id}` with `{backend}` backend.",
        "config": {
            "backend": backend,
            "topic": idea.get("topic", "forecasting"),
            "model": "dlinear-mini" if backend == "dlinear-mini" else "smoke-candidate",
            "data": "synthetic" if backend == "smoke" else "user_csv",
            "seq_len": 12,
            "label_len": 0,
            "pred_len": 1,
            "seed": 2021,
            "train_epochs": 1,
            "batch_size": 1,
            "learning_rate": "not_applicable" if backend != "tsl-simple" else "0.001",
            "patience": 1,
            "timeout_sec": 60,
            "split_policy": "chronological_split_from_backend",
        },
    }
    queue = read_json(workspace.queue_json, default=[])
    queue = [item for item in queue if item.get("id") != plan["id"]] + [plan]
    write_json(workspace.queue_json, queue)
    write_yaml(workspace.queue_yaml, queue)
    return plan


def next_queued_plan(workspace: Workspace, backend: str | None = None) -> dict[str, Any] | None:
    queue = read_json(workspace.queue_json, default=[])
    for plan in queue:
        if plan.get("status") == "queued" and (backend is None or plan.get("backend") == backend):
            return plan
    return None


def mark_plan_status(workspace: Workspace, plan_id: str, status: str) -> None:
    queue = read_json(workspace.queue_json, default=[])
    for plan in queue:
        if plan.get("id") == plan_id:
            plan["status"] = status
    write_json(workspace.queue_json, queue)
    write_yaml(workspace.queue_yaml, queue)
