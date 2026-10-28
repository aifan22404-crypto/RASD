"""Page 6 — Decisions & Audit Trail."""
import pandas as pd
import streamlit as st

from rasd import storage
from rasd.i18n import t

st.title(t("nav_audit"))
st.caption(t("audit_note"))

decisions = pd.DataFrame(storage.list_decisions())
if decisions.empty:
    st.info(t("no_decisions"))
else:
    f1, f2 = st.columns(2)
    chosen_decisions = f1.multiselect(t("filter_decision"), list(storage.DECISIONS), format_func=lambda d: t(f"dec_{d}"))
    chosen_tenders = f2.multiselect(t("filter_tender"), sorted(decisions.tender_id.unique()))
    if chosen_decisions:
        decisions = decisions[decisions.decision.isin(chosen_decisions)]
    if chosen_tenders:
        decisions = decisions[decisions.tender_id.isin(chosen_tenders)]

    view = decisions.assign(
        decision_label=decisions.decision.map(lambda d: t(f"dec_{d}")),
        include_stretch=decisions.include_stretch.map(lambda v: t("yes") if v else t("no")),
    )
    columns = {"id": t("col_id"), "created_at": t("col_created"), "tender_id": t("col_tender_id"),
               "decision_label": t("decision_label"), "decision": t("code"), "reason": t("col_reason"),
               "reviewer": t("col_reviewer"), "priority_at_decision": t("col_priority_at"),
               "alert_codes": t("col_alert_codes"), "engine_version": t("col_engine"),
               "include_stretch": t("col_stretch")}
    st.dataframe(view[list(columns)].rename(columns=columns), hide_index=True, width="stretch")
    st.download_button(t("download_csv"), decisions.to_csv(index=False).encode("utf-8"),
                       file_name="rasd_decisions.csv", mime="text/csv")

st.subheader(t("timing_title"))
summary = storage.timing_summary()
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(t("median_manual"), "—" if summary["median_manual"] is None else f"{summary['median_manual']:.1f}")
m2.metric(t("median_assisted"), "—" if summary["median_assisted"] is None else f"{summary['median_assisted']:.1f}")
m3.metric(t("reduction"), "—" if summary["reduction_pct"] is None else f"{summary['reduction_pct']:.1f}%")
m4.metric(t("sessions_manual"), summary["n_manual"])
m5.metric(t("sessions_assisted"), summary["n_assisted"])
if summary["reduction_pct"] is None:
    st.info(t("timing_need"))
elif summary["reduction_pct"] > 0:
    st.success(t("faster_claim", p=f"{summary['reduction_pct']:.1f}"))
