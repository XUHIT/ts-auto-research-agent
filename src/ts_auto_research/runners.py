"""Experiment backends for the research loop."""

from __future__ import annotations

import csv
import math
from pathlib import Path
import statistics
import time
from typing import Any


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
