"""Rasd (رصد) — Procurement Integrity Radar. Entry point: page config, sidebar, navigation.

Run:  streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="Rasd | رصد", page_icon="🛰️", layout="wide")

from rasd import storage, ui  # noqa: E402  (set_page_config must run first)
from rasd.i18n import t  # noqa: E402

ui.init_state()
storage.init_db()
ui.sidebar()
ui.inject_css()

pages = [
    st.Page("pages/1_dashboard.py", title=t("nav_dashboard"), default=True),
    st.Page("pages/2_precheck.py", title=t("nav_precheck")),
    st.Page("pages/3_radar.py", title=t("nav_radar")),
    st.Page("pages/4_connections.py", title=t("nav_connections")),
    st.Page("pages/5_review.py", title=t("nav_review")),
    st.Page("pages/6_audit.py", title=t("nav_audit")),
    st.Page("pages/7_model_card.py", title=t("nav_model")),
]
page = st.navigation(pages)
ui.banner()
page.run()
