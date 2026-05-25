from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ts_auto_research.assets import filter_assets, scan_assets, write_asset_inventory
from ts_auto_research.literature import build_index, read_index
from ts_auto_research.demo import run_public_mini_demo
from ts_auto_research.loop import run_loop_budget, run_next
from ts_auto_research.paths import Workspace
from ts_auto_research.multiagent import read_multiagent_trace, run_research_crew
from ts_auto_research.reviewer import decide_next_action
from ts_auto_research.scope import scoped_assets, set_scope
from ts_auto_research.state import init_workspace
from ts_auto_research.taste import review_idea
from ts_auto_research.vibe import propose_vibes


class CoreLoopTests(unittest.TestCase):
    def workspace(self, tmp: str) -> Workspace:
        return Workspace.from_root(tmp)

    def write_note_source(self, tmp_path: Path) -> Path:
        source = tmp_path / "paper-notes" / "ICLR2025"
        source.mkdir(parents=True)
        (source / "forecasting_note.md").write_text(
            "# Long Context Forecasting\n\n"
            "## Contribution\n"
            "Treats long history as compressed predictive state for forecasting.\n\n"
            "## Keywords\n"
            "time series, forecasting, long-context\n\n"
            "## Limitations\n"
            "May overfit irrelevant context without a taste gate.\n",
            encoding="utf-8",
        )
        return tmp_path / "paper-notes"

    def test_init_creates_state_files(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = self.workspace(tmp)
            init_workspace(workspace)
            self.assertTrue(workspace.research_state.exists())
            self.assertTrue(workspace.leaderboard_csv.exists())
            self.assertTrue(workspace.trajectory_jsonl.exists())

    def test_literature_vibe_and_taste(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = self.workspace(tmp)
            init_workspace(workspace)
            source = self.write_note_source(Path(tmp))
            result = build_index(workspace, source)
            self.assertEqual(result["count"], 1)
            self.assertEqual(len(read_index(workspace)), 1)
            ideas = propose_vibes(workspace, topic="forecasting", count=3)
            self.assertEqual(len(ideas), 3)
            review = review_idea(workspace, ideas[0]["id"])
            self.assertIn(review["status"], {"approved", "blocked", "defer", "needs_defense"})

    def test_smoke_loop_creates_two_runs_and_protocol_files(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = self.workspace(tmp)
            init_workspace(workspace)
            source = self.write_note_source(Path(tmp))
            build_index(workspace, source)
            results = run_loop_budget(workspace, budget=2, backend="smoke", topic="forecasting")
            self.assertEqual(len(results), 2)
            for run_number in ["run_0001", "run_0002"]:
                run_dir = workspace.run_dir(run_number)
                self.assertTrue((run_dir / "vibe_idea.yaml").exists())
                self.assertTrue((run_dir / "taste_pre.yaml").exists())
                self.assertTrue((run_dir / "experiment_plan.yaml").exists())
                self.assertTrue((run_dir / "command.sh").exists())
                self.assertTrue((run_dir / "metrics.json").exists())
                self.assertTrue((run_dir / "taste_post.yaml").exists())
                self.assertTrue((run_dir / "review.md").exists())
            rows = workspace.leaderboard_csv.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(rows), 3)
            trajectory = workspace.trajectory_jsonl.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(trajectory), 2)
            self.assertEqual(json.loads(trajectory[0])["next_action"], "continue")

    def test_dlinear_mini_reports_missing_data_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = self.workspace(tmp)
            init_workspace(workspace)
            result = run_next(workspace, backend="dlinear-mini", topic="forecasting")
            self.assertEqual(result["metrics"]["status"], "blocked")
            self.assertEqual(result["review"]["decision"], "needs_human_confirmation")
            self.assertIn("--data-csv", result["metrics"]["blocker"])

    def test_dlinear_mini_runs_with_csv(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = self.workspace(tmp)
            init_workspace(workspace)
            csv_path = Path(tmp) / "series.csv"
            rows = ["t,value"]
            for idx in range(48):
                rows.append(f"{idx},{10 + 0.1 * idx + ((idx % 6) - 3) * 0.05:.4f}")
            csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            result = run_next(workspace, backend="dlinear-mini", topic="forecasting", data_csv=str(csv_path), column="value")
            self.assertEqual(result["metrics"]["status"], "completed")
            self.assertIsInstance(result["metrics"]["metric_value"], float)
            self.assertTrue(workspace.run_dir("run_0001").joinpath("metrics.json").exists())

    def test_asset_scan_registers_external_resources(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = self.workspace(tmp)
            init_workspace(workspace)
            root = Path(tmp) / "external"
            repo = root / "baseline_repo"
            (repo / ".git").mkdir(parents=True)
            (repo / "models").mkdir()
            (repo / "run.py").write_text("print('run')\n", encoding="utf-8")
            data_dir = root / "benchmark_datasets" / "ETT"
            data_dir.mkdir(parents=True)
            (data_dir / "ETTh1.csv").write_text("x\n1\n", encoding="utf-8")
            ckpt_dir = root / "checkpoints" / "model_a"
            ckpt_dir.mkdir(parents=True)
            (ckpt_dir / "checkpoint.pth").write_bytes(b"checkpoint")
            assets = scan_assets([root], max_depth=4, limit=100)
            write_asset_inventory(workspace, [root], assets)
            kinds = {item["kind"] for item in assets}
            self.assertIn("baseline_repo", kinds)
            self.assertIn("data_benchmark", kinds)
            self.assertIn("model_checkpoint", kinds)
            self.assertGreaterEqual(len(filter_assets(workspace, kind="baseline_repo")), 1)

    def test_scope_limits_active_assets(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = self.workspace(tmp)
            init_workspace(workspace)
            root = Path(tmp) / "external"
            repo_a = root / "Time-Series-Library_simple"
            repo_b = root / "TSFM_EVAL"
            for repo in [repo_a, repo_b]:
                (repo / ".git").mkdir(parents=True)
                (repo / "models").mkdir()
                (repo / "run.py").write_text("print('run')\n", encoding="utf-8")
            assets = scan_assets([root], max_depth=3, limit=20)
            write_asset_inventory(workspace, [root], assets)
            ids = [item["id"] for item in assets if item["kind"] == "baseline_repo"]
            self.assertEqual(len(ids), 2)
            set_scope(workspace, "general-ts", ids[:1], note="test scope")
            active = scoped_assets(workspace)
            self.assertEqual(len(active), 1)
            self.assertEqual(active[0]["id"], ids[0])

    def test_baseline_anchor_reviewer_continues(self) -> None:
        metrics = {"status": "completed", "metric_value": 1.0, "delta": 0.0, "diagnostics": {"baseline_anchor": True}}
        self.assertEqual(decide_next_action(metrics, {}), "continue")


    def test_multiagent_orchestration_writes_recoverable_trace(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = self.workspace(tmp)
            init_workspace(workspace)
            source = self.write_note_source(Path(tmp))
            trace = run_research_crew(
                workspace,
                topic="forecasting",
                paper_source=source,
                literature_limit=1,
                models=["DLinear"],
                execute_demo=False,
            )
            self.assertEqual(trace["mode"], "dry-run")
            self.assertTrue(workspace.multiagent_trace_json.exists())
            self.assertTrue(workspace.multiagent_trace_md.exists())
            agent_ids = {task["agent_id"] for task in trace["tasks"]}
            self.assertIn("literature_curator", agent_ids)
            self.assertIn("experiment_runner", agent_ids)
            self.assertIn("synthesis_agent", agent_ids)
            self.assertIn("ts-agent demo full-research", trace["execution_plan"]["command"])
            self.assertEqual(read_multiagent_trace(workspace)["run_id"], trace["run_id"])


    def test_public_mini_demo_runs_full_portable_loop(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = self.workspace(tmp)
            init_workspace(workspace)
            source = self.write_note_source(Path(tmp))
            csv_path = Path(tmp) / "series.csv"
            rows = ["t,value"]
            for idx in range(60):
                value = 10 + 0.08 * idx + 0.004 * idx * idx
                rows.append(f"{idx},{value:.4f}")
            csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            result = run_public_mini_demo(workspace, paper_source=source, data_csv=csv_path, budget=1)
            self.assertTrue(Path(result["report_path"]).exists())
            self.assertTrue(workspace.multiagent_trace_json.exists())
            trace = result["trace"]
            self.assertEqual(trace["mode"], "execute-demo")
            self.assertEqual(trace["execution_plan"]["backend"], "dlinear-mini")
            runner = next(task for task in trace["tasks"] if task["agent_id"] == "experiment_runner")
            reviewer = next(task for task in trace["tasks"] if task["agent_id"] == "result_reviewer")
            self.assertEqual(runner["status"], "completed")
            self.assertEqual(reviewer["status"], "completed")
            self.assertEqual(len(runner["data"]["run_ids"]), 1)
            run_id = runner["data"]["run_ids"][0]
            self.assertTrue(workspace.run_dir(run_id).joinpath("review.md").exists())


if __name__ == "__main__":
    unittest.main()
