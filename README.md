# Rasd (رصد) — Procurement Integrity Radar

Rasd is a bilingual (English/Arabic) web app for government procurement teams. Before a contract is awarded it (1) **pre-checks bids** for missing documents and expired licences, (2) runs an **Integrity Radar** that raises explained warning signs of possible bid-rigging or overpricing as **reason codes** (never a "fraud %"), and (3) prepares an **Evidence Review Pack** so a human reviewer can decide quickly. Every human decision is logged. Rasd is an add-on layer for existing procurement platforms, built for the UAE Hackathon 2026, Theme "Zero Bureaucracy & Seamless Government", Challenge 5 (procurement).

> **Data disclaimer:** all demo data is synthetic. Every tender, company and relationship is fictional. Indicators require human review and are not evidence of wrongdoing.

## Screenshots

_Add screenshots to `docs/screenshots/` before submission (dashboard, Integrity Radar for T-104, Bidder Connections, Evidence tab, Arabic view)._

## Run locally

Python 3.11+ (3.12 recommended).

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest -q
```

The suite contains the 11 engine acceptance tests from the starter kit, review-pack / template / storage / LLM fact-check tests, and `streamlit.testing` smoke tests that load every page in English and Arabic.

## Project layout

```
app.py                 entry point: page config, sidebar, navigation, banner
pages/1_dashboard.py … pages/7_model_card.py
rasd/engine.py         verified detection engine (unchanged)
rasd/data_access.py    cached loading + engine run + lookups
rasd/i18n.py           all UI strings EN/AR
rasd/templates.py      review-pack sentence templates EN/AR
rasd/review_pack.py    make_review_pack(), pack_to_markdown()
rasd/storage.py        SQLite decisions + timing sessions (rasd.db)
rasd/llm.py            optional AI rewrite + fact check (off by default)
rasd/ui.py             banner, badges, language toggle, RTL CSS
data/                  synthetic CSVs
tests/                 tests
MODEL_CARD.md          purpose, detectors, limitations, claims, human-in-the-loop rules
```

## Optional AI summary

Off by default. To enable, set `LLM_API_KEY`, `LLM_BASE_URL` (an OpenAI-compatible endpoint, e.g. `https://…/v1`) and `LLM_MODEL` in `.streamlit/secrets.toml` or as environment variables, then switch on "Plain-language summary (AI)" in the sidebar. Only the already-filled template sentences of one tender are sent. Output that changes any ID, number or date, or uses accusatory words, is rejected and the standard text is shown instead.

## Deployment (Streamlit Community Cloud)

1. Push this folder to a public GitHub repository (`.gitignore` already excludes `rasd.db`, `.venv/`, `__pycache__/` and `.streamlit/secrets.toml`).
2. Streamlit Community Cloud → New app → the repo, branch `main`, main file `app.py`, Advanced settings → Python 3.12.
3. Optional LLM keys go in the app's Secrets panel.

The cloud demo uses synthetic data only, and its SQLite database resets whenever the app restarts. A production deployment would run on UAE-hosted infrastructure with read-only access to procurement systems.

## Research datasets

None are used by this app. If an offline experiment on public research data is added, cite it here.

## Team

_Team names go here._
