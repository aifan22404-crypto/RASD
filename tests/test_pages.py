"""Smoke tests: every page loads without exceptions in English and Arabic (SPEC section 14.2)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from rasd import storage
from rasd.i18n import t

ROOT = Path(__file__).resolve().parents[1]
PAGE_TITLES = {"pages/1_dashboard.py": "nav_dashboard", "pages/2_precheck.py": "nav_precheck",
               "pages/3_radar.py": "nav_radar", "pages/4_connections.py": "nav_connections",
               "pages/5_review.py": "nav_review", "pages/6_audit.py": "nav_audit", "pages/7_model_card.py": "nav_model"}
PAGES = list(PAGE_TITLES)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test_rasd.db")


def _app(lang="en", **state) -> AppTest:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.session_state["lang"] = lang
    for key, value in state.items():
        at.session_state[key] = value
    return at


def _all_text(at) -> str:
    return "\n".join(str(e.value) for e in at.markdown) + "\n".join(str(e.value) for e in at.caption)


@pytest.mark.parametrize("lang", ["en", "ar"])
@pytest.mark.parametrize("page", PAGES)
def test_page_loads(page, lang):
    at = _app(lang, pack_tender="T-104")
    at.switch_page(page).run()
    assert not at.exception, at.exception
    assert at.title[0].value == t(PAGE_TITLES[page], lang)


@pytest.mark.parametrize("lang", ["en", "ar"])
def test_banner_on_first_load(lang):
    # AppTest re-indexes entry-script elements after switch_page, so the banner is checked on the default page.
    at = _app(lang)
    at.run()
    assert not at.exception
    assert at.warning[0].value == t("banner", lang)


def test_dashboard_kpis_and_t104_first():
    at = _app()
    at.run()
    assert not at.exception
    assert [m.value for m in at.metric] == ["12", "45", "8", "6"]
    df = at.dataframe[0].value
    first = df.data.iloc[0] if hasattr(df, "data") else df.iloc[0]
    assert first["Tender"] == "T-104" and first["Priority"] == "🔴 Urgent review"


def test_stretch_off_leaves_only_t104_above_routine():
    at = _app(include_stretch=False)
    at.run()
    assert not at.exception
    assert [m.value for m in at.metric][2] == "1"


def test_review_page_highlights_rare_sentence_and_saves_decision():
    at = _app(pack_tender="T-104")
    at.switch_page("pages/5_review.py").run()
    assert not at.exception
    text = _all_text(at)
    assert "<mark>We will deliver 500 laptpos configured to the required build within 21 days of the purchase order.</mark>" in text
    assert "Standard tender wording — ignored" in text

    decision_radio = next(r for r in at.radio if len(r.options) == 3)
    decision_radio.set_value("REFER_FOR_INTERNAL_REVIEW")
    at.text_area[0].input("Undisclosed shared owner, refer to internal audit.")
    # AppTest drops entry-script (sidebar) widgets from its tree after switch_page, so set the name directly.
    at.session_state["reviewer"] = "Reviewer 1"
    next(b for b in at.button if b.label == "Submit decision").click()
    at.run()
    assert not at.exception
    latest = storage.latest_decision("T-104")
    assert latest is not None and latest["decision"] == "REFER_FOR_INTERNAL_REVIEW"
    assert latest["reviewer"] == "Reviewer 1" and latest["priority_at_decision"] == "Urgent review"

    at.switch_page("pages/6_audit.py").run()
    assert not at.exception
    assert "T-104" in at.dataframe[0].value.to_string()
