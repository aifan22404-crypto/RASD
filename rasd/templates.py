"""Review-pack sentence templates (EN/AR). Wording is fixed by SPEC section 7; only `{}` slots are filled."""
from __future__ import annotations

import re

from rasd.i18n import doc_name, t

SEVERITY_ORDER = {"strong": 0, "moderate": 1, "weak": 2, "context": 3}


def _pair(en: str, ar: str) -> dict[str, str]:
    return {"en": en, "ar": ar}


# key: (code, variant). variant is None except for BIDDER_RELATIONSHIP.
TEMPLATES: dict[tuple[str, str | None], dict] = {
    ("PRICE_PATTERN_REVIEW", None): {
        "summary": _pair(
            "The {bid_count} bids are unusually close together (coefficient of variation {cv}), and the lowest bid is {gap_pct} below the next one (relative distance {rd}).",
            "العروض البالغ عددها {bid_count} متقاربة بشكل غير معتاد (معامل الاختلاف {cv})، والعرض الأدنى أقل من العرض التالي بنسبة {gap_pct} (المسافة النسبية {rd}).",
        ),
        "innocent": _pair(
            "Bids for well-defined products can legitimately be close in price.",
            "قد تتقارب أسعار العروض بشكل مشروع عندما تكون مواصفات المنتج محددة بدقة.",
        ),
        "checklist": [
            _pair("Compare with past tenders in the same category.", "قارن مع مناقصات سابقة من نفس الفئة."),
            _pair("Check whether the higher bids look realistic.", "تحقق مما إذا كانت العروض الأعلى واقعية."),
        ],
    },
    ("BIDDER_RELATIONSHIP", "owner"): {
        "summary": _pair(
            "{company_a} and {company_b} bid against each other but share the same owner ({value}) in the registry, and no relationship was disclosed.",
            "تنافست {company_a} و{company_b} في هذه المناقصة رغم أن لهما المالك نفسه ({value}) في السجل، ولم يتم الإفصاح عن هذه العلاقة.",
        ),
        "innocent": _pair(
            "Registry data can be outdated or ownership may have changed.",
            "قد تكون بيانات السجل قديمة أو قد تكون الملكية قد تغيّرت.",
        ),
        "checklist": [
            _pair("Verify ownership with the licensing authority.", "تحقق من الملكية لدى جهة الترخيص."),
            _pair("Check whether a conflict-of-interest declaration was required.", "تحقق مما إذا كان مطلوباً تقديم إقرار بتضارب المصالح."),
        ],
    },
    ("BIDDER_RELATIONSHIP", "owner_disclosed"): {
        "summary": _pair(
            "{company_a} and {company_b} share an owner and declared it as group {group}.",
            "تشترك {company_a} و{company_b} في المالك وقد أفصحتا عن ذلك ضمن المجموعة {group}.",
        ),
        "innocent": _pair(
            "Disclosed group companies may legitimately bid separately.",
            "يجوز للشركات المفصح عن انتمائها لمجموعة واحدة التقدم بعروض منفصلة.",
        ),
        "checklist": [
            _pair("Confirm the tender rules allow related bidders.", "تأكد من أن شروط المناقصة تسمح بمشاركة شركات مرتبطة."),
        ],
    },
    ("BIDDER_RELATIONSHIP", "phone"): {
        "summary": _pair(
            "{company_a} and {company_b} list the same phone number ({value}).",
            "تستخدم {company_a} و{company_b} رقم الهاتف نفسه ({value}).",
        ),
        "innocent": _pair(
            "Shared switchboards or service providers exist.",
            "قد تتشارك الشركات خدمة اتصال أو مقسماً واحداً.",
        ),
        "checklist": [
            _pair("Verify contact details with both companies.", "تحقق من بيانات الاتصال لدى الشركتين."),
        ],
    },
    ("BIDDER_RELATIONSHIP", "address"): {
        "summary": _pair(
            "{company_a} and {company_b} list the same address ({value}).",
            "تستخدم {company_a} و{company_b} العنوان نفسه ({value}).",
        ),
        "innocent": _pair(
            "Companies can share premises legitimately.",
            "قد تتشارك الشركات المقر بشكل مشروع.",
        ),
        "innocent_business_centre": _pair(
            "Business centres host many unrelated firms.",
            "تستضيف مراكز الأعمال العديد من الشركات غير المرتبطة.",
        ),
        "checklist": [
            _pair("Verify the premises.", "تحقق من المقر."),
        ],
    },
    ("SHARED_RARE_PHRASE", None): {
        "summary": _pair(
            "Proposals {bid_a} and {bid_b} share {count} rare sentence(s) that do not appear in the tender wording, e.g. \"{sentence}\".",
            "يشترك العرضان {bid_a} و{bid_b} في {count} جملة نادرة غير موجودة في نص المناقصة، مثل: \"{sentence}\".",
        ),
        "innocent": _pair(
            "Companies may use the same consultant or template.",
            "قد تستعين الشركات بالمستشار نفسه أو بالقالب نفسه.",
        ),
        "checklist": [
            _pair("Compare both proposals in full.", "قارن العرضين بالكامل."),
            _pair("Ask how each proposal was prepared.", "استفسر عن طريقة إعداد كل عرض."),
        ],
    },
    ("DOC_METADATA_MATCH", None): {
        "summary": _pair(
            "Proposals {bid_a} and {bid_b} list the same document author ('{author}').",
            "يحمل العرضان {bid_a} و{bid_b} اسم مؤلف المستند نفسه ('{author}').",
        ),
        "innocent": _pair(
            "Default or shared software accounts can produce the same author name.",
            "قد ينتج اسم المؤلف نفسه عن إعدادات افتراضية أو حساب برمجي مشترك.",
        ),
        "checklist": [
            _pair("Check document properties of the original files.", "افحص خصائص الملفات الأصلية."),
        ],
    },
    ("BENCHMARK_GAP", None): {
        "summary": _pair(
            "The lowest unit price (AED {lowest_unit}) is {ratio}× the median of comparable purchases (AED {median}) for {spec}.",
            "أدنى سعر للوحدة ({lowest_unit} درهم) يعادل {ratio} ضعف متوسط المشتريات المماثلة ({median} درهم) للمواصفة {spec}.",
        ),
        "innocent": _pair(
            "Supply shortages, delivery terms or extra services can justify higher prices.",
            "قد تبرر ندرة المعروض أو شروط التسليم أو الخدمات الإضافية ارتفاع الأسعار.",
        ),
        "checklist": [
            _pair("Confirm the specifications truly match.", "تأكد من تطابق المواصفات فعلياً."),
            _pair("Request a price breakdown.", "اطلب تفصيلاً للأسعار."),
        ],
    },
    ("REPEATED_WIN_SEQUENCE", None): {
        "summary": _pair(
            "The same {group_size} companies bid in {n} tenders and the winners took turns: {sequence}.",
            "تقدمت الشركات نفسها وعددها {group_size} في {n} مناقصات وتناوبت على الفوز: {sequence}.",
        ),
        "innocent": _pair(
            "In small markets, alternation can happen by chance.",
            "في الأسواق الصغيرة قد يحدث التناوب بالصدفة.",
        ),
        "checklist": [
            _pair("Review the full bidding history of the group.", "راجع سجل العطاءات الكامل للمجموعة."),
        ],
    },
}

PRECHECK_TEMPLATES = {
    "MISSING_DOCUMENT": _pair("{company} did not attach: {document}.", "لم ترفق {company}: {document}."),
    "LICENCE_EXPIRED": _pair(
        "{company}'s trade licence expired on {date}, before the tender closing date.",
        "انتهت الرخصة التجارية لـ{company} في {date} قبل تاريخ إغلاق المناقصة.",
    ),
}


def variant(alert: dict) -> str | None:
    if alert["code"] != "BIDDER_RELATIONSHIP":
        return None
    p = alert["params"]
    if p.get("link_type") == "owner":
        return "owner_disclosed" if p.get("disclosed") else "owner"
    return p.get("link_type")


def _template(alert: dict) -> dict:
    return TEMPLATES[(alert["code"], variant(alert))]


def _num(value, fmt: str, lang: str) -> str:
    return t("na", lang) if value is None else format(float(value), fmt)


def format_params(alert: dict, lang: str, original_sentence: str | None = None) -> dict[str, str]:
    """Template slot values: AED with thousands separators, cv 3 dp, rd 2 dp, percentages 1 dp."""
    p = alert["params"]
    code = alert["code"]
    if code == "PRICE_PATTERN_REVIEW":
        gap = p.get("gap_pct")
        return {"bid_count": str(int(p["bid_count"])), "cv": _num(p.get("cv"), ".3f", lang),
                "rd": _num(p.get("rd"), ".2f", lang),
                "gap_pct": t("na", lang) if gap is None else f"{float(gap) * 100:.1f}%"}
    if code == "BENCHMARK_GAP":
        return {"lowest_unit": f"{float(p['lowest_unit']):,.0f}", "median": f"{float(p['median']):,.0f}",
                "ratio": f"{float(p['ratio']):.2f}", "spec": str(p["spec"])}
    if code == "REPEATED_WIN_SEQUENCE":
        return {"group_size": str(p["group_size"]), "n": str(len(p["tenders"])), "sequence": " → ".join(p["sequence"])}
    if code == "SHARED_RARE_PHRASE":
        return {"bid_a": p["bid_a"], "bid_b": p["bid_b"], "count": str(p["count"]),
                "sentence": original_sentence or p["sentence"]}
    return {k: "" if v is None else str(v) for k, v in p.items()}


def original_sentence(db, bid_id: str, normalized: str) -> str | None:
    """The proposal's own wording of a normalized sentence (for readable quotes), if found."""
    if db is None:
        return None
    from rasd import engine  # local import keeps this module importable without the engine deps

    pr = db["proposals"].set_index("bid_id")
    if bid_id not in pr.index:
        return None
    for raw in split_sentences(pr.loc[bid_id, "text"]):
        if normalized in engine.sentences(raw):
            return raw.rstrip(".!? ")
    return None


def split_sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", str(text).strip()) if s]


def summary(alert: dict, lang: str, db=None) -> str:
    orig = None
    if alert["code"] == "SHARED_RARE_PHRASE":
        orig = original_sentence(db, alert["params"]["bid_a"], alert["params"]["sentence"])
    return _template(alert)["summary"][lang].format(**format_params(alert, lang, orig))


def innocent(alert: dict, lang: str) -> str:
    tpl = _template(alert)
    if alert["params"].get("business_centre") and "innocent_business_centre" in tpl:
        return tpl["innocent_business_centre"][lang]
    return tpl["innocent"][lang]


def checklist(alert: dict, lang: str) -> list[str]:
    return [item[lang] for item in _template(alert)["checklist"]]


def precheck_line(finding: dict, db, lang: str) -> str:
    co = db["companies"].set_index("company_id")
    cid = finding["company_id"]
    company = f"{co.loc[cid, 'name_en']} ({cid})"
    tpl = PRECHECK_TEMPLATES[finding["code"]][lang]
    if finding["code"] == "MISSING_DOCUMENT":
        return tpl.format(company=company, document=doc_name(finding["detail"], lang))
    return tpl.format(company=company, date=co.loc[cid, "licence_expiry"])
