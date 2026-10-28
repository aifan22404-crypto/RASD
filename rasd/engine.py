"""
Rasd reference detection engine (verified against data/*.csv).

This file is the SOURCE OF TRUTH for detection logic. The app must reproduce
its outputs exactly (see expected_results.json). Split it into src/ modules
as described in SPEC.md, but do not change thresholds or rules.

Run from project root:  python rasd/engine.py data   -> prints results, writes expected_results.json
"""
from __future__ import annotations

import itertools
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

# ---------------------------------------------------------------- config
CONFIG = {
    "MIN_BIDS_CV": 3,          # need >= 3 bids to compute coefficient of variation
    "MIN_BIDS_RD": 4,          # need >= 4 bids (>= 3 losing bids) for relative distance
    "CV_LOW": 0.03,            # demo threshold, NOT a proven collusion threshold
    "RD_HIGH": 1.0,            # demo threshold (relative distance screen)
    "SENT_MIN_WORDS": 6,       # ignore sentences shorter than this
    "BOILER_SIM": 90,          # rapidfuzz ratio vs RFP sentence => boilerplate, removed
    "SHARED_SIM": 92,          # rapidfuzz ratio between two bidders' sentences => "same"
    "MAX_DOC_FREQ": 2,         # a sentence is "rare" only if found in <= 2 proposals overall
    "BENCH_RATIO": 1.25,       # lowest unit price >= 1.25 x benchmark median => gap
    "BENCH_MIN_POINTS": 3,     # need >= 3 comparable benchmark prices
    "ROT_MIN_TENDERS": 5,      # same bidder set in >= 5 awarded tenders of one category
    "ROT_MIN_GROUP": 3,        # bidder set of >= 3 companies
}
SEVERITY_POINTS = {"strong": 3, "moderate": 2, "weak": 1, "context": 0}
MVP_CODES = {"PRICE_PATTERN_REVIEW", "BIDDER_RELATIONSHIP", "SHARED_RARE_PHRASE", "DOC_METADATA_MATCH"}
STRETCH_CODES = {"REPEATED_WIN_SEQUENCE", "BENCHMARK_GAP"}


# ---------------------------------------------------------------- loading
def load(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    d = Path(data_dir)
    co = pd.read_csv(d / "companies.csv", dtype=str).fillna("")
    te = pd.read_csv(d / "tenders.csv", dtype={"tender_id": str, "standardized": str}).fillna("")
    bi = pd.read_csv(d / "bids.csv", dtype={"is_winner": str, "documents_attached": str}).fillna("")
    pr = pd.read_csv(d / "proposals.csv", dtype=str).fillna("")
    bm = pd.read_csv(d / "benchmarks.csv")
    # referential integrity (fail loudly)
    assert bi.bid_id.is_unique, "duplicate bid_id"
    assert bi.tender_id.isin(te.tender_id).all(), "bid references unknown tender"
    assert bi.company_id.isin(co.company_id).all(), "bid references unknown company"
    assert pr.bid_id.isin(bi.bid_id).all(), "proposal references unknown bid"
    return {"companies": co, "tenders": te, "bids": bi, "proposals": pr, "benchmarks": bm}


def _alert(tender_id, code, severity, label, observed, comparator, evidence_ids, limitations, params=None):
    """One structured alert. `params` holds the raw values used by the review-pack templates."""
    return {
        "tender_id": tender_id, "code": code, "severity": severity, "label": label,
        "observed_value": observed, "comparator": comparator,
        "evidence_ids": evidence_ids, "limitations": limitations,
        "params": params or {},
    }


# ---------------------------------------------------------------- module 1: pre-check
def precheck(db) -> list[dict]:
    te = db["tenders"].set_index("tender_id")
    co = db["companies"].set_index("company_id")
    out = []
    for _, b in db["bids"].iterrows():
        t = te.loc[b.tender_id]
        required = [x for x in t.required_documents.split("|") if x]
        attached = [x for x in b.documents_attached.split("|") if x]
        for doc in required:
            if doc not in attached:
                out.append({"tender_id": b.tender_id, "bid_id": b.bid_id, "company_id": b.company_id,
                            "code": "MISSING_DOCUMENT", "detail": doc})
        expiry = co.loc[b.company_id, "licence_expiry"]
        if expiry and expiry < t.closing_date:  # ISO dates compare correctly as strings
            out.append({"tender_id": b.tender_id, "bid_id": b.bid_id, "company_id": b.company_id,
                        "code": "LICENCE_EXPIRED", "detail": f"licence expired {expiry}, tender closes {t.closing_date}"})
    return out


# ---------------------------------------------------------------- detector A: price pattern
def price_features(amounts) -> dict:
    x = np.sort(np.asarray(amounts, dtype=float))
    n = len(x)
    f = {"bid_count": n, "cv": None, "gap_pct": None, "rd": None}
    if n >= 2 and x[0] > 0:
        f["gap_pct"] = float((x[1] - x[0]) / x[0])
    if n >= CONFIG["MIN_BIDS_CV"] and np.all(x > 0):
        f["cv"] = float(np.std(x, ddof=1) / np.mean(x))
    if n >= CONFIG["MIN_BIDS_RD"]:
        s = float(np.std(x[1:], ddof=1))
        if s > 0:
            f["rd"] = float((x[1] - x[0]) / s)
    return f


def price_alerts(db) -> tuple[list[dict], dict]:
    te = db["tenders"].set_index("tender_id")
    alerts, feats = [], {}
    for tid, g in db["bids"].groupby("tender_id"):
        f = price_features(g.amount_aed.values)
        feats[tid] = f
        hits = []
        if f["cv"] is not None and f["cv"] <= CONFIG["CV_LOW"]:
            hits.append("cv")
        if f["rd"] is not None and f["rd"] >= CONFIG["RD_HIGH"]:
            hits.append("rd")
        if not hits:
            continue
        standardized = te.loc[tid, "standardized"] == "yes"
        severity = "weak" if standardized else ("strong" if len(hits) == 2 else "moderate")
        rd_txt = "n/a" if f["rd"] is None else f"{f['rd']:.2f}"
        alerts.append(_alert(
            tid, "PRICE_PATTERN_REVIEW", severity, "Unusual price pattern",
            f"CV={f['cv']:.4f}; relative distance={rd_txt}; gap between two lowest bids={f['gap_pct']:.2%}",
            f"CV <= {CONFIG['CV_LOW']} and/or relative distance >= {CONFIG['RD_HIGH']} (demo thresholds)",
            ";".join(f"bids:{b}" for b in g.bid_id),
            "Standardized products naturally attract close prices." if standardized
            else "A clue only; small bid counts make statistics noisy.",
            params={"bid_count": f["bid_count"], "cv": f["cv"], "rd": f["rd"], "gap_pct": f["gap_pct"], "standardized": standardized},
        ))
    return alerts, feats


# ---------------------------------------------------------------- detector C: bidder links
def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def relationship_alerts(db) -> list[dict]:
    co = db["companies"].set_index("company_id")
    out = []
    for tid, g in db["bids"].groupby("tender_id"):
        for a, b in itertools.combinations(sorted(g.company_id), 2):
            A, B = co.loc[a], co.loc[b]
            ev = f"companies:{a};companies:{b}"
            if A.owner_id and A.owner_id == B.owner_id:
                disclosed = bool(A.disclosed_group) and A.disclosed_group == B.disclosed_group
                out.append(_alert(
                    tid, "BIDDER_RELATIONSHIP", "context" if disclosed else "strong", "Linked bidders",
                    f"{a} and {b} share owner {A.owner_id}" + (f" (disclosed group {A.disclosed_group})" if disclosed else " (not disclosed)"),
                    "same owner_id in registry", ev,
                    "Disclosed group companies may legitimately bid separately." if disclosed
                    else "Verify registry data and whether the relationship was disclosed.",
                    params={"company_a": a, "company_b": b, "link_type": "owner", "value": A.owner_id, "disclosed": disclosed, "group": A.disclosed_group}))
            if A.phone and _norm(A.phone) == _norm(B.phone):
                out.append(_alert(tid, "BIDDER_RELATIONSHIP", "moderate", "Linked bidders",
                                  f"{a} and {b} share phone {A.phone}", "same phone", ev,
                                  "Shared switchboards exist.",
                                  params={"company_a": a, "company_b": b, "link_type": "phone", "value": A.phone}))
            if A.address and _norm(A.address) == _norm(B.address):
                bc = A.address_type == "business_centre" and B.address_type == "business_centre"
                out.append(_alert(tid, "BIDDER_RELATIONSHIP", "weak" if bc else "moderate", "Linked bidders",
                                  f"{a} and {b} share address '{A.address}'", "same address", ev,
                                  "Business centres host many unrelated firms." if bc else "Verify the address.",
                                  params={"company_a": a, "company_b": b, "link_type": "address", "value": A.address, "business_centre": bc}))
    return out


# ---------------------------------------------------------------- detector D: rare shared text
def sentences(text: str) -> list[str]:
    out = []
    for s in re.split(r"[.!?]+", text):
        s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
        s = re.sub(r"\s+", " ", s).strip()
        if len(s.split()) >= CONFIG["SENT_MIN_WORDS"]:
            out.append(s)
    return out


def document_alerts(db) -> list[dict]:
    te = db["tenders"].set_index("tender_id")
    pm = db["proposals"].set_index("bid_id")
    bids = db["bids"]
    # 1) remove RFP boilerplate
    S = {}
    for _, b in bids.iterrows():
        rfp = sentences(te.loc[b.tender_id, "rfp_text"])
        own = sentences(pm.loc[b.bid_id, "text"]) if b.bid_id in pm.index else []
        S[b.bid_id] = [s for s in own if not any(fuzz.ratio(s, r) >= CONFIG["BOILER_SIM"] for r in rfp)]

    # 2) corpus document frequency (how many proposals contain a similar sentence)
    def doc_freq(sent: str) -> int:
        return sum(1 for ss in S.values() if any(fuzz.ratio(sent, o) >= CONFIG["SHARED_SIM"] for o in ss))

    out = []
    for tid, g in bids.groupby("tender_id"):
        for x, y in itertools.combinations(list(g.bid_id), 2):
            shared = [(s, t) for s in S[x] for t in S[y]
                      if fuzz.ratio(s, t) >= CONFIG["SHARED_SIM"] and doc_freq(s) <= CONFIG["MAX_DOC_FREQ"]]
            if shared:
                out.append(_alert(
                    tid, "SHARED_RARE_PHRASE", "moderate", "Rare shared text",
                    f"{len(shared)} rare sentence(s) shared, e.g. \"{shared[0][0]}\"",
                    f"similarity >= {CONFIG['SHARED_SIM']}, not in RFP text, found in <= {CONFIG['MAX_DOC_FREQ']} proposals overall",
                    f"proposals:{x};proposals:{y}",
                    "Similar wording can be coincidental; check context.",
                    params={"bid_a": x, "bid_b": y, "count": len(shared), "sentence": shared[0][0]}))
            if x in pm.index and y in pm.index and pm.loc[x, "doc_author"] and pm.loc[x, "doc_author"] == pm.loc[y, "doc_author"]:
                out.append(_alert(
                    tid, "DOC_METADATA_MATCH", "weak", "Same document author",
                    f"both proposals list author '{pm.loc[x, 'doc_author']}'", "document author metadata",
                    f"proposals:{x};proposals:{y}", "Default author names can match innocently.",
                    params={"bid_a": x, "bid_b": y, "author": pm.loc[x, "doc_author"]}))
    return out


# ---------------------------------------------------------------- detector E (stretch): benchmark
def benchmark_alerts(db) -> list[dict]:
    bm, out = db["benchmarks"], []
    for _, t in db["tenders"].iterrows():
        sub = bm[bm.specification_id == t.specification_id]
        if len(sub) < CONFIG["BENCH_MIN_POINTS"] or float(t.quantity) <= 0:
            continue
        lowest_unit = db["bids"][db["bids"].tender_id == t.tender_id].amount_aed.min() / float(t.quantity)
        med = float(sub.unit_price_aed.median())
        ratio = lowest_unit / med
        if ratio >= CONFIG["BENCH_RATIO"]:
            out.append(_alert(
                t.tender_id, "BENCHMARK_GAP", "moderate", "Price above comparable purchases",
                f"lowest unit price AED {lowest_unit:,.0f} vs benchmark median AED {med:,.0f} ({ratio:.2f}x)",
                f">= {CONFIG['BENCH_RATIO']}x median of >= {CONFIG['BENCH_MIN_POINTS']} comparable purchases",
                f"benchmarks:{t.specification_id}",
                "Specification, quantity, timing and delivery terms must genuinely match.",
                params={"spec": t.specification_id, "lowest_unit": float(lowest_unit), "median": med, "ratio": float(ratio)}))
    return out


# ---------------------------------------------------------------- detector B (stretch): rotation
def rotation_alerts(db) -> list[dict]:
    bi, te = db["bids"], db["tenders"]
    aw = bi[bi.is_winner.isin(["yes", "no"])].merge(te[["tender_id", "category", "closing_date"]], on="tender_id")
    out = []
    for _, g in aw.groupby("category"):
        sets = g.groupby("tender_id").company_id.apply(lambda s: tuple(sorted(s)))
        for group, count in sets.value_counts().items():
            if count < CONFIG["ROT_MIN_TENDERS"] or len(group) < CONFIG["ROT_MIN_GROUP"]:
                continue
            tids = list(sets[sets == group].index)
            w = g[g.tender_id.isin(tids) & (g.is_winner == "yes")].sort_values("closing_date")
            seq = list(w.company_id)
            consecutive_repeat = any(seq[i] == seq[i + 1] for i in range(len(seq) - 1))
            fair_share = math.ceil(len(seq) / len(group))
            if len(set(seq)) >= 3 and not consecutive_repeat and max(seq.count(s) for s in set(seq)) <= fair_share:
                for tid in w.tender_id:
                    out.append(_alert(
                        tid, "REPEATED_WIN_SEQUENCE", "moderate", "Winners take turns",
                        "winners in date order: " + " > ".join(seq),
                        f"same {len(group)} bidders in {len(seq)} tenders; each wins in turn, nobody wins twice in a row",
                        ";".join(f"tenders:{t}" for t in w.tender_id),
                        "Alternation can happen by chance in small markets.",
                        params={"sequence": seq, "tenders": list(w.tender_id), "group_size": len(group)}))
    return out


# ---------------------------------------------------------------- risk engine
def triage(alerts_for_tender: list[dict]) -> str:
    pts = sum(SEVERITY_POINTS[a["severity"]] for a in alerts_for_tender)
    strong = sum(1 for a in alerts_for_tender if a["severity"] == "strong")
    if strong >= 1 and pts >= 5:
        return "Urgent review"
    if pts >= 2:
        return "Review"
    return "Routine"


def run_all(db, include_stretch: bool = True) -> dict:
    pa, feats = price_alerts(db)
    alerts = pa + relationship_alerts(db) + document_alerts(db)
    if include_stretch:
        alerts += benchmark_alerts(db) + rotation_alerts(db)
    by_t = {t: [] for t in db["tenders"].tender_id}
    for a in alerts:
        by_t[a["tender_id"]].append(a)
    return {
        "precheck": precheck(db),
        "price_features": feats,
        "alerts": alerts,
        "priority": {t: triage(v) for t, v in by_t.items()},
    }


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    db = load(data_dir)
    mvp = run_all(db, include_stretch=False)
    full = run_all(db, include_stretch=True)
    expected = {
        "config": CONFIG,
        "precheck": mvp["precheck"],
        "price_features": {k: {kk: (None if vv is None else round(vv, 4)) for kk, vv in v.items()} for k, v in mvp["price_features"].items()},
        "mvp": {"alerts": [{k: a[k] for k in ("tender_id", "code", "severity")} for a in mvp["alerts"]], "priority": mvp["priority"]},
        "full": {"alerts": [{k: a[k] for k in ("tender_id", "code", "severity")} for a in full["alerts"]], "priority": full["priority"]},
    }
    out = Path("tests") / "expected_results.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(expected, indent=2))
    print(json.dumps(expected["mvp"]["priority"], indent=1))
    print(json.dumps(expected["full"]["priority"], indent=1))
