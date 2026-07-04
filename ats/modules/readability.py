"""Readability metrics using textstat."""
from __future__ import annotations

from typing import Dict

import textstat


def readability_metrics(text: str) -> Dict:
    if not text.strip():
        return {"score": 0, "flesch_reading_ease": 0, "grade_level": 0, "smog": 0}
    ease = textstat.flesch_reading_ease(text)
    grade = textstat.flesch_kincaid_grade(text)
    smog = textstat.smog_index(text)
    # Map Flesch reading ease (0-100) to a normalized score for ATS clarity
    score = max(0, min(100, int(ease)))
    return {
        "score": score,
        "flesch_reading_ease": round(ease, 2),
        "grade_level": round(grade, 2),
        "smog": round(smog, 2),
    }
