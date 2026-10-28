"""Page 5 — Evidence Review Assistant."""
import html
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from rasd import data_access as da
from rasd import llm, review_pack, storage, ui
from rasd.i18n import current_lang, doc_name, t

db, res = da.get()
lang = current_lang()

st.title(t("nav_review"))
c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
with c1:
    tid = ui.tender_selector(db)
if c2.button(t("btn_prepare"), type="primary", width="stretch"):
    st.session_state["pack_tender"] = tid


# ---------------------------------------------------------------- timed evaluation (review-time KPI)
with st.expander(t("eval_mode")):
    mode = st.radio(t("mode_label"), ["manual", "assisted"], horizontal=True, key="timer_mode",
                    format_func=lambda m: t(f"mode_{m}"))
    b1, b2, _ = st.columns([1, 1, 4])
    if b1.button(t("timer_start"), disabled="timer_id" in st.session_state):
        st.session_state["timer_id"] = storage.start_timer(tid, st.session_state.get("reviewer", ""), mode)
        st.session_state["timer_meta"] = {"tender_id": tid, "mode": mode, "started": datetime.now(timezone.utc)}
    if b2.button(t("timer_stop"), disabled="timer_id" not in st.session_state):
        seconds = storage.stop_timer(st.session_state.pop("timer_id"))
        st.session_state.pop("timer_meta", None)
        if seconds is not None:
            st.success(t("timer_stopped", s=f"{seconds:.1f}"))
    meta = st.session_state.get("timer_meta")
    if meta:
        elapsed = (datetime.now(timezone.utc) - meta["started"]).total_seconds()
        st.info(t("timer_running", tender_id=meta["tender_id"], mode=t(f"mode_{meta['mode']}"), s=f"{elapsed:.0f}"))
    elif "timer_id" not in st.session_state:
        st.caption(t("timer_idle"))

if st.session_state.get("pack_tender") != tid:
    st.info(t("pack_prompt"))
    st.stop()

pack = review_pack.make_review_pack(tid, res, db, lang)
h = pack["header"]

st.download_button(t("btn_download"), review_pack.pack_to_markdown(pack, lang),
                   file_name=f"rasd_review_pack_{tid}_{lang}.md", mime="text/markdown")

tab_summary, tab_evidence, tab_checklist, tab_decision = st.tabs(
    [t("tab_summary"), t("tab_evidence"), t("tab_checklist"), t("tab_decision")])


def indicator_block(ind: dict) -> None:
    with st.container(border=True):
        st.markdown(f"**{ind['label']}** &nbsp; {ui.severity_badge(ind['severity'])}", unsafe_allow_html=True)
        st.markdown(ind["summary"])
        st.markdown(f"**{t('innocent')}:** {ind['innocent']}")
        st.markdown(f"_{t('limitations')}: {ind['limitations']}_")
        st.markdown(f"{t('evidence_ids')}: {ui.ltr(ind['evidence_ids'])}", unsafe_allow_html=True)


# ---------------------------------------------------------------- Summary
with tab_summary:
    st.markdown(f"### {t('pack_title', tender_id=tid)}")
    st.markdown(f"{ui.priority_badge(h['priority_raw'])} &nbsp; **{t('needs_review')}**", unsafe_allow_html=True)
    facts = st.columns(4)
    facts[0].markdown(f"**{t('col_title')}**  \n{h['title']}")
    facts[1].markdown(f"**{t('col_entity')}**  \n{h['entity']}  \n{h['category']}")
    facts[2].markdown(f"**{t('col_value')}**  \n{h['estimated_value']}  \n{t('col_bids')}: {h['bid_count']}")
    facts[3].markdown(f"**{t('col_closing')}**  \n{h['closing_date']}  \n{h['status']}")

    if st.session_state.get("ai_on") and llm.is_configured() and pack["indicators"]:
        cache_key = f"ai_{tid}_{lang}_{int(da.include_stretch())}"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = llm.rewrite(review_pack.summary_sentences(pack), lang)
        text, used_ai = st.session_state[cache_key]
        with st.container(border=True):
            st.markdown(text)
            st.caption(t("ai_note") if used_ai else t("ai_unavailable"))

    st.markdown(f"#### {t('top_indicators')}")
    if not pack["indicators"]:
        st.info(t("no_alerts"))
    for ind in pack["top"]:
        indicator_block(ind)
    if pack["more"]:
        with st.expander(f"{t('more_indicators')} ({len(pack['more'])})"):
            for ind in pack["more"]:
                indicator_block(ind)

    st.markdown(f"#### {t('precheck_findings')}")
    if pack["precheck"]:
        for p in pack["precheck"]:
            st.markdown(f"- {p['line']}")
    else:
        st.caption(t("no_precheck"))


# ---------------------------------------------------------------- Evidence
def proposal_html(item: dict) -> str:
    author = item["records"][0]["doc_author"] if item["records"] else ""
    parts = []
    for seg in item["segments"]:
        text = html.escape(seg["text"])
        if seg["kind"] == "rare":
            parts.append(f"<mark>{text}</mark>")
        elif seg["kind"] == "rfp":
            parts.append(f'<span class="rasd-grey">{text}</span><span class="rasd-grey-tag">{t("standard_wording")}</span>')
        else:
            parts.append(text)
    return (f'<div class="rasd-proposal"><b>{html.escape(item["id"])}</b> · {t("doc_author")}: '
            f'{ui.ltr(author)}<br>{" ".join(parts)}</div>')


def records_frame(item: dict) -> pd.DataFrame:
    df = pd.DataFrame(item["records"])
    if item["table"] == "bids" and not df.empty:
        df["documents_attached"] = df["documents_attached"].map(
            lambda v: ", ".join(doc_name(d) for d in str(v).split("|") if d))
    if item["table"] == "tenders":
        df = df.drop(columns=["rfp_text", "required_documents"], errors="ignore")
    return df


with tab_evidence:
    if not pack["indicators"]:
        st.info(t("no_alerts"))
    for ind in pack["indicators"]:
        st.markdown(f"#### {ind['label']} &nbsp; {ui.severity_badge(ind['severity'])}", unsafe_allow_html=True)
        st.caption(f"{t('evidence')}: {ind['evidence_ids']}")
        proposals = [e for e in ind["evidence"] if e["table"] == "proposals"]
        others = [e for e in ind["evidence"] if e["table"] != "proposals"]
        if proposals:
            if any(s["kind"] == "rare" for e in proposals for s in e["segments"]):
                st.markdown(f"<mark>{t('rare_legend')}</mark>", unsafe_allow_html=True)
            cols = st.columns(len(proposals))
            for col, item in zip(cols, proposals):
                col.markdown(proposal_html(item), unsafe_allow_html=True)
        tables = {}
        for item in others:
            tables.setdefault(item["table"], []).append(item)
        for table, items in tables.items():
            st.markdown(f"**{t('tbl_' + table)}**")
            st.dataframe(pd.concat([records_frame(i) for i in items], ignore_index=True), hide_index=True, width="stretch")
        st.markdown(f"_{t('limitations')}: {ind['limitations']}_")
        st.divider()


# ---------------------------------------------------------------- Checklist
with tab_checklist:
    st.markdown(f"#### {t('checklist')}")
    if not pack["checklist"]:
        st.caption("—")
    for i, item in enumerate(pack["checklist"]):
        st.checkbox(item, key=f"chk_{tid}_{lang}_{i}")
    st.caption(t("checklist_note"))


# ---------------------------------------------------------------- Decision
with tab_decision:
    st.caption(t("decision_help"))
    with st.form(f"decision_form_{tid}", clear_on_submit=True):
        decision = st.radio(t("decision_label"), list(storage.DECISIONS), format_func=lambda d: t(f"dec_{d}"))
        reason = st.text_area(t("reason_label"))
        submitted = st.form_submit_button(t("submit_decision"), type="primary")
    if submitted:
        reviewer = st.session_state.get("reviewer", "").strip()
        if len(reason.strip()) < storage.MIN_REASON_CHARS:
            st.error(t("reason_too_short"))
        elif not reviewer:
            st.error(t("reviewer_missing"))
        else:
            saved = storage.save_decision(
                tender_id=tid, decision=decision, reason=reason, reviewer=reviewer,
                priority_at_decision=res["priority"][tid], alert_codes=da.alert_codes(res, tid),
                engine_version=da.ENGINE_VERSION, include_stretch=da.include_stretch())
            st.success(t("decision_saved", ts=saved["created_at"]))

    st.markdown(f"#### {t('decision_history')}")
    history = storage.list_decisions(tid)
    if history:
        st.dataframe(pd.DataFrame([{
            t("col_created"): d["created_at"], t("decision_label"): t(f"dec_{d['decision']}"),
            t("col_reason"): d["reason"], t("col_reviewer"): d["reviewer"],
            t("col_priority_at"): d["priority_at_decision"], t("col_alert_codes"): d["alert_codes"],
        } for d in history]), hide_index=True, width="stretch")
    else:
        st.caption(t("no_decisions"))
