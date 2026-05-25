"""Presentation-grade demo workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .io_utils import ensure_dir, write_json, write_yaml
from .paths import Workspace
from .registry import register_run
from .reviewer import review_run, review_to_markdown
from .runners import run_backend
from .state import init_workspace, next_run_id, utc_now
from .taste import get_pre_taste, post_taste, review_idea
from .vibe import get_vibe, propose_vibes


def _split_output(output: str) -> tuple[str, str]:
    marker = "\n--- STDERR ---\n"
    if marker not in output:
        return output, ""
    stdout, stderr = output.split(marker, 1)
    return stdout, stderr


def _shell_command_from_metrics(metrics: dict[str, Any]) -> str:
    command = metrics.get("diagnostics", {}).get("command")
    if command:
        return str(command)
    return "ts-agent demo tsl-simple"


def _demo_plan(idea: dict[str, Any], model: str, index: int, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"demo_tsl_simple_{index:02d}_{model.lower()}",
        "idea_id": idea["id"],
        "hypothesis_id": f"demo_tsl_simple_{model.lower()}",
        "backend": "tsl-simple",
        "status": "queued",
        "hypothesis": f"Measure whether {model} changes the short-horizon ETTh1 research trajectory under a tiny controlled run.",
        "metric_name": "rmse",
        "optimize": "minimize",
        "success_criteria": "Lower RMSE than the DLinear anchor under the same data and budget.",
        "kill_criteria": "Higher RMSE than the DLinear anchor with no useful diagnostic surprise.",
        "changed_config_summary": f"Run {model} on Time-Series-Library_simple with a small ETTh1 controlled configuration.",
        "config": config,
    }


def run_tsl_simple_demo(
    workspace: Workspace,
    models: list[str],
    data: str = "ETTh1.csv",
    seq_len: int = 24,
    pred_len: int = 24,
    subset_ratio: float = 0.05,
    train_epochs: int = 1,
) -> dict[str, Any]:
    init_workspace(workspace)
    if not models:
        models = ["DLinear", "PatchTST", "MLP"]

    ideas = propose_vibes(workspace, topic="forecasting-demo", count=1)
    idea = ideas[0]
    taste_pre = get_pre_taste(workspace, idea["id"]) or review_idea(workspace, idea["id"])

    results: list[dict[str, Any]] = []
    baseline_rmse: float | None = None
    baseline_model: str | None = None
    for index, model in enumerate(models, start=1):
        config: dict[str, Any] = {
            "model": model,
            "data": data,
            "seq_len": seq_len,
            "label_len": max(0, pred_len // 2),
            "pred_len": pred_len,
            "enc_in": 7,
            "dec_in": 7,
            "c_out": 7,
            "d_model": 64,
            "d_ff": 64,
            "train_epochs": train_epochs,
            "batch_size": 16,
            "num_workers": 0,
            "learning_rate": "0.001",
            "patience": 1,
            "subset_ratio": subset_ratio,
            "timeout_sec": 240,
            "des": "tsagent_demo",
        }
        if baseline_rmse is not None:
            config["baseline_rmse"] = baseline_rmse
            config["baseline_model"] = baseline_model

        plan = _demo_plan(idea, model, index, config)
        run_id = next_run_id(workspace)
        run_dir = ensure_dir(workspace.run_dir(run_id))
        run = {
            "run_id": run_id,
            "created_at": utc_now(),
            "plan_id": plan["id"],
            "idea_id": plan["idea_id"],
            "hypothesis_id": plan["hypothesis_id"],
            "backend": "tsl-simple",
            "run_dir": str(run_dir),
        }

        write_yaml(run_dir / "vibe_idea.yaml", idea)
        write_json(run_dir / "vibe_idea.json", idea)
        write_yaml(run_dir / "taste_pre.yaml", taste_pre)
        write_json(run_dir / "taste_pre.json", taste_pre)
        write_yaml(run_dir / "experiment_plan.yaml", plan)
        write_json(run_dir / "experiment_plan.json", plan)
        write_json(run_dir / "run.json", run)

        metrics, output = run_backend("tsl-simple", run_id, plan)
        if baseline_rmse is None and metrics.get("status") == "completed" and metrics.get("metric_value") is not None:
            baseline_rmse = float(metrics["metric_value"])
            baseline_model = model
            metrics["baseline"] = baseline_rmse
            metrics["delta"] = 0.0
            metrics.setdefault("diagnostics", {})["baseline_anchor"] = True
            metrics["diagnostics"]["baseline_model"] = model

        stdout, stderr = _split_output(output)
        (run_dir / "stdout.log").write_text(stdout, encoding="utf-8")
        (run_dir / "stderr.log").write_text(stderr, encoding="utf-8")
        command_path = run_dir / "command.sh"
        command_path.write_text(f"#!/usr/bin/env bash\nset -euo pipefail\ncd {metrics.get('diagnostics', {}).get('repo_path', '.')}\n{_shell_command_from_metrics(metrics)}\n", encoding="utf-8")
        command_path.chmod(command_path.stat().st_mode | 0o111)

        write_json(run_dir / "metrics.json", metrics)
        taste_after = post_taste(run, metrics)
        write_yaml(run_dir / "taste_post.yaml", taste_after)
        write_json(run_dir / "taste_post.json", taste_after)
        review = review_run(run, metrics, taste_after)
        (run_dir / "review.md").write_text(review_to_markdown(review, metrics, taste_after), encoding="utf-8")
        write_json(run_dir / "review.json", review)
        trajectory = register_run(workspace, run, plan, metrics, review)
        results.append({"run": run, "plan": plan, "metrics": metrics, "review": review, "trajectory": trajectory})

    report = _demo_report(results, data=data, seq_len=seq_len, pred_len=pred_len, subset_ratio=subset_ratio)
    report_path = workspace.research_state / "tsl_simple_demo_report.md"
    report_path.write_text(report, encoding="utf-8")
    return {"results": results, "report_path": str(report_path)}


def _demo_report(results: list[dict[str, Any]], data: str, seq_len: int, pred_len: int, subset_ratio: float) -> str:
    lines = [
        "# TSL Simple Demo Report",
        "",
        "## Demo Setup",
        f"- Dataset: `{data}`",
        f"- Sequence length: `{seq_len}`",
        f"- Prediction length: `{pred_len}`",
        f"- Training subset ratio: `{subset_ratio}`",
        f"- Runs: `{len(results)}`",
        "",
        "## Results",
        "",
        "| Run | Model | RMSE | MAE | Baseline | Delta | Decision |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    best: dict[str, Any] | None = None
    for result in results:
        metrics = result["metrics"]
        diag = metrics.get("diagnostics", {})
        row = {
            "run_id": result["run"]["run_id"],
            "model": diag.get("model", "unknown"),
            "rmse": metrics.get("metric_value"),
            "mae": diag.get("mae"),
            "baseline": metrics.get("baseline"),
            "delta": metrics.get("delta"),
            "decision": result["review"].get("decision"),
        }
        if row["rmse"] is not None and (best is None or float(row["rmse"]) < float(best["rmse"])):
            best = row
        lines.append(
            f"| `{row['run_id']}` | {row['model']} | {row['rmse']} | {row['mae']} | {row['baseline']} | {row['delta']} | `{row['decision']}` |"
        )
    lines.extend(["", "## Takeaway"])
    if best:
        lines.append(f"Best model in this tiny controlled demo: `{best['model']}` with RMSE `{best['rmse']}`.")
    else:
        lines.append("No completed model run was available for comparison.")
    lines.extend(
        [
            "",
            "This report is generated from real Time-Series-Library_simple executions and the same run protocol used by the autonomous research loop.",
        ]
    )
    return "\n".join(lines) + "\n"
