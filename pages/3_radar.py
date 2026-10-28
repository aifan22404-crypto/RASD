"""Page 3 — Integrity Radar."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from rasd import data_access as da
from rasd import storage, ui
from rasd.i18n import limitation, t
from rasd.review_pack import sort_alerts

db, res = da.get()

st.title(t("nav_radar"))
tid = ui.tender_selector(db)
tender = da.tender(db, tid)
prio = res["priority"][tid]
alerts = sort_alerts(da.alerts_for(res, tid))

st.markdown(f"### {tid} — {tender.title_en}")
st.markdown(f"{ui.priority_badge(prio)} &nbsp; {t('decision_status')}: **{ui.decision_status(storage.latest_decision(tid))}**",
            unsafe_allow_html=True)

left, right = st.columns([2, 1])
with left:
    st.subheader(t("bid_amounts"))
    bids = da.bids_for(db, tid).sort_values("amount_aed")
    lowest = bids.amount_aed.min()
    fig = go.Figure(go.Bar(
        x=bids.company_id, y=bids.amount_aed,
        marker_color=["#0B5394" if a == lowest else "#9FB3C8" for a in bids.amount_aed],
        customdata=bids.bid_id,
        hovertemplate="%{x} (%{customdata})<br>AED %{y:,.0f}<extra></extra>",
        showlegend=False,
    ))
    fig.add_hline(y=float(tender.estimated_value_aed), line_dash="dash", line_color="#52606D",
                  annotation_text=f"{t('est_value_line')}: AED {ui.fmt_aed(tender.estimated_value_aed)}",
                  annotation_position="top left")
    top = max(float(bids.amount_aed.max()), float(tender.estimated_value_aed))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="#FFFFFF",
                      xaxis_title=t("axis_company"), yaxis_title=t("axis_aed"),
                      yaxis=dict(range=[0, top * 1.12], tickformat=",.0f", gridcolor="#E4E7EB"))
    with ui.ltr_container("radar_chart"):
        st.plotly_chart(fig, width="stretch")
    st.markdown(f'<small><span style="color:#0B5394">■</span> {t("lowest_bid")} &nbsp; '
                f'<span style="color:#9FB3C8">■</span> {t("other_bids")} &nbsp; '
                f'<span style="color:#52606D">- - -</span> {t("est_value_line")}</small>', unsafe_allow_html=True)

    st.subheader(t("price_features"))
    f = res["price_features"].get(tid, {})
    na = t("na")
    features = pd.DataFrame([
        {t("feat_metric"): t("feat_bid_count"), t("feat_value"): str(f.get("bid_count", na)), t("feat_explain"): t("explain_bid_count")},
        {t("feat_metric"): t("feat_cv"), t("feat_value"): na if f.get("cv") is None else f"{f['cv']:.3f}", t("feat_explain"): t("explain_cv")},
        {t("feat_metric"): t("feat_gap"), t("feat_value"): na if f.get("gap_pct") is None else f"{f['gap_pct'] * 100:.1f}%", t("feat_explain"): t("explain_gap")},
        {t("feat_metric"): t("feat_rd"), t("feat_value"): na if f.get("rd") is None else f"{f['rd']:.2f}", t("feat_explain"): t("explain_rd")},
    ])
    st.dataframe(features, hide_index=True, width="stretch")

with right:
    st.subheader(t("reason_codes"))
    if not alerts:
        st.info(t("no_alerts"))
    else:
        st.caption(t("n_indicators", n=len(alerts)))
        for a in alerts:
            with st.container(border=True):
                st.markdown(f"**{t('code_' + a['code'])}** &nbsp; {ui.severity_badge(a['severity'])}", unsafe_allow_html=True)
                st.markdown(f"{t('observed')}: {ui.ltr(a['observed_value'])}", unsafe_allow_html=True)
                st.markdown(f"{t('comparator')}: {ui.ltr(a['comparator'])}", unsafe_allow_html=True)
                st.markdown(f"_{t('limitations')}: {limitation(a['limitations'])}_")
                st.markdown(f"{t('evidence_ids')}: {ui.ltr(a['evidence_ids'])}", unsafe_allow_html=True)
        st.caption(t("engine_text_note"))

if st.button(t("btn_prepare"), type="primary"):
    st.session_state["tender_id"] = tid
    st.session_state["pack_tender"] = tid
    st.switch_page("pages/5_review.py")
