"""Workspace initialization and state management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .io_utils import ensure_dir, read_json, write_json, write_yaml
from .paths import Workspace


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def initial_state() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "active",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "current_phase": "bootstrap",
        "next_run_number": 1,
        "active_backend": "smoke",
        "confirmation_policy": "stage_gate",
    }


def init_workspace(workspace: Workspace, force: bool = False) -> dict[str, Any]:
    ensure_dir(workspace.research_state)
    ensure_dir(workspace.runs)
    ensure_dir(workspace.literature)
    state = read_json(workspace.state_json)
    if state is None or force:
        state = initial_state()
        write_json(workspace.state_json, state)
        write_yaml(workspace.state_yaml, state)
    for path, payload in [
        (workspace.vibe_json, []),
        (workspace.taste_json, []),
        (workspace.queue_json, []),
        (workspace.claims_json, []),
    ]:
        if force or not path.exists():
            write_json(path, payload)
    for path, payload in [
        (workspace.vibe_yaml, []),
        (workspace.taste_yaml, []),
        (workspace.queue_yaml, []),
        (workspace.claims_yaml, []),
    ]:
        if force or not path.exists():
            write_yaml(path, payload)
    if force or not workspace.leaderboard_csv.exists():
        workspace.leaderboard_csv.write_text(
            "run_id,hypothesis_id,backend,status,metric_name,metric_value,baseline,delta,wall_time_sec,next_action\n",
            encoding="utf-8",
        )
    if force or not workspace.trajectory_jsonl.exists():
        workspace.trajectory_jsonl.write_text("", encoding="utf-8")
    return state


def load_state(workspace: Workspace) -> dict[str, Any]:
    state = read_json(workspace.state_json)
    if state is None:
        return init_workspace(workspace)
    return state


def save_state(workspace: Workspace, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    write_json(workspace.state_json, state)
    write_yaml(workspace.state_yaml, state)


def next_run_id(workspace: Workspace) -> str:
    state = load_state(workspace)
    number = int(state.get("next_run_number", 1))
    state["next_run_number"] = number + 1
    save_state(workspace, state)
    return f"run_{number:04d}"
