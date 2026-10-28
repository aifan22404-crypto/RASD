"""Page 1 — Tenders Dashboard."""
import pandas as pd
import streamlit as st

from rasd import data_access as da
from rasd import storage, ui
from rasd.i18n import priority_label, t, tender_status

db, res = da.get()
tenders, priority = db["tenders"], res["priority"]

st.title(t("nav_dashboard"))

needing_review = sum(1 for p in priority.values() if p != "Routine")
k1, k2, k3, k4 = st.columns(4)
k1.metric(t("kpi_tenders"), len(tenders))
k2.metric(t("kpi_bids"), len(db["bids"]))
k3.metric(t("kpi_need_review"), needing_review)
k4.metric(t("kpi_precheck"), len(res["precheck"]))

f1, f2 = st.columns(2)
categories = sorted(tenders.category.unique())
chosen_categories = f1.multiselect(t("filter_category"), categories)
chosen_priorities = f2.multiselect(t("filter_priority"), list(da.PRIORITY_ORDER), format_func=priority_label)

rows = []
for _, tr in tenders.iterrows():
    tid = tr.tender_id
    rows.append({
        "_priority": priority[tid],
        "_rank": da.PRIORITY_ORDER[priority[tid]],
        t("col_tender_id"): tid,
        t("col_title"): tr.title_en,
        t("col_entity"): tr.entity,
        t("col_category"): tr.category,
        t("col_value"): ui.fmt_aed(tr.estimated_value_aed),
        t("col_bids"): len(da.bids_for(db, tid)),
        t("col_closing"): tr.closing_date,
        t("col_status"): tender_status(tr.status),
        t("col_priority"): ui.priority_text(priority[tid]),
        t("col_alerts"): ", ".join(da.alert_codes(res, tid)),
        t("col_decision"): ui.decision_status(storage.latest_decision(tid)),
    })
df = pd.DataFrame(rows).sort_values(["_rank", t("col_closing")], ascending=[True, False])
if chosen_categories:
    df = df[df[t("col_category")].isin(chosen_categories)]
if chosen_priorities:
    df = df[df["_priority"].isin(chosen_priorities)]
df = df.reset_index(drop=True)

colors = df["_priority"].map(ui.PRIORITY_COLORS).tolist()
view = df.drop(columns=["_priority", "_rank"])
styled = view.style.apply(lambda col: [f"color: {c}; font-weight: 600" for c in colors], subset=[t("col_priority")])
st.dataframe(styled, hide_index=True, width="stretch")
st.caption(t("dash_caption"))

o1, o2 = st.columns([3, 1], vertical_alignment="bottom")
ids = da.tender_ids(db)
default = st.session_state.get("tender_id", ui.DEFAULT_TENDER)
open_id = o1.selectbox(t("open_tender"), ids, index=ids.index(default) if default in ids else 0,
                       format_func=lambda tid: f"{tid} — {da.tender(db, tid)['title_en']}")
if o2.button(t("btn_open_radar"), type="primary", width="stretch"):
    st.session_state["tender_id"] = open_id
    st.switch_page("pages/3_radar.py")
