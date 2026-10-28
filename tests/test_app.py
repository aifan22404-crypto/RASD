"""Tests for the review pack, templates, storage and LLM fact check (SPEC section 14.1)."""
from pathlib import Path

import pytest

from rasd import engine, llm, review_pack, storage, templates

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def db():
    return engine.load(ROOT / "data")


@pytest.fixture(scope="module")
def res_full(db):
    return engine.run_all(db, include_stretch=True)


@pytest.fixture(scope="module")
def res_mvp(db):
    return engine.run_all(db, include_stretch=False)


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test_rasd.db")
    storage.init_db()
    return tmp_path / "test_rasd.db"


# ---------------------------------------------------------------- review pack
def test_t104_pack_contents(db, res_full):
    pack = review_pack.make_review_pack("T-104", res_full, db, "en")
    codes = {ind["code"] for ind in pack["indicators"]}
    assert {"BIDDER_RELATIONSHIP", "PRICE_PATTERN_REVIEW", "SHARED_RARE_PHRASE", "DOC_METADATA_MATCH"} <= codes
    assert sorted((p["bid_id"], p["code"]) for p in pack["precheck"]) == [
        ("B-016", "LICENCE_EXPIRED"), ("B-017", "MISSING_DOCUMENT")]
    assert pack["header"]["priority"] == "Urgent review"
    assert len(pack["top"]) == 3 and len(pack["more"]) == 1
    # sorted by severity: the two strong indicators come first
    assert [ind["severity"] for ind in pack["indicators"]] == ["strong", "strong", "moderate", "weak"]


def test_t104_template_sentences(db, res_full):
    pack = review_pack.make_review_pack("T-104", res_full, db, "en")
    by_code = {ind["code"]: ind["summary"] for ind in pack["indicators"]}
    assert by_code["PRICE_PATTERN_REVIEW"] == (
        "The 5 bids are unusually close together (coefficient of variation 0.027), and the lowest bid is 3.2% "
        "below the next one (relative distance 1.53).")
    assert by_code["BIDDER_RELATIONSHIP"] == (
        "C04 and C05 bid against each other but share the same owner (O-17) in the registry, "
        "and no relationship was disclosed.")
    assert "We will deliver 500 laptpos configured to the required build within 21 days of the purchase order" in by_code["SHARED_RARE_PHRASE"]
    assert by_code["DOC_METADATA_MATCH"] == "Proposals B-013 and B-014 list the same document author ('m.khan')."


def test_rare_sentence_highlighted_and_rfp_greyed(db, res_full):
    pack = review_pack.make_review_pack("T-104", res_full, db, "en")
    rare = next(ind for ind in pack["indicators"] if ind["code"] == "SHARED_RARE_PHRASE")
    proposals = {e["id"]: e for e in rare["evidence"] if e["table"] == "proposals"}
    assert set(proposals) == {"B-013", "B-014"}
    for item in proposals.values():
        kinds = {s["text"]: s["kind"] for s in item["segments"]}
        assert kinds["We will deliver 500 laptpos configured to the required build within 21 days of the purchase order."] == "rare"
        assert kinds["The supplier shall provide three years of on-site warranty support."] == "rfp"


def test_evidence_resolves_source_records(db, res_full):
    for alert in res_full["alerts"]:
        items = review_pack.resolve_evidence(alert["evidence_ids"], db)
        assert items and all(item["records"] for item in items), alert["evidence_ids"]


@pytest.mark.parametrize("lang", ["en", "ar"])
def test_templates_leave_no_braces(db, res_full, res_mvp, lang):
    for alert in res_full["alerts"] + res_mvp["alerts"]:
        texts = [templates.summary(alert, lang, db), templates.innocent(alert, lang), *templates.checklist(alert, lang)]
        for text in texts:
            assert "{" not in text and "}" not in text, text
    for finding in res_full["precheck"]:
        line = templates.precheck_line(finding, db, lang)
        assert "{" not in line and "}" not in line


@pytest.mark.parametrize("lang", ["en", "ar"])
def test_markdown_export_framing(db, res_full, lang):
    from rasd.i18n import t
    for tid in db["tenders"].tender_id:
        md = review_pack.pack_to_markdown(review_pack.make_review_pack(tid, res_full, db, lang), lang)
        assert md.startswith(f"> {t('banner', lang)}")
        assert md.rstrip().endswith(t("disclaimer", lang))
        assert "{" not in md and "}" not in md


def test_no_accusatory_wording_in_ui_strings():
    from rasd.i18n import STRINGS
    banned = ("fraud", "guilty", "corrupt", "cartel", "criminal")
    for key, entry in STRINGS.items():
        for text in entry.values():
            assert not any(word in text.lower() for word in banned), key


# ---------------------------------------------------------------- storage
def test_storage_round_trip(temp_db):
    saved = storage.save_decision("T-104", "REFER_FOR_INTERNAL_REVIEW", "Owner link needs checking.", "Reviewer 1",
                                  "Urgent review", ["BIDDER_RELATIONSHIP", "PRICE_PATTERN_REVIEW"],
                                  "rasd-engine-1.0", True)
    storage.save_decision("T-101", "CLEAR", "Rotation explained by market size.", "Reviewer 2",
                          "Review", "REPEATED_WIN_SEQUENCE", "rasd-engine-1.0", False)
    all_rows = storage.list_decisions()
    assert [r["tender_id"] for r in all_rows] == ["T-101", "T-104"]  # newest first
    t104 = storage.list_decisions("T-104")
    assert len(t104) == 1 and t104[0]["alert_codes"] == "BIDDER_RELATIONSHIP,PRICE_PATTERN_REVIEW"
    latest = storage.latest_decision("T-104")
    assert latest == saved and latest["include_stretch"] == 1 and latest["created_at"]
    assert storage.latest_decision("T-105") is None


def test_storage_rejects_short_reason_and_unknown_decision(temp_db):
    with pytest.raises(ValueError):
        storage.save_decision("T-104", "CLEAR", "too short", "R", "Routine", [], "rasd-engine-1.0", True)
    with pytest.raises(ValueError):
        storage.save_decision("T-104", "REJECT", "a long enough reason", "R", "Routine", [], "rasd-engine-1.0", True)
    assert storage.list_decisions() == []


def test_timing_summary(temp_db):
    assert storage.timing_summary()["reduction_pct"] is None
    for mode in ("manual", "assisted"):
        sid = storage.start_timer("T-104", "Reviewer 1", mode)
        assert storage.stop_timer(sid) is not None
        assert storage.stop_timer(sid) is None  # already closed
    summary = storage.timing_summary()
    assert summary["n_manual"] == 1 and summary["n_assisted"] == 1


# ---------------------------------------------------------------- LLM fact check
SOURCE = ("The 5 bids are unusually close together (coefficient of variation 0.027), and the lowest bid is 3.2% "
          "below the next one (relative distance 1.53). C04 and C05 share owner O-17. Licence expired on 2026-08-31.")


def test_fact_check_accepts_faithful_rewrite():
    assert llm.fact_check("Five bids from C04 and C05 are close (CV 0.027, gap 3.2%, distance 1.53); "
                          "a licence expired 2026-08-31.", SOURCE)


def test_fact_check_rejects_new_number():
    assert not llm.fact_check("The 6 bids are close (CV 0.027).", SOURCE)


def test_fact_check_rejects_banned_word():
    assert not llm.fact_check("The 5 bids suggest fraud by C04.", SOURCE)


def test_fact_check_rejects_new_id():
    assert not llm.fact_check("C04 and C07 share owner O-17.", SOURCE)


def test_llm_off_without_config(monkeypatch):
    for key in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        monkeypatch.delenv(key, raising=False)
    assert not llm.is_configured()
    text, used = llm.rewrite(["One sentence."], "en")
    assert text == "One sentence." and used is False
