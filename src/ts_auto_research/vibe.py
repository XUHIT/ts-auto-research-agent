"""Vibe idea generation."""

from __future__ import annotations

from typing import Any

from .io_utils import read_json, write_json, write_yaml
from .literature import read_index
from .methods import select_literature_evidence
from .paths import Workspace


def _signals_for_topic(workspace: Workspace, topic: str, limit: int = 5) -> list[str]:
    records = read_index(workspace, limit=1000)
    evidence = select_literature_evidence(records, limit=limit)
    return [f"{item['title']} ({item['venue']}): {item['lesson']}" for item in evidence]


def propose_vibes(workspace: Workspace, topic: str, count: int = 3) -> list[dict[str, Any]]:
    existing = read_json(workspace.vibe_json, default=[])
    start = len(existing) + 1
    signals = _signals_for_topic(workspace, topic)
    templates = [
        (
            "A publishable forecasting agent should test one literature-backed residual against a locked DLinear anchor before scaling the search.",
            "DLinear is strong because simple structure matters; a candidate must add a precise mechanism, such as known-horizon calendar context, without hiding inside a large backbone.",
            "Benchmark-first / lightweight method",
            "Could be only a DLinear improvement and not a SOTA claim if PatchTST remains stronger.",
        ),
        (
            "Online forecasting should decide when not to adapt before inventing another adapter.",
            "Existing methods optimize update rules, while the decision to update may be the higher-level bottleneck.",
            "Problem-first / decision policy",
            "Could look like a selector unless tied to regime evidence and cost-risk metrics.",
        ),
        (
            "Delayed supervision contains credit structure that should not be averaged away before adaptation.",
            "Multi-horizon feedback matures late and may contain horizon/age-specific signals.",
            "Mechanism-first / structured supervision",
            "Could be seen as attention over memory unless the compression loss is measured first.",
        ),
        (
            "A time-series research agent should optimize for belief change, not just metric gain.",
            "Cheap experiments can generate local optima; taste gates force experiments to answer research questions.",
            "Meta-research / agent protocol",
            "Needs concrete experiment-loop evidence, not just methodology prose.",
        ),
    ]
    ideas: list[dict[str, Any]] = []
    for offset in range(count):
        one_liner, core_tension, paper_shape, risk = templates[offset % len(templates)]
        idx = start + offset
        idea = {
            "id": f"vibe_{idx:03d}",
            "topic": topic,
            "one_liner": one_liner,
            "why_exciting": "It creates a paper-level question before committing to a method module.",
            "core_tension": core_tension,
            "possible_paper_shape": paper_shape,
            "risk": risk,
            "literature_signals": signals,
            "status": "proposed",
        }
        ideas.append(idea)
    all_ideas = existing + ideas
    write_json(workspace.vibe_json, all_ideas)
    write_yaml(workspace.vibe_yaml, all_ideas)
    return ideas


def get_vibe(workspace: Workspace, idea_id: str) -> dict[str, Any]:
    for idea in read_json(workspace.vibe_json, default=[]):
        if idea.get("id") == idea_id:
            return idea
    raise KeyError(f"Unknown vibe idea: {idea_id}")
