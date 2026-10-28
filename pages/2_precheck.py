"""Page 2 — Bid Pre-check."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from rasd import data_access as da
from rasd import templates, ui
from rasd.i18n import current_lang, doc_name, t

db, res = da.get()
lang = current_lang()

st.title(t("nav_precheck"))
tid = ui.tender_selector(db)
tender = da.tender(db, tid)
required = [d for d in tender.required_documents.split("|") if d]
findings = da.precheck_for(res, tid)

left, right = st.columns([2, 1])
with left:
    st.subheader(t("pc_table"))
    kind_label = {"MISSING_DOCUMENT": t("pc_missing"), "LICENCE_EXPIRED": t("pc_expired")}
    rows = []
    for _, bid in da.bids_for(db, tid).iterrows():
        attached = set(bid.documents_attached.split("|"))
        row = {t("col_bid"): bid.bid_id, t("col_company"): da.company_label(db, bid.company_id)}
        for code in required:
            row[doc_name(code)] = "✅" if code in attached else "❌"
        expiry = da.company(db, bid.company_id)["licence_expiry"]
        row[t("col_licence_expiry")] = f"⚠️ {expiry}" if expiry and expiry < tender.closing_date else expiry
        issues = [p for p in findings if p["bid_id"] == bid.bid_id]
        if issues:
            kinds = ", ".join(dict.fromkeys(kind_label[p["code"]] for p in issues))
            row[t("col_overall")] = t("pc_issues", n=len(issues), kinds=kinds)
        else:
            row[t("col_overall")] = t("pc_complete")
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    st.subheader(t("pc_fix_title"))
    lines = [templates.precheck_line(p, db, lang) for p in findings]
    if lines:
        st.text_area(t("fix_list"), "\n".join(lines), height=40 + 28 * len(lines))
    else:
        st.success(t("pc_no_issues"))

with right:
    st.subheader(t("all_tenders"))
    ids = da.tender_ids(db)
    counts = [len(da.precheck_for(res, x)) for x in ids]
    fig = go.Figure(go.Bar(
        x=counts, y=ids, orientation="h",
        marker_color=["#0B5394" if x == tid else "#9FB3C8" for x in ids],
        hovertemplate="%{y}: %{x}<extra></extra>",
    ))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10), xaxis_title=t("issues_axis"),
                      yaxis=dict(autorange="reversed"), xaxis=dict(dtick=1), plot_bgcolor="#FFFFFF")
    with ui.ltr_container("precheck_chart"):
        st.plotly_chart(fig, width="stretch")

st.caption(t("pc_caption"))
