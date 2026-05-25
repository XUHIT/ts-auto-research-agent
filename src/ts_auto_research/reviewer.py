"""Run review logic with a constrained action vocabulary."""

from __future__ import annotations

from typing import Any

ALLOWED_ACTIONS = {"continue", "kill", "pivot", "needs_human_confirmation"}


def decide_next_action(metrics: dict[str, Any], taste_post: dict[str, Any]) -> str:
    if metrics.get("status") == "blocked":
        return "needs_human_confirmation"
    if metrics.get("diagnostics", {}).get("baseline_anchor"):
        return "continue"
    delta = metrics.get("delta")
    metric = metrics.get("metric_value")
    if metric is None or delta is None:
        return "needs_human_confirmation"
    try:
        delta_value = float(delta)
    except (TypeError, ValueError):
        return "needs_human_confirmation"
    paper_potential = int(taste_post.get("paper_potential_after_result", 0))
    surprise = int(taste_post.get("surprise_level", 0))
    if delta_value > 0 and paper_potential >= 3:
        return "continue"
    if delta_value <= 0 and surprise <= 2:
        return "kill"
    return "pivot"


def review_run(run: dict[str, Any], metrics: dict[str, Any], taste_post: dict[str, Any]) -> dict[str, Any]:
    decision = decide_next_action(metrics, taste_post)
    if decision not in ALLOWED_ACTIONS:
        decision = "needs_human_confirmation"
    return {
        "id": f"review_{run['run_id']}",
        "run_id": run["run_id"],
        "decision": decision,
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "rationale": _rationale(decision, metrics, taste_post),
        "next_action": decision,
    }


def _rationale(decision: str, metrics: dict[str, Any], taste_post: dict[str, Any]) -> str:
    if decision == "needs_human_confirmation":
        return metrics.get("blocker", "The run needs a human decision before the loop can continue.")
    if decision == "continue":
        if metrics.get("diagnostics", {}).get("baseline_anchor"):
            return "Baseline anchor established for the controlled comparison suite."
        return "Metric improved and post-taste suggests the result can support a research trajectory."
    if decision == "kill":
        return "The run did not improve the metric and did not create enough surprise to justify more budget."
    return "The result has some signal but the current hypothesis shape should change before spending more budget."


def review_to_markdown(review: dict[str, Any], metrics: dict[str, Any], taste_post: dict[str, Any]) -> str:
    lines = [
        f"# Review {review['run_id']}",
        "",
        f"Decision: `{review['decision']}`",
        "",
        "## Metric",
        f"- Status: {metrics.get('status')}",
        f"- Metric: {metrics.get('metric_name')} = {metrics.get('metric_value')}",
        f"- Baseline: {metrics.get('baseline')}",
        f"- Delta: {metrics.get('delta')}",
        "",
        "## Taste After Result",
        f"- Belief changed: {taste_post.get('did_result_change_belief')}",
        f"- Surprise level: {taste_post.get('surprise_level')}",
        f"- Paper potential: {taste_post.get('paper_potential_after_result')}",
        "",
        "## Rationale",
        review.get("rationale", ""),
        "",
        "## Allowed Reviewer Outputs",
    ]
    for action in sorted(ALLOWED_ACTIONS):
        lines.append(f"- `{action}`")
    return "\n".join(lines) + "\n"
