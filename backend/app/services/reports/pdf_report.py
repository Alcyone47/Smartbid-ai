"""PDF executive summary via reportlab (pure-Python, no native deps)."""

from __future__ import annotations

import io
from datetime import date
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.reports.data import ReportRow

_HEADER_BG = colors.HexColor("#1F2937")
_MAX_GAPS = 15


def generate_summary_pdf(project: Any, summaries: list, rows: list[ReportRow]) -> bytes:
    stream = io.BytesIO()
    doc = SimpleDocTemplate(
        stream, pagesize=A4, topMargin=1.6 * cm, bottomMargin=1.6 * cm, leftMargin=1.6 * cm, rightMargin=1.6 * cm
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], fontSize=18, spaceAfter=4)
    subtitle_style = ParagraphStyle("ReportSubtitle", parent=styles["Normal"], textColor=colors.grey)

    story: list = [Paragraph(f"Compliance Summary - {_escape(project.name)}", title_style)]
    client = getattr(project, "client_name", None)
    if client:
        story.append(Paragraph(f"Client: {_escape(client)}", subtitle_style))
    story.append(Paragraph(f"Generated {date.today().isoformat()}", subtitle_style))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Vendor Compliance", styles["Heading2"]))
    story.append(_vendor_table(summaries))

    gaps = [r for r in rows if r.is_mandatory and r.status == "no_match"]
    if gaps:
        story.append(Spacer(1, 0.6 * cm))
        story.append(Paragraph(f"Top Mandatory Gaps ({len(gaps)})", styles["Heading2"]))
        story.append(_gaps_table(gaps[:_MAX_GAPS], styles))

    doc.build(story)
    return stream.getvalue()


def _vendor_table(summaries: list) -> Table:
    data = [["Vendor", "Overall", "Matched", "Partial", "Unmet", "Mandatory", "Optional"]]
    for s in summaries:
        data.append(
            [
                s.vendor_name,
                f"{s.overall_compliance_pct}%",
                str(s.matched),
                str(s.partial),
                str(s.unmatched),
                f"{s.mandatory_met}/{s.mandatory_total}",
                f"{s.optional_met}/{s.optional_total}",
            ]
        )
    table = Table(data, hAlign="LEFT", colWidths=[4.5 * cm, 2 * cm, 2 * cm, 2 * cm, 1.8 * cm, 2.2 * cm, 2 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _gaps_table(gaps: list[ReportRow], styles) -> Table:
    cell = ParagraphStyle("GapCell", parent=styles["Normal"], fontSize=8.5, leading=11)
    data = [["Equipment", "Requirement", "Vendor", "Required", "Offered"]]
    for g in gaps:
        required = " ".join(filter(None, [g.operator, g.expected_value, g.unit])) or g.requirement_text
        data.append(
            [
                Paragraph(_escape(g.equipment_label), cell),
                Paragraph(_escape(g.requirement_label), cell),
                Paragraph(_escape(g.vendor_name), cell),
                Paragraph(_escape(required), cell),
                Paragraph(_escape(g.vendor_value or "-"), cell),
            ]
        )
    table = Table(data, hAlign="LEFT", colWidths=[3 * cm, 5 * cm, 2.5 * cm, 3 * cm, 3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
