"""Method roles and literature-grounded benchmark cards."""

from __future__ import annotations

from typing import Any

BASELINE_ANCHOR = "baseline_anchor"
STRONG_REFERENCE = "strong_reference"
INNOVATION_CANDIDATE = "innovation_candidate"
BASELINE_CONTROL = "baseline_control"
UNKNOWN_METHOD = "unknown_method"

METHOD_CATALOG: dict[str, dict[str, Any]] = {
    "DLinear": {
        "role": BASELINE_ANCHOR,
        "display_role": "DLinear baseline anchor",
        "claim": "No innovation claim. This run locks the same-protocol metric anchor.",
        "acceptance": "Must complete and define the comparison baseline.",
    },
    "PatchTST": {
        "role": STRONG_REFERENCE,
        "display_role": "strong published reference",
        "claim": "Reference arm for checking whether a lightweight candidate is only beating a weak baseline.",
        "acceptance": "Used as a strong comparator, not counted as this project innovation.",
    },
    "CalDLinear": {
        "role": INNOVATION_CANDIDATE,
        "display_role": "literature-grounded innovation candidate",
        "claim": (
            "Calendar-conditioned DLinear keeps the linear anchor and adds a small future-time residual, "
            "testing whether known horizon calendar structure improves a simple baseline without hiding behind a large backbone."
        ),
        "acceptance": (
            "Accept only as a bounded candidate if it improves RMSE over DLinear under the locked benchmark protocol; "
            "do not claim SOTA unless it also beats the strong reference arm."
        ),
    },
    "PSLinear": {
        "role": INNOVATION_CANDIDATE,
        "display_role": "literature-grounded innovation candidate",
        "claim": "Predictive-state Linear keeps DLinear raw-scale behavior and adds a selective instance-normalized branch.",
        "acceptance": "Accept only if the selective branch improves DLinear and does not degrade secondary diagnostics.",
    },
    "RLinear": {
        "role": BASELINE_CONTROL,
        "display_role": "normalization control",
        "claim": "Control arm for reversible instance normalization, not a new contribution.",
        "acceptance": "Used to test whether the candidate is better than plain reversible normalization.",
    },
    "MLP": {
        "role": BASELINE_CONTROL,
        "display_role": "simple nonlinear control",
        "claim": "Control arm for a small nonlinear baseline.",
        "acceptance": "Useful only if it changes the interpretation of the baseline suite.",
    },
    "LSTNet": {
        "role": BASELINE_CONTROL,
        "display_role": "legacy architecture control",
        "claim": "Control arm for an older CNN/RNN temporal-pattern architecture.",
        "acceptance": "Useful as a rejected branch or diagnostic control, not as the primary innovation.",
    },
}

EVIDENCE_RULES: list[tuple[tuple[str, ...], str]] = [
    (("iclr_2022_revin", "revin"), "Reversible normalization can help distribution shift, but its lookback-to-horizon statistic assumption must be tested."),
    (("icml_2024_linearanalysis", "analysis of linear time series"), "Recent linear-model analysis suggests constraints, normalization, and simple residual structure may matter more than adding heavy backbones."),
    (("icml_2024_sin", "selective and interpretable normalization"), "Selective normalization argues against one fixed statistic for every series and motivates gated lightweight adapters."),
    (("aaai_2026_apt", "affine prototype-timestamp"), "Prototype or timestamp-conditioned affine structure motivates using known horizon context instead of only local instance statistics."),
    (("wsdm_2026_timereasoner", "timereasoner"), "Some forecasting settings need absolute scale; a candidate must preserve raw-scale information rather than blindly normalize it away."),
    (("kdd_2023_tsmixer", "tsmixer"), "Strong MLP/patch baselines show that lightweight methods need controlled comparisons against PatchTST-style references."),
    (("patchtst",), "Patch-based strong references prevent overstating a DLinear-only improvement."),
]


def role_for_model(model: str) -> str:
    return METHOD_CATALOG.get(model, {}).get("role", UNKNOWN_METHOD)


def display_role_for_model(model: str) -> str:
    return METHOD_CATALOG.get(model, {}).get("display_role", UNKNOWN_METHOD.replace("_", " "))


def is_innovation_candidate(model: str) -> bool:
    return role_for_model(model) == INNOVATION_CANDIDATE


def default_full_research_models() -> list[str]:
    return ["DLinear", "PatchTST", "CalDLinear"]


def select_literature_evidence(records: list[dict[str, Any]], limit: int = 5) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    seen_lessons: set[str] = set()
    for record in records:
        key = " ".join(str(record.get(field, "")) for field in ["title", "venue", "path"]).lower()
        for keywords, lesson in EVIDENCE_RULES:
            if any(keyword in key for keyword in keywords) and lesson not in seen_lessons:
                evidence.append(
                    {
                        "title": str(record.get("title", "untitled")),
                        "venue": str(record.get("venue", "unknown")),
                        "lesson": lesson,
                    }
                )
                seen_lessons.add(lesson)
                break
        if len(evidence) >= limit:
            break
    if evidence:
        return evidence
    return [
        {
            "title": "Curated time-series paper notes",
            "venue": "local knowledge base",
            "lesson": "Use the paper library to define the baseline, candidate mechanism, risk, and acceptance criteria before running experiments.",
        }
    ]


def method_card_for_model(model: str, literature_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    catalog = METHOD_CATALOG.get(model, {})
    records = literature_records or []
    return {
        "model": model,
        "role": catalog.get("role", UNKNOWN_METHOD),
        "display_role": catalog.get("display_role", UNKNOWN_METHOD.replace("_", " ")),
        "claim": catalog.get("claim", "Unregistered method; treat as exploratory until a method card is written."),
        "acceptance": catalog.get("acceptance", "Requires an explicit baseline, metric, and reviewer decision."),
        "literature_evidence": select_literature_evidence(records),
    }
