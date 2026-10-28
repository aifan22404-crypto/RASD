"""Page 7 — Model Card."""
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

from rasd import data_access as da
from rasd import engine
from rasd.i18n import t

db, res = da.get()

st.title(t("nav_model"))
if t("model_card_lang_note"):
    st.caption(t("model_card_lang_note"))

card = Path(__file__).resolve().parents[1] / "MODEL_CARD.md"
if card.exists():
    st.markdown(card.read_text(encoding="utf-8"))
else:
    st.error(t("model_card_missing"))

st.subheader(t("config_table"))
st.dataframe(pd.DataFrame([{t("param"): k, t("value"): str(v)} for k, v in engine.CONFIG.items()]),
             hide_index=True, width="stretch")

st.subheader(t("alert_counts"))
counts = Counter(a["code"] for a in res["alerts"])
codes = sorted(engine.MVP_CODES | engine.STRETCH_CODES)
st.dataframe(pd.DataFrame([{t("code"): c, t("label"): t(f"code_{c}"), t("count"): counts.get(c, 0)} for c in codes]),
             hide_index=True, width="stretch")
