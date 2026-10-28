"""Optional plain-language rewrite of the template sentences (OFF by default).

Only the already-filled template sentences for one tender are sent; never raw tables.
Every output is fact-checked against the input; on any failure the caller shows the template text.
"""
from __future__ import annotations

import os
import re

import requests

TIMEOUT_S = 10
_KEYS = ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL")

SYSTEM_PROMPT = ("Rewrite the following review notes as one short paragraph in {language} for a procurement officer. "
                 "Use only the facts given. Do not add facts, opinions, accusations or legal conclusions. "
                 "Keep every company ID, bid ID, number and date exactly as written.")

BANNED_WORDS = ("fraud", "fraudulent", "guilty", "corrupt", "cartel", "criminal", "احتيال", "مذنب", "فساد", "كارتل")

_TOKEN_PATTERNS = (
    r"\d{4}-\d{2}-\d{2}",  # dates
    r"C\d{2}",             # company IDs
    r"B-\d{3}",            # bid IDs
    r"T-\d{3}",            # tender IDs
    r"\d[\d,.]*",          # numbers (\d also matches non-Western digits, which are then rejected)
)


def _config() -> dict | None:
    values = {}
    for key in _KEYS:
        value = None
        try:
            import streamlit as st
            value = st.secrets.get(key)
        except Exception:  # no secrets file, or not running under Streamlit
            value = None
        values[key] = value or os.environ.get(key)
    return values if all(values.values()) else None


def is_configured() -> bool:
    return _config() is not None


def _tokens(text: str) -> set[str]:
    found = set()
    for pattern in _TOKEN_PATTERNS:
        for match in re.findall(pattern, text):
            found.add(match.rstrip(".,"))
    found.discard("")
    return found


def fact_check(output: str, source: str) -> bool:
    """True only if every ID, number and date in `output` appears in `source` and no banned word is used."""
    lowered = output.lower()
    if any(word in lowered for word in BANNED_WORDS):
        return False
    return _tokens(output) <= _tokens(source)


def rewrite(sentences: list[str], lang: str) -> tuple[str, bool]:
    """(text, used_ai). Falls back to the joined template sentences on any error or failed check."""
    source = " ".join(sentences)
    cfg = _config()
    if cfg is None or not sentences:
        return source, False
    language = "Arabic" if lang == "ar" else "English"
    url = cfg["LLM_BASE_URL"].rstrip("/")
    if not url.endswith("/chat/completions"):
        url += "/chat/completions"
    try:
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {cfg['LLM_API_KEY']}"},
            json={"model": cfg["LLM_MODEL"], "temperature": 0,
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT.format(language=language)},
                               {"role": "user", "content": source}]},
            timeout=TIMEOUT_S,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return source, False
    if not text or not fact_check(text, source):
        return source, False
    return text, True
