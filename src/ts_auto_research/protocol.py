"""Experiment protocol, registry, and validation utilities."""

from __future__ import annotations

from typing import Any

from .io_utils import write_json, write_yaml
from .methods import (
    BASELINE_ANCHOR,
    BASELINE_CONTROL,
    INNOVATION_CANDIDATE,
    STRONG_REFERENCE,
    METHOD_CATALOG,
    method_card_for_model,
    role_for_model,
    select_literature_evidence,
)
from .paths import Workspace

SCHEMA_VERSION = 1
LOCKED_METRICS = {"rmse", "mse", "mae"}
LOCKED_OPTIMIZE = {"minimize", "maximize"}


FIVE_ROLE_LANES: tuple[dict[str, Any], ...] = (
    {
        "lane_id": "planner",
        "display_name": "Planner",
        "mission": "Turn literature signals and taste constraints into a bounded, testable hypothesis.",
        "owns": ("literature context", "idea selection", "experiment protocol"),
    },
    {
        "lane_id": "engineer",
        "display_name": "Engineer",
        "mission": "Bind the hypothesis to model code, baseline registry, dataset contracts, and run commands.",
        "owns": ("model registry", "schema validation", "code-change summary"),
    },
    {
        "lane_id": "executor",
        "display_name": "Executor",
        "mission": "Launch the selected backend and preserve stdout, stderr, metrics, and reproducible commands.",
        "owns": ("training execution", "run artifacts", "leaderboard updates"),
    },
    {
        "lane_id": "evaluator",
        "display_name": "Evaluator",
        "mission": "Check metrics, fairness, leakage risk, post-result taste, and continue/pivot/kill decisions.",
        "owns": ("metric audit", "fairness checks", "review decision"),
    },
    {
        "lane_id": "reporter",
        "display_name": "Reporter",
        "mission": "Convert the research trace into a visual cockpit, report packet, and paper-ready material.",
        "owns": ("dashboard", "PDF report", "research summary"),
    },
)


ROLE_TASK_MAP: dict[str, tuple[str, ...]] = {
    "planner": ("literature_curator", "idea_scout", "taste_reviewer", "experiment_planner"),
    "engineer": ("scope_manager", "code_engineer"),
    "executor": ("experiment_runner",),
    "evaluator": ("result_reviewer",),
    "reporter": ("synthesis_agent", "reporter_agent"),
}


def build_baseline_registry(literature_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build the model and baseline registry used by the experiment schema."""
    records = literature_records or []
    models = []
    for name, card in METHOD_CATALOG.items():
        models.append(
            {
                "name": name,
                "role": card.get("role"),
                "display_role": card.get("display_role"),
                "claim": card.get("claim"),
                "acceptance": card.get("acceptance"),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_anchor": "DLinear",
        "strong_references": [item["name"] for item in models if item.get("role") == STRONG_REFERENCE],
        "innovation_candidates": [item["name"] for item in models if item.get("role") == INNOVATION_CANDIDATE],
        "controls": [item["name"] for item in models if item.get("role") == BASELINE_CONTROL],
        "models": models,
        "literature_evidence": select_literature_evidence(records),
        "claim_policy": [
            "A candidate must first beat the locked DLinear anchor under the same dataset, horizon, metric, and budget.",
            "A DLinear-only improvement is reported as a bounded signal until it is checked against a strong reference.",
            "Reviewer decisions are restricted to continue, kill, pivot, or needs_human_confirmation.",
        ],
    }


def write_baseline_registry(workspace: Workspace, literature_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    registry = build_baseline_registry(literature_records)
    write_json(workspace.baseline_registry_json, registry)
    write_yaml(workspace.baseline_registry_yaml, registry)
    return registry


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_experiment_schema(plan: dict[str, Any], run: dict[str, Any], command: str | None = None) -> dict[str, Any]:
    config = dict(plan.get("config") or {})
    method_card = dict(plan.get("method_card") or {})
    model = str(config.get("model") or method_card.get("model") or plan.get("backend") or "unknown")
    role = str(plan.get("method_role") or method_card.get("role") or role_for_model(model))
    metric_name = str(plan.get("metric_name") or "rmse")
    optimize = str(plan.get("optimize") or "minimize")
    seed = _as_int(config.get("seed"), 2021)
    baseline_model = str(config.get("baseline_model") or ("DLinear" if model != "DLinear" else model))
    baseline_metric = config.get("baseline_rmse") or config.get("baseline_metric")
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment": {
            "run_id": run.get("run_id"),
            "plan_id": plan.get("id"),
            "idea_id": plan.get("idea_id"),
            "hypothesis_id": plan.get("hypothesis_id"),
            "backend": plan.get("backend"),
            "hypothesis": plan.get("hypothesis"),
            "success_criteria": plan.get("success_criteria"),
            "kill_criteria": plan.get("kill_criteria"),
        },
        "dataset": {
            "name": config.get("data") or config.get("data_csv") or "not_declared",
            "features": config.get("features", "M"),
            "target": config.get("target"),
            "seq_len": _as_int(config.get("seq_len"), 0),
            "label_len": _as_int(config.get("label_len"), 0),
            "pred_len": _as_int(config.get("pred_len"), 0),
            "subset_ratio": _as_float(config.get("subset_ratio"), 1.0),
            "split_policy": config.get("split_policy", "chronological_split_from_backend"),
        },
        "model": {
            "name": model,
            "role": role,
            "claim": method_card.get("claim"),
            "changed_config_summary": plan.get("changed_config_summary"),
        },
        "baseline": {
            "anchor_model": baseline_model,
            "anchor_metric": baseline_metric,
            "strong_reference": "PatchTST",
            "controls": ["RLinear", "MLP", "LSTNet"],
        },
        "evaluation": {
            "metric_name": metric_name,
            "optimize": optimize,
            "seed": seed,
            "train_epochs": _as_int(config.get("train_epochs"), 0),
            "batch_size": _as_int(config.get("batch_size"), 0),
            "learning_rate": str(config.get("learning_rate", "not_declared")),
            "patience": _as_int(config.get("patience"), 0),
            "timeout_sec": _as_int(config.get("timeout_sec"), 0),
        },
        "ablation": {
            "required_for_candidate": role == INNOVATION_CANDIDATE,
            "minimum_grid": [
                "DLinear anchor",
                "strong reference arm",
                "candidate full model",
                "candidate without the proposed mechanism",
                "normalization or capacity control when applicable",
            ],
        },
        "leakage_policy": {
            "temporal_order": "train/validation/test must preserve chronological order",
            "future_covariates": "future covariates may contain calendar or known timestamp features only, never future target values",
            "metric_visibility": "metrics are read only after command execution and are not used to modify the same run",
        },
        "artifacts": {
            "run_dir": run.get("run_dir"),
            "command": command,
            "stdout": "stdout.log",
            "stderr": "stderr.log",
            "metrics": "metrics.json",
            "review": "review.md",
        },
    }


def _check(name: str, passed: bool, evidence: str, severity: str = "error") -> dict[str, str]:
    return {"name": name, "status": "pass" if passed else "fail", "severity": severity, "evidence": evidence}


def validate_experiment_schema(schema: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    dataset = schema.get("dataset", {})
    model = schema.get("model", {})
    baseline = schema.get("baseline", {})
    evaluation = schema.get("evaluation", {})
    experiment = schema.get("experiment", {})

    for section in ["experiment", "dataset", "model", "baseline", "evaluation", "ablation", "leakage_policy"]:
        if not schema.get(section):
            errors.append(f"missing required section: {section}")

    if not experiment.get("hypothesis_id"):
        errors.append("hypothesis_id is required")
    if dataset.get("name") in {None, "", "not_declared"}:
        errors.append("dataset name or data_csv is required")
    if int(dataset.get("seq_len") or 0) <= 0:
        errors.append("seq_len must be positive")
    if int(dataset.get("pred_len") or 0) <= 0:
        errors.append("pred_len must be positive")
    if str(evaluation.get("metric_name")) not in LOCKED_METRICS:
        errors.append(f"metric_name must be one of {sorted(LOCKED_METRICS)}")
    if str(evaluation.get("optimize")) not in LOCKED_OPTIMIZE:
        errors.append(f"optimize must be one of {sorted(LOCKED_OPTIMIZE)}")
    if int(evaluation.get("seed") or 0) <= 0:
        warnings.append("seed is missing or non-positive")
    if model.get("role") == INNOVATION_CANDIDATE and baseline.get("anchor_model") != "DLinear":
        errors.append("innovation candidates must declare DLinear as the anchor baseline")
    if model.get("role") == INNOVATION_CANDIDATE and baseline.get("anchor_metric") in {None, ""}:
        warnings.append("candidate run is missing a resolved anchor metric before execution")

    fairness_checks = [
        _check("locked_dataset", dataset.get("name") not in {None, "", "not_declared"}, str(dataset.get("name"))),
        _check("locked_horizon", int(dataset.get("seq_len") or 0) > 0 and int(dataset.get("pred_len") or 0) > 0, f"seq_len={dataset.get('seq_len')} pred_len={dataset.get('pred_len')}"),
        _check("locked_metric", str(evaluation.get("metric_name")) in LOCKED_METRICS, str(evaluation.get("metric_name"))),
        _check("seed_recorded", int(evaluation.get("seed") or 0) > 0, str(evaluation.get("seed")), severity="warning"),
        _check("budget_recorded", int(evaluation.get("train_epochs") or 0) > 0 and int(evaluation.get("batch_size") or 0) > 0, f"epochs={evaluation.get('train_epochs')} batch={evaluation.get('batch_size')}"),
        _check("baseline_declared", bool(baseline.get("anchor_model")), str(baseline.get("anchor_model"))),
    ]
    leakage_checks = [
        _check("chronological_split_policy", "chronological" in str(dataset.get("split_policy", "")).lower(), str(dataset.get("split_policy"))),
        _check("future_covariate_policy", "never future target" in str(schema.get("leakage_policy", {}).get("future_covariates", "")), schema.get("leakage_policy", {}).get("future_covariates", "")),
        _check("metric_after_execution", "after command execution" in str(schema.get("leakage_policy", {}).get("metric_visibility", "")), schema.get("leakage_policy", {}).get("metric_visibility", "")),
    ]
    failed_required = [item for item in fairness_checks + leakage_checks if item["status"] == "fail" and item["severity"] == "error"]
    status = "invalid" if errors or failed_required else "warning" if warnings else "valid"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "fairness_checks": fairness_checks,
        "leakage_checks": leakage_checks,
        "summary": f"{len(errors)} errors, {len(warnings)} warnings, {len(failed_required)} failed required checks",
    }


def protocol_markdown(schema: dict[str, Any], validation: dict[str, Any]) -> str:
    lines = [
        f"# Experiment Protocol {schema.get('experiment', {}).get('run_id')}",
        "",
        "## Schema Status",
        f"- Status: `{validation.get('status')}`",
        f"- Summary: {validation.get('summary')}",
        "",
        "## Core Contract",
        f"- Dataset: `{schema.get('dataset', {}).get('name')}`",
        f"- Model: `{schema.get('model', {}).get('name')}` ({schema.get('model', {}).get('role')})",
        f"- Horizon: `{schema.get('dataset', {}).get('seq_len')}` -> `{schema.get('dataset', {}).get('pred_len')}`",
        f"- Metric: `{schema.get('evaluation', {}).get('metric_name')}` / `{schema.get('evaluation', {}).get('optimize')}`",
        f"- Baseline anchor: `{schema.get('baseline', {}).get('anchor_model')}`",
        "",
        "## Fairness Checks",
    ]
    for item in validation.get("fairness_checks", []):
        lines.append(f"- `{item.get('status')}` {item.get('name')}: {item.get('evidence')}")
    lines.append("")
    lines.append("## Leakage Checks")
    for item in validation.get("leakage_checks", []):
        lines.append(f"- `{item.get('status')}` {item.get('name')}: {item.get('evidence')}")
    if validation.get("errors"):
        lines.extend(["", "## Errors"])
        lines.extend(f"- {item}" for item in validation["errors"])
    if validation.get("warnings"):
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {item}" for item in validation["warnings"])
    return "\n".join(lines) + "\n"


def write_protocol_bundle(workspace: Workspace, run_dir: Any, plan: dict[str, Any], run: dict[str, Any], command: str | None = None) -> dict[str, Any]:
    schema = build_experiment_schema(plan, run, command=command)
    validation = validate_experiment_schema(schema)
    write_json(run_dir / "experiment_schema.json", schema)
    write_yaml(run_dir / "experiment_schema.yaml", schema)
    write_json(run_dir / "schema_validation.json", validation)
    write_yaml(run_dir / "schema_validation.yaml", validation)
    (run_dir / "protocol_audit.md").write_text(protocol_markdown(schema, validation), encoding="utf-8")
    return {"schema": schema, "validation": validation}


def build_role_lanes(tasks: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    tasks = tasks or []
    by_id = {str(task.get("agent_id")): task for task in tasks}
    lanes = []
    for lane in FIVE_ROLE_LANES:
        task_ids = ROLE_TASK_MAP[lane["lane_id"]]
        lane_tasks = [by_id[task_id] for task_id in task_ids if task_id in by_id]
        statuses = [str(task.get("status", "unknown")) for task in lane_tasks]
        if any(status in {"blocked", "attention_required", "pending"} for status in statuses):
            status = "attention_required"
        elif statuses and all(status == "completed" for status in statuses):
            status = "completed"
        elif statuses:
            status = "active"
        else:
            status = "not_started"
        lanes.append(
            {
                **lane,
                "task_ids": list(task_ids),
                "status": status,
                "task_summaries": [str(task.get("summary", "")) for task in lane_tasks],
            }
        )
    return lanes
