"""Cached data loading, engine run and small lookups shared by the pages."""
from __future__ import annotations

import itertools
from pathlib import Path

import pandas as pd
import streamlit as st

from rasd import engine
from rasd.i18n import t

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ENGINE_VERSION = "rasd-engine-1.0"
PRIORITY_ORDER = {"Urgent review": 0, "Review": 1, "Routine": 2}


@st.cache_data(show_spinner=False)
def load_db() -> dict[str, pd.DataFrame]:
    return engine.load(DATA_DIR)


@st.cache_data(show_spinner=False)
def run_engine(include_stretch: bool) -> dict:
    return engine.run_all(load_db(), include_stretch=include_stretch)


def include_stretch() -> bool:
    return bool(st.session_state.get("include_stretch", True))


def get() -> tuple[dict[str, pd.DataFrame], dict]:
    """(db, res) for the current stretch setting. Shows a friendly error and stops the page on failure."""
    try:
        db = load_db()
        res = run_engine(include_stretch())
    except Exception as exc:  # missing CSV, failed integrity assertion, malformed data
        st.error(t("data_error", msg=str(exc) or type(exc).__name__))
        st.stop()
    return db, res


# ---------------------------------------------------------------- lookups
def tender(db, tender_id: str) -> pd.Series:
    return db["tenders"].set_index("tender_id").loc[tender_id]


def tender_ids(db) -> list[str]:
    return list(db["tenders"].tender_id)


def bids_for(db, tender_id: str) -> pd.DataFrame:
    return db["bids"][db["bids"].tender_id == tender_id]


def company(db, company_id: str) -> pd.Series:
    return db["companies"].set_index("company_id").loc[company_id]


def company_label(db, company_id: str) -> str:
    return f"{company(db, company_id)['name_en']} ({company_id})"


def alerts_for(res, tender_id: str) -> list[dict]:
    return [a for a in res["alerts"] if a["tender_id"] == tender_id]


def precheck_for(res, tender_id: str) -> list[dict]:
    return [p for p in res["precheck"] if p["tender_id"] == tender_id]


def alert_codes(res, tender_id: str) -> list[str]:
    return sorted({a["code"] for a in alerts_for(res, tender_id)})


# ---------------------------------------------------------------- registry links (Bidder Connections)
def registry_links(db) -> list[dict]:
    """Every pair of companies in the registry sharing an owner, phone or address (same matching as the engine)."""
    co = db["companies"]
    out = []
    for (_, a), (_, b) in itertools.combinations(co.iterrows(), 2):
        if a.owner_id and a.owner_id == b.owner_id:
            disclosed = bool(a.disclosed_group) and a.disclosed_group == b.disclosed_group
            out.append({"a": a.company_id, "b": b.company_id, "link_type": "owner", "value": a.owner_id,
                        "disclosed": disclosed, "group": a.disclosed_group if disclosed else ""})
        if a.phone and engine._norm(a.phone) == engine._norm(b.phone):
            out.append({"a": a.company_id, "b": b.company_id, "link_type": "phone", "value": a.phone,
                        "disclosed": None, "group": ""})
        if a.address and engine._norm(a.address) == engine._norm(b.address):
            out.append({"a": a.company_id, "b": b.company_id, "link_type": "address", "value": a.address,
                        "disclosed": None, "group": "",
                        "business_centre": a.address_type == "business_centre" and b.address_type == "business_centre"})
    return out


def connection_graph(db, tender_id: str) -> tuple[list[str], set[str], list[dict]]:
    """(nodes, bidders, edges): bidders in the tender plus any company linked to one of them."""
    bidders = set(bids_for(db, tender_id).company_id)
    links = [lk for lk in registry_links(db) if lk["a"] in bidders or lk["b"] in bidders]
    nodes = sorted(bidders | {lk["a"] for lk in links} | {lk["b"] for lk in links})
    return nodes, bidders, links
