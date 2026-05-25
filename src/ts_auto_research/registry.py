"""Leaderboard and trajectory persistence."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .io_utils import append_jsonl, ensure_dir, read_json
from .paths import Workspace

LEADERBOARD_FIELDS = [
    "run_id",
    "hypothesis_id",
    "backend",
    "status",
    "metric_name",
    "metric_value",
    "baseline",
    "delta",
    "wall_time_sec",
    "next_action",
]


def append_leaderboard(workspace: Workspace, row: dict[str, Any]) -> None:
    ensure_dir(workspace.leaderboard_csv.parent)
    exists = workspace.leaderboard_csv.exists() and workspace.leaderboard_csv.stat().st_size > 0
    with workspace.leaderboard_csv.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEADERBOARD_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in LEADERBOARD_FIELDS})


def register_run(
    workspace: Workspace,
    run: dict[str, Any],
    plan: dict[str, Any],
    metrics: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    row = {
        "run_id": run["run_id"],
        "hypothesis_id": plan.get("hypothesis_id"),
        "backend": metrics.get("backend", plan.get("backend")),
        "status": metrics.get("status"),
        "metric_name": metrics.get("metric_name"),
        "metric_value": metrics.get("metric_value"),
        "baseline": metrics.get("baseline"),
        "delta": metrics.get("delta"),
        "wall_time_sec": metrics.get("wall_time_sec"),
        "next_action": review.get("decision"),
    }
    append_leaderboard(workspace, row)
    trajectory = {
        "run_id": run["run_id"],
        "hypothesis_id": plan.get("hypothesis_id"),
        "idea_id": plan.get("idea_id"),
        "backend": metrics.get("backend", plan.get("backend")),
        "changed_config_summary": plan.get("changed_config_summary"),
        "metric_name": metrics.get("metric_name"),
        "metric_value": metrics.get("metric_value"),
        "baseline": metrics.get("baseline"),
        "delta": metrics.get("delta"),
        "wall_time_sec": metrics.get("wall_time_sec"),
        "next_action": review.get("decision"),
        "run_dir": str(workspace.run_dir(run["run_id"])),
    }
    append_jsonl(workspace.trajectory_jsonl, trajectory)
    return trajectory


def latest_run_dir(workspace: Workspace) -> Path | None:
    if not workspace.runs.exists():
        return None
    runs = sorted(path for path in workspace.runs.iterdir() if path.is_dir() and path.name.startswith("run_"))
    return runs[-1] if runs else None


def latest_metrics(workspace: Workspace) -> dict[str, Any] | None:
    run_dir = latest_run_dir(workspace)
    if run_dir is None:
        return None
    return read_json(run_dir / "metrics.json")


def leaderboard_text(workspace: Workspace) -> str:
    if not workspace.leaderboard_csv.exists():
        return ""
    return workspace.leaderboard_csv.read_text(encoding="utf-8")
