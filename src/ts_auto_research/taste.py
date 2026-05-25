"""Taste evaluation before and after experiments."""

from __future__ import annotations

from typing import Any

from .io_utils import read_json, write_json, write_yaml
from .paths import Workspace
from .vibe import get_vibe

TASTE_FIELDS = [
    "interestingness",
    "non_obviousness",
    "importance",
    "story_potential",
    "experimentability",
    "defensibility",
    "trend_alignment",
    "personal_fit",
]


def _score_idea(idea: dict[str, Any]) -> dict[str, int]:
    text = " ".join(str(idea.get(key, "")) for key in ["one_liner", "core_tension", "risk", "possible_paper_shape"]).lower()
    scores = {
        "interestingness": 4,
        "non_obviousness": 4 if any(word in text for word in ["not", "before", "instead", "compression", "credit"]) else 3,
        "importance": 4 if any(word in text for word in ["forecast", "online", "supervision", "agent"]) else 3,
        "story_potential": 4,
        "experimentability": 4 if "experiment" in text or "test" in text or "forecast" in text else 3,
        "defensibility": 3 if "could" in text or "risk" in text else 4,
        "trend_alignment": 4 if any(word in text for word in ["online", "long-context", "agent", "supervision"]) else 3,
        "personal_fit": 4,
    }
    return scores


def gate_status(scores: dict[str, int]) -> tuple[str, str]:
    if scores["interestingness"] < 3:
        return "blocked", "interestingness below threshold"
    if scores["non_obviousness"] < 3:
        return "blocked", "non_obviousness below threshold"
    if scores["experimentability"] < 3:
        return "defer", "experimentability below threshold"
    if scores["defensibility"] < 3:
        return "needs_defense", "defensibility below threshold"
    return "approved", "passes taste gate"


def review_idea(workspace: Workspace, idea_id: str) -> dict[str, Any]:
    idea = get_vibe(workspace, idea_id)
    scores = _score_idea(idea)
    status, reason = gate_status(scores)
    review = {
        "id": f"taste_pre_{idea_id}",
        "idea_id": idea_id,
        "phase": "pre",
        "scores": scores,
        "total": sum(scores.values()),
        "status": status,
        "reason": reason,
        "if_success_claim": "A successful experiment should support a research-level belief change, not only a better metric.",
        "if_failure_learning": "A failed experiment should narrow whether the idea is a story problem, method problem, or benchmark problem.",
    }
    reviews = read_json(workspace.taste_json, default=[])
    reviews = [item for item in reviews if item.get("id") != review["id"]] + [review]
    write_json(workspace.taste_json, reviews)
    write_yaml(workspace.taste_yaml, reviews)
    return review


def get_pre_taste(workspace: Workspace, idea_id: str) -> dict[str, Any] | None:
    for review in read_json(workspace.taste_json, default=[]):
        if review.get("idea_id") == idea_id and review.get("phase") == "pre":
            return review
    return None


def post_taste(run: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    status = metrics.get("status", "completed")
    metric = metrics.get("metric_value")
    baseline = metrics.get("baseline")
    delta = None if metric is None or baseline is None else float(baseline) - float(metric)
    improved = bool(delta is not None and delta > 0)
    blocked = status == "blocked"
    surprise = 1 if blocked else (4 if improved and abs(delta or 0) > 0.02 else 2)
    paper_potential = 1 if blocked else (4 if improved else 2)
    next_move = "needs_human_confirmation" if blocked else ("deepen" if improved else "kill")
    return {
        "id": f"taste_post_{run['run_id']}",
        "run_id": run["run_id"],
        "phase": "post",
        "did_result_change_belief": improved,
        "surprise_level": surprise,
        "paper_potential_after_result": paper_potential,
        "strongest_claim_now": "The direction has measurable signal." if improved else "The current experiment does not yet support the idea.",
        "weakest_point": metrics.get("blocker", "Metric gain alone is not enough without a stronger claim."),
        "next_best_move": next_move,
    }
