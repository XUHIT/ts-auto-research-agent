"""Generate dashboard, monitor, figures, and PDF reports for benchmark demos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import textwrap
from typing import Any

from .io_utils import ensure_dir, read_json
from .literature import read_index
from .methods import INNOVATION_CANDIDATE, STRONG_REFERENCE, select_literature_evidence
from .paths import Workspace
from .showcase import build_showcase

ROLE_COLORS = {
    "baseline_anchor": "#4A5568",
    "strong_reference": "#2B6CB0",
    "innovation_candidate": "#C05621",
    "baseline_control": "#718096",
    "unknown_method": "#A0AEC0",
}


@dataclass(frozen=True)
class ReportArtifacts:
    dashboard_html: Path
    monitor_html: Path
    pdf_report: Path
    metrics_svg: Path
    delta_svg: Path


def generate_report(workspace: Workspace, output_dir: Path | None = None) -> dict[str, str]:
    """Generate public-safe visual report artifacts from current benchmark state."""
    showcase = build_showcase(workspace)
    output_dir = output_dir or workspace.root / "docs" / "demo_results"
    output_dir = ensure_dir(output_dir)
    figures_dir = ensure_dir(output_dir / "figures")

    results = _enrich_results(workspace, showcase.get("results", []))
    evidence = _literature_evidence(workspace, results)
    summary = _summary(showcase, results)

    metrics_svg = figures_dir / "benchmark_metrics.svg"
    delta_svg = figures_dir / "delta_vs_dlinear.svg"
    metrics_svg.write_text(_render_metrics_svg(results), encoding="utf-8")
    delta_svg.write_text(_render_delta_svg(results), encoding="utf-8")

    dashboard_html = output_dir / "dashboard.html"
    monitor_html = output_dir / "monitor.html"
    pdf_report = output_dir / "benchmark_report.pdf"

    dashboard_html.write_text(
        _render_dashboard_html(
            title="TS Auto Research Agent Benchmark Dashboard",
            showcase=showcase,
            results=results,
            evidence=evidence,
            summary=summary,
            metrics_svg="figures/benchmark_metrics.svg",
            delta_svg="figures/delta_vs_dlinear.svg",
            auto_refresh=False,
        ),
        encoding="utf-8",
    )
    monitor_html.write_text(
        _render_dashboard_html(
            title="TS Auto Research Agent Monitor",
            showcase=showcase,
            results=results,
            evidence=evidence,
            summary=summary,
            metrics_svg="figures/benchmark_metrics.svg",
            delta_svg="figures/delta_vs_dlinear.svg",
            auto_refresh=True,
        ),
        encoding="utf-8",
    )
    _write_pdf_report(pdf_report, showcase, results, evidence, summary)

    artifacts = ReportArtifacts(
        dashboard_html=dashboard_html,
        monitor_html=monitor_html,
        pdf_report=pdf_report,
        metrics_svg=metrics_svg,
        delta_svg=delta_svg,
    )
    return {key: str(value) for key, value in artifacts.__dict__.items()}


def _enrich_results(workspace: Workspace, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for item in results:
        run_id = str(item.get("run_id") or "")
        metrics = read_json(workspace.run_dir(run_id) / "metrics.json", default={})
        review = read_json(workspace.run_dir(run_id) / "review.json", default={})
        plan = read_json(workspace.run_dir(run_id) / "experiment_plan.json", default={})
        diagnostics = metrics.get("diagnostics", {})
        copy = dict(item)
        copy["mae"] = _to_float(diagnostics.get("mae"))
        copy["method_claim"] = diagnostics.get("method_claim") or plan.get("method_card", {}).get("claim")
        copy["success_criteria"] = plan.get("success_criteria")
        copy["review_rationale"] = review.get("rationale")
        enriched.append(copy)
    return enriched


def _literature_evidence(workspace: Workspace, results: list[dict[str, Any]]) -> list[dict[str, str]]:
    for item in reversed(results):
        if item.get("role") == INNOVATION_CANDIDATE:
            run_id = str(item.get("run_id") or "")
            plan = read_json(workspace.run_dir(run_id) / "experiment_plan.json", default={})
            evidence = plan.get("method_card", {}).get("literature_evidence") or plan.get("literature_context")
            if evidence:
                return [dict(record) for record in evidence]
    return select_literature_evidence(read_index(workspace, limit=1000))


def _summary(showcase: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = _first_role(results, "baseline_anchor")
    candidate = _best_role(results, INNOVATION_CANDIDATE)
    strong = _best_role(results, STRONG_REFERENCE)
    return {
        "effect": showcase.get("effect", ""),
        "baseline": baseline,
        "candidate": candidate,
        "strong_reference": strong,
        "claim": _claim_text(baseline, candidate, strong),
        "next_action": showcase.get("next_action", ""),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def _claim_text(baseline: dict[str, Any] | None, candidate: dict[str, Any] | None, strong: dict[str, Any] | None) -> str:
    if not baseline or not candidate:
        return "No innovation candidate has been evaluated against the locked baseline yet."
    delta = _to_float(candidate.get("delta"))
    if delta is None or delta <= 0:
        return f"{candidate.get('model', 'Candidate')} does not clear the DLinear baseline and should be redesigned."
    if strong and _to_float(strong.get("metric_value")) is not None and _to_float(candidate.get("metric_value")) is not None:
        if float(strong["metric_value"]) < float(candidate["metric_value"]):
            return (
                f"{candidate.get('model')} improves RMSE over DLinear by {_fmt(delta)}, "
                f"but {strong.get('model')} remains stronger. This is a bounded candidate, not a SOTA claim."
            )
    return f"{candidate.get('model')} clears the DLinear baseline and should move to ablation and broader validation."


def _first_role(results: list[dict[str, Any]], role: str) -> dict[str, Any] | None:
    for item in results:
        if item.get("role") == role:
            return item
    return None


def _best_role(results: list[dict[str, Any]], role: str) -> dict[str, Any] | None:
    scored = [item for item in results if item.get("role") == role and _to_float(item.get("metric_value")) is not None]
    if not scored:
        return None
    return min(scored, key=lambda item: float(item["metric_value"]))


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any) -> str:
    number = _to_float(value)
    if number is None:
        return "n/a"
    return f"{number:.8g}"


def _role_color(role: Any) -> str:
    return ROLE_COLORS.get(str(role), ROLE_COLORS["unknown_method"])


def _render_metrics_svg(results: list[dict[str, Any]]) -> str:
    width, height = 900, 360
    margin_left, margin_right, margin_top, margin_bottom = 72, 28, 36, 70
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    max_value = max([_to_float(item.get("metric_value")) or 0 for item in results] + [_to_float(item.get("mae")) or 0 for item in results] + [1e-6])
    max_value = max_value * 1.15
    group_w = plot_w / max(1, len(results))
    bar_w = min(34, group_w / 4)
    parts = [_svg_header(width, height), f'<rect width="100%" height="100%" fill="#ffffff"/>']
    parts.append(f'<text x="{margin_left}" y="24" class="title">RMSE and MAE by method</text>')
    parts.append(f'<line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{width - margin_right}" y2="{margin_top + plot_h}" stroke="#CBD5E0"/>')
    parts.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" stroke="#CBD5E0"/>')
    for idx in range(5):
        value = max_value * idx / 4
        y = margin_top + plot_h - (value / max_value) * plot_h
        parts.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{width - margin_right}" y2="{y:.2f}" stroke="#EDF2F7"/>')
        parts.append(f'<text x="{margin_left - 10}" y="{y + 4:.2f}" text-anchor="end" class="axis">{value:.2f}</text>')
    for i, item in enumerate(results):
        center = margin_left + group_w * i + group_w / 2
        rmse = _to_float(item.get("metric_value"))
        mae = _to_float(item.get("mae"))
        color = _role_color(item.get("role"))
        if rmse is not None:
            h = (rmse / max_value) * plot_h
            x = center - bar_w - 3
            y = margin_top + plot_h - h
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{h:.2f}" rx="3" fill="{color}"/>')
            parts.append(f'<text x="{x + bar_w/2:.2f}" y="{y - 6:.2f}" text-anchor="middle" class="value">{_fmt(rmse)}</text>')
        if mae is not None:
            h = (mae / max_value) * plot_h
            x = center + 3
            y = margin_top + plot_h - h
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{h:.2f}" rx="3" fill="#A0AEC0"/>')
        label = escape(str(item.get("model", "unknown")))
        parts.append(f'<text x="{center:.2f}" y="{height - 38}" text-anchor="middle" class="label">{label}</text>')
        parts.append(f'<text x="{center:.2f}" y="{height - 20}" text-anchor="middle" class="axis">{escape(str(item.get("role", "")))}</text>')
    parts.append('<rect x="690" y="18" width="14" height="14" rx="2" fill="#2B6CB0"/><text x="710" y="30" class="axis">Role-colored RMSE</text>')
    parts.append('<rect x="690" y="40" width="14" height="14" rx="2" fill="#A0AEC0"/><text x="710" y="52" class="axis">MAE</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _render_delta_svg(results: list[dict[str, Any]]) -> str:
    width, height = 900, 300
    margin_left, margin_right, margin_top, row_h = 180, 40, 34, 54
    deltas = [_to_float(item.get("delta")) or 0.0 for item in results]
    max_abs = max([abs(value) for value in deltas] + [1e-6]) * 1.2
    zero_x = margin_left + (width - margin_left - margin_right) / 2
    scale = (width - margin_left - margin_right) / 2 / max_abs
    parts = [_svg_header(width, height), '<rect width="100%" height="100%" fill="#ffffff"/>']
    parts.append(f'<text x="{margin_left}" y="24" class="title">Delta vs DLinear baseline</text>')
    parts.append(f'<line x1="{zero_x:.2f}" y1="{margin_top}" x2="{zero_x:.2f}" y2="{height - 28}" stroke="#4A5568"/>')
    for i, item in enumerate(results):
        y = margin_top + i * row_h + 18
        delta = _to_float(item.get("delta")) or 0.0
        color = _role_color(item.get("role"))
        x = zero_x if delta >= 0 else zero_x + delta * scale
        w = abs(delta * scale)
        parts.append(f'<text x="20" y="{y + 8:.2f}" class="label">{escape(str(item.get("model", "unknown")))}</text>')
        parts.append(f'<text x="105" y="{y + 8:.2f}" class="axis">{escape(str(item.get("role", "")))}</text>')
        parts.append(f'<rect x="{x:.2f}" y="{y - 8:.2f}" width="{max(w, 1):.2f}" height="18" rx="3" fill="{color}"/>')
        label_x = x + w + 8 if delta >= 0 else x - 8
        anchor = "start" if delta >= 0 else "end"
        parts.append(f'<text x="{label_x:.2f}" y="{y + 6:.2f}" text-anchor="{anchor}" class="value">{_fmt(delta)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _svg_header(width: int, height: int) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<style>
.title{{font:600 18px Arial,Helvetica,sans-serif;fill:#1A202C}}
.label{{font:600 12px Arial,Helvetica,sans-serif;fill:#2D3748}}
.axis{{font:400 11px Arial,Helvetica,sans-serif;fill:#4A5568}}
.value{{font:600 11px Arial,Helvetica,sans-serif;fill:#1A202C}}
</style>'''


def _render_dashboard_html(
    title: str,
    showcase: dict[str, Any],
    results: list[dict[str, Any]],
    evidence: list[dict[str, str]],
    summary: dict[str, Any],
    metrics_svg: str,
    delta_svg: str,
    auto_refresh: bool,
) -> str:
    refresh = '<meta http-equiv="refresh" content="30">' if auto_refresh else ""
    rows = "\n".join(_html_result_row(item) for item in results)
    evidence_items = "\n".join(
        f"<li><strong>{escape(item.get('title', 'untitled'))}</strong> <span>{escape(item.get('venue', 'unknown'))}</span><p>{escape(item.get('lesson', ''))}</p></li>"
        for item in evidence
    )
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {refresh}
  <title>{escape(title)}</title>
  <style>
    :root {{ --ink:#1a202c; --muted:#4a5568; --line:#d7dee8; --panel:#f7fafc; --accent:#c05621; }}
    body {{ margin:0; font-family: Inter, Arial, Helvetica, sans-serif; color:var(--ink); background:#ffffff; }}
    main {{ max-width:1180px; margin:0 auto; padding:28px 24px 48px; }}
    header {{ border-bottom:1px solid var(--line); padding-bottom:18px; margin-bottom:22px; }}
    h1 {{ font-size:30px; line-height:1.15; margin:0 0 10px; letter-spacing:0; }}
    h2 {{ font-size:18px; margin:28px 0 12px; }}
    p {{ color:var(--muted); line-height:1.55; }}
    .effect {{ font-size:17px; color:#2d3748; max-width:960px; }}
    .grid {{ display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:14px; margin:18px 0; }}
    .card {{ border:1px solid var(--line); border-radius:8px; padding:14px 16px; background:#fff; }}
    .card .k {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}
    .card .v {{ margin-top:8px; font-size:22px; font-weight:700; }}
    .claim {{ border-left:5px solid var(--accent); background:#fff7ed; padding:14px 16px; border-radius:6px; }}
    .chart-grid {{ display:grid; grid-template-columns:1fr; gap:18px; }}
    .chart {{ border:1px solid var(--line); border-radius:8px; padding:10px; background:#fff; overflow:auto; }}
    .chart img {{ max-width:100%; height:auto; display:block; }}
    table {{ width:100%; border-collapse:collapse; margin-top:10px; font-size:14px; }}
    th, td {{ border-bottom:1px solid var(--line); padding:10px 8px; text-align:left; vertical-align:top; }}
    th {{ color:#2d3748; background:var(--panel); font-weight:700; }}
    .badge {{ display:inline-block; border-radius:999px; padding:4px 9px; font-size:12px; font-weight:700; background:#edf2f7; }}
    .role-baseline_anchor {{ background:#edf2f7; color:#2d3748; }}
    .role-strong_reference {{ background:#ebf8ff; color:#2b6cb0; }}
    .role-innovation_candidate {{ background:#fff7ed; color:#c05621; }}
    ol.evidence {{ padding-left:22px; }}
    ol.evidence li {{ margin:0 0 12px; }}
    ol.evidence span {{ color:var(--muted); font-size:13px; }}
    ol.evidence p {{ margin:4px 0 0; }}
    footer {{ margin-top:34px; color:var(--muted); font-size:13px; }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns:1fr; }} main {{ padding:20px 14px 36px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>{escape(title)}</h1>
    <div class="effect">{escape(str(summary.get('effect', '')))}</div>
  </header>

  <section class="grid">
    {_summary_card('Baseline', summary.get('baseline'))}
    {_summary_card('Strong reference', summary.get('strong_reference'))}
    {_summary_card('Innovation candidate', summary.get('candidate'))}
  </section>

  <section class="claim">
    <strong>Current claim.</strong> {escape(str(summary.get('claim', '')))}
  </section>

  <section class="chart-grid">
    <div class="chart"><img src="{escape(metrics_svg)}" alt="RMSE and MAE by method"></div>
    <div class="chart"><img src="{escape(delta_svg)}" alt="Delta vs DLinear baseline"></div>
  </section>

  <section>
    <h2>Benchmark Rows</h2>
    <table>
      <thead><tr><th>Run</th><th>Role</th><th>Model</th><th>RMSE</th><th>MAE</th><th>Delta</th><th>Decision</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </section>

  <section>
    <h2>Literature Evidence</h2>
    <ol class="evidence">{evidence_items}</ol>
  </section>

  <section>
    <h2>Next Action</h2>
    <p>{escape(str(summary.get('next_action', '')))}</p>
  </section>

  <footer>Generated at {escape(str(summary.get('generated_at', '')))} from the local benchmark trajectory.</footer>
</main>
</body>
</html>
'''


def _summary_card(label: str, item: dict[str, Any] | None) -> str:
    if not item:
        return f'<div class="card"><div class="k">{escape(label)}</div><div class="v">n/a</div></div>'
    return (
        f'<div class="card"><div class="k">{escape(label)}</div>'
        f'<div class="v">{escape(str(item.get("model", "unknown")))}</div>'
        f'<p>RMSE {_fmt(item.get("metric_value"))} / MAE {_fmt(item.get("mae"))}</p></div>'
    )


def _html_result_row(item: dict[str, Any]) -> str:
    role = str(item.get("role", "unknown_method"))
    return (
        f'<tr><td><code>{escape(str(item.get("run_id", "")))}</code></td>'
        f'<td><span class="badge role-{escape(role)}">{escape(role)}</span></td>'
        f'<td>{escape(str(item.get("model", "unknown")))}</td>'
        f'<td>{_fmt(item.get("metric_value"))}</td>'
        f'<td>{_fmt(item.get("mae"))}</td>'
        f'<td>{_fmt(item.get("delta"))}</td>'
        f'<td>{escape(str(item.get("decision", "")))}</td></tr>'
    )


class _SimplePDF:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.objects: list[bytes] = []
        self.pages: list[int] = []
        self.font_regular = self._add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        self.font_bold = self._add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    def _add(self, payload: bytes) -> int:
        self.objects.append(payload)
        return len(self.objects)

    def add_page(self, commands: list[str], width: int = 612, height: int = 792) -> None:
        stream = "\n".join(commands).encode("latin-1", errors="replace")
        content_id = self._add(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
        page = (
            f"<< /Type /Page /Parent 0 0 R /MediaBox [0 0 {width} {height}] "
            f"/Resources << /Font << /F1 {self.font_regular} 0 R /F2 {self.font_bold} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("ascii")
        self.pages.append(self._add(page))

    def save(self) -> None:
        pages_kids = " ".join(f"{page_id} 0 R" for page_id in self.pages)
        pages_id = self._add(f"<< /Type /Pages /Kids [{pages_kids}] /Count {len(self.pages)} >>".encode("ascii"))
        catalog_id = self._add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii"))
        updated: list[bytes] = []
        for payload in self.objects:
            updated.append(payload.replace(b"/Parent 0 0 R", f"/Parent {pages_id} 0 R".encode("ascii")))
        self.objects = updated
        body = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for index, payload in enumerate(self.objects, start=1):
            offsets.append(len(body))
            body.extend(f"{index} 0 obj\n".encode("ascii"))
            body.extend(payload)
            body.extend(b"\nendobj\n")
        xref = len(body)
        body.extend(f"xref\n0 {len(self.objects) + 1}\n".encode("ascii"))
        body.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            body.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        body.extend(
            f"trailer\n<< /Size {len(self.objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
        )
        self.path.write_bytes(bytes(body))


def _write_pdf_report(path: Path, showcase: dict[str, Any], results: list[dict[str, Any]], evidence: list[dict[str, str]], summary: dict[str, Any]) -> None:
    pdf = _SimplePDF(path)
    commands: list[str] = []
    y = 750
    _pdf_text(commands, 54, y, "TS Auto Research Agent Benchmark Report", size=18, bold=True)
    y -= 30
    y = _pdf_wrapped(commands, 54, y, str(summary.get("effect", "")), size=10, width=86)
    y -= 12
    _pdf_text(commands, 54, y, "Current Claim", size=13, bold=True)
    y -= 18
    y = _pdf_wrapped(commands, 54, y, str(summary.get("claim", "")), size=10, width=92)
    y -= 16
    _pdf_text(commands, 54, y, "Benchmark Results", size=13, bold=True)
    y -= 22
    _pdf_table(commands, 54, y, results)
    y -= 120
    _pdf_text(commands, 54, y, "Literature Evidence", size=13, bold=True)
    y -= 18
    for item in evidence[:5]:
        line = f"- {item.get('title', 'untitled')} ({item.get('venue', 'unknown')}): {item.get('lesson', '')}"
        y = _pdf_wrapped(commands, 64, y, line, size=8.5, width=105)
        y -= 5
    y -= 8
    _pdf_text(commands, 54, y, "Next Action", size=13, bold=True)
    y -= 18
    _pdf_wrapped(commands, 54, y, str(summary.get("next_action", "")), size=10, width=92)
    _pdf_text(commands, 54, 36, f"Generated at {summary.get('generated_at', '')}", size=8)
    pdf.add_page(commands)
    pdf.save()


def _pdf_table(commands: list[str], x: int, y: int, results: list[dict[str, Any]]) -> None:
    headers = ["Role", "Model", "RMSE", "MAE", "Delta", "Decision"]
    widths = [110, 82, 70, 70, 70, 78]
    _pdf_rect(commands, x, y - 4, sum(widths), 20, fill="#EDF2F7")
    cursor = x + 4
    for header, width in zip(headers, widths):
        _pdf_text(commands, cursor, y + 2, header, size=8, bold=True)
        cursor += width
    row_y = y - 22
    for item in results:
        cursor = x + 4
        values = [item.get("role"), item.get("model"), _fmt(item.get("metric_value")), _fmt(item.get("mae")), _fmt(item.get("delta")), item.get("decision")]
        for value, width in zip(values, widths):
            _pdf_text(commands, cursor, row_y, str(value), size=8)
            cursor += width
        row_y -= 18


def _pdf_text(commands: list[str], x: float, y: float, text: str, size: float = 10, bold: bool = False) -> None:
    font = "F2" if bold else "F1"
    commands.append(f"BT /{font} {size} Tf {x:.2f} {y:.2f} Td ({_pdf_escape(text)}) Tj ET")


def _pdf_wrapped(commands: list[str], x: float, y: float, text: str, size: float = 10, width: int = 90) -> float:
    for line in textwrap.wrap(text, width=width):
        _pdf_text(commands, x, y, line, size=size)
        y -= size + 4
    return y


def _pdf_rect(commands: list[str], x: float, y: float, w: float, h: float, fill: str) -> None:
    r, g, b = _hex_to_rgb(fill)
    commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg {x:.2f} {y:.2f} {w:.2f} {h:.2f} re f")


def _hex_to_rgb(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    return int(value[0:2], 16) / 255, int(value[2:4], 16) / 255, int(value[4:6], 16) / 255


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
