"""One-screen showcase summaries for demos and reviews."""

from __future__ import annotations

import csv
from typing import Any

from .io_utils import read_json, write_json
from .literature import read_index
from .paths import Workspace


def _as_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def _read_leaderboard_rows(workspace: Workspace) -> list[dict[str, str]]:
    if not workspace.leaderboard_csv.exists():
        return []
    with workspace.leaderboard_csv.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _model_name(workspace: Workspace, row: dict[str, str]) -> str:
    metrics = read_json(workspace.run_dir(row.get("run_id", "")) / "metrics.json", default={})
    model = metrics.get("diagnostics", {}).get("model")
    if model:
        return str(model)
    hypothesis = row.get("hypothesis_id", "")
    for candidate in ["DLinear", "PatchTST", "MLP", "dlinear-mini"]:
        if candidate.lower().replace("-", "_") in hypothesis.lower().replace("-", "_"):
            return candidate
    return row.get("backend", "unknown") or "unknown"


def _select_result_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    completed = [row for row in rows if row.get("status") == "completed"]
    server_rows = [row for row in completed if row.get("backend") == "tsl-simple"]
    if server_rows:
        return server_rows[-3:]
    return completed[-3:]


def _result_cards(workspace: Workspace, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in rows:
        cards.append(
            {
                "run_id": row.get("run_id"),
                "backend": row.get("backend"),
                "model": _model_name(workspace, row),
                "metric_name": row.get("metric_name"),
                "metric_value": _as_float(row.get("metric_value")),
                "baseline": _as_float(row.get("baseline")),
                "delta": _as_float(row.get("delta")),
                "decision": row.get("next_action"),
                "wall_time_sec": _as_float(row.get("wall_time_sec")),
            }
        )
    return cards


def _best_result(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [item for item in results if item.get("metric_value") is not None]
    if not scored:
        return None
    return min(scored, key=lambda item: float(item["metric_value"]))


def _best_delta(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [item for item in results if item.get("delta") is not None]
    if not scored:
        return None
    return max(scored, key=lambda item: float(item["delta"]))


def _format_float(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.8g}"


def build_showcase(workspace: Workspace) -> dict[str, Any]:
    """Build and persist a compact demo showcase from current state."""
    rows = _read_leaderboard_rows(workspace)
    result_rows = _select_result_rows(rows)
    results = _result_cards(workspace, result_rows)
    best = _best_result(results)
    best_delta = _best_delta(results)
    paper_count = len(read_index(workspace))
    decision_counts: dict[str, int] = {}
    for item in results:
        decision = str(item.get("decision") or "unknown")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1

    if best_delta and best_delta.get("delta") is not None and float(best_delta["delta"]) > 0:
        effect = (
            f"{paper_count} paper notes -> taste-gated idea -> {len(results)} real experiment runs -> "
            f"{best_delta['model']} improved {best_delta['metric_name']} by {_format_float(best_delta['delta'])}."
        )
    elif best:
        effect = (
            f"{paper_count} paper notes -> taste-gated idea -> {len(results)} experiment runs -> "
            f"best current result is {best['model']} with {best['metric_name']}={_format_float(best['metric_value'])}."
        )
    else:
        effect = "No completed experiment rows are available yet. Run `ts-agent demo full-research` first."

    novelty = [
        "Research taste gates before and after experiments, not just metric chasing.",
        "Role-based agent orchestration creates an inspectable research trajectory.",
        "Server paper notes guide ideas while real benchmark runs decide what survives.",
    ]
    usefulness = [
        "Shows which forecasting branch deserves continuation.",
        "Records every run as recoverable protocol files for audit and resume.",
        "Turns local papers, baselines, metrics, and decisions into one reviewable loop.",
    ]
    next_action = "Run `ts-agent demo full-research`, then inspect `research_state/showcase.md`."
    if best_delta and best_delta.get("decision") == "continue":
        next_action = f"Continue from `{best_delta['model']}` and deepen the benchmark question."
    elif best:
        next_action = f"Use `{best['model']}` as the current reference point and test the next bounded variant."

    showcase = {
        "effect": effect,
        "novelty": novelty,
        "usefulness": usefulness,
        "paper_count": paper_count,
        "results": results,
        "best_result": best,
        "best_delta": best_delta,
        "decision_counts": decision_counts,
        "next_action": next_action,
        "artifacts": {
            "showcase_md": str(workspace.showcase_md),
            "leaderboard": str(workspace.leaderboard_csv),
            "trajectory": str(workspace.trajectory_jsonl),
            "full_demo_report": str(workspace.research_state / "full_research_demo_report.md"),
        },
    }
    write_json(workspace.showcase_json, showcase)
    workspace.showcase_md.write_text(render_showcase_markdown(showcase), encoding="utf-8")
    return showcase


def render_showcase_terminal(showcase: dict[str, Any]) -> str:
    lines = [
        "",
        "TS Auto Research Agent - Showcase",
        "=================================",
        f"Effect: {showcase.get('effect')}",
        "",
        "Novelty:",
    ]
    lines.extend(f"- {item}" for item in showcase.get("novelty", []))
    lines.extend(["", "Use:"])
    lines.extend(f"- {item}" for item in showcase.get("usefulness", []))
    lines.extend(["", "Latest results:", "Run      Model      Metric      Value       Delta       Decision"])
    for item in showcase.get("results", []):
        lines.append(
            f"{item.get('run_id', ''):<8} {item.get('model', ''):<10} {item.get('metric_name', ''):<10} "
            f"{_format_float(item.get('metric_value')):<10} {_format_float(item.get('delta')):<10} {item.get('decision', '')}"
        )
    lines.extend(["", f"Next: {showcase.get('next_action')}", f"Report: {showcase.get('artifacts', {}).get('showcase_md')}"])
    return "\n".join(lines) + "\n"


def render_showcase_markdown(showcase: dict[str, Any]) -> str:
    lines = [
        "# TS Auto Research Agent Showcase",
        "",
        "## Effect",
        showcase.get("effect", ""),
        "",
        "## What Is New",
    ]
    lines.extend(f"- {item}" for item in showcase.get("novelty", []))
    lines.extend(["", "## Why It Is Useful"])
    lines.extend(f"- {item}" for item in showcase.get("usefulness", []))
    lines.extend(
        [
            "",
            "## Latest Results",
            "",
            "| Run | Model | Backend | Metric | Value | Baseline | Delta | Decision |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for item in showcase.get("results", []):
        lines.append(
            f"| `{item.get('run_id')}` | `{item.get('model')}` | `{item.get('backend')}` | `{item.get('metric_name')}` | "
            f"{_format_float(item.get('metric_value'))} | {_format_float(item.get('baseline'))} | {_format_float(item.get('delta'))} | `{item.get('decision')}` |"
        )
    lines.extend(
        [
            "",
            "## Next Action",
            showcase.get("next_action", ""),
            "",
            "## Artifacts",
        ]
    )
    for name, path in showcase.get("artifacts", {}).items():
        lines.append(f"- `{name}`: `{path}`")
    return "\n".join(lines) + "\n"
