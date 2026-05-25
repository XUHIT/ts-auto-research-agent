"""Server-side asset discovery for external research resources."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import re
from typing import Any, Iterable

from .io_utils import read_json, write_json, write_yaml
from .paths import Workspace

CHECKPOINT_SUFFIXES = {".pt", ".pth", ".ckpt", ".bin", ".safetensors"}
DATA_SUFFIXES = {".csv", ".npy", ".npz", ".parquet", ".pkl", ".h5", ".hdf5"}
SKIP_DIRS = {
    ".cache",
    ".git",
    ".ipynb_checkpoints",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "pkgs",
    "site-packages",
    "wandb",
}


@dataclass(frozen=True)
class AssetRule:
    kind: str
    pattern: re.Pattern[str]
    adapter: str
    capabilities: tuple[str, ...]


DIR_RULES = [
    AssetRule("literature_source", re.compile(r"paper-notes|conference-papers|downloaded-papers|literature", re.I), "literature_index", ("idea_context", "novelty_warning", "venue_taste_hint")),
    AssetRule("data_benchmark", re.compile(r"dataset|datasets|benchmark|pretrain_data|pretrained_datasets|data_clean", re.I), "dataset_registry", ("benchmark_data", "dataset_selection")),
    AssetRule("model_checkpoint_store", re.compile(r"checkpoint|checkpoints|pretrained_model|pretrained", re.I), "checkpoint_registry", ("checkpoint_evaluation", "baseline_comparison")),
    AssetRule("experiment_environment", re.compile(r"^(data_clean|time-moe|time-moe-lora|time_series_library|timeseries-idea-cln)$", re.I), "environment_registry", ("command_execution", "dependency_reuse")),
]

SCRIPT_RULE = AssetRule("experiment_script", re.compile(r"(^|_)(run|train|eval|benchmark|experiment).*\.(py|sh)$", re.I), "external_backend", ("baseline_execution", "metric_parsing"))


def _stable_id(kind: str, path: Path) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", path.name.lower()).strip("_") or "asset"
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:8]
    return f"{kind}_{slug}_{digest}"


def _depth(root: Path, path: Path) -> int:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return 0
    if str(rel) == ".":
        return 0
    return len(rel.parts)


def _asset(kind: str, path: Path, adapter: str, capabilities: Iterable[str], evidence: str) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    return {
        "id": _stable_id(kind, resolved),
        "kind": kind,
        "path": str(resolved),
        "name": resolved.name,
        "adapter": adapter,
        "capabilities": sorted(set(capabilities)),
        "evidence": evidence,
        "status": "discovered",
    }


def _repo_asset(path: Path) -> dict[str, Any] | None:
    files = {child.name for child in path.iterdir() if child.is_file()}
    dirs = {child.name for child in path.iterdir() if child.is_dir()}
    if ".git" not in dirs:
        return None
    has_runner = bool(files & {"run.py", "main.py", "run_eval.py"}) or any(name.startswith("run_") for name in files)
    has_ts_shape = bool(dirs & {"models", "exp", "data_provider", "dataset", "datasets", "scripts", "data", "configs", "metrics"})
    kind = "baseline_repo" if has_runner and has_ts_shape else "code_repo"
    capabilities = ["baseline_execution", "metric_parsing"] if kind == "baseline_repo" else ["code_reference"]
    return _asset(kind, path, "external_backend", capabilities, "git repository with runnable time-series structure" if kind == "baseline_repo" else "git repository")


def scan_assets(roots: list[Path], max_depth: int = 4, limit: int = 1000) -> list[dict[str, Any]]:
    assets: dict[str, dict[str, Any]] = {}
    for raw_root in roots:
        root = raw_root.expanduser().resolve()
        if not root.exists():
            continue
        if root.is_file():
            candidates = [_classify_file(root)]
            for item in candidates:
                if item:
                    assets[item["id"]] = item
            continue
        for current, dirs, files in os.walk(root):
            path = Path(current)
            depth = _depth(root, path)
            if depth >= max_depth:
                dirs[:] = []
            else:
                dirs[:] = [name for name in dirs if name not in SKIP_DIRS and not name.startswith(".")]

            if path.parent.name == "envs" and DIR_RULES[-1].pattern.search(path.name):
                item = _asset("experiment_environment", path, "environment_registry", ("command_execution", "dependency_reuse"), "conda environment directory")
                assets[item["id"]] = item
                dirs[:] = []
                continue

            repo = _repo_asset(path)
            if repo:
                assets[repo["id"]] = repo

            if path.parent.name in {"checkpoints", "pretrained_model", "pretrained_models"}:
                item = _asset("model_checkpoint_store", path, "checkpoint_registry", ("checkpoint_evaluation", "baseline_comparison"), "model directory under checkpoint store")
                assets[item["id"]] = item
            else:
                for rule in DIR_RULES:
                    if rule.pattern.search(path.name):
                        item = _asset(rule.kind, path, rule.adapter, rule.capabilities, f"directory matched {rule.kind}")
                        assets[item["id"]] = item
                        break

            for filename in files:
                file_path = path / filename
                item = _classify_file(file_path)
                if item:
                    assets[item["id"]] = item
                if len(assets) >= limit:
                    return sorted(assets.values(), key=lambda item: (item["kind"], item["path"]))[:limit]
    return sorted(assets.values(), key=lambda item: (item["kind"], item["path"]))[:limit]


def _classify_file(path: Path) -> dict[str, Any] | None:
    suffix = path.suffix.lower()
    name = path.name
    if suffix in CHECKPOINT_SUFFIXES:
        if re.search(r"(checkpoint_step_|epoch[_-]?\d+|step[_-]?\d+)", path.name, re.I):
            return None
        return _asset("model_checkpoint", path, "checkpoint_registry", ("checkpoint_evaluation", "baseline_comparison"), "checkpoint-like file suffix")
    if suffix in DATA_SUFFIXES and any(token in str(path).lower() for token in ["dataset", "data", "benchmark", "ett", "weather", "traffic", "solar", "wind"]):
        return _asset("data_file", path, "dataset_registry", ("benchmark_data",), "data-like file suffix under data path")
    if SCRIPT_RULE.pattern.search(name):
        return _asset(SCRIPT_RULE.kind, path, SCRIPT_RULE.adapter, SCRIPT_RULE.capabilities, "runner/evaluation script naming pattern")
    return None


def write_asset_inventory(workspace: Workspace, roots: list[Path], assets: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "roots": [str(path.expanduser().resolve()) for path in roots],
        "count": len(assets),
        "kind_counts": dict(Counter(item["kind"] for item in assets)),
        "assets": assets,
    }
    write_json(workspace.assets_json, payload)
    write_yaml(workspace.assets_yaml, payload)
    return payload


def read_asset_inventory(workspace: Workspace) -> dict[str, Any]:
    return read_json(workspace.assets_json, default={"schema_version": 1, "roots": [], "count": 0, "kind_counts": {}, "assets": []})


def filter_assets(workspace: Workspace, kind: str | None = None, adapter: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    assets = read_asset_inventory(workspace).get("assets", [])
    if kind:
        assets = [item for item in assets if item.get("kind") == kind]
    if adapter:
        assets = [item for item in assets if item.get("adapter") == adapter]
    if limit is not None:
        assets = assets[:limit]
    return assets
