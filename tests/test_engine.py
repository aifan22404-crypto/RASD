"""Acceptance tests. The finished app must keep all of these passing.
Run from the project root:  pytest -q
"""
import json
from pathlib import Path

import pytest

from rasd import engine

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXPECTED = json.loads((ROOT / "tests" / "expected_results.json").read_text())


@pytest.fixture(scope="module")
def db():
    return engine.load(DATA)


def _triples(alerts):
    return sorted((a["tender_id"], a["code"], a["severity"]) for a in alerts)


def test_precheck_matches_expected(db):
    got = sorted((p["bid_id"], p["code"]) for p in engine.precheck(db))
    exp = sorted((p["bid_id"], p["code"]) for p in EXPECTED["precheck"])
    assert got == exp


def test_mvp_alerts_and_priority(db):
    res = engine.run_all(db, include_stretch=False)
    assert _triples(res["alerts"]) == _triples(EXPECTED["mvp"]["alerts"])
    assert res["priority"] == EXPECTED["mvp"]["priority"]


def test_full_alerts_and_priority(db):
    res = engine.run_all(db, include_stretch=True)
    assert _triples(res["alerts"]) == _triples(EXPECTED["full"]["alerts"])
    assert res["priority"] == EXPECTED["full"]["priority"]


def test_t104_is_the_only_urgent_case(db):
    pr = engine.run_all(db, include_stretch=True)["priority"]
    assert [t for t, p in pr.items() if p == "Urgent review"] == ["T-104"]


def test_price_features_t104(db):
    f = engine.price_features(db["bids"][db["bids"].tender_id == "T-104"].amount_aed)
    assert f["bid_count"] == 5
    assert round(f["cv"], 4) == 0.0268
    assert round(f["rd"], 2) == 1.53


def test_cv_zero_for_equal_prices():
    assert engine.price_features([100, 100, 100])["cv"] == 0.0


def test_too_few_bids_gives_no_statistics():
    f = engine.price_features([100, 120])
    assert f["cv"] is None and f["rd"] is None


def test_missing_owner_never_links(db):
    co = db["companies"].copy()
    co.loc[co.company_id.isin(["C04", "C05"]), "owner_id"] = ""
    db2 = dict(db, companies=co)
    alerts = engine.relationship_alerts(db2)
    assert not any("owner" in a["observed_value"] and a["tender_id"] == "T-104" for a in alerts)


def test_rfp_boilerplate_is_not_flagged(db):
    # T-108 bids all copy RFP sentences; this must not create a text alert
    assert not any(a["tender_id"] == "T-108" for a in engine.document_alerts(db))


def test_common_industry_phrase_is_not_rare(db):
    # "We are committed to quality, safety..." appears in many proposals -> never flagged
    assert all("committed to quality" not in a["observed_value"] for a in engine.document_alerts(db))


def test_disclosed_group_is_context_only(db):
    t107 = [a for a in engine.relationship_alerts(db) if a["tender_id"] == "T-107"]
    assert t107 and all(a["severity"] == "context" for a in t107)
