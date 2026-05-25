"""Command line interface for ts-auto-research-agent."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .assets import filter_assets, scan_assets, write_asset_inventory
from .demo import run_full_research_demo, run_tsl_simple_demo
from .io_utils import read_json
from .literature import build_index
from .loop import parse_last, read_leaderboard, run_loop_budget, run_next
from .paths import Workspace
from .planner import plan_experiment
from .registry import latest_run_dir
from .scope import get_scope, scoped_assets, set_scope
from .state import init_workspace
from .taste import review_idea
from .vibe import propose_vibes


def _workspace(args: argparse.Namespace) -> Workspace:
    return Workspace.from_root(getattr(args, "root", "."))


def cmd_init(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    state = init_workspace(workspace, force=args.force)
    print(f"initialized {workspace.root}")
    print(f"state={state['status']} next_run_number={state['next_run_number']}")
    return 0


def cmd_literature_build_index(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    init_workspace(workspace)
    result = build_index(workspace, Path(args.source), limit=args.limit)
    print(f"indexed {result['count']} papers")
    print(result["output"])
    return 0


def cmd_assets_scan(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    init_workspace(workspace)
    roots = [Path(root) for root in args.scan_root]
    assets = scan_assets(roots, max_depth=args.max_depth, limit=args.limit)
    inventory = write_asset_inventory(workspace, roots, assets)
    print(f"discovered {inventory['count']} assets")
    for kind, count in sorted(inventory["kind_counts"].items()):
        print(f"{kind}: {count}")
    print(workspace.assets_json)
    return 0


def cmd_assets_list(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    assets = filter_assets(workspace, kind=args.kind, adapter=args.adapter, limit=args.limit)
    for item in assets:
        print(f"{item['id']}	{item['kind']}	{item['adapter']}	{item['path']}")
    return 0


def cmd_scope_set(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    scope = set_scope(workspace, name=args.name, asset_ids=args.asset_id, note=args.note or "")
    print(f"scope={scope['name']} assets={len(scope['asset_ids'])}")
    print(workspace.scope_json)
    return 0


def cmd_scope_show(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    scope = get_scope(workspace)
    print(f"scope={scope.get('name')} assets={len(scope.get('asset_ids', []))}")
    if scope.get("note"):
        print(scope["note"])
    for item in scoped_assets(workspace):
        print(f"{item['id']}	{item['kind']}	{item['path']}")
    return 0


def cmd_vibe_propose(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    init_workspace(workspace)
    ideas = propose_vibes(workspace, topic=args.topic, count=args.count)
    for idea in ideas:
        print(f"{idea['id']}: {idea['one_liner']}")
    return 0


def cmd_taste_review(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    init_workspace(workspace)
    review = review_idea(workspace, args.idea)
    print(f"{review['id']}: {review['status']} ({review['reason']}) total={review['total']}")
    return 0


def cmd_plan_experiment(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    init_workspace(workspace)
    plan = plan_experiment(workspace, args.idea, backend=args.backend)
    print(f"{plan['id']}: {plan['status']} backend={plan['backend']}")
    return 0


def cmd_run_next(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    result = run_next(
        workspace,
        backend=args.backend,
        topic=args.topic,
        data_csv=args.data_csv,
        column=args.column,
    )
    run = result["run"]
    metrics = result["metrics"]
    review = result["review"]
    print(f"{run['run_id']} status={metrics.get('status')} decision={review.get('decision')}")
    print(f"metric={metrics.get('metric_name')} value={metrics.get('metric_value')} delta={metrics.get('delta')}")
    print(run["run_dir"])
    return 0


def cmd_parse_last(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    parsed = parse_last(workspace)
    if parsed is None:
        print("no runs found")
        return 1
    print(parsed["run_dir"])
    metrics = parsed.get("metrics") or {}
    print(f"status={metrics.get('status')} metric={metrics.get('metric_name')} value={metrics.get('metric_value')}")
    return 0


def cmd_review_last(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    run_dir = latest_run_dir(workspace)
    if run_dir is None:
        print("no runs found")
        return 1
    review = read_json(run_dir / "review.json", default={})
    if not review:
        print(f"review not found in {run_dir}")
        return 1
    print(f"{review.get('run_id')} decision={review.get('decision')}")
    print(review.get("rationale", ""))
    return 0


def cmd_loop(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    results = run_loop_budget(
        workspace,
        budget=args.budget,
        backend=args.backend,
        topic=args.topic,
        data_csv=args.data_csv,
        column=args.column,
    )
    for result in results:
        run = result["run"]
        metrics = result["metrics"]
        review = result["review"]
        print(f"{run['run_id']} status={metrics.get('status')} decision={review.get('decision')} delta={metrics.get('delta')}")
    return 0


def cmd_leaderboard(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    text = read_leaderboard(workspace)
    print(text, end="" if text.endswith("\n") else "\n")
    return 0


def cmd_demo_tsl_simple(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    result = run_tsl_simple_demo(
        workspace,
        models=args.model,
        data=args.data,
        seq_len=args.seq_len,
        pred_len=args.pred_len,
        subset_ratio=args.subset_ratio,
        train_epochs=args.train_epochs,
    )
    print(f"demo_report={result['report_path']}")
    for item in result["results"]:
        run = item["run"]
        metrics = item["metrics"]
        review = item["review"]
        model = metrics.get("diagnostics", {}).get("model")
        mae = metrics.get("diagnostics", {}).get("mae")
        print(f"{run['run_id']} model={model} rmse={metrics.get('metric_value')} mae={mae} decision={review.get('decision')}")
    return 0


def cmd_demo_full_research(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    result = run_full_research_demo(
        workspace,
        paper_source=Path(args.paper_source),
        topic=args.topic,
        models=args.model,
        data=args.data,
        seq_len=args.seq_len,
        pred_len=args.pred_len,
        subset_ratio=args.subset_ratio,
        train_epochs=args.train_epochs,
        literature_limit=args.literature_limit,
    )
    print(f"demo_report={result['report_path']}")
    print(f"idea={result['idea']['id']} taste={result['taste_pre']['status']}")
    print(f"indexed_papers={result['literature']['count']}")
    for item in result["results"]:
        run = item["run"]
        metrics = item["metrics"]
        review = item["review"]
        model = metrics.get("diagnostics", {}).get("model")
        mae = metrics.get("diagnostics", {}).get("mae")
        print(f"{run['run_id']} model={model} rmse={metrics.get('metric_value')} mae={mae} decision={review.get('decision')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ts-agent", description="Time-series autonomous research loop.")
    parser.add_argument("--root", default=".", help="Workspace root. Defaults to current directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_p = subparsers.add_parser("init", help="Initialize research_state and runs directories.")
    init_p.add_argument("--force", action="store_true", help="Reset generated state files.")
    init_p.set_defaults(func=cmd_init)

    lit_p = subparsers.add_parser("literature", help="Literature index commands.")
    lit_sub = lit_p.add_subparsers(dest="literature_command", required=True)
    lit_build = lit_sub.add_parser("build-index", help="Build read-only paper_index.jsonl from markdown notes.")
    lit_build.add_argument("--source", required=True, help="Paper-note source directory.")
    lit_build.add_argument("--limit", type=int, default=None, help="Optional maximum number of notes to index.")
    lit_build.set_defaults(func=cmd_literature_build_index)

    assets_p = subparsers.add_parser("assets", help="Server asset discovery and registry commands.")
    assets_sub = assets_p.add_subparsers(dest="assets_command", required=True)
    assets_scan = assets_sub.add_parser("scan", help="Scan external papers, data, baselines, environments, and checkpoints into research_state/assets.json.")
    assets_scan.add_argument("--scan-root", action="append", required=True, help="Root path to scan. Can be passed multiple times.")
    assets_scan.add_argument("--max-depth", type=int, default=4)
    assets_scan.add_argument("--limit", type=int, default=1000)
    assets_scan.set_defaults(func=cmd_assets_scan)
    assets_list = assets_sub.add_parser("list", help="List discovered assets from research_state/assets.json.")
    assets_list.add_argument("--kind", default=None)
    assets_list.add_argument("--adapter", default=None)
    assets_list.add_argument("--limit", type=int, default=None)
    assets_list.set_defaults(func=cmd_assets_list)

    scope_p = subparsers.add_parser("scope", help="Active experiment scope commands.")
    scope_sub = scope_p.add_subparsers(dest="scope_command", required=True)
    scope_set = scope_sub.add_parser("set", help="Set the active experiment asset scope.")
    scope_set.add_argument("--name", required=True)
    scope_set.add_argument("--asset-id", action="append", required=True, help="Asset id to keep active. Can be passed multiple times.")
    scope_set.add_argument("--note", default="")
    scope_set.set_defaults(func=cmd_scope_set)
    scope_show = scope_sub.add_parser("show", help="Show active experiment asset scope.")
    scope_show.set_defaults(func=cmd_scope_show)

    vibe_p = subparsers.add_parser("vibe", help="Vibe idea commands.")
    vibe_sub = vibe_p.add_subparsers(dest="vibe_command", required=True)
    vibe_propose = vibe_sub.add_parser("propose", help="Propose vibe ideas.")
    vibe_propose.add_argument("--topic", default="forecasting")
    vibe_propose.add_argument("--count", type=int, default=3)
    vibe_propose.set_defaults(func=cmd_vibe_propose)

    taste_p = subparsers.add_parser("taste", help="Taste gate commands.")
    taste_sub = taste_p.add_subparsers(dest="taste_command", required=True)
    taste_review = taste_sub.add_parser("review", help="Review a vibe idea before running it.")
    taste_review.add_argument("--idea", required=True)
    taste_review.set_defaults(func=cmd_taste_review)

    plan_p = subparsers.add_parser("plan-experiment", help="Queue an experiment plan for an idea.")
    plan_p.add_argument("--idea", required=True)
    plan_p.add_argument("--backend", default="smoke", choices=["smoke", "dlinear-mini", "tsl-simple"])
    plan_p.set_defaults(func=cmd_plan_experiment)

    run_p = subparsers.add_parser("run-next", help="Run the next queued or seeded experiment.")
    run_p.add_argument("--backend", default="smoke", choices=["smoke", "dlinear-mini", "tsl-simple"])
    run_p.add_argument("--topic", default="forecasting")
    run_p.add_argument("--data-csv", default=None)
    run_p.add_argument("--column", default=None)
    run_p.set_defaults(func=cmd_run_next)

    parse_p = subparsers.add_parser("parse-last", help="Print the latest run metrics.")
    parse_p.set_defaults(func=cmd_parse_last)

    review_p = subparsers.add_parser("review-last", help="Print the latest strict reviewer decision.")
    review_p.set_defaults(func=cmd_review_last)

    loop_p = subparsers.add_parser("loop", help="Run a bounded autonomous experiment loop.")
    loop_p.add_argument("--budget", type=int, required=True)
    loop_p.add_argument("--backend", default="smoke", choices=["smoke", "dlinear-mini", "tsl-simple"])
    loop_p.add_argument("--topic", default="forecasting")
    loop_p.add_argument("--data-csv", default=None)
    loop_p.add_argument("--column", default=None)
    loop_p.set_defaults(func=cmd_loop)

    demo_p = subparsers.add_parser("demo", help="Presentation-grade demo commands.")
    demo_sub = demo_p.add_subparsers(dest="demo_command", required=True)
    demo_tsl = demo_sub.add_parser("tsl-simple", help="Run a small real Time-Series-Library_simple comparison demo.")
    demo_tsl.add_argument("--model", action="append", default=[], help="Model to run. Pass multiple times. Defaults to DLinear, PatchTST, MLP.")
    demo_tsl.add_argument("--data", default="ETTh1.csv")
    demo_tsl.add_argument("--seq-len", type=int, default=24)
    demo_tsl.add_argument("--pred-len", type=int, default=24)
    demo_tsl.add_argument("--subset-ratio", type=float, default=0.05)
    demo_tsl.add_argument("--train-epochs", type=int, default=1)
    demo_tsl.set_defaults(func=cmd_demo_tsl_simple)

    demo_full = demo_sub.add_parser("full-research", help="Run the complete literature-to-experiment research demo.")
    demo_full.add_argument("--paper-source", default="/home/xu/autoresearch-agent/knowledge-base/paper-notes")
    demo_full.add_argument("--literature-limit", type=int, default=50)
    demo_full.add_argument("--topic", default="forecasting")
    demo_full.add_argument("--model", action="append", default=[], help="Model to run. Pass multiple times. Defaults to DLinear, PatchTST, MLP.")
    demo_full.add_argument("--data", default="ETTh1.csv")
    demo_full.add_argument("--seq-len", type=int, default=24)
    demo_full.add_argument("--pred-len", type=int, default=24)
    demo_full.add_argument("--subset-ratio", type=float, default=0.05)
    demo_full.add_argument("--train-epochs", type=int, default=1)
    demo_full.set_defaults(func=cmd_demo_full_research)

    board_p = subparsers.add_parser("leaderboard", help="Print leaderboard.csv.")
    board_p.set_defaults(func=cmd_leaderboard)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
