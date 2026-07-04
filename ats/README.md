# AI-Powered ATS Resume Analyzer

Modern ATS resume analyzer built with **Streamlit + Google Gemini**.

## Features
- Upload resume (PDF / DOCX / TXT) and optional Job Description
- Rule-based text extraction (PyMuPDF, pdfplumber, python-docx)
- Preprocessing with spaCy + NLTK
- TF-IDF + Cosine similarity for Resume vs JD match
- Gemini-powered analysis (scores, strengths, weaknesses, rewriting, suggestions)
- Interactive dashboard (gauge, radar, bar, keyword frequency, missing skills)
- Downloadable PDF report

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m nltk.downloader punkt stopwords wordnet
```

## Configure Gemini API Key

Either export env var:
```bash
export GEMINI_API_KEY="your_key_here"
```

Or create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your_key_here"
```

Get a key at https://aistudio.google.com/app/apikey

## Run

```bash
streamlit run app.py
```

## Project Structure

```
app.py                     # Streamlit UI + dashboard
modules/
  parser.py                # Resume text extraction (PDF/DOCX/TXT)
  preprocess.py            # spaCy + NLTK cleaning, tokenizing
  similarity.py            # TF-IDF cosine similarity
  skills.py                # Skill extraction + missing-skill detection
  grammar.py               # LanguageTool grammar checks
  readability.py           # textstat readability metrics
  gemini_analyzer.py       # Gemini structured JSON analysis
  report_generator.py      # PDF report (ReportLab)
requirements.txt
```

## Notes
- No ML training. Gemini handles evaluation/scoring/rewriting.
- Rule-based extraction + TF-IDF only for similarity.
- API errors and rate limits are handled gracefully with fallbacks.
