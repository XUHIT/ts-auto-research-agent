"""Presentation-grade demo workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .io_utils import ensure_dir, read_json, write_json, write_yaml
from .literature import build_index, read_index
from .methods import default_full_research_models, display_role_for_model, method_card_for_model, role_for_model, select_literature_evidence
from .multiagent import run_research_crew
from .paths import Workspace
from .protocol import write_baseline_registry, write_protocol_bundle
from .registry import register_run
from .reviewer import review_run, review_to_markdown
from .runners import run_backend
from .scope import get_scope
from .state import init_workspace, next_run_id, utc_now
from .taste import get_pre_taste, post_taste, review_idea
from .vibe import get_vibe, propose_vibes


def _split_output(output: str) -> tuple[str, str]:
    marker = "\n--- STDERR ---\n"
    if marker not in output:
        return output, ""
    stdout, stderr = output.split(marker, 1)
    return stdout, stderr


def _default_public_demo_paper_source(workspace: Workspace) -> Path:
    return workspace.root / "examples" / "demo_paper_notes"


def _default_public_demo_data_csv(workspace: Workspace) -> Path:
    return workspace.root / "examples" / "sample_series.csv"


def _shell_command_from_metrics(metrics: dict[str, Any]) -> str:
    command = metrics.get("diagnostics", {}).get("command")
    if command:
        return str(command)
    return "ts-agent demo tsl-simple"


def _demo_plan(
    idea: dict[str, Any],
    model: str,
    index: int,
    config: dict[str, Any],
    literature_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    method_card = method_card_for_model(model, literature_records or [])
    role = method_card["role"]
    if role == "baseline_anchor":
        hypothesis = f"Reproduce {model} as the locked DLinear baseline anchor for the benchmark study."
        success = "The run completes and defines the baseline metric for every later candidate."
        kill = "A blocked or unstable baseline invalidates the benchmark protocol."
    elif role == "strong_reference":
        hypothesis = f"Run {model} as a strong reference so a candidate cannot be oversold against DLinear only."
        success = "The reference completes under the same data, budget, and metric protocol."
        kill = "A blocked reference is recorded, but it is not treated as project innovation."
    elif role == "innovation_candidate":
        hypothesis = method_card["claim"]
        success = method_card["acceptance"]
        kill = "Kill or pivot if it cannot beat the DLinear baseline or if secondary diagnostics undermine the story."
    else:
        hypothesis = f"Measure whether {model} changes the benchmark trajectory under the locked protocol."
        success = "Lower RMSE than the DLinear anchor under the same data and budget."
        kill = "Higher RMSE than the DLinear anchor with no useful diagnostic surprise."
    return {
        "id": f"demo_tsl_simple_{index:02d}_{model.lower()}",
        "idea_id": idea["id"],
        "hypothesis_id": f"demo_tsl_simple_{model.lower()}",
        "backend": "tsl-simple",
        "status": "queued",
        "hypothesis": hypothesis,
        "metric_name": "rmse",
        "optimize": "minimize",
        "method_role": role,
        "method_card": method_card,
        "success_criteria": success,
        "kill_criteria": kill,
        "changed_config_summary": f"Run {model} as {display_role_for_model(model)} on Time-Series-Library_simple under the locked ETTh1 benchmark protocol.",
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
        models = default_full_research_models()

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
            "seed": 2021,
            "batch_size": 16,
            "num_workers": 0,
            "learning_rate": "0.001",
            "patience": 1,
            "subset_ratio": subset_ratio,
            "split_policy": "chronological_split_from_backend",
            "timeout_sec": 240,
            "des": "tsagent_demo",
        }
        if baseline_rmse is not None:
            config["baseline_rmse"] = baseline_rmse
            config["baseline_model"] = baseline_model

        plan = _demo_plan(idea, model, index, config, literature_records=[])
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
        metrics.setdefault("diagnostics", {})["method_role"] = plan.get("method_role", role_for_model(model))
        metrics["diagnostics"]["method_claim"] = plan.get("method_card", {}).get("claim")
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
        write_protocol_bundle(workspace, run_dir, plan, run, command=_shell_command_from_metrics(metrics))

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
        "# TSL Simple Benchmark Report",
        "",
        "## Benchmark Setup",
        f"- Dataset: `{data}`",
        f"- Sequence length: `{seq_len}`",
        f"- Prediction length: `{pred_len}`",
        f"- Training subset ratio: `{subset_ratio}`",
        f"- Runs: `{len(results)}`",
        "",
        "## Results",
        "",
        "| Run | Role | Model | RMSE | MAE | Baseline | Delta | Decision |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    best: dict[str, Any] | None = None
    for result in results:
        metrics = result["metrics"]
        diag = metrics.get("diagnostics", {})
        row = {
            "run_id": result["run"]["run_id"],
            "model": diag.get("model", "unknown"),
            "role": diag.get("method_role", role_for_model(str(diag.get("model", "unknown")))),
            "rmse": metrics.get("metric_value"),
            "mae": diag.get("mae"),
            "baseline": metrics.get("baseline"),
            "delta": metrics.get("delta"),
            "decision": result["review"].get("decision"),
        }
        if row["rmse"] is not None and (best is None or float(row["rmse"]) < float(best["rmse"])):
            best = row
        lines.append(
            f"| `{row['run_id']}` | `{row['role']}` | {row['model']} | {row['rmse']} | {row['mae']} | {row['baseline']} | {row['delta']} | `{row['decision']}` |"
        )
    lines.extend(["", "## Takeaway"])
    if best:
        lines.append(f"Best model in this locked benchmark study: `{best['model']}` with RMSE `{best['rmse']}`.")
    else:
        lines.append("No completed model run was available for comparison.")
    lines.extend(
        [
            "",
            "This report is generated from real Time-Series-Library_simple executions under the same locked benchmark protocol used by the autonomous research loop.",
        ]
    )
    return "\n".join(lines) + "\n"



def run_full_research_demo(
    workspace: Workspace,
    paper_source: Path,
    topic: str,
    models: list[str],
    data: str = "ETTh1.csv",
    seq_len: int = 24,
    pred_len: int = 24,
    subset_ratio: float = 0.05,
    train_epochs: int = 3,
    literature_limit: int = 1000,
) -> dict[str, Any]:
    """Run the full demo: literature, idea, taste, real experiments, review, report."""
    init_workspace(workspace)
    if not models:
        models = default_full_research_models()

    literature_result = build_index(workspace, paper_source, limit=literature_limit)
    literature_records = read_index(workspace, limit=1000)
    write_baseline_registry(workspace, literature_records)
    ideas = propose_vibes(workspace, topic=topic, count=3)
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
            "seed": 2021,
            "batch_size": 16,
            "num_workers": 0,
            "learning_rate": "0.001",
            "patience": 1,
            "subset_ratio": subset_ratio,
            "split_policy": "chronological_split_from_backend",
            "timeout_sec": 240,
            "des": "tsagent_full_demo",
        }
        if baseline_rmse is not None:
            config["baseline_rmse"] = baseline_rmse
            config["baseline_model"] = baseline_model

        plan = _demo_plan(idea, model, index, config, literature_records=literature_records)
        plan["id"] = f"full_demo_tsl_simple_{index:02d}_{model.lower()}"
        plan["hypothesis_id"] = f"full_demo_tsl_simple_{model.lower()}"
        plan["literature_context"] = select_literature_evidence(literature_records)
        plan["changed_config_summary"] = (
            f"Use literature-grounded idea `{idea['id']}` to evaluate {model} on "
            f"Time-Series-Library_simple under a controlled ETTh1 setting."
        )

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
        metrics.setdefault("diagnostics", {})["method_role"] = plan.get("method_role", role_for_model(model))
        metrics["diagnostics"]["method_claim"] = plan.get("method_card", {}).get("claim")
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
        command_path.write_text(
            f"#!/usr/bin/env bash\nset -euo pipefail\ncd {metrics.get('diagnostics', {}).get('repo_path', '.')}\n{_shell_command_from_metrics(metrics)}\n",
            encoding="utf-8",
        )
        command_path.chmod(command_path.stat().st_mode | 0o111)
        write_protocol_bundle(workspace, run_dir, plan, run, command=_shell_command_from_metrics(metrics))

        write_json(run_dir / "metrics.json", metrics)
        taste_after = post_taste(run, metrics)
        write_yaml(run_dir / "taste_post.yaml", taste_after)
        write_json(run_dir / "taste_post.json", taste_after)
        review = review_run(run, metrics, taste_after)
        (run_dir / "review.md").write_text(review_to_markdown(review, metrics, taste_after), encoding="utf-8")
        write_json(run_dir / "review.json", review)
        trajectory = register_run(workspace, run, plan, metrics, review)
        results.append({"run": run, "plan": plan, "metrics": metrics, "review": review, "trajectory": trajectory})

    report = _full_research_report(
        workspace=workspace,
        literature_result=literature_result,
        literature_records=literature_records,
        idea=idea,
        taste_pre=taste_pre,
        results=results,
        topic=topic,
        data=data,
        seq_len=seq_len,
        pred_len=pred_len,
        subset_ratio=subset_ratio,
    )
    report_path = workspace.research_state / "full_research_demo_report.md"
    report_path.write_text(report, encoding="utf-8")
    return {"results": results, "report_path": str(report_path), "idea": idea, "taste_pre": taste_pre, "literature": literature_result}


def _full_research_report(
    workspace: Workspace,
    literature_result: dict[str, Any],
    literature_records: list[dict[str, Any]],
    idea: dict[str, Any],
    taste_pre: dict[str, Any],
    results: list[dict[str, Any]],
    topic: str,
    data: str,
    seq_len: int,
    pred_len: int,
    subset_ratio: float,
) -> str:
    scope = get_scope(workspace)
    lines = [
        "# Server Benchmark Research Demo Report",
        "",
        "## Demo Goal",
        "Show one rigorous benchmark study: DLinear is the locked baseline, PatchTST is the strong reference, and only literature-grounded candidates can be treated as project innovation.",
        "",
        "## Literature Substrate",
        f"- Source: `{literature_result.get('source')}`",
        f"- Indexed papers: `{literature_result.get('count')}`",
        "",
        "### Representative Literature Signals",
    ]
    for evidence in select_literature_evidence(literature_records):
        title = evidence.get("title", "untitled")
        venue = evidence.get("venue", "unknown")
        lesson = evidence.get("lesson", "No compact lesson extracted.")
        lines.append(f"- **{title}** ({venue}): {lesson}")

    lines.extend(
        [
            "",
            "## Active Scope",
            f"- Scope: `{scope.get('name', 'default')}`",
            f"- Asset count: `{len(scope.get('asset_ids', []))}`",
            f"- Note: {scope.get('note', '')}",
            "",
            "## Proposed Vibe Idea",
            f"- Idea id: `{idea.get('id')}`",
            f"- One-liner: {idea.get('one_liner')}",
            f"- Core tension: {idea.get('core_tension')}",
            f"- Risk: {idea.get('risk')}",
            "",
            "## Pre-Taste Gate",
            f"- Status: `{taste_pre.get('status')}`",
            f"- Reason: {taste_pre.get('reason')}",
            f"- Total score: `{taste_pre.get('total')}`",
            "",
            "## Experiment Setup",
            f"- Backend: `tsl-simple`",
            f"- Dataset: `{data}`",
            f"- Sequence length: `{seq_len}`",
            f"- Prediction length: `{pred_len}`",
            f"- Training subset ratio: `{subset_ratio}`",
            f"- Training epochs: `{results[0]['plan']['config'].get('train_epochs') if results else 'n/a'}`",
            "- Baseline rule: `DLinear` is the metric anchor; strong references and innovation candidates are labeled separately.",
            "",
            "## Real Experiment Results",
            "",
            "| Run | Role | Model | RMSE | MAE | Baseline | Delta | Decision |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    best: dict[str, Any] | None = None
    for result in results:
        metrics = result["metrics"]
        diag = metrics.get("diagnostics", {})
        row = {
            "run_id": result["run"]["run_id"],
            "model": diag.get("model", "unknown"),
            "role": diag.get("method_role", role_for_model(str(diag.get("model", "unknown")))),
            "rmse": metrics.get("metric_value"),
            "mae": diag.get("mae"),
            "baseline": metrics.get("baseline"),
            "delta": metrics.get("delta"),
            "decision": result["review"].get("decision"),
        }
        if row["rmse"] is not None and (best is None or float(row["rmse"]) < float(best["rmse"])):
            best = row
        lines.append(f"| `{row['run_id']}` | `{row['role']}` | {row['model']} | {row['rmse']} | {row['mae']} | {row['baseline']} | {row['delta']} | `{row['decision']}` |")

    lines.extend(["", "## Research Interpretation"])
    if best:
        lines.append(f"The best RMSE in this locked benchmark study is `{best['model']}` with RMSE `{best['rmse']}`.")
    baseline = next((item for item in results if item["metrics"].get("diagnostics", {}).get("method_role") == "baseline_anchor"), None)
    strong_refs = [item for item in results if item["metrics"].get("diagnostics", {}).get("method_role") == "strong_reference"]
    candidates = [item for item in results if item["metrics"].get("diagnostics", {}).get("method_role") == "innovation_candidate"]
    baseline_value = baseline["metrics"].get("metric_value") if baseline else None
    best_strong = min(
        (item for item in strong_refs if item["metrics"].get("metric_value") is not None),
        key=lambda item: float(item["metrics"]["metric_value"]),
        default=None,
    )
    best_candidate = min(
        (item for item in candidates if item["metrics"].get("metric_value") is not None),
        key=lambda item: float(item["metrics"]["metric_value"]),
        default=None,
    )
    if baseline_value is not None and best_candidate is not None:
        candidate_metrics = best_candidate["metrics"]
        candidate_model = candidate_metrics.get("diagnostics", {}).get("model", "candidate")
        candidate_delta = candidate_metrics.get("delta")
        if candidate_delta is not None and float(candidate_delta) > 0:
            lines.append(
                f"`{candidate_model}` is a bounded positive innovation candidate against DLinear: RMSE improves by `{candidate_delta}` under the same protocol."
            )
        else:
            lines.append(f"`{candidate_model}` does not clear the DLinear baseline and should be killed or redesigned.")
    if best_strong is not None and best_candidate is not None:
        strong_metric = float(best_strong["metrics"]["metric_value"])
        candidate_metric = float(best_candidate["metrics"]["metric_value"])
        strong_model = best_strong["metrics"].get("diagnostics", {}).get("model", "strong reference")
        candidate_model = best_candidate["metrics"].get("diagnostics", {}).get("model", "candidate")
        if strong_metric < candidate_metric:
            lines.append(
                f"`{strong_model}` remains the stronger reference, so `{candidate_model}` is not a SOTA claim; it is a lightweight baseline-improvement signal."
            )
    lines.extend(
        [
            "The result is a bounded benchmark claim, not a final paper claim: an innovation candidate must beat DLinear first, then be checked against the strong reference before any larger claim is allowed.",
            "",
            "## Next Automated Step",
            "Deepen the accepted candidate with ablations, secondary metrics, and more datasets before turning it into a paper-level claim.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_public_mini_demo(
    workspace: Workspace,
    topic: str = "forecasting",
    paper_source: Path | None = None,
    data_csv: Path | None = None,
    column: str = "value",
    budget: int = 1,
) -> dict[str, Any]:
    """Run the portable public demo with only bundled assets and stdlib code."""
    init_workspace(workspace)
    paper_source = paper_source or _default_public_demo_paper_source(workspace)
    data_csv = data_csv or _default_public_demo_data_csv(workspace)
    if not paper_source.exists():
        raise RuntimeError(f"public demo paper source not found: {paper_source}")
    if not data_csv.exists():
        raise RuntimeError(f"public demo data CSV not found: {data_csv}")

    trace = run_research_crew(
        workspace,
        topic=topic,
        paper_source=paper_source,
        literature_limit=20,
        models=["dlinear-mini"],
        data="sample_series.csv",
        data_csv=str(data_csv),
        column=column,
        backend="dlinear-mini",
        budget=budget,
        execute_demo=True,
    )
    report = _public_mini_report(workspace, trace, paper_source=paper_source, data_csv=data_csv, column=column)
    report_path = workspace.research_state / "public_mini_demo_report.md"
    report_path.write_text(report, encoding="utf-8")
    return {"trace": trace, "report_path": str(report_path)}


def _public_mini_report(workspace: Workspace, trace: dict[str, Any], paper_source: Path, data_csv: Path, column: str) -> str:
    runner_task = next((task for task in trace.get("tasks", []) if task.get("agent_id") == "experiment_runner"), {})
    reviewer_task = next((task for task in trace.get("tasks", []) if task.get("agent_id") == "result_reviewer"), {})
    run_ids = runner_task.get("data", {}).get("run_ids", [])
    literature_records = read_index(workspace, limit=3)
    lines = [
        "# Public Mini Demo Report",
        "",
        "## What This Demonstrates",
        "A clone-local research loop that needs no private server paths: bundled paper notes, bundled CSV data, multi-agent orchestration, mini time-series benchmark execution, leaderboard update, and strict review.",
        "",
        "## Inputs",
        f"- Paper notes: `{paper_source}`",
        f"- Data CSV: `{data_csv}`",
        f"- Target column: `{column}`",
        f"- Topic: `{trace.get('topic')}`",
        f"- Selected idea: `{trace.get('selected_idea_id')}`",
        "",
        "## Literature Signals",
    ]
    for record in literature_records:
        contribution = str(record.get("contribution", ""))[:180]
        lines.append(f"- **{record.get('title', 'untitled')}**: {contribution}")

    lines.extend(
        [
            "",
            "## Multi-Agent Stages",
            "",
            "| Agent | Status | Summary |",
            "|---|---|---|",
        ]
    )
    for task in trace.get("tasks", []):
        lines.append(f"| `{task.get('agent_id')}` | `{task.get('status')}` | {task.get('summary')} |")

    lines.extend(
        [
            "",
            "## Experiment Results",
            "",
            "| Run | Backend | Metric | Value | Baseline | Delta | Decision |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for run_id in run_ids:
        metrics = read_json(workspace.run_dir(run_id) / "metrics.json", default={})
        review = read_json(workspace.run_dir(run_id) / "review.json", default={})
        lines.append(
            f"| `{run_id}` | `{metrics.get('backend')}` | `{metrics.get('metric_name')}` | {metrics.get('metric_value')} | {metrics.get('baseline')} | {metrics.get('delta')} | `{review.get('decision')}` |"
        )

    lines.extend(
        [
            "",
            "## Artifacts",
            f"- Multi-agent trace: `{workspace.multiagent_trace_md}`",
            f"- Leaderboard: `{workspace.leaderboard_csv}`",
            f"- Trajectory: `{workspace.trajectory_jsonl}`",
            f"- Reviewer summary: {reviewer_task.get('summary', '')}",
            "",
            "## Reproduce",
            "",
            "```bash",
            "ts-agent demo public-mini",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"
