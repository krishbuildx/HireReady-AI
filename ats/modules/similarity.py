"""TF-IDF + Cosine similarity between resume and job description."""
from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocess import clean_text


def similarity_score(resume_text: str, jd_text: str) -> float:
    if not resume_text.strip() or not jd_text.strip():
        return 0.0
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
    tfidf = vec.fit_transform([clean_text(resume_text), clean_text(jd_text)])
    sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return float(round(sim * 100, 2))
