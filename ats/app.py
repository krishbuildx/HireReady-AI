"""Streamlit UI for the AI-powered ATS Resume Analyzer."""
from __future__ import annotations

import os
from typing import Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules.parser import extract_text, detect_sections, missing_sections
from modules.similarity import similarity_score
from modules.skills import compare_skills
from modules.grammar import check_grammar
from modules.readability import readability_metrics
from modules.gemini_analyzer import analyze_resume, configure
from modules.report_generator import build_pdf_report


st.set_page_config(page_title="AI ATS Resume Analyzer", page_icon="📄", layout="wide")


# ---------------- Sidebar ----------------
with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Set GEMINI_API_KEY env var or paste here. Get one at aistudio.google.com/app/apikey",
    )
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
    st.caption("Powered by Google Gemini · Streamlit · spaCy · scikit-learn")


st.title("📄 AI-Powered ATS Resume Analyzer")
st.write(
    "Upload your resume (and optionally a job description) to get an ATS score, "
    "detailed section analysis, missing-skills detection, and AI-powered rewriting."
)

col1, col2 = st.columns(2)
with col1:
    resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
with col2:
    jd_file = st.file_uploader("Upload Job Description (optional)", type=["pdf", "docx", "txt"])
    jd_text_input = st.text_area("...or paste Job Description here", height=120)


analyze_btn = st.button("🚀 Analyze Resume", type="primary", use_container_width=True)


def _gauge(score: float, title: str) -> go.Figure:
    return go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#1f77b4"},
            "steps": [
                {"range": [0, 50], "color": "#ffcccc"},
                {"range": [50, 75], "color": "#fff2cc"},
                {"range": [75, 100], "color": "#ccffcc"},
            ],
        },
    ))


def _radar(section_scores: Dict[str, float]) -> go.Figure:
    cats = [k.replace("_", " ").title() for k in section_scores.keys()]
    vals = list(section_scores.values())
    fig = go.Figure(data=go.Scatterpolar(
        r=vals + [vals[0]], theta=cats + [cats[0]], fill="toself", name="Score",
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    return fig


def _render(analysis: Dict, resume_text: str, jd_text: str):
    # ---- Top scores ----
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall ATS", f"{analysis.get('overall_ats_score', 0)}/100")
    stars = int(analysis.get("rating_stars", 0))
    c2.metric("Rating", "★" * stars + "☆" * (5 - stars))
    c3.metric("Job Match", f"{analysis.get('job_match_score', 0)}/100")
    sim = similarity_score(resume_text, jd_text) if jd_text else 0.0
    c4.metric("TF-IDF Similarity", f"{sim}%")

    st.divider()

    # ---- Gauge + Radar ----
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(_gauge(analysis.get("overall_ats_score", 0), "ATS Score"), use_container_width=True)
    with g2:
        section_scores = analysis.get("section_scores") or {}
        if section_scores:
            st.plotly_chart(_radar(section_scores), use_container_width=True)

    # ---- Section bar chart ----
    if section_scores:
        df = pd.DataFrame(
            {"Section": [k.replace("_", " ").title() for k in section_scores],
             "Score": list(section_scores.values())}
        )
        fig = px.bar(df, x="Section", y="Score", color="Score", range_y=[0, 100],
                     color_continuous_scale="Blues", title="Section-wise Scores")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Progress")
        for k, v in section_scores.items():
            st.write(f"**{k.replace('_', ' ').title()}** — {v}/100")
            st.progress(min(int(v), 100))

    st.divider()

    # ---- Strengths / Weaknesses ----
    sc1, sc2 = st.columns(2)
    with sc1:
        st.subheader("✅ Strengths")
        for x in analysis.get("strengths", []) or ["—"]:
            st.write(f"• {x}")
    with sc2:
        st.subheader("⚠️ Weaknesses")
        for x in analysis.get("weaknesses", []) or ["—"]:
            st.write(f"• {x}")

    st.subheader("🎯 ATS Optimization Suggestions")
    for x in analysis.get("ats_suggestions", []) or ["—"]:
        st.write(f"• {x}")

    # ---- Missing sections & skills ----
    ms1, ms2 = st.columns(2)
    with ms1:
        st.subheader("🧩 Missing Sections")
        for x in analysis.get("missing_sections", []) or ["None detected"]:
            st.write(f"• {x}")
    with ms2:
        st.subheader("🛠️ Missing Skills (from JD)")
        ms = analysis.get("missing_skills", []) or []
        if ms:
            for m in ms:
                st.markdown(f"**{m.get('skill','')}** — {m.get('why_it_matters','')}")
        else:
            st.write("None detected")
            
    # ---- Skills gap viz ----
    gap = compare_skills(resume_text, jd_text)
    if gap["jd_skills"]:
        st.subheader("📊 Resume vs JD Skills")
        gdf = pd.DataFrame({
            "Category": ["Matched", "Missing", "Only in Resume"],
            "Count": [
                len(gap["matched"]),
                len(gap["missing"]),
                len(set(gap["resume_skills"]) - set(gap["jd_skills"])),
            ],
        })
        st.plotly_chart(px.bar(gdf, x="Category", y="Count", color="Category",
                               title="Skills Gap Analysis"), use_container_width=True)

    # ---- Rewritten content ----
    st.divider()
    st.subheader("✍️ Rewritten Summary")
    st.write(analysis.get("rewritten_summary") or "—")

    st.subheader("✨ Rewritten Bullet Points")
    for x in analysis.get("rewritten_bullets", []) or ["—"]:
        st.write(f"• {x}")

    st.subheader("📈 Quantified Achievement Suggestions")
    for x in analysis.get("quantified_achievement_suggestions", []) or ["—"]:
        st.write(f"• {x}")

    st.subheader("💡 Personalized Recommendations")
    for x in analysis.get("personalized_recommendations", []) or ["—"]:
        st.write(f"• {x}")

    # ---- PDF report ----
    st.divider()
    pdf = build_pdf_report(analysis, sim, kf, gap)
    st.download_button(
        "⬇️ Download PDF Report",
        data=pdf,
        file_name="ats_resume_analysis.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


if analyze_btn:
    if not resume_file:
        st.error("Please upload a resume.")
        st.stop()
    if not configure():
        st.error("Gemini API key missing. Add it in the sidebar or set GEMINI_API_KEY.")
        st.stop()

    with st.spinner("Extracting resume text..."):
        resume_text = extract_text(resume_file.name, resume_file.read())

    jd_text = ""
    if jd_file is not None:
        jd_text = extract_text(jd_file.name, jd_file.read())
    if jd_text_input.strip():
        jd_text = (jd_text + "\n" + jd_text_input).strip()

    with st.expander("📄 Extracted Resume Text", expanded=False):
        st.text(resume_text[:5000] + ("..." if len(resume_text) > 5000 else ""))
        sections = detect_sections(resume_text)
        st.write("**Detected sections:**", list(sections.keys()))
        st.write("**Missing common sections:**", missing_sections(sections) or "None")

    with st.spinner("Running grammar + readability checks..."):
        grammar_res = check_grammar(resume_text)
        read_res = readability_metrics(resume_text)

    r1, r2 = st.columns(2)
    r1.metric("Grammar Score", f"{grammar_res['score']}/100",
              help=f"{grammar_res.get('total_issues', 0)} issues detected")
    r2.metric("Readability (Flesch)", read_res["flesch_reading_ease"],
              help=f"Grade level: {read_res['grade_level']}")

    with st.spinner("🤖 Gemini is analyzing your resume..."):
        analysis = analyze_resume(resume_text, jd_text)

    if "error" in analysis and analysis.get("overall_ats_score", 0) == 0:
        st.error(f"Gemini analysis failed: {analysis['error']}")
        st.stop()

    _render(analysis, resume_text, jd_text)
else:
    st.info("Upload a resume and click **Analyze Resume** to begin.")
