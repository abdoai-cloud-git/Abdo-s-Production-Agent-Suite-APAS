"""PDF export utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from fpdf import FPDF


class PDFExporter:
    """Creates PDF artifacts from structured data."""

    def __init__(self, *, output_dir: str = "/tmp") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_calendar(self, calendar: Dict[str, object], filename: Optional[str] = None) -> str:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Helvetica", size=16)
        pdf.cell(0, 10, txt=f"Content Calendar — {calendar.get('brand', 'Brand')}", ln=True)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 6, txt=f"Niche: {calendar.get('niche', 'n/a')} | Days: {calendar.get('days', 'n/a')}")
        pdf.ln(4)

        ideas: List[Dict[str, object]] = calendar.get("ideas", [])  # type: ignore[assignment]
        for idea in ideas:
            pdf.set_font("Helvetica", "B", size=12)
            pdf.cell(0, 7, txt=f"Day {idea.get('day_index')}: {idea.get('theme')}", ln=True)
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(0, 6, txt=f"Hook: {idea.get('hook', '')}")
            pdf.multi_cell(0, 6, txt=f"CTA: {idea.get('call_to_action', '')}")
            pdf.multi_cell(0, 6, txt=f"Primary Channel: {idea.get('primary_channel', '')}")
            pdf.multi_cell(0, 6, txt=f"Assets Needed: {', '.join(idea.get('assets_needed', []))}")
            notes = idea.get('notes')
            if notes:
                pdf.multi_cell(0, 6, txt=f"Notes: {notes}")
            pdf.ln(2)

        output_path = self.output_dir / (filename or f"content-calendar-{uuid4().hex}.pdf")
        pdf.output(str(output_path))
        return str(output_path)

    def export_analytics_report(self, report: Dict[str, object], filename: Optional[str] = None) -> str:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Helvetica", size=16)
        pdf.cell(0, 10, txt="Analytics Report", ln=True)
        summary = report.get("summary", {})
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(
            0,
            6,
            txt=f"Timeframe: {summary.get('timeframe', 'n/a')} | Goal: {summary.get('primary_goal', 'n/a')}",
        )
        pdf.multi_cell(0, 6, txt=summary.get("headline", ""))
        pdf.ln(4)

        kpis: List[Dict[str, object]] = report.get("kpis", [])  # type: ignore[assignment]
        for kpi in kpis:
            pdf.set_font("Helvetica", "B", size=12)
            pdf.cell(0, 7, txt=f"{kpi.get('metric')}: {kpi.get('value')} {kpi.get('unit', '')}", ln=True)
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(0, 6, txt=f"Trend: {kpi.get('trend_vs_prior')}")
            pdf.multi_cell(0, 6, txt=f"Insight: {kpi.get('insight')}")
            pdf.multi_cell(0, 6, txt=f"Action: {kpi.get('recommended_action')}")
            pdf.ln(1)

        anomalies = report.get("anomalies") or []
        if anomalies:
            pdf.set_font("Helvetica", "B", size=12)
            pdf.cell(0, 7, txt="Anomalies", ln=True)
            pdf.set_font("Helvetica", size=11)
            for anomaly in anomalies:
                pdf.multi_cell(0, 6, txt=f"- {anomaly}")

        output_path = self.output_dir / (filename or f"analytics-report-{uuid4().hex}.pdf")
        pdf.output(str(output_path))
        return str(output_path)


if __name__ == "__main__":
    exporter = PDFExporter()
    sample = {
        "brand": "APAS Fitness",
        "niche": "fitness",
        "days": 3,
        "ideas": [
            {
                "day_index": 1,
                "theme": "Leg Day",
                "hook": "Stop skipping legs",
                "call_to_action": "Join the 30-day challenge",
                "primary_channel": "instagram",
                "assets_needed": ["reel", "caption"],
                "notes": "Highlight testimonials",
            }
        ],
    }
    print(exporter.export_calendar(sample))
