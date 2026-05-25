"""Experiment backends for the research loop."""

from __future__ import annotations

import csv
import math
from pathlib import Path
import re
import shlex
import statistics
import subprocess
import time
from typing import Any

TSL_SIMPLE_REPO = Path("/home/xu/pytorch_projects/my_time_series_lab/Time-Series-Library_simple")
TSL_SIMPLE_PYTHON = Path("/home/xu/anaconda3/envs/time_series_library/bin/python")


def _safe_run_number(run_id: str) -> int:
    try:
        return int(run_id.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return 1


def run_smoke_backend(run_id: str, plan: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Return deterministic synthetic metrics for validating the loop."""
    started = time.perf_counter()
    run_number = _safe_run_number(run_id)
    hypothesis_id = str(plan.get("hypothesis_id", "hyp_unknown"))
    signal = (sum(ord(ch) for ch in hypothesis_id) % 9) * 0.004
    baseline = 1.0
    metric_value = round(max(0.15, baseline - 0.055 - min(run_number, 12) * 0.012 + signal), 6)
    wall_time = round(time.perf_counter() - started, 6)
    delta = round(baseline - metric_value, 6)
    metrics = {
        "status": "completed",
        "backend": "smoke",
        "metric_name": plan.get("metric_name", "mse"),
        "metric_value": metric_value,
        "baseline": baseline,
        "delta": delta,
        "optimize": plan.get("optimize", "minimize"),
        "wall_time_sec": wall_time,
        "diagnostics": {
            "synthetic": True,
            "run_number": run_number,
            "hypothesis_signal": signal,
        },
    }
    stdout = "\n".join(
        [
            f"backend=smoke run_id={run_id}",
            f"hypothesis_id={hypothesis_id}",
            f"metric_name={metrics['metric_name']} metric_value={metric_value}",
            f"baseline={baseline} delta={delta}",
        ]
    ) + "\n"
    return metrics, stdout


def _coerce_float(value: str) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isfinite(result):
        return result
    return None


def _read_numeric_series(path: Path, column: str | None = None) -> list[float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample)
    except csv.Error:
        dialect = csv.excel
    try:
        has_header = csv.Sniffer().has_header(sample)
    except csv.Error:
        has_header = False

    rows = list(csv.reader(text.splitlines(), dialect))
    if not rows:
        return []

    if has_header:
        header = rows[0]
        data_rows = rows[1:]
        if column is not None and column not in header:
            raise ValueError(f"column `{column}` not found in {path}")
        candidate_indices = [header.index(column)] if column is not None else list(range(len(header)))
    else:
        data_rows = rows
        candidate_indices = [int(column)] if column and column.isdigit() else list(range(max(len(row) for row in rows)))

    best: list[float] = []
    for idx in candidate_indices:
        series: list[float] = []
        for row in data_rows:
            if idx >= len(row):
                continue
            value = _coerce_float(row[idx])
            if value is not None:
                series.append(value)
        if len(series) > len(best):
            best = series
    return best


def _mse(predictions: list[float], targets: list[float]) -> float:
    return sum((pred - actual) ** 2 for pred, actual in zip(predictions, targets)) / len(targets)


def _mae(predictions: list[float], targets: list[float]) -> float:
    return sum(abs(pred - actual) for pred, actual in zip(predictions, targets)) / len(targets)


def _last_value_forecast(history: list[float]) -> float:
    return history[-1]


def _dlinear_mini_forecast(history: list[float], window: int) -> float:
    recent = history[-window:] if len(history) >= window else history[:]
    if len(recent) < 4:
        return recent[-1]
    half = max(1, len(recent) // 2)
    first = statistics.fmean(recent[:half])
    second = statistics.fmean(recent[-half:])
    slope = (second - first) / half
    trend_next = recent[-1] + slope
    residuals = [value - statistics.fmean(recent[max(0, i - half + 1) : i + 1]) for i, value in enumerate(recent)]
    seasonal_hint = statistics.fmean(residuals[-min(half, len(residuals)) :])
    return trend_next + 0.25 * seasonal_hint


def run_dlinear_mini_backend(
    run_id: str,
    plan: dict[str, Any],
    data_csv: str | Path | None = None,
    column: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Run a minimal real-valued time-series benchmark using stdlib only.

    This backend is intentionally small: it proves that the agent can connect to
    real CSV data before introducing heavier model and benchmark dependencies.
    """
    started = time.perf_counter()
    if data_csv is None:
        metrics = {
            "status": "blocked",
            "backend": "dlinear-mini",
            "metric_name": plan.get("metric_name", "mse"),
            "metric_value": None,
            "baseline": None,
            "delta": None,
            "optimize": plan.get("optimize", "minimize"),
            "wall_time_sec": round(time.perf_counter() - started, 6),
            "blocker": "dlinear-mini requires --data-csv PATH for the first real time-series run.",
        }
        stdout = "backend=dlinear-mini\nstatus=blocked\nreason=missing --data-csv PATH\n"
        return metrics, stdout

    path = Path(data_csv).expanduser().resolve()
    if not path.exists():
        metrics = {
            "status": "blocked",
            "backend": "dlinear-mini",
            "metric_name": plan.get("metric_name", "mse"),
            "metric_value": None,
            "baseline": None,
            "delta": None,
            "optimize": plan.get("optimize", "minimize"),
            "wall_time_sec": round(time.perf_counter() - started, 6),
            "blocker": f"data_csv not found: {path}",
        }
        stdout = f"backend=dlinear-mini\nstatus=blocked\nreason=data_csv not found: {path}\n"
        return metrics, stdout

    try:
        series = _read_numeric_series(path, column=column)
    except ValueError as exc:
        metrics = {
            "status": "blocked",
            "backend": "dlinear-mini",
            "metric_name": plan.get("metric_name", "mse"),
            "metric_value": None,
            "baseline": None,
            "delta": None,
            "optimize": plan.get("optimize", "minimize"),
            "wall_time_sec": round(time.perf_counter() - started, 6),
            "blocker": str(exc),
        }
        return metrics, f"backend=dlinear-mini\nstatus=blocked\nreason={exc}\n"

    if len(series) < 24:
        metrics = {
            "status": "blocked",
            "backend": "dlinear-mini",
            "metric_name": plan.get("metric_name", "mse"),
            "metric_value": None,
            "baseline": None,
            "delta": None,
            "optimize": plan.get("optimize", "minimize"),
            "wall_time_sec": round(time.perf_counter() - started, 6),
            "blocker": f"need at least 24 numeric observations, found {len(series)}",
        }
        return metrics, f"backend=dlinear-mini\nstatus=blocked\nreason=only {len(series)} numeric observations\n"

    split = max(12, int(len(series) * 0.75))
    split = min(split, len(series) - 6)
    window = int(plan.get("config", {}).get("context_window", 12))
    targets: list[float] = []
    baseline_preds: list[float] = []
    model_preds: list[float] = []
    for idx in range(split, len(series)):
        history = series[:idx]
        actual = series[idx]
        targets.append(actual)
        baseline_preds.append(_last_value_forecast(history))
        model_preds.append(_dlinear_mini_forecast(history, window=window))

    baseline_mse = _mse(baseline_preds, targets)
    model_mse = _mse(model_preds, targets)
    delta = baseline_mse - model_mse
    metrics = {
        "status": "completed",
        "backend": "dlinear-mini",
        "metric_name": plan.get("metric_name", "mse"),
        "metric_value": round(model_mse, 8),
        "baseline": round(baseline_mse, 8),
        "delta": round(delta, 8),
        "optimize": plan.get("optimize", "minimize"),
        "wall_time_sec": round(time.perf_counter() - started, 6),
        "diagnostics": {
            "data_csv": str(path),
            "n_observations": len(series),
            "train_size": split,
            "test_size": len(targets),
            "context_window": window,
            "mae": round(_mae(model_preds, targets), 8),
            "baseline_mae": round(_mae(baseline_preds, targets), 8),
        },
    }
    stdout = "\n".join(
        [
            f"backend=dlinear-mini run_id={run_id}",
            f"data_csv={path}",
            f"n_observations={len(series)} train_size={split} test_size={len(targets)}",
            f"metric_name={metrics['metric_name']} metric_value={metrics['metric_value']}",
            f"baseline={metrics['baseline']} delta={metrics['delta']}",
        ]
    ) + "\n"
    return metrics, stdout


def _parse_tsl_metrics(stdout: str) -> dict[str, float] | None:
    matches = re.findall(r"rmse:([0-9.eE+-]+),\s*mae:([0-9.eE+-]+)", stdout)
    if not matches:
        return None
    rmse, mae = matches[-1]
    return {"rmse": float(rmse), "mae": float(mae)}


def _format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def run_tsl_simple_backend(run_id: str, plan: dict[str, Any]) -> tuple[dict[str, Any], str]:
    started = time.perf_counter()
    config = dict(plan.get("config", {}))
    repo_path = Path(config.get("repo_path", str(TSL_SIMPLE_REPO))).expanduser().resolve()
    python_path = Path(config.get("python", str(TSL_SIMPLE_PYTHON))).expanduser().resolve()
    if not repo_path.exists():
        return _blocked_tsl(started, f"repo_path not found: {repo_path}")
    if not python_path.exists():
        return _blocked_tsl(started, f"python executable not found: {python_path}")

    model = str(config.get("model", "DLinear"))
    data = str(config.get("data", "ETTh1.csv"))
    seq_len = int(config.get("seq_len", 24))
    pred_len = int(config.get("pred_len", 24))
    label_len = int(config.get("label_len", max(0, pred_len // 2)))
    enc_in = int(config.get("enc_in", 7))
    dec_in = int(config.get("dec_in", enc_in))
    c_out = int(config.get("c_out", enc_in))
    train_epochs = int(config.get("train_epochs", 1))
    batch_size = int(config.get("batch_size", 16))
    subset_ratio = float(config.get("subset_ratio", 0.05))
    timeout_sec = int(config.get("timeout_sec", 240))
    learning_rate = str(config.get("learning_rate", "0.001"))
    model_id = str(config.get("model_id", f"tsagent_{run_id}_{model}"))
    des = str(config.get("des", "tsagent_demo"))

    command = [
        str(python_path),
        "run.py",
        "--is_training",
        "1",
        "--model_id",
        model_id,
        "--model",
        model,
        "--data",
        data,
        "--features",
        str(config.get("features", "M")),
        "--seq_len",
        str(seq_len),
        "--label_len",
        str(label_len),
        "--pred_len",
        str(pred_len),
        "--enc_in",
        str(enc_in),
        "--dec_in",
        str(dec_in),
        "--c_out",
        str(c_out),
        "--d_model",
        str(config.get("d_model", 64)),
        "--d_ff",
        str(config.get("d_ff", 64)),
        "--train_epochs",
        str(train_epochs),
        "--itr",
        str(config.get("itr", 1)),
        "--batch_size",
        str(batch_size),
        "--num_workers",
        str(config.get("num_workers", 0)),
        "--learning_rate",
        learning_rate,
        "--patience",
        str(config.get("patience", 1)),
        "--des",
        des,
        "--use_swanlab",
        "0",
        "--subset_ratio",
        str(subset_ratio),
    ]
    try:
        proc = subprocess.run(command, cwd=repo_path, text=True, capture_output=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired as exc:
        wall_time = round(time.perf_counter() - started, 6)
        stdout = (exc.stdout or "") + "\n--- STDERR ---\n" + (exc.stderr or "")
        metrics = {
            "status": "blocked",
            "backend": "tsl-simple",
            "metric_name": "rmse",
            "metric_value": None,
            "baseline": None,
            "delta": None,
            "optimize": "minimize",
            "wall_time_sec": wall_time,
            "blocker": f"tsl-simple command timed out after {timeout_sec}s",
            "diagnostics": {"command": _format_command(command), "repo_path": str(repo_path), "model": model, "data": data},
        }
        return metrics, stdout

    wall_time = round(time.perf_counter() - started, 6)
    stdout = proc.stdout + "\n--- STDERR ---\n" + proc.stderr
    parsed = _parse_tsl_metrics(stdout)
    if proc.returncode != 0 or parsed is None:
        blocker = f"tsl-simple command failed with return code {proc.returncode}"
        if parsed is None and proc.returncode == 0:
            blocker = "tsl-simple completed but rmse/mae could not be parsed"
        metrics = {
            "status": "blocked",
            "backend": "tsl-simple",
            "metric_name": "rmse",
            "metric_value": None,
            "baseline": None,
            "delta": None,
            "optimize": "minimize",
            "wall_time_sec": wall_time,
            "blocker": blocker,
            "diagnostics": {"command": _format_command(command), "return_code": proc.returncode, "repo_path": str(repo_path), "model": model, "data": data},
        }
        return metrics, stdout

    metric_value = round(parsed["rmse"], 8)
    baseline = config.get("baseline_rmse")
    baseline_value = None if baseline is None else round(float(baseline), 8)
    delta = None if baseline_value is None else round(baseline_value - metric_value, 8)
    metrics = {
        "status": "completed",
        "backend": "tsl-simple",
        "metric_name": "rmse",
        "metric_value": metric_value,
        "baseline": baseline_value,
        "delta": delta,
        "optimize": "minimize",
        "wall_time_sec": wall_time,
        "diagnostics": {
            "mae": round(parsed["mae"], 8),
            "command": _format_command(command),
            "return_code": proc.returncode,
            "repo_path": str(repo_path),
            "python": str(python_path),
            "model": model,
            "data": data,
            "seq_len": seq_len,
            "label_len": label_len,
            "pred_len": pred_len,
            "train_epochs": train_epochs,
            "subset_ratio": subset_ratio,
        },
    }
    return metrics, stdout


def _blocked_tsl(started: float, reason: str) -> tuple[dict[str, Any], str]:
    metrics = {
        "status": "blocked",
        "backend": "tsl-simple",
        "metric_name": "rmse",
        "metric_value": None,
        "baseline": None,
        "delta": None,
        "optimize": "minimize",
        "wall_time_sec": round(time.perf_counter() - started, 6),
        "blocker": reason,
    }
    return metrics, f"backend=tsl-simple\nstatus=blocked\nreason={reason}\n"


def run_backend(
    backend: str,
    run_id: str,
    plan: dict[str, Any],
    data_csv: str | Path | None = None,
    column: str | None = None,
) -> tuple[dict[str, Any], str]:
    if backend == "smoke":
        return run_smoke_backend(run_id, plan)
    if backend == "dlinear-mini":
        return run_dlinear_mini_backend(run_id, plan, data_csv=data_csv, column=column)
    if backend == "tsl-simple":
        return run_tsl_simple_backend(run_id, plan)
    metrics = {
        "status": "blocked",
        "backend": backend,
        "metric_name": plan.get("metric_name", "mse"),
        "metric_value": None,
        "baseline": None,
        "delta": None,
        "optimize": plan.get("optimize", "minimize"),
        "wall_time_sec": 0.0,
        "blocker": f"unknown backend: {backend}",
    }
    return metrics, f"status=blocked\nreason=unknown backend: {backend}\n"
