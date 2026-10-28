"""Evidence Review Pack: everything a reviewer needs for one tender, plus Markdown export."""
from __future__ import annotations

from rapidfuzz import fuzz

from rasd import engine, templates
from rasd.i18n import doc_name, limitation, priority_label, t, tender_status

TOP_N = 3


# ---------------------------------------------------------------- proposal text analysis
def _non_boilerplate(db) -> dict[str, list[str]]:
    """Normalized proposal sentences per bid with the tender's RFP wording removed (same rule as the engine)."""
    te = db["tenders"].set_index("tender_id")
    pm = db["proposals"].set_index("bid_id")
    out = {}
    for _, b in db["bids"].iterrows():
        rfp = engine.sentences(te.loc[b.tender_id, "rfp_text"])
        own = engine.sentences(pm.loc[b.bid_id, "text"]) if b.bid_id in pm.index else []
        out[b.bid_id] = [s for s in own if not any(fuzz.ratio(s, r) >= engine.CONFIG["BOILER_SIM"] for r in rfp)]
    return out


def _rare_shared(corpus: dict[str, list[str]], a: str, b: str) -> list[str]:
    """Sentences of proposal `a` that the engine would count as rare and shared with proposal `b`."""
    def doc_freq(sent):
        return sum(1 for ss in corpus.values() if any(fuzz.ratio(sent, o) >= engine.CONFIG["SHARED_SIM"] for o in ss))
    return [s for s in corpus.get(a, []) for o in corpus.get(b, [])
            if fuzz.ratio(s, o) >= engine.CONFIG["SHARED_SIM"] and doc_freq(s) <= engine.CONFIG["MAX_DOC_FREQ"]]


def proposal_segments(db, bid_id: str, partners: list[str], corpus: dict[str, list[str]]) -> list[dict]:
    """Proposal text split into sentences tagged 'rare' (shared with a partner), 'rfp' (tender wording) or 'normal'."""
    pm = db["proposals"].set_index("bid_id")
    if bid_id not in pm.index:
        return []
    tender_id = db["bids"].set_index("bid_id").loc[bid_id, "tender_id"]
    rfp = engine.sentences(db["tenders"].set_index("tender_id").loc[tender_id, "rfp_text"])
    rare = [s for p in partners for s in _rare_shared(corpus, bid_id, p)]
    segments = []
    for raw in templates.split_sentences(pm.loc[bid_id, "text"]):
        norms = engine.sentences(raw)
        kind = "normal"
        if any(fuzz.ratio(n, r) >= engine.CONFIG["BOILER_SIM"] for n in norms for r in rfp):
            kind = "rfp"
        elif any(fuzz.ratio(n, r) >= engine.CONFIG["SHARED_SIM"] for n in norms for r in rare):
            kind = "rare"
        segments.append({"text": raw, "kind": kind})
    return segments


# ---------------------------------------------------------------- evidence resolution
def resolve_evidence(evidence_ids: str, db, corpus: dict[str, list[str]] | None = None) -> list[dict]:
    """Turn 'table:id;table:id' into the source records they point to."""
    refs = [r for r in evidence_ids.split(";") if r]
    proposal_ids = [r.partition(":")[2] for r in refs if r.startswith("proposals:")]
    items = []
    for ref in refs:
        table, _, key = ref.partition(":")
        item = {"ref": ref, "table": table, "id": key, "records": [], "segments": []}
        if table == "companies":
            rows = db["companies"][db["companies"].company_id == key]
        elif table == "bids":
            rows = db["bids"][db["bids"].bid_id == key]
        elif table == "proposals":
            rows = db["proposals"][db["proposals"].bid_id == key]
            if corpus is None:
                corpus = _non_boilerplate(db)
            item["segments"] = proposal_segments(db, key, [p for p in proposal_ids if p != key], corpus)
        elif table == "benchmarks":
            rows = db["benchmarks"][db["benchmarks"].specification_id == key]
        elif table == "tenders":
            rows = db["tenders"][db["tenders"].tender_id == key]
        else:
            rows = None
        if rows is not None:
            item["records"] = [{k: (v.item() if hasattr(v, "item") else v) for k, v in r.items()}
                               for r in rows.to_dict("records")]
        items.append(item)
    return items


# ---------------------------------------------------------------- the pack
def sort_alerts(alerts: list[dict]) -> list[dict]:
    return sorted(alerts, key=lambda a: (templates.SEVERITY_ORDER[a["severity"]], a["code"]))


def make_review_pack(tender_id: str, res: dict, db, lang: str = "en") -> dict:
    tender = db["tenders"].set_index("tender_id").loc[tender_id]
    bids = db["bids"][db["bids"].tender_id == tender_id]
    priority = res["priority"][tender_id]
    corpus = _non_boilerplate(db)

    indicators = []
    for a in sort_alerts([a for a in res["alerts"] if a["tender_id"] == tender_id]):
        indicators.append({
            "code": a["code"],
            "label": t(f"code_{a['code']}", lang),
            "severity": a["severity"],
            "severity_label": t(f"sev_{a['severity']}", lang),
            "summary": templates.summary(a, lang, db),
            "innocent": templates.innocent(a, lang),
            "limitations": limitation(a["limitations"], lang),
            "observed_value": a["observed_value"],
            "comparator": a["comparator"],
            "evidence_ids": a["evidence_ids"],
            "evidence": resolve_evidence(a["evidence_ids"], db, corpus),
            "checklist": templates.checklist(a, lang),
        })

    checklist = []
    for ind in indicators:
        for item in ind["checklist"]:
            if item not in checklist:
                checklist.append(item)

    precheck = [{**p, "line": templates.precheck_line(p, db, lang)}
                for p in res["precheck"] if p["tender_id"] == tender_id]

    return {
        "tender_id": tender_id,
        "lang": lang,
        "header": {
            "tender_id": tender_id,
            "title": tender["title_en"],
            "entity": tender["entity"],
            "category": tender["category"],
            "estimated_value": f"AED {float(tender['estimated_value_aed']):,.0f}",
            "closing_date": tender["closing_date"],
            "status": tender_status(tender["status"], lang),
            "bid_count": int(len(bids)),
            "priority": priority_label(priority, lang),
            "priority_raw": priority,
        },
        "indicators": indicators,
        "top": indicators[:TOP_N],
        "more": indicators[TOP_N:],
        "precheck": precheck,
        "checklist": checklist,
        "disclaimer": t("disclaimer", lang),
        "banner": t("banner", lang),
    }


def summary_sentences(pack: dict) -> list[str]:
    """The filled template sentences of a pack (the only text ever sent to the optional LLM)."""
    return [ind["summary"] for ind in pack["indicators"]] + [p["line"] for p in pack["precheck"]]


# ---------------------------------------------------------------- Markdown export
HEADER_LABELS = [("tender_id", "col_tender_id"), ("title", "col_title"), ("entity", "col_entity"),
                 ("category", "col_category"), ("estimated_value", "col_value"), ("closing_date", "col_closing"),
                 ("status", "col_status"), ("bid_count", "col_bids"), ("priority", "col_priority")]


def _record_line(item: dict, record: dict, lang: str) -> str:
    table = item["table"]
    if table == "companies":
        return (f"{record['company_id']} — {record['name_en']}; owner {record['owner_id']}; {record['phone']}; "
                f"{record['address']}, {record['emirate']}; group: {record['disclosed_group'] or '—'}")
    if table == "bids":
        docs = ", ".join(doc_name(d, lang) for d in str(record["documents_attached"]).split("|") if d)
        return f"{record['bid_id']} — {record['company_id']}; AED {float(record['amount_aed']):,.0f}; {record['submitted_at']}; {docs}"
    if table == "benchmarks":
        return f"{record['specification_id']} — {record['purchase_date']}; AED {float(record['unit_price_aed']):,.0f}; {record['source']}"
    if table == "tenders":
        return f"{record['tender_id']} — {record['title_en']}; {record['closing_date']}; {record['status']}"
    return "; ".join(f"{k}: {v}" for k, v in record.items())


def _proposal_markdown(item: dict, lang: str) -> list[str]:
    author = item["records"][0]["doc_author"] if item["records"] else ""
    lines = [f"  - **{item['id']}** — {t('doc_author', lang)}: `{author}`"]
    for seg in item["segments"]:
        if seg["kind"] == "rare":
            lines.append(f"    - **{seg['text']}** ← {t('code_SHARED_RARE_PHRASE', lang)}")
        elif seg["kind"] == "rfp":
            lines.append(f"    - _{seg['text']}_ ({t('standard_wording', lang)})")
        else:
            lines.append(f"    - {seg['text']}")
    return lines


def _indicator_markdown(ind: dict, lang: str) -> list[str]:
    lines = [f"### {ind['label']} — {ind['severity_label']}", "", ind["summary"], "",
             f"- **{t('innocent', lang)}:** {ind['innocent']}",
             f"- **{t('limitations', lang)}:** _{ind['limitations']}_",
             f"- **{t('evidence', lang)}:** `{ind['evidence_ids']}`"]
    for item in ind["evidence"]:
        if item["table"] == "proposals":
            lines += _proposal_markdown(item, lang)
        else:
            lines += [f"  - {_record_line(item, r, lang)}" for r in item["records"]]
    lines.append("")
    return lines


def pack_to_markdown(pack: dict, lang: str | None = None) -> str:
    lang = lang or pack["lang"]
    h = pack["header"]
    lines = [f"> {t('banner', lang)}", "", f"# {t('pack_title', lang, tender_id=pack['tender_id'])}", "",
             f"**{t('needs_review', lang)}**", "", f"## {t('pack_header', lang)}", "",
             "| | |", "|---|---|"]
    lines += [f"| {t(label, lang)} | {h[key]} |" for key, label in HEADER_LABELS]
    lines += ["", f"## {t('indicators', lang)}", ""]
    if not pack["indicators"]:
        lines += [t("no_alerts", lang), ""]
    for ind in pack["top"]:
        lines += _indicator_markdown(ind, lang)
    if pack["more"]:
        lines += [f"## {t('more_indicators', lang)}", ""]
        for ind in pack["more"]:
            lines += _indicator_markdown(ind, lang)
    lines += [f"## {t('precheck_findings', lang)}", ""]
    lines += [f"- {p['line']}" for p in pack["precheck"]] or [t("no_precheck", lang)]
    lines += ["", f"## {t('checklist', lang)}", ""]
    lines += [f"- [ ] {item}" for item in pack["checklist"]] or ["—"]
    lines += ["", "---", "", t("disclaimer", lang)]
    return "\n".join(lines) + "\n"
