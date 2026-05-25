"""Active experiment scope management."""

from __future__ import annotations

from typing import Any

from .assets import read_asset_inventory
from .io_utils import read_json, write_json, write_yaml
from .paths import Workspace
from .state import utc_now


def set_scope(workspace: Workspace, name: str, asset_ids: list[str], note: str = "") -> dict[str, Any]:
    inventory = read_asset_inventory(workspace)
    known = {item["id"] for item in inventory.get("assets", [])}
    missing = [asset_id for asset_id in asset_ids if asset_id not in known]
    if missing:
        raise KeyError(f"Unknown asset ids: {', '.join(missing)}")
    scope = {
        "schema_version": 1,
        "name": name,
        "updated_at": utc_now(),
        "asset_ids": asset_ids,
        "note": note,
    }
    write_json(workspace.scope_json, scope)
    write_yaml(workspace.scope_yaml, scope)
    return scope


def get_scope(workspace: Workspace) -> dict[str, Any]:
    return read_json(workspace.scope_json, default={"schema_version": 1, "name": "default", "asset_ids": [], "note": ""})


def scoped_assets(workspace: Workspace) -> list[dict[str, Any]]:
    scope = get_scope(workspace)
    asset_ids = set(scope.get("asset_ids", []))
    assets = read_asset_inventory(workspace).get("assets", [])
    if not asset_ids:
        return assets
    return [item for item in assets if item.get("id") in asset_ids]
