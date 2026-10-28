"""All UI strings in English and Arabic. Pages never hard-code display text; they call t(key).

Arabic strings MUST be proof-read by a native speaker on the team before the pitch.
"""
from __future__ import annotations

LANGS = ("en", "ar")

STRINGS: dict[str, dict[str, str]] = {
    # ------------------------------------------------------------ app shell
    "app_name": {"en": "Rasd", "ar": "رصد"},
    "logo": {"en": "Rasd رصد", "ar": "Rasd رصد"},
    "tagline": {"en": "Procurement Integrity Radar", "ar": "رادار نزاهة المشتريات"},
    "banner": {
        "en": "SYNTHETIC DEMO DATA — all tenders, companies and relationships are fictional. Indicators require human review and are not evidence of wrongdoing.",
        "ar": "بيانات تجريبية مصطنعة — جميع المناقصات والشركات والعلاقات وهمية. المؤشرات تتطلب مراجعة بشرية وليست دليلاً على أي مخالفة.",
    },
    "lang_label": {"en": "Language", "ar": "اللغة"},
    "reviewer": {"en": "Reviewer name", "ar": "اسم المراجع"},
    "stretch_toggle": {"en": "Include stretch detectors (rotation, benchmark)", "ar": "تضمين أدوات الكشف الإضافية (التناوب، المقارنة السعرية)"},
    "ai_toggle": {"en": "Plain-language summary (AI)", "ar": "ملخص بلغة مبسطة (ذكاء اصطناعي)"},
    "engine_caption": {"en": "Engine: {version}", "ar": "المحرك: {version}"},
    "data_error": {"en": "The demo data could not be loaded: {msg}", "ar": "تعذّر تحميل البيانات التجريبية: {msg}"},
    "tender": {"en": "Tender", "ar": "المناقصة"},
    "na": {"en": "n/a", "ar": "غير متاح"},
    "yes": {"en": "Yes", "ar": "نعم"},
    "no": {"en": "No", "ar": "لا"},
    # ------------------------------------------------------------ navigation
    "nav_dashboard": {"en": "Tenders Dashboard", "ar": "لوحة المناقصات"},
    "nav_precheck": {"en": "Bid Pre-check", "ar": "الفحص المسبق للعطاءات"},
    "nav_radar": {"en": "Integrity Radar", "ar": "رادار النزاهة"},
    "nav_connections": {"en": "Bidder Connections", "ar": "روابط المتقدمين"},
    "nav_review": {"en": "Evidence Review Assistant", "ar": "مساعد مراجعة الأدلة"},
    "nav_audit": {"en": "Decisions & Audit Trail", "ar": "القرارات وسجل التدقيق"},
    "nav_model": {"en": "Model Card", "ar": "بطاقة النموذج"},
    # ------------------------------------------------------------ priority / severity / codes
    "prio_routine": {"en": "Routine", "ar": "اعتيادي"},
    "prio_review": {"en": "Review", "ar": "يحتاج مراجعة"},
    "prio_urgent": {"en": "Urgent review", "ar": "مراجعة عاجلة"},
    "sev_strong": {"en": "Strong", "ar": "قوي"},
    "sev_moderate": {"en": "Moderate", "ar": "متوسط"},
    "sev_weak": {"en": "Weak", "ar": "ضعيف"},
    "sev_context": {"en": "Context", "ar": "سياق"},
    "code_PRICE_PATTERN_REVIEW": {"en": "Unusual price pattern", "ar": "نمط أسعار غير معتاد"},
    "code_BIDDER_RELATIONSHIP": {"en": "Linked bidders", "ar": "ارتباط بين المتقدمين"},
    "code_SHARED_RARE_PHRASE": {"en": "Rare shared text", "ar": "نص نادر مشترك"},
    "code_DOC_METADATA_MATCH": {"en": "Same document author", "ar": "نفس مؤلف المستند"},
    "code_BENCHMARK_GAP": {"en": "Price above comparable purchases", "ar": "سعر أعلى من المشتريات المماثلة"},
    "code_REPEATED_WIN_SEQUENCE": {"en": "Winners take turns", "ar": "تناوب الفائزين"},
    # ------------------------------------------------------------ pre-check
    "pc_complete": {"en": "Complete", "ar": "مكتمل"},
    "pc_missing": {"en": "Missing document", "ar": "مستند ناقص"},
    "pc_expired": {"en": "Licence expired", "ar": "رخصة منتهية"},
    "pc_issues": {"en": "{n} issue(s): {kinds}", "ar": "عدد الملاحظات {n}: {kinds}"},
    "pc_table": {"en": "Bids received", "ar": "العطاءات المستلمة"},
    "pc_fix_title": {"en": "Fix list", "ar": "قائمة الإصلاحات"},
    "fix_list": {"en": "Copy fix list", "ar": "نسخ قائمة الإصلاحات"},
    "pc_no_issues": {"en": "No pre-check issues for this tender.", "ar": "لا توجد ملاحظات في الفحص المسبق لهذه المناقصة."},
    "all_tenders": {"en": "All tenders", "ar": "جميع المناقصات"},
    "issues_axis": {"en": "Pre-check issues", "ar": "ملاحظات الفحص المسبق"},
    "pc_caption": {
        "en": "Pre-check checks completeness and dates only; it does not verify identities or document authenticity.",
        "ar": "يتحقق الفحص المسبق من اكتمال المستندات والتواريخ فقط، ولا يتحقق من الهويات أو من صحة المستندات.",
    },
    # ------------------------------------------------------------ table columns
    "col_tender_id": {"en": "Tender", "ar": "المناقصة"},
    "col_title": {"en": "Title", "ar": "العنوان"},
    "col_entity": {"en": "Entity", "ar": "الجهة"},
    "col_category": {"en": "Category", "ar": "الفئة"},
    "col_value": {"en": "Estimated value (AED)", "ar": "القيمة التقديرية (درهم)"},
    "col_bids": {"en": "Bids", "ar": "العطاءات"},
    "col_closing": {"en": "Closing date", "ar": "تاريخ الإغلاق"},
    "col_status": {"en": "Tender status", "ar": "حالة المناقصة"},
    "col_priority": {"en": "Priority", "ar": "الأولوية"},
    "col_alerts": {"en": "Alert codes", "ar": "رموز التنبيهات"},
    "col_decision": {"en": "Latest decision", "ar": "آخر قرار"},
    "col_bid": {"en": "Bid", "ar": "العطاء"},
    "col_company": {"en": "Company", "ar": "الشركة"},
    "col_amount": {"en": "Amount (AED)", "ar": "المبلغ (درهم)"},
    "col_licence_expiry": {"en": "Licence expiry", "ar": "انتهاء الرخصة"},
    "col_overall": {"en": "Overall status", "ar": "الحالة العامة"},
    "tstatus_awarded": {"en": "Awarded", "ar": "تمت الترسية"},
    "tstatus_pre-award": {"en": "Pre-award", "ar": "قبل الترسية"},
    "status_open": {"en": "Open", "ar": "مفتوحة"},
    # ------------------------------------------------------------ dashboard
    "kpi_tenders": {"en": "Tenders screened", "ar": "المناقصات المفحوصة"},
    "kpi_bids": {"en": "Bids", "ar": "العطاءات"},
    "kpi_need_review": {"en": "Tenders needing review", "ar": "مناقصات تحتاج مراجعة"},
    "kpi_precheck": {"en": "Pre-check issues", "ar": "ملاحظات الفحص المسبق"},
    "dash_caption": {
        "en": "Priority orders the review queue. It is not a legal status and no decision is made automatically.",
        "ar": "الأولوية تحدد ترتيب قائمة المراجعة فقط، وليست وضعاً قانونياً، ولا يُتخذ أي قرار بشكل آلي.",
    },
    "filter_category": {"en": "Category", "ar": "الفئة"},
    "filter_priority": {"en": "Priority", "ar": "الأولوية"},
    "open_tender": {"en": "Open tender", "ar": "فتح مناقصة"},
    "btn_open_radar": {"en": "Open in Integrity Radar", "ar": "فتح في رادار النزاهة"},
    # ------------------------------------------------------------ radar
    "decision_status": {"en": "Decision status", "ar": "حالة القرار"},
    "bid_amounts": {"en": "Bid amounts", "ar": "مبالغ العطاءات"},
    "axis_company": {"en": "Company", "ar": "الشركة"},
    "axis_aed": {"en": "AED", "ar": "درهم"},
    "lowest_bid": {"en": "Lowest bid", "ar": "أدنى عطاء"},
    "other_bids": {"en": "Other bids", "ar": "العطاءات الأخرى"},
    "est_value_line": {"en": "Estimated value", "ar": "القيمة التقديرية"},
    "price_features": {"en": "Price features", "ar": "مؤشرات الأسعار"},
    "feat_metric": {"en": "Metric", "ar": "المؤشر"},
    "feat_value": {"en": "Value", "ar": "القيمة"},
    "feat_explain": {"en": "What it means", "ar": "المعنى"},
    "feat_bid_count": {"en": "Bid count", "ar": "عدد العطاءات"},
    "feat_cv": {"en": "Coefficient of variation (CV)", "ar": "معامل الاختلاف"},
    "feat_gap": {"en": "Gap between two lowest bids", "ar": "الفرق بين أدنى عطاءين"},
    "feat_rd": {"en": "Relative distance", "ar": "المسافة النسبية"},
    "explain_bid_count": {"en": "Number of bids received for this tender.", "ar": "عدد العطاءات المستلمة لهذه المناقصة."},
    "explain_cv": {
        "en": "Spread of the bids relative to their average; a very low value means the bids are unusually close.",
        "ar": "مدى تشتت العطاءات مقارنة بمتوسطها؛ القيمة المنخفضة جداً تعني أن العطاءات متقاربة بشكل غير معتاد.",
    },
    "explain_gap": {"en": "How far the lowest bid is below the second-lowest bid.", "ar": "مقدار انخفاض أدنى عطاء عن العطاء الذي يليه."},
    "explain_rd": {
        "en": "Gap between the two lowest bids divided by the spread of the losing bids; a high value means the lowest bid stands apart.",
        "ar": "الفرق بين أدنى عطاءين مقسوماً على تشتت العطاءات غير الفائزة؛ القيمة المرتفعة تعني أن أدنى عطاء منفصل عن البقية.",
    },
    "reason_codes": {"en": "Reason codes", "ar": "رموز الأسباب"},
    "observed": {"en": "Observed", "ar": "القيمة المرصودة"},
    "comparator": {"en": "Compared with", "ar": "أساس المقارنة"},
    "evidence_ids": {"en": "Evidence IDs", "ar": "معرّفات الأدلة"},
    "engine_text_note": {"en": "Observed values are shown as recorded by the engine.", "ar": "تُعرض القيم المرصودة كما سجلها المحرك."},
    "no_alerts": {"en": "No indicators found. Ordinary procurement checks still apply.", "ar": "لم يتم العثور على مؤشرات. تبقى إجراءات التحقق الاعتيادية في المشتريات سارية."},
    "n_indicators": {"en": "{n} indicator(s) found; needs human review.", "ar": "تم العثور على {n} مؤشر/مؤشرات؛ يتطلب مراجعة بشرية."},
    # ------------------------------------------------------------ connections
    "graph_title": {"en": "Bidders and linked companies", "ar": "المتقدمون والشركات المرتبطة بهم"},
    "legend_title": {"en": "How to read the graph", "ar": "طريقة قراءة الشبكة"},
    "legend_owner": {"en": "Solid red: same owner, not disclosed", "ar": "خط أحمر متصل: المالك نفسه، دون إفصاح"},
    "legend_owner_disclosed": {"en": "Solid dark grey: same owner, declared as a group", "ar": "خط رمادي داكن متصل: المالك نفسه، مع الإفصاح عن المجموعة"},
    "legend_phone": {"en": "Dashed orange: same phone number", "ar": "خط برتقالي متقطع: رقم الهاتف نفسه"},
    "legend_address": {"en": "Dotted grey: same address (often a business centre)", "ar": "خط رمادي منقّط: العنوان نفسه (غالباً مركز أعمال)"},
    "legend_nodes": {
        "en": "Filled circle: company that bid in this tender. Hollow circle: linked company that did not bid.",
        "ar": "دائرة ممتلئة: شركة تقدمت لهذه المناقصة. دائرة فارغة: شركة مرتبطة لم تتقدم.",
    },
    "links_table": {"en": "All links", "ar": "جميع الروابط"},
    "col_company_a": {"en": "Company A", "ar": "الشركة أ"},
    "col_company_b": {"en": "Company B", "ar": "الشركة ب"},
    "col_link_type": {"en": "Link type", "ar": "نوع الرابط"},
    "col_link_value": {"en": "Shared value", "ar": "القيمة المشتركة"},
    "col_disclosed": {"en": "Disclosed?", "ar": "مُفصح عنه؟"},
    "link_owner": {"en": "Owner", "ar": "المالك"},
    "link_phone": {"en": "Phone", "ar": "الهاتف"},
    "link_address": {"en": "Address", "ar": "العنوان"},
    "edge_owner_nd": {"en": "owner {value}, not disclosed", "ar": "المالك {value}، دون إفصاح"},
    "edge_owner_d": {"en": "owner {value}, disclosed group {group}", "ar": "المالك {value}، مجموعة مفصح عنها {group}"},
    "edge_phone": {"en": "phone {value}", "ar": "الهاتف {value}"},
    "edge_address": {"en": "address {value}", "ar": "العنوان {value}"},
    "hover_owner": {"en": "Owner", "ar": "المالك"},
    "hover_emirate": {"en": "Emirate", "ar": "الإمارة"},
    "hover_size": {"en": "Size", "ar": "الحجم"},
    "no_links": {"en": "No owner, phone or address links found for these bidders.", "ar": "لا توجد روابط ملكية أو هاتف أو عنوان بين هؤلاء المتقدمين."},
    "conn_caption": {
        "en": "Links come from the synthetic registry. A link is a reason to check, not proof of coordination.",
        "ar": "الروابط مأخوذة من السجل التجريبي المصطنع. الرابط سبب للتحقق وليس دليلاً على التنسيق.",
    },
    # ------------------------------------------------------------ review pack
    "btn_prepare": {"en": "Prepare Review Pack", "ar": "إعداد ملف المراجعة"},
    "btn_download": {"en": "Download review pack", "ar": "تنزيل ملف المراجعة"},
    "pack_prompt": {"en": "Select a tender and press Prepare Review Pack.", "ar": "اختر مناقصة ثم اضغط على إعداد ملف المراجعة."},
    "tab_summary": {"en": "Summary", "ar": "الملخص"},
    "tab_evidence": {"en": "Evidence", "ar": "الأدلة"},
    "tab_checklist": {"en": "Checklist", "ar": "قائمة التحقق"},
    "tab_decision": {"en": "Decision", "ar": "القرار"},
    "pack_title": {"en": "Evidence Review Pack — {tender_id}", "ar": "ملف مراجعة الأدلة — {tender_id}"},
    "pack_header": {"en": "Tender facts", "ar": "بيانات المناقصة"},
    "top_indicators": {"en": "Top indicators", "ar": "أهم المؤشرات"},
    "indicators": {"en": "Indicators", "ar": "المؤشرات"},
    "more_indicators": {"en": "More indicators", "ar": "مؤشرات إضافية"},
    "precheck_findings": {"en": "Pre-check findings", "ar": "نتائج الفحص المسبق"},
    "no_precheck": {"en": "No pre-check findings.", "ar": "لا توجد نتائج في الفحص المسبق."},
    "needs_review": {"en": "Needs human review — not proof of wrongdoing", "ar": "يتطلب مراجعة بشرية — وليس دليلاً على مخالفة"},
    "innocent": {"en": "Possible innocent explanation", "ar": "تفسير بريء محتمل"},
    "limitations": {"en": "Limitations", "ar": "القيود"},
    "evidence": {"en": "Evidence (source records)", "ar": "الأدلة (السجلات المصدرية)"},
    "checklist": {"en": "Verification checklist", "ar": "قائمة التحقق"},
    "severity": {"en": "Severity", "ar": "الدرجة"},
    "disclaimer": {
        "en": "This pack lists indicators for human review. It is not evidence of wrongdoing.",
        "ar": "يعرض هذا الملف مؤشرات للمراجعة البشرية، وهو ليس دليلاً على أي مخالفة.",
    },
    "ai_note": {"en": "AI-generated wording, facts checked against records", "ar": "صياغة مولّدة بالذكاء الاصطناعي، وتمت مطابقة الحقائق مع السجلات"},
    "ai_unavailable": {"en": "AI summary unavailable — showing standard text", "ar": "الملخص بالذكاء الاصطناعي غير متاح — يُعرض النص القياسي"},
    "standard_wording": {"en": "Standard tender wording — ignored", "ar": "صياغة المناقصة القياسية — تم تجاهلها"},
    "rare_legend": {"en": "Highlighted: rare sentence shared by the two proposals", "ar": "النص المظلل: جملة نادرة مشتركة بين العرضين"},
    "doc_author": {"en": "Document author", "ar": "مؤلف المستند"},
    "tbl_companies": {"en": "Company registry record", "ar": "سجل الشركة"},
    "tbl_bids": {"en": "Bid record", "ar": "سجل العطاء"},
    "tbl_proposals": {"en": "Proposal", "ar": "العرض الفني"},
    "tbl_benchmarks": {"en": "Comparable purchases", "ar": "المشتريات المماثلة"},
    "tbl_tenders": {"en": "Tender record", "ar": "سجل المناقصة"},
    "checklist_note": {"en": "Ticks are kept for this session only.", "ar": "تُحفظ علامات التحقق لهذه الجلسة فقط."},
    # ------------------------------------------------------------ decisions
    "dec_CLEAR": {"en": "Clear — no further action", "ar": "إغلاق — لا إجراء إضافي"},
    "dec_NEEDS_MORE_INFORMATION": {"en": "Needs more information", "ar": "يحتاج إلى معلومات إضافية"},
    "dec_REFER_FOR_INTERNAL_REVIEW": {"en": "Refer for internal review", "ar": "إحالة للمراجعة الداخلية"},
    "decision_label": {"en": "Decision", "ar": "القرار"},
    "decision_help": {
        "en": "The reviewer decides. Rasd never rejects, blacklists, cancels or awards automatically.",
        "ar": "القرار للمراجع. لا يقوم رصد أبداً بالرفض أو الإدراج في القوائم السوداء أو الإلغاء أو الترسية بشكل آلي.",
    },
    "reason_label": {"en": "Reason (at least 10 characters)", "ar": "السبب (10 أحرف على الأقل)"},
    "submit_decision": {"en": "Submit decision", "ar": "تسجيل القرار"},
    "reason_too_short": {"en": "Please write a reason of at least 10 characters.", "ar": "يرجى كتابة سبب لا يقل عن 10 أحرف."},
    "reviewer_missing": {"en": "Please enter a reviewer name in the sidebar.", "ar": "يرجى إدخال اسم المراجع في الشريط الجانبي."},
    "decision_saved": {"en": "Decision saved at {ts} (UTC).", "ar": "تم حفظ القرار في {ts} (بالتوقيت العالمي)."},
    "decision_history": {"en": "Decision history for this tender", "ar": "سجل القرارات لهذه المناقصة"},
    "no_decisions": {"en": "No decisions recorded yet.", "ar": "لم يتم تسجيل أي قرار بعد."},
    # ------------------------------------------------------------ timing
    "eval_mode": {"en": "Evaluation mode (timed test)", "ar": "وضع التقييم (اختبار مؤقت)"},
    "mode_label": {"en": "Mode", "ar": "الوضع"},
    "mode_manual": {"en": "Manual", "ar": "يدوي"},
    "mode_assisted": {"en": "Assisted", "ar": "بمساعدة رصد"},
    "timer_start": {"en": "Start", "ar": "ابدأ"},
    "timer_stop": {"en": "Stop", "ar": "أوقف"},
    "timer_running": {"en": "Timer running for {tender_id} ({mode}): {s} s elapsed.", "ar": "المؤقت يعمل للمناقصة {tender_id} ({mode}): مضى {s} ثانية."},
    "timer_stopped": {"en": "Session recorded: {s} seconds.", "ar": "تم تسجيل الجلسة: {s} ثانية."},
    "timer_idle": {"en": "No timer running.", "ar": "لا يوجد مؤقت قيد التشغيل."},
    # ------------------------------------------------------------ audit
    "filter_decision": {"en": "Decision", "ar": "القرار"},
    "filter_tender": {"en": "Tender", "ar": "المناقصة"},
    "download_csv": {"en": "Download as CSV", "ar": "تنزيل بصيغة CSV"},
    "audit_note": {"en": "Decisions are append-only and cannot be edited or deleted.", "ar": "القرارات تُضاف فقط ولا يمكن تعديلها أو حذفها."},
    "col_id": {"en": "ID", "ar": "الرقم"},
    "col_reason": {"en": "Reason", "ar": "السبب"},
    "col_reviewer": {"en": "Reviewer", "ar": "المراجع"},
    "col_priority_at": {"en": "Priority at decision", "ar": "الأولوية وقت القرار"},
    "col_alert_codes": {"en": "Alert codes", "ar": "رموز التنبيهات"},
    "col_engine": {"en": "Engine version", "ar": "إصدار المحرك"},
    "col_stretch": {"en": "Stretch detectors", "ar": "أدوات الكشف الإضافية"},
    "col_created": {"en": "Created (UTC)", "ar": "تاريخ الإنشاء (UTC)"},
    "timing_title": {"en": "Review-time evaluation", "ar": "تقييم زمن المراجعة"},
    "median_manual": {"en": "Median manual (s)", "ar": "الوسيط اليدوي (ث)"},
    "median_assisted": {"en": "Median assisted (s)", "ar": "الوسيط بمساعدة رصد (ث)"},
    "reduction": {"en": "Reduction in median time", "ar": "الانخفاض في الزمن الوسيط"},
    "sessions_manual": {"en": "Manual sessions", "ar": "الجلسات اليدوية"},
    "sessions_assisted": {"en": "Assisted sessions", "ar": "الجلسات بمساعدة رصد"},
    "timing_need": {"en": "Run at least one manual and one assisted session.", "ar": "نفّذ جلسة يدوية واحدة وجلسة واحدة بمساعدة رصد على الأقل."},
    "faster_claim": {"en": "Reviewers were {p}% faster on these test cases.", "ar": "كان المراجعون أسرع بنسبة {p}% في حالات الاختبار هذه."},
    # ------------------------------------------------------------ model card
    "config_table": {"en": "Live detector configuration (engine.CONFIG)", "ar": "إعدادات أدوات الكشف الحالية (engine.CONFIG)"},
    "param": {"en": "Parameter", "ar": "المعامل"},
    "value": {"en": "Value", "ar": "القيمة"},
    "alert_counts": {"en": "Indicators by code (current settings)", "ar": "المؤشرات حسب الرمز (الإعدادات الحالية)"},
    "code": {"en": "Code", "ar": "الرمز"},
    "label": {"en": "Label", "ar": "الوصف"},
    "count": {"en": "Count", "ar": "العدد"},
    "model_card_missing": {"en": "MODEL_CARD.md was not found.", "ar": "لم يتم العثور على الملف MODEL_CARD.md."},
    "model_card_lang_note": {"en": "", "ar": "بطاقة النموذج متاحة باللغة الإنجليزية فقط."},
}

# Document codes used in tenders.required_documents and bids.documents_attached.
DOC_NAMES = {
    "trade_licence": {"en": "Trade licence", "ar": "الرخصة التجارية"},
    "vat_certificate": {"en": "VAT certificate", "ar": "شهادة التسجيل الضريبي"},
    "bank_guarantee": {"en": "Bank guarantee", "ar": "الضمان البنكي"},
    "signed_declaration": {"en": "Signed declaration", "ar": "الإقرار الموقّع"},
}

# Arabic renderings of the engine's fixed limitation sentences (the engine itself is English-only).
LIMITATIONS_AR = {
    "Standardized products naturally attract close prices.": "المنتجات ذات المواصفات الموحدة تجذب بطبيعتها أسعاراً متقاربة.",
    "A clue only; small bid counts make statistics noisy.": "مؤشر أولي فقط؛ قلة عدد العطاءات تجعل الإحصاءات غير مستقرة.",
    "Disclosed group companies may legitimately bid separately.": "يجوز للشركات المفصح عن انتمائها لمجموعة واحدة التقدم بعروض منفصلة.",
    "Verify registry data and whether the relationship was disclosed.": "تحقق من بيانات السجل ومما إذا كان قد تم الإفصاح عن العلاقة.",
    "Shared switchboards exist.": "توجد مقاسم هاتفية مشتركة.",
    "Business centres host many unrelated firms.": "تستضيف مراكز الأعمال العديد من الشركات غير المرتبطة.",
    "Verify the address.": "تحقق من العنوان.",
    "Similar wording can be coincidental; check context.": "قد يكون تشابه الصياغة مصادفة؛ راجع السياق.",
    "Default author names can match innocently.": "قد تتطابق أسماء المؤلفين الافتراضية دون أي قصد.",
    "Specification, quantity, timing and delivery terms must genuinely match.": "يجب أن تتطابق المواصفات والكمية والتوقيت وشروط التسليم فعلياً.",
    "Alternation can happen by chance in small markets.": "قد يحدث التناوب بالصدفة في الأسواق الصغيرة.",
}

PRIORITY_KEYS = {"Routine": "prio_routine", "Review": "prio_review", "Urgent review": "prio_urgent"}


def current_lang() -> str:
    try:
        import streamlit as st
        lang = st.session_state.get("lang", "en")
    except Exception:
        lang = "en"
    return lang if lang in LANGS else "en"


def t(key: str, lang: str | None = None, **kwargs) -> str:
    """String for `key` in `lang` (default: the language selected in the sidebar)."""
    lang = lang or current_lang()
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry["en"]
    return text.format(**kwargs) if kwargs else text


def doc_name(code: str, lang: str | None = None) -> str:
    lang = lang or current_lang()
    return DOC_NAMES.get(code, {}).get(lang, code)


def limitation(text: str, lang: str | None = None) -> str:
    lang = lang or current_lang()
    return LIMITATIONS_AR.get(text, text) if lang == "ar" else text


def priority_label(priority: str, lang: str | None = None) -> str:
    return t(PRIORITY_KEYS.get(priority, "prio_routine"), lang)


def tender_status(status: str, lang: str | None = None) -> str:
    return t(f"tstatus_{status}", lang) if f"tstatus_{status}" in STRINGS else status
