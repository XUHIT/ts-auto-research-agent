"""One-screen benchmark showcase summaries."""

from __future__ import annotations

import csv
from typing import Any

from .io_utils import read_json, write_json
from .literature import read_index
from .methods import INNOVATION_CANDIDATE, STRONG_REFERENCE, role_for_model
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
    for candidate in ["CalDLinear", "PSLinear", "RLinear", "DLinear", "PatchTST", "MLP", "LSTNet", "dlinear-mini"]:
        if candidate.lower().replace("-", "_") in hypothesis.lower().replace("-", "_"):
            return candidate
    return row.get("backend", "unknown") or "unknown"


def _select_result_rows(workspace: Workspace, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    server_rows = [row for row in rows if row.get("backend") == "tsl-simple"]
    if server_rows:
        anchor_indices = [idx for idx, row in enumerate(server_rows) if _model_name(workspace, row) == "DLinear"]
        start = anchor_indices[-1] if anchor_indices else max(0, len(server_rows) - 3)
        return server_rows[start : start + 6]
    completed = [row for row in rows if row.get("status") == "completed"]
    return completed[-3:]


def _result_cards(workspace: Workspace, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in rows:
        metrics = read_json(workspace.run_dir(row.get("run_id", "")) / "metrics.json", default={})
        diagnostics = metrics.get("diagnostics", {})
        model = str(diagnostics.get("model") or _model_name(workspace, row))
        cards.append(
            {
                "run_id": row.get("run_id"),
                "backend": row.get("backend"),
                "status": row.get("status"),
                "model": model,
                "role": diagnostics.get("method_role") or role_for_model(model),
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


def _best_by_role(results: list[dict[str, Any]], role: str) -> dict[str, Any] | None:
    scored = [item for item in results if item.get("role") == role and item.get("metric_value") is not None]
    if not scored:
        return None
    return min(scored, key=lambda item: float(item["metric_value"]))


def _first_by_role(results: list[dict[str, Any]], role: str) -> dict[str, Any] | None:
    for item in results:
        if item.get("role") == role:
            return item
    return None


def _format_float(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.8g}"


def _effect_text(paper_count: int, results: list[dict[str, Any]]) -> str:
    baseline = _first_by_role(results, "baseline_anchor")
    best_candidate = _best_by_role(results, INNOVATION_CANDIDATE)
    best_strong = _best_by_role(results, STRONG_REFERENCE)
    best = _best_result(results)
    if baseline and best_candidate and best_candidate.get("delta") is not None:
        candidate_delta = float(best_candidate["delta"])
        if candidate_delta > 0:
            text = (
                f"{paper_count} paper notes -> locked ETTh1 benchmark -> DLinear baseline "
                f"{_format_float(baseline.get('metric_value'))} -> {best_candidate['model']} improves "
                f"{best_candidate['metric_name']} by {_format_float(candidate_delta)}."
            )
            if best_strong and best_strong.get("metric_value") is not None:
                if float(best_strong["metric_value"]) < float(best_candidate["metric_value"]):
                    text += f" {best_strong['model']} remains the stronger reference, so the claim stays bounded."
            return text
        return (
            f"{paper_count} paper notes -> locked ETTh1 benchmark -> innovation candidate "
            f"{best_candidate['model']} does not clear DLinear and should be killed or redesigned."
        )
    if best:
        return (
            f"{paper_count} paper notes -> locked benchmark -> best current result is {best['model']} "
            f"with {best['metric_name']}={_format_float(best['metric_value'])}."
        )
    return "No completed benchmark rows are available yet. Run `ts-agent demo full-research` first."


def build_showcase(workspace: Workspace) -> dict[str, Any]:
    """Build and persist a compact benchmark showcase from current state."""
    rows = _read_leaderboard_rows(workspace)
    result_rows = _select_result_rows(workspace, rows)
    results = _result_cards(workspace, result_rows)
    best = _best_result(results)
    best_candidate = _best_by_role(results, INNOVATION_CANDIDATE)
    paper_count = len(read_index(workspace))
    decision_counts: dict[str, int] = {}
    for item in results:
        decision = str(item.get("decision") or "unknown")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1

    novelty = [
        "DLinear is locked as the baseline anchor; project innovation is labeled separately from baselines.",
        "Paper-note evidence is written into method cards before the benchmark runs.",
        "The reviewer can keep a bounded candidate while refusing to call it SOTA when a strong reference still wins.",
    ]
    usefulness = [
        "Shows the exact benchmark branch worth deepening and the branch that only clears a weak baseline.",
        "Records every run as recoverable protocol files for audit and resume.",
        "Turns local papers, baselines, metrics, and decisions into one reviewable research loop.",
    ]
    next_action = "Run `ts-agent demo full-research`, then inspect `research_state/showcase.md`."
    if best_candidate and best_candidate.get("delta") is not None and float(best_candidate["delta"]) > 0:
        next_action = f"Deepen `{best_candidate['model']}` with ablations and more datasets before making a paper-level claim."
    elif best:
        next_action = f"Use `{best['model']}` as the current reference point and redesign the next candidate."

    showcase = {
        "effect": _effect_text(paper_count, results),
        "novelty": novelty,
        "usefulness": usefulness,
        "paper_count": paper_count,
        "results": results,
        "best_result": best,
        "best_candidate": best_candidate,
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
        "TS Auto Research Agent - Benchmark Showcase",
        "===========================================",
        f"Effect: {showcase.get('effect')}",
        "",
        "Novelty:",
    ]
    lines.extend(f"- {item}" for item in showcase.get("novelty", []))
    lines.extend(["", "Use:"])
    lines.extend(f"- {item}" for item in showcase.get("usefulness", []))
    lines.extend(["", "Latest benchmark rows:", "Run      Role                  Model       Metric      Value       Delta       Decision"])
    for item in showcase.get("results", []):
        lines.append(
            f"{item.get('run_id', ''):<8} {item.get('role', ''):<21} {item.get('model', ''):<11} {item.get('metric_name', ''):<10} "
            f"{_format_float(item.get('metric_value')):<10} {_format_float(item.get('delta')):<10} {item.get('decision', '')}"
        )
    lines.extend(["", f"Next: {showcase.get('next_action')}", f"Report: {showcase.get('artifacts', {}).get('showcase_md')}"])
    return "\n".join(lines) + "\n"


def render_showcase_markdown(showcase: dict[str, Any]) -> str:
    lines = [
        "# TS Auto Research Agent Benchmark Showcase",
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
            "## Latest Benchmark Rows",
            "",
            "| Run | Role | Model | Backend | Status | Metric | Value | Baseline | Delta | Decision |",
            "|---|---|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for item in showcase.get("results", []):
        lines.append(
            f"| `{item.get('run_id')}` | `{item.get('role')}` | `{item.get('model')}` | `{item.get('backend')}` | `{item.get('status')}` | `{item.get('metric_name')}` | "
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
