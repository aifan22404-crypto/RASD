"""Shared UI pieces: session defaults, sidebar, CSS/RTL, banner, badges, tender selector."""
from __future__ import annotations

import html

import streamlit as st

from rasd import llm
from rasd.data_access import ENGINE_VERSION
from rasd.i18n import PRIORITY_KEYS, t

PRIORITY_COLORS = {"Urgent review": "#C62828", "Review": "#EF8F00", "Routine": "#2E7D32"}
PRIORITY_DOTS = {"Urgent review": "🔴", "Review": "🟠", "Routine": "🟢"}
SEVERITY_COLORS = {"strong": "#C62828", "moderate": "#EF8F00", "weak": "#7B8794", "context": "#546E7A"}
DEFAULT_TENDER = "T-104"

_BASE_CSS = """
<style>
.rasd-logo {font-size: 1.6rem; font-weight: 700; color: #0B5394; margin-bottom: 0;}
.rasd-badge {display: inline-block; padding: 2px 10px; border-radius: 12px; color: #FFFFFF;
             font-size: 0.8rem; font-weight: 600; white-space: nowrap;}
.rasd-ltr {direction: ltr; unicode-bidi: isolate; font-family: monospace; font-size: 0.85rem;}
.rasd-proposal {border: 1px solid #D9E2EC; border-radius: 8px; padding: 12px 14px; background: #F8FAFC; line-height: 1.7;}
[data-testid="stMain"] mark {background: #FFE08A; padding: 1px 2px; border-radius: 3px;}
.rasd-grey {color: #9AA5B1;}
.rasd-grey-tag {font-size: 0.72rem; color: #7B8794; border: 1px solid #CBD2D9; border-radius: 8px; padding: 0 6px; margin: 0 4px;}
.rasd-legend-line {display: inline-block; width: 36px; vertical-align: middle; margin: 0 8px;}
</style>
"""

_ARABIC_CSS = """
<style>@import url('https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@400;600&display=swap'); [data-testid="stMain"] * { font-family: 'Noto Kufi Arabic', sans-serif; }</style>
<style>
[data-testid="stMain"] { direction: rtl; text-align: right; }
[data-testid="stMain"] [data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
[data-testid="stMain"] [class*="st-key-ltr"] { direction: ltr; text-align: left; }
[data-testid="stMain"] .rasd-ltr { font-family: monospace; }
</style>
"""


_DEFAULTS = {"lang": "en", "reviewer": "Reviewer 1", "include_stretch": True, "ai_on": False,
             "tender_id": DEFAULT_TENDER}
# Persistent value key -> sidebar widget key. Streamlit drops widget-bound keys when the page changes,
# so the values live under plain keys and each widget is re-seeded from them on every run.
_SIDEBAR_WIDGETS = {"lang": "_lang_widget", "reviewer": "_reviewer_widget",
                    "include_stretch": "_stretch_widget", "ai_on": "_ai_widget"}


def init_state() -> None:
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _sync(key: str) -> None:
    value = st.session_state[_SIDEBAR_WIDGETS[key]]
    if key == "lang" and value is None:  # clicking the active segment deselects it; keep the current language
        return
    st.session_state[key] = value


def sidebar() -> None:
    for key, widget_key in _SIDEBAR_WIDGETS.items():
        st.session_state[widget_key] = st.session_state[key]
    with st.sidebar:
        st.markdown(f'<p class="rasd-logo">{t("logo")}</p>', unsafe_allow_html=True)
        st.caption(t("tagline"))
        st.segmented_control(t("lang_label"), options=["en", "ar"], key="_lang_widget",
                             format_func=lambda code: "EN" if code == "en" else "العربية",
                             on_change=_sync, args=("lang",))
        st.text_input(t("reviewer"), key="_reviewer_widget", on_change=_sync, args=("reviewer",))
        st.checkbox(t("stretch_toggle"), key="_stretch_widget", on_change=_sync, args=("include_stretch",))
        if llm.is_configured():
            st.toggle(t("ai_toggle"), key="_ai_widget", on_change=_sync, args=("ai_on",))
        st.caption(t("engine_caption", version=ENGINE_VERSION))


def inject_css() -> None:
    st.markdown(_BASE_CSS, unsafe_allow_html=True)
    if st.session_state.get("lang") == "ar":
        st.markdown(_ARABIC_CSS, unsafe_allow_html=True)


def banner() -> None:
    st.warning(t("banner"))


def ltr_container(name: str):
    """Container whose content stays left-to-right in Arabic mode (charts, network graph)."""
    return st.container(key=f"ltr_{name}")


# ---------------------------------------------------------------- badges and formatting
def priority_text(priority: str) -> str:
    return f"{PRIORITY_DOTS[priority]} {t(PRIORITY_KEYS[priority])}"


def badge_html(text: str, color: str) -> str:
    return f'<span class="rasd-badge" style="background:{color}">{html.escape(text)}</span>'


def priority_badge(priority: str) -> str:
    return badge_html(priority_text(priority), PRIORITY_COLORS[priority])


def severity_badge(severity: str) -> str:
    return badge_html(t(f"sev_{severity}"), SEVERITY_COLORS[severity])


def ltr(text: str) -> str:
    return f'<span class="rasd-ltr">{html.escape(str(text))}</span>'


def fmt_aed(value) -> str:
    return f"{float(value):,.0f}"


def decision_status(latest: dict | None) -> str:
    return t(f"dec_{latest['decision']}") if latest else t("status_open")


# ---------------------------------------------------------------- tender selector (pages 2-5)
def _sync_tender() -> None:
    st.session_state["tender_id"] = st.session_state["_tender_widget"]


def tender_selector(db) -> str:
    """Selectbox shared through st.session_state['tender_id'] (default T-104)."""
    tenders = db["tenders"].set_index("tender_id")
    ids = list(tenders.index)
    if st.session_state.get("tender_id") not in ids:
        st.session_state["tender_id"] = DEFAULT_TENDER if DEFAULT_TENDER in ids else ids[0]
    st.session_state["_tender_widget"] = st.session_state["tender_id"]
    st.selectbox(t("tender"), ids, key="_tender_widget", on_change=_sync_tender,
                 format_func=lambda tid: f"{tid} — {tenders.loc[tid, 'title_en']}")
    return st.session_state["tender_id"]
