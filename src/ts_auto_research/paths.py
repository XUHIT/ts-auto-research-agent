"""Runtime path handling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Workspace:
    root: Path

    @classmethod
    def from_root(cls, root: str | Path = ".") -> "Workspace":
        return cls(Path(root).expanduser().resolve())

    @property
    def research_state(self) -> Path:
        return self.root / "research_state"

    @property
    def runs(self) -> Path:
        return self.root / "runs"

    @property
    def literature(self) -> Path:
        return self.root / "literature"

    @property
    def paper_index(self) -> Path:
        return self.literature / "paper_index.jsonl"

    @property
    def selected_context(self) -> Path:
        return self.literature / "selected_context.md"

    @property
    def state_yaml(self) -> Path:
        return self.research_state / "state.yaml"

    @property
    def state_json(self) -> Path:
        return self.research_state / "state.json"

    @property
    def vibe_yaml(self) -> Path:
        return self.research_state / "vibe_ideas.yaml"

    @property
    def vibe_json(self) -> Path:
        return self.research_state / "vibe_ideas.json"

    @property
    def taste_yaml(self) -> Path:
        return self.research_state / "taste_reviews.yaml"

    @property
    def taste_json(self) -> Path:
        return self.research_state / "taste_reviews.json"

    @property
    def queue_yaml(self) -> Path:
        return self.research_state / "experiment_queue.yaml"

    @property
    def queue_json(self) -> Path:
        return self.research_state / "experiment_queue.json"

    @property
    def multiagent_trace_json(self) -> Path:
        return self.research_state / "multiagent_trace.json"

    @property
    def multiagent_trace_md(self) -> Path:
        return self.research_state / "multiagent_trace.md"

    @property
    def baseline_registry_json(self) -> Path:
        return self.research_state / "baseline_registry.json"

    @property
    def baseline_registry_yaml(self) -> Path:
        return self.research_state / "baseline_registry.yaml"

    @property
    def showcase_json(self) -> Path:
        return self.research_state / "showcase.json"

    @property
    def showcase_md(self) -> Path:
        return self.research_state / "showcase.md"

    @property
    def scope_yaml(self) -> Path:
        return self.research_state / "experiment_scope.yaml"

    @property
    def scope_json(self) -> Path:
        return self.research_state / "experiment_scope.json"

    @property
    def assets_yaml(self) -> Path:
        return self.research_state / "assets.yaml"

    @property
    def assets_json(self) -> Path:
        return self.research_state / "assets.json"

    @property
    def leaderboard_csv(self) -> Path:
        return self.research_state / "leaderboard.csv"

    @property
    def trajectory_jsonl(self) -> Path:
        return self.research_state / "trajectory.jsonl"

    @property
    def claims_yaml(self) -> Path:
        return self.research_state / "claims.yaml"

    @property
    def claims_json(self) -> Path:
        return self.research_state / "claims.json"

    @property
    def demo_packet_json(self) -> Path:
        return self.research_state / "demo_packet.json"

    @property
    def research_cockpit_html(self) -> Path:
        return self.root / "docs" / "demo_results" / "research_cockpit.html"

    def run_dir(self, run_id: str) -> Path:
        return self.runs / run_id
