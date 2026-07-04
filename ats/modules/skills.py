"""Skill extraction and JD-vs-resume gap detection."""
from __future__ import annotations

import re
from typing import Dict, List

# Non-exhaustive skill lexicon. Gemini handles the rest.
SKILL_LEXICON = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby", "php",
    "sql", "nosql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "react", "next.js", "vue", "angular", "svelte", "node.js", "express", "django", "flask", "fastapi",
    "spring", "rails", "laravel",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible", "jenkins", "ci/cd",
    "git", "github", "gitlab", "linux", "bash",
    "machine learning", "deep learning", "nlp", "computer vision", "pytorch", "tensorflow",
    "scikit-learn", "pandas", "numpy", "spark", "hadoop", "airflow", "kafka",
    "tableau", "power bi", "excel", "figma",
    "rest", "graphql", "microservices", "agile", "scrum", "jira",
    "html", "css", "tailwind", "sass",
}


def extract_skills(text: str) -> List[str]:
    lower = text.lower()
    found = set()
    for skill in SKILL_LEXICON:
        pattern = r"(?<![A-Za-z0-9])" + re.escape(skill) + r"(?![A-Za-z0-9])"
        if re.search(pattern, lower):
            found.add(skill)
    return sorted(found)


def compare_skills(resume_text: str, jd_text: str) -> Dict[str, List[str]]:
    resume_skills = set(extract_skills(resume_text))
    jd_skills = set(extract_skills(jd_text)) if jd_text else set()
    return {
        "resume_skills": sorted(resume_skills),
        "jd_skills": sorted(jd_skills),
        "matched": sorted(resume_skills & jd_skills),
        "missing": sorted(jd_skills - resume_skills),
    }
