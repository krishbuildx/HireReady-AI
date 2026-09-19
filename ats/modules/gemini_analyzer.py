"""Gemini-based resume analysis returning structured JSON."""
from __future__ import annotations

import json
import os
import re
import time
from typing import Dict, Optional

import google.generativeai as genai

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5")

def configure(api_key: Optional[str] = None) -> bool:
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("GEMINI_API_KEY")  # type: ignore[attr-defined]
        except Exception:
            key = None
    if not key:
        return False
    genai.configure(api_key=key)
    return True


ANALYSIS_SCHEMA_HINT = """
Return STRICT JSON with this shape:
{
  "overall_ats_score": 0-100,
  "section_scores": {
    "formatting": 0-100,
    "keywords": 0-100,
    "skills_match": 0-100,
    "experience": 0-100,
    "education": 0-100,
    "projects": 0-100,
    "grammar": 0-100,
    "readability": 0-100,
    "confidence": 0-100
  },
  "rating_stars": 1-5,
  "strengths": [string, ...],
  "weaknesses": [string, ...],
  "ats_suggestions": [string, ...],
  "missing_sections": [string, ...],
  "missing_skills": [{"skill": string, "why_it_matters": string}, ...],
  "completeness": {"score": 0-100, "notes": string},
  "rewritten_summary": string,
  "rewritten_bullets": [string, ...],
  "quantified_achievement_suggestions": [string, ...],
  "personalized_recommendations": [string, ...],
  "job_match_score": 0-100
}
Only output JSON. No prose, no code fences.
"""


def _extract_json(raw: str) -> Dict:
    raw = raw.strip()
    # Strip code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    # Grab outermost JSON object
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        raw = match.group(0)
    return json.loads(raw)


def _fallback(reason: str) -> Dict:
    return {
        "overall_ats_score": 0,
        "section_scores": {k: 0 for k in [
            "formatting", "keywords", "skills_match", "experience", "education",
            "projects", "grammar", "readability", "confidence",
        ]},
        "rating_stars": 0,
        "strengths": [],
        "weaknesses": [],
        "ats_suggestions": [],
        "missing_sections": [],
        "missing_skills": [],
        "completeness": {"score": 0, "notes": ""},
        "rewritten_summary": "",
        "rewritten_bullets": [],
        "quantified_achievement_suggestions": [],
        "personalized_recommendations": [],
        "job_match_score": 0,
        "error": reason,
    }


def analyze_resume(resume_text: str, jd_text: str = "", retries: int = 2) -> Dict:
    if not configure():
        return _fallback("GEMINI_API_KEY not configured")

    prompt = f"""
You are a senior technical recruiter and ATS optimization expert.
Analyze the following resume{" against the provided job description" if jd_text else ""}.

RESUME:
\"\"\"
{resume_text[:15000]}
\"\"\"

{"JOB DESCRIPTION:\\n\\\"\\\"\\\"\\n" + jd_text[:8000] + "\\n\\\"\\\"\\\"" if jd_text else ""}

Tasks:
- Score overall ATS compatibility (0-100).
- Score each section listed in the schema (0-100).
- Provide a star rating (1-5).
- Identify strengths, weaknesses, missing sections.
- Identify missing skills from the JD (empty if no JD) and explain why each matters.
- Assess resume completeness.
- Rewrite the professional summary in a stronger, ATS-friendly form.
- Rewrite up to 5 weak bullet points using strong action verbs + quantified impact.
- Suggest quantified achievements the candidate should add.
- Provide personalized recommendations to improve ATS compatibility.
- Provide a final job_match_score (0-100). If no JD, set 0.

{ANALYSIS_SCHEMA_HINT}
""".strip()

    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config={"response_mime_type": "application/json", "temperature": 0.4},
    )

    last_err = ""
    for attempt in range(retries + 1):
        try:
            resp = model.generate_content(prompt)
            text = resp.text or ""
            return _extract_json(text)
        except Exception as e:
            last_err = str(e)
            time.sleep(1.5 * (attempt + 1))
    return _fallback(f"Gemini call failed: {last_err}")
