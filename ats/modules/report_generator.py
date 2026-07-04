"""Generate a downloadable PDF analysis report using ReportLab."""
from __future__ import annotations

import io
from typing import Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, ListFlowable, ListItem,
)


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name="H1c", parent=s["Heading1"], textColor=colors.HexColor("#1f3a5f")))
    s.add(ParagraphStyle(name="H2c", parent=s["Heading2"], textColor=colors.HexColor("#2e5c8a")))
    return s


def _bullets(items, style):
    items = [str(i) for i in (items or []) if str(i).strip()]
    if not items:
        return Paragraph("<i>None</i>", style)
    return ListFlowable(
        [ListItem(Paragraph(i, style), leftIndent=10) for i in items],
        bulletType="bullet",
    )


def build_pdf_report(analysis: Dict, similarity: float, keyword_freq, skills_gap: Dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        title="ATS Resume Analysis Report",
    )
    s = _styles()
    story = []

    story.append(Paragraph("ATS Resume Analysis Report", s["H1c"]))
    story.append(Spacer(1, 12))

    overall = analysis.get("overall_ats_score", 0)
    stars = "★" * int(analysis.get("rating_stars", 0)) + "☆" * (5 - int(analysis.get("rating_stars", 0)))
    story.append(Paragraph(f"<b>Overall ATS Score:</b> {overall}/100", s["Normal"]))
    story.append(Paragraph(f"<b>Rating:</b> {stars}", s["Normal"]))
    story.append(Paragraph(f"<b>Job Match Score:</b> {analysis.get('job_match_score', 0)}/100", s["Normal"]))
    story.append(Paragraph(f"<b>TF-IDF Similarity:</b> {similarity}%", s["Normal"]))
    story.append(Spacer(1, 10))

    # Section scores table
    story.append(Paragraph("Section Scores", s["H2c"]))
    ss = analysis.get("section_scores", {}) or {}
    data = [["Section", "Score"]] + [[k.replace("_", " ").title(), str(v)] for k, v in ss.items()]
    t = Table(data, colWidths=[3 * inch, 1.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Strengths", s["H2c"]))
    story.append(_bullets(analysis.get("strengths"), s["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Weaknesses", s["H2c"]))
    story.append(_bullets(analysis.get("weaknesses"), s["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("ATS Optimization Suggestions", s["H2c"]))
    story.append(_bullets(analysis.get("ats_suggestions"), s["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Missing Sections", s["H2c"]))
    story.append(_bullets(analysis.get("missing_sections"), s["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Missing Skills (from Job Description)", s["H2c"]))
    ms = analysis.get("missing_skills", []) or []
    ms_lines = [f"<b>{m.get('skill','')}</b> — {m.get('why_it_matters','')}" for m in ms]
    story.append(_bullets(ms_lines or skills_gap.get("missing", []), s["Normal"]))
    story.append(Spacer(1, 8))

    story.append(PageBreak())

    story.append(Paragraph("Rewritten Summary", s["H2c"]))
    story.append(Paragraph(analysis.get("rewritten_summary") or "<i>N/A</i>", s["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Rewritten Bullet Points", s["H2c"]))
    story.append(_bullets(analysis.get("rewritten_bullets"), s["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Quantified Achievement Suggestions", s["H2c"]))
    story.append(_bullets(analysis.get("quantified_achievement_suggestions"), s["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Personalized Recommendations", s["H2c"]))
    story.append(_bullets(analysis.get("personalized_recommendations"), s["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Top Resume Keywords", s["H2c"]))
    kf = keyword_freq or []
    kf_data = [["Keyword", "Count"]] + [[k, str(v)] for k, v in kf[:15]]
    kt = Table(kf_data, colWidths=[3 * inch, 1.5 * inch])
    kt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e5c8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(kt)

    doc.build(story)
    return buf.getvalue()
