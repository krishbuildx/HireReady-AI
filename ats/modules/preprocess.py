"""Text preprocessing using spaCy + NLTK."""
from __future__ import annotations

import re
from functools import lru_cache
from typing import List

import nltk
from nltk.corpus import stopwords


def _ensure_nltk():
    for pkg in ("stopwords", "punkt", "wordnet"):
        try:
            nltk.data.find(f"corpora/{pkg}" if pkg != "punkt" else "tokenizers/punkt")
        except LookupError:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                pass


@lru_cache(maxsize=1)
def _nlp():
    import spacy
    try:
        return spacy.load("en_core_web_sm", disable=["ner", "parser"])
    except OSError:
        from spacy.cli import download
        download("en_core_web_sm")
        return spacy.load("en_core_web_sm", disable=["ner", "parser"])


@lru_cache(maxsize=1)
def _stopwords() -> set:
    _ensure_nltk()
    try:
        return set(stopwords.words("english"))
    except Exception:
        return set()


def clean_text(text: str) -> str:
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^A-Za-z0-9+#.\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def tokenize_lemmatize(text: str) -> List[str]:
    doc = _nlp()(clean_text(text))
    sw = _stopwords()
    out = []
    for tok in doc:
        if tok.is_space or tok.is_punct:
            continue
        lemma = tok.lemma_.strip().lower()
        if not lemma or lemma in sw or len(lemma) < 2:
            continue
        out.append(lemma)
    return out


def keyword_frequency(text: str, top_n: int = 20) -> List[tuple]:
    from collections import Counter
    tokens = tokenize_lemmatize(text)
    return Counter(tokens).most_common(top_n)
