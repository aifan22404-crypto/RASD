# Rasd (رصد) — Procurement Integrity Radar
## Build specification for the web application (v1.0, 28 Oct 2026)

> **To the AI coding tool / engineer reading this:** build exactly what this document describes. Where this spec and your own judgement disagree, follow the spec. Everything marked **MUST** is required for acceptance. Do not invent features, data, numbers or claims that are not in this document.

---

## 0. What you are given (the starter kit)

```
rasd-starter-kit/
  SPEC.md                    <- this file
  requirements.txt           <- pinned, tested versions
  rasd/__init__.py
  rasd/engine.py             <- VERIFIED detection engine. Use as-is. Do not change rules or thresholds.
  data/companies.csv         <- synthetic demo data (do not edit)
  data/tenders.csv
  data/bids.csv
  data/proposals.csv
  data/benchmarks.csv
  tests/test_engine.py       <- 11 acceptance tests, all passing today
  tests/expected_results.json
  pytest.ini                 <- makes `pytest -q` find the rasd package
  README.md
```

`rasd/engine.py` and the CSVs were built together and tested: running the engine on the CSVs produces exactly `tests/expected_results.json`. **Your job is to build the web application around this engine.** You MUST keep `pytest -q` passing (11 tests) at every step.

---

## 1. Product in one paragraph

Rasd is a bilingual (English/Arabic) web app for government procurement teams. Before a contract is awarded it (1) **pre-checks bids** for missing documents and expired licences, (2) runs an **Integrity Radar** that raises explained warning signs of possible bid-rigging or overpricing as **reason codes** (never a "fraud %"), and (3) prepares an **Evidence Review Pack** so a human reviewer can decide quickly. Every human decision is logged. It is an add-on layer for existing procurement platforms, built for the UAE Hackathon 2026, Theme "Zero Bureaucracy & Seamless Government", Challenge 5 (procurement). All demo data is synthetic.

**Golden rules (MUST, everywhere in the UI and code):**
1. The app never says a company is guilty, fraudulent, corrupt or a cartel. Wording is always "needs review", "warning sign", "indicator".
2. A human makes every decision. No automatic rejection, blacklisting, cancellation or award.
3. Every screen shows the synthetic-data banner.
4. Every alert shown links to the exact evidence (source record IDs) and shows its limitation text.
5. No real company names, personal data or IDs anywhere.

---

## 2. Tech stack (MUST)

| Item | Choice |
|---|---|
| Language | Python 3.12 (3.11+ works; pandas 3 needs ≥ 3.11) |
| Web framework | Streamlit, multipage via `st.navigation` + `st.Page` |
| Data | pandas, numpy |
| Detection | `rasd/engine.py` (rapidfuzz, numpy, pandas) |
| Graphs/charts | Plotly (`plotly.graph_objects`), networkx for layout |
| Storage | SQLite file `rasd.db` (Python `sqlite3`, no ORM) |
| Tests | pytest |
| Optional LLM | Any OpenAI-compatible chat endpoint via `requests` — OFF by default |

`requirements.txt` (already in the kit — tested together on Python 3.13):
```
streamlit==1.66.1
pandas==3.0.5
numpy==2.5.3
scipy==1.18.1
scikit-learn==1.9.1
networkx==3.7
plotly==7.1.0
rapidfuzz==3.14.6
pytest==9.1.1
requests>=2.31
```

**Streamlit API notes (to avoid deprecated calls):** use `width="stretch"` (not `use_container_width=True`) for `st.dataframe` and `st.plotly_chart`; use `st.navigation([...]).run()` for pages; use `st.segmented_control` for the EN/AR toggle; use `@st.cache_data` for loading data and running the engine.

Do NOT use React, a separate backend, a mobile app, Docker, or an external database.

---

## 3. Project structure (MUST)

```
rasd/
  __init__.py
  engine.py          # given — DO NOT MODIFY detection logic
  data_access.py     # cached loading + engine run + lookups
  i18n.py            # all UI strings EN/AR (section 9)
  templates.py       # review-pack sentence templates EN/AR (section 7)
  review_pack.py     # make_review_pack(), export to Markdown (section 7)
  llm.py             # optional LLM rewrite + fact check (section 8)
  storage.py         # SQLite: decisions + timing sessions (section 6)
  ui.py              # shared UI pieces: banner, badges, language toggle, CSS
pages/
  1_dashboard.py
  2_precheck.py
  3_radar.py
  4_connections.py
  5_review.py
  6_audit.py
  7_model_card.py
app.py               # entry point: page config, sidebar, navigation
data/                # given CSVs
tests/               # given tests + your new tests
.streamlit/config.toml
requirements.txt
README.md
MODEL_CARD.md
```

Run locally: `pip install -r requirements.txt` → `streamlit run app.py`. Tests: `pytest -q` from the project root.

---

## 4. Data model (given — do not edit the CSVs)

All dates are ISO `YYYY-MM-DD` (bids `submitted_at` is `YYYY-MM-DD HH:MM`). Multi-value fields use `|`.

**companies.csv** (15 rows): `company_id` (C01–C15), `name_en` (every name ends with "(Synthetic)"), `owner_id`, `phone`, `address`, `emirate`, `size` (SME/Large), `disclosed_group` (blank or group id, e.g. G-1), `licence_no`, `licence_expiry`, `address_type` (office / business_centre).

**tenders.csv** (12 rows, T-101–T-112): `tender_id`, `entity`, `title_en`, `category`, `specification_id`, `quantity`, `unit`, `estimated_value_aed`, `closing_date`, `status` (awarded / pre-award), `standardized` (yes/no), `required_documents` (pipe list), `rfp_text` (the tender's standard wording).

**bids.csv** (45 rows, B-001–B-045): `bid_id`, `tender_id`, `company_id`, `amount_aed`, `submitted_at`, `documents_attached` (pipe list), `is_winner` (yes / no for awarded tenders; blank for pre-award).

**proposals.csv** (45 rows): `bid_id`, `text`, `doc_author`.

**benchmarks.csv** (6 rows): `specification_id`, `purchase_date`, `unit_price_aed`, `source`.

Document codes and display names:

| code | English | Arabic |
|---|---|---|
| trade_licence | Trade licence | الرخصة التجارية |
| vat_certificate | VAT certificate | شهادة التسجيل الضريبي |
| bank_guarantee | Bank guarantee | الضمان البنكي |
| signed_declaration | Signed declaration | الإقرار الموقّع |

---

## 5. The engine (given) — what it returns

```python
from rasd import engine
db = engine.load("data")                       # dict of DataFrames; asserts referential integrity
res = engine.run_all(db, include_stretch=True)  # dict
res["precheck"]        # list of {tender_id, bid_id, company_id, code: MISSING_DOCUMENT|LICENCE_EXPIRED, detail}
res["price_features"]  # {tender_id: {bid_count, cv, gap_pct, rd}}  (values may be None)
res["alerts"]          # list of alert dicts (below)
res["priority"]        # {tender_id: "Routine" | "Review" | "Urgent review"}
```

Alert dict: `tender_id, code, severity (strong|moderate|weak|context), label, observed_value, comparator, evidence_ids ("table:id;table:id"), limitations, params (dict)`.

| Code | Meaning | Detector | MVP? | `params` keys |
|---|---|---|---|---|
| PRICE_PATTERN_REVIEW | Bids unusually close and/or lowest bid far from the rest | A | yes | bid_count, cv, rd, gap_pct, standardized |
| BIDDER_RELATIONSHIP | Two bidders in the same tender share owner / phone / address | C | yes | company_a, company_b, link_type (owner/phone/address), value, disclosed?, group?, business_centre? |
| SHARED_RARE_PHRASE | Two proposals share a rare sentence not in the RFP text | D | yes | bid_a, bid_b, count, sentence |
| DOC_METADATA_MATCH | Two proposals list the same document author | D | yes | bid_a, bid_b, author |
| BENCHMARK_GAP | Lowest unit price far above comparable purchases | E | stretch | spec, lowest_unit, median, ratio |
| REPEATED_WIN_SEQUENCE | Same bidder group, winners take turns | B | stretch | sequence, tenders, group_size |

Severity points: strong 3, moderate 2, weak 1, context 0. Priority: **Urgent review** if ≥ 1 strong AND total ≥ 5; **Review** if total ≥ 2; else **Routine**. "Urgent" is a queue priority, never a legal status.

**Stretch toggle (MUST):** a sidebar checkbox "Include stretch detectors (rotation, benchmark)" → `include_stretch` (default **ON**). Expected priorities are in `tests/expected_results.json` under `mvp` (OFF) and `full` (ON).

**Expected demo results with stretch ON (MUST match):** T-104 = Urgent review; T-101, T-103, T-105, T-106, T-110, T-112 = Review (rotation); T-111 = Review (benchmark); T-102, T-107, T-108, T-109 = Routine (with weak/context notes on T-102, T-107, T-109). Pre-check finds exactly 6 issues: B-004 missing signed_declaration; B-016 licence expired (C08); B-017 missing bank_guarantee; B-031 missing bank_guarantee; B-034 missing vat_certificate; B-037 missing bank_guarantee.

---

## 6. Storage (rasd/storage.py) — SQLite `rasd.db`

Create tables on startup if missing (`CREATE TABLE IF NOT EXISTS`). Use parameterized queries only.

```sql
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tender_id TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision IN ('CLEAR','NEEDS_MORE_INFORMATION','REFER_FOR_INTERNAL_REVIEW')),
  reason TEXT NOT NULL,              -- reviewer's note, min 10 characters
  reviewer TEXT NOT NULL,            -- display name typed in sidebar
  priority_at_decision TEXT NOT NULL,
  alert_codes TEXT NOT NULL,         -- comma-separated codes shown at decision time
  engine_version TEXT NOT NULL,      -- e.g. "rasd-engine-1.0"
  include_stretch INTEGER NOT NULL,  -- 0/1
  created_at TEXT NOT NULL           -- UTC ISO timestamp
);
CREATE TABLE IF NOT EXISTS timing_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tender_id TEXT NOT NULL,
  reviewer TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('manual','assisted')),
  started_at TEXT NOT NULL,
  ended_at TEXT,
  seconds REAL
);
```

Functions: `init_db()`, `save_decision(...)`, `list_decisions(tender_id=None)`, `latest_decision(tender_id)`, `start_timer(tender_id, reviewer, mode)`, `stop_timer(session_id)`, `timing_summary()` → median seconds per mode and % reduction = (median_manual − median_assisted) / median_manual × 100 (only if both modes have ≥ 1 completed session).

Decisions are append-only (no edit/delete in the UI). A tender's "status" = its latest decision, else "Open".

---

## 7. Evidence Review Pack (rasd/review_pack.py + rasd/templates.py)

`make_review_pack(tender_id, res, db, lang) -> dict` with keys:

1. `header`: tender_id, title, entity, category, estimated value, closing date, status, number of bids, **priority**.
2. `indicators`: the tender's alerts sorted by severity (strong > moderate > weak > context), then code. Top 3 shown first; the rest under "More indicators".
3. Each indicator has: label (EN/AR), severity, **summary sentence** from the template, **innocent explanation**, `limitations` (from engine), and `evidence` = list of source records resolved from `evidence_ids` (e.g. `companies:C04` → that company row; `bids:B-013`; `proposals:B-013` → text with the rare sentence highlighted; `benchmarks:LAPTOP-A` → all benchmark rows; `tenders:T-101`).
4. `precheck`: that tender's pre-check findings.
5. `checklist`: de-duplicated checklist items for the codes present.
6. `disclaimer`: "This pack lists indicators for human review. It is not evidence of wrongdoing." (AR in section 9).

**Templates (MUST use exactly; fill `{}` from `params`; format AED with thousands separators; cv to 3 decimals; rd to 2 decimals; percentages to 1 decimal):**

| Code | English summary | Arabic summary | Innocent explanation (EN / AR) | Checklist (EN / AR) |
|---|---|---|---|---|
| PRICE_PATTERN_REVIEW | "The {bid_count} bids are unusually close together (coefficient of variation {cv}), and the lowest bid is {gap_pct} below the next one (relative distance {rd})." | "العروض البالغ عددها {bid_count} متقاربة بشكل غير معتاد (معامل الاختلاف {cv})، والعرض الأدنى أقل من العرض التالي بنسبة {gap_pct} (المسافة النسبية {rd})." | "Bids for well-defined products can legitimately be close in price." / "قد تتقارب أسعار العروض بشكل مشروع عندما تكون مواصفات المنتج محددة بدقة." | "Compare with past tenders in the same category." / "قارن مع مناقصات سابقة من نفس الفئة." ; "Check whether the higher bids look realistic." / "تحقق مما إذا كانت العروض الأعلى واقعية." |
| BIDDER_RELATIONSHIP (owner, not disclosed) | "{company_a} and {company_b} bid against each other but share the same owner ({value}) in the registry, and no relationship was disclosed." | "تنافست {company_a} و{company_b} في هذه المناقصة رغم أن لهما المالك نفسه ({value}) في السجل، ولم يتم الإفصاح عن هذه العلاقة." | "Registry data can be outdated or ownership may have changed." / "قد تكون بيانات السجل قديمة أو قد تكون الملكية قد تغيّرت." | "Verify ownership with the licensing authority." / "تحقق من الملكية لدى جهة الترخيص." ; "Check whether a conflict-of-interest declaration was required." / "تحقق مما إذا كان مطلوباً تقديم إقرار بتضارب المصالح." |
| BIDDER_RELATIONSHIP (owner, disclosed) | "{company_a} and {company_b} share an owner and declared it as group {group}." | "تشترك {company_a} و{company_b} في المالك وقد أفصحتا عن ذلك ضمن المجموعة {group}." | "Disclosed group companies may legitimately bid separately." / "يجوز للشركات المفصح عن انتمائها لمجموعة واحدة التقدم بعروض منفصلة." | "Confirm the tender rules allow related bidders." / "تأكد من أن شروط المناقصة تسمح بمشاركة شركات مرتبطة." |
| BIDDER_RELATIONSHIP (phone) | "{company_a} and {company_b} list the same phone number ({value})." | "تستخدم {company_a} و{company_b} رقم الهاتف نفسه ({value})." | "Shared switchboards or service providers exist." / "قد تتشارك الشركات خدمة اتصال أو مقسماً واحداً." | "Verify contact details with both companies." / "تحقق من بيانات الاتصال لدى الشركتين." |
| BIDDER_RELATIONSHIP (address) | "{company_a} and {company_b} list the same address ({value})." | "تستخدم {company_a} و{company_b} العنوان نفسه ({value})." | if business_centre: "Business centres host many unrelated firms." / "تستضيف مراكز الأعمال العديد من الشركات غير المرتبطة." else "Companies can share premises legitimately." / "قد تتشارك الشركات المقر بشكل مشروع." | "Verify the premises." / "تحقق من المقر." |
| SHARED_RARE_PHRASE | "Proposals {bid_a} and {bid_b} share {count} rare sentence(s) that do not appear in the tender wording, e.g. \"{sentence}\"." | "يشترك العرضان {bid_a} و{bid_b} في {count} جملة نادرة غير موجودة في نص المناقصة، مثل: \"{sentence}\"." | "Companies may use the same consultant or template." / "قد تستعين الشركات بالمستشار نفسه أو بالقالب نفسه." | "Compare both proposals in full." / "قارن العرضين بالكامل." ; "Ask how each proposal was prepared." / "استفسر عن طريقة إعداد كل عرض." |
| DOC_METADATA_MATCH | "Proposals {bid_a} and {bid_b} list the same document author ('{author}')." | "يحمل العرضان {bid_a} و{bid_b} اسم مؤلف المستند نفسه ('{author}')." | "Default or shared software accounts can produce the same author name." / "قد ينتج اسم المؤلف نفسه عن إعدادات افتراضية أو حساب برمجي مشترك." | "Check document properties of the original files." / "افحص خصائص الملفات الأصلية." |
| BENCHMARK_GAP | "The lowest unit price (AED {lowest_unit}) is {ratio}× the median of comparable purchases (AED {median}) for {spec}." | "أدنى سعر للوحدة ({lowest_unit} درهم) يعادل {ratio} ضعف متوسط المشتريات المماثلة ({median} درهم) للمواصفة {spec}." | "Supply shortages, delivery terms or extra services can justify higher prices." / "قد تبرر ندرة المعروض أو شروط التسليم أو الخدمات الإضافية ارتفاع الأسعار." | "Confirm the specifications truly match." / "تأكد من تطابق المواصفات فعلياً." ; "Request a price breakdown." / "اطلب تفصيلاً للأسعار." |
| REPEATED_WIN_SEQUENCE | "The same {group_size} companies bid in {n} tenders and the winners took turns: {sequence}." (n = len(tenders); sequence joined with " → ") | "تقدمت الشركات نفسها وعددها {group_size} في {n} مناقصات وتناوبت على الفوز: {sequence}." | "In small markets, alternation can happen by chance." / "في الأسواق الصغيرة قد يحدث التناوب بالصدفة." | "Review the full bidding history of the group." / "راجع سجل العطاءات الكامل للمجموعة." |

Pre-check lines (EN/AR): MISSING_DOCUMENT → "{company} did not attach: {document}." / "لم ترفق {company}: {document}."; LICENCE_EXPIRED → "{company}'s trade licence expired on {date}, before the tender closing date." / "انتهت الرخصة التجارية لـ{company} في {date} قبل تاريخ إغلاق المناقصة." Show company as "name (ID)".

**Export (MUST):** `pack_to_markdown(pack, lang) -> str`, offered with `st.download_button` as `rasd_review_pack_{tender_id}_{lang}.md` (mime `text/markdown`). The file starts with the synthetic-data disclaimer and ends with the "not evidence of wrongdoing" line. (No PDF: Arabic PDF shaping is out of scope.)

---

## 8. Optional LLM rewrite (rasd/llm.py) — OFF by default

- Enabled only if `st.secrets` (or env) has `LLM_API_KEY`, `LLM_BASE_URL` (OpenAI-compatible `/v1/chat/completions`), `LLM_MODEL`; plus the sidebar toggle "Plain-language summary (AI)".
- Input: ONLY the already-filled template sentences for one tender (no raw tables). System prompt: *"Rewrite the following review notes as one short paragraph in {English|Arabic} for a procurement officer. Use only the facts given. Do not add facts, opinions, accusations or legal conclusions. Keep every company ID, bid ID, number and date exactly as written."*
- **Fact check (MUST):** extract all tokens matching `C\d{2}`, `B-\d{3}`, `T-\d{3}`, numbers (`\d[\d,.]*`) and dates from the output; every one must appear in the input; also reject the output if it contains any of: fraud, fraudulent, guilty, corrupt, cartel, criminal, احتيال, مذنب, فساد, كارتل. If the check fails or the call errors/times out (10 s), show the template text and a small note "AI summary unavailable — showing standard text".
- Never send data to an LLM unless the toggle is on. Show "AI-generated wording, facts checked against records" under any AI paragraph.

---

## 9. Language, RTL and strings (rasd/i18n.py)

- Sidebar language toggle EN / العربية (`st.segmented_control`), stored in `st.session_state["lang"]`, default EN.
- `t(key) -> str` returns the string for the current language. No hard-coded UI text in pages.
- When Arabic is selected inject CSS so the main content is right-to-left: `[data-testid="stMain"] { direction: rtl; text-align: right; }` (keep charts and the network graph LTR by wrapping them in a container with `direction: ltr`). Use a font stack that renders Arabic well: inject `<style>@import url('https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@400;600&display=swap'); [data-testid="stMain"] * { font-family: 'Noto Kufi Arabic', sans-serif; }</style>` with `st.markdown(..., unsafe_allow_html=True)` only when Arabic is active (`stMain` is a valid test id in Streamlit 1.66).
- IDs (C04, B-013, T-104), amounts and dates stay in Western digits in both languages.

Required strings (extend as needed, same style):

| key | EN | AR |
|---|---|---|
| app_name | Rasd | رصد |
| tagline | Procurement Integrity Radar | رادار نزاهة المشتريات |
| banner | SYNTHETIC DEMO DATA — all tenders, companies and relationships are fictional. Indicators require human review and are not evidence of wrongdoing. | بيانات تجريبية مصطنعة — جميع المناقصات والشركات والعلاقات وهمية. المؤشرات تتطلب مراجعة بشرية وليست دليلاً على أي مخالفة. |
| nav_dashboard | Tenders Dashboard | لوحة المناقصات |
| nav_precheck | Bid Pre-check | الفحص المسبق للعطاءات |
| nav_radar | Integrity Radar | رادار النزاهة |
| nav_connections | Bidder Connections | روابط المتقدمين |
| nav_review | Evidence Review Assistant | مساعد مراجعة الأدلة |
| nav_audit | Decisions & Audit Trail | القرارات وسجل التدقيق |
| nav_model | Model Card | بطاقة النموذج |
| prio_routine | Routine | اعتيادي |
| prio_review | Review | يحتاج مراجعة |
| prio_urgent | Urgent review | مراجعة عاجلة |
| sev_strong / moderate / weak / context | Strong / Moderate / Weak / Context | قوي / متوسط / ضعيف / سياق |
| code_PRICE_PATTERN_REVIEW | Unusual price pattern | نمط أسعار غير معتاد |
| code_BIDDER_RELATIONSHIP | Linked bidders | ارتباط بين المتقدمين |
| code_SHARED_RARE_PHRASE | Rare shared text | نص نادر مشترك |
| code_DOC_METADATA_MATCH | Same document author | نفس مؤلف المستند |
| code_BENCHMARK_GAP | Price above comparable purchases | سعر أعلى من المشتريات المماثلة |
| code_REPEATED_WIN_SEQUENCE | Winners take turns | تناوب الفائزين |
| pc_complete | Complete | مكتمل |
| pc_missing | Missing document | مستند ناقص |
| pc_expired | Licence expired | رخصة منتهية |
| btn_prepare | Prepare Review Pack | إعداد ملف المراجعة |
| btn_download | Download review pack | تنزيل ملف المراجعة |
| dec_CLEAR | Clear — no further action | إغلاق — لا إجراء إضافي |
| dec_NEEDS_MORE_INFORMATION | Needs more information | يحتاج إلى معلومات إضافية |
| dec_REFER_FOR_INTERNAL_REVIEW | Refer for internal review | إحالة للمراجعة الداخلية |
| needs_review | Needs human review — not proof of wrongdoing | يتطلب مراجعة بشرية — وليس دليلاً على مخالفة |
| innocent | Possible innocent explanation | تفسير بريء محتمل |
| limitations | Limitations | القيود |
| evidence | Evidence (source records) | الأدلة (السجلات المصدرية) |
| checklist | Verification checklist | قائمة التحقق |
| reviewer | Reviewer name | اسم المراجع |
| stretch_toggle | Include stretch detectors (rotation, benchmark) | تضمين أدوات الكشف الإضافية (التناوب، المقارنة السعرية) |

Arabic strings MUST be proof-read by a native speaker on the team before the pitch.

---

## 10. Pages (MUST)

Shared layout (every page): `st.set_page_config(page_title="Rasd | رصد", page_icon="🛰️", layout="wide")` once in `app.py`; sidebar has logo text "Rasd رصد", tagline, language toggle, reviewer name text input (default "Reviewer 1"), stretch toggle, optional AI toggle (only visible if LLM secrets exist), and a small "Engine: rasd-engine-1.0" caption. Top of every page: the yellow synthetic banner (`st.warning(t("banner"))`). A tender selector (`st.selectbox`) appears on pages 3–5 and is shared through `st.session_state["tender_id"]` (default "T-104").

### Page 1 — Tenders Dashboard
- KPI row (`st.metric` ×4): Tenders screened (12); Bids (45); Tenders needing review (count of Review + Urgent); Pre-check issues (6).
- Table (`st.dataframe`, hide index): tender_id, title, entity, category, estimated value (AED, formatted), bids count, closing date, status, **priority** (colored badge text: Urgent = red 🔴, Review = amber 🟠, Routine = green 🟢), alert codes (comma list), latest decision. Default sort: priority (Urgent, Review, Routine) then closing date (newest first).
- Filters: category multiselect, priority multiselect.
- Button per row is not possible in st.dataframe; instead a selectbox "Open tender" + button "Open in Integrity Radar" that sets `st.session_state["tender_id"]` and calls `st.switch_page("pages/3_radar.py")`.

### Page 2 — Bid Pre-check
- Tender selector. For the selected tender a table: one row per bid: company (name + ID), each required document as a column showing ✅ / ❌, licence expiry with ⚠️ if before closing date, overall status (Complete / issues count).
- Below: the fix list (pre-check lines from section 7) — "Copy fix list" text area with all lines for that tender.
- Right column: "All tenders" summary: issues per tender (bar chart, Plotly).
- Caption: "Pre-check checks completeness and dates only; it does not verify identities or document authenticity."

### Page 3 — Integrity Radar
- Header: tender title, priority badge, status.
- Left (2/3): Plotly bar chart of bid amounts (x = company ID, y = AED), lowest bid highlighted, dashed horizontal line at the estimated value; a table of price features: bid count, CV, gap %, relative distance (show "n/a" for None) with a one-line explanation of each metric.
- Right (1/3): "Reason codes" cards — one `st.container(border=True)` per alert: label, severity badge, observed_value, comparator, limitations (italic), evidence IDs.
- If no alerts: "No indicators found. Ordinary procurement checks still apply."
- Button "Prepare Review Pack" → set tender_id, `st.switch_page("pages/5_review.py")`.

### Page 4 — Bidder Connections
- Network graph (Plotly) of all companies that bid in the selected tender plus any company linked to them by owner/phone/address (from companies.csv). Layout `networkx.spring_layout(G, seed=42)`.
- Nodes: company ID labels, hover = name, owner, emirate, size. Nodes bidding in this tender: filled; others: hollow.
- Edges: owner = solid red (dark grey if disclosed group); phone = dashed orange; address = dotted grey (business centre); edge hover = link type + value.
- Legend under the graph explaining edge styles, plus a table of all links with "Disclosed?" column.
- Caption: "Links come from the synthetic registry. A link is a reason to check, not proof of coordination."

### Page 5 — Evidence Review Assistant (primary efficiency feature)
- Tender selector + "Prepare Review Pack" button (also auto-built when arriving from page 3).
- Tabs: **Summary** | **Evidence** | **Checklist** | **Decision**.
  - Summary: priority, header facts, top-3 indicators with template sentences and innocent explanations; optional AI paragraph (section 8); pre-check findings.
  - Evidence: for each indicator, the resolved source records. For SHARED_RARE_PHRASE show the two proposals side by side with the rare sentence highlighted (`<mark>`), and RFP-matching sentences shown greyed out with label "Standard tender wording — ignored".
  - Checklist: `st.checkbox` per item (state in session only).
  - Decision: radio of the 3 decisions, reason text area (min 10 chars, required), Submit → `storage.save_decision(...)` → success message with timestamp; show decision history for this tender.
- Download button for the Markdown pack (EN or AR according to current language).
- **Timing (evaluation mode):** an expander "Evaluation mode (timed test)" with mode radio (manual / assisted), Start and Stop buttons that call `start_timer` / `stop_timer`, showing elapsed seconds. Used for the review-time KPI.

### Page 6 — Decisions & Audit Trail
- Table of all decisions (newest first) with all columns from section 6; filters by decision and tender.
- Download as CSV.
- Timing summary from `timing_summary()`: median manual seconds, median assisted seconds, % reduction, number of sessions per mode. If not enough data: "Run at least one manual and one assisted session."

### Page 7 — Model Card
- Render `MODEL_CARD.md` (you write it): purpose; data (synthetic + note that research datasets are optional and cited); detectors and thresholds (read live from `engine.CONFIG`); what each priority means; known limitations; claims we do and do not make (table from section 12); human-in-the-loop rules; version.
- Show the live config table from `engine.CONFIG` and counts of alerts by code.

---

## 11. Visual design

- `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#0B5394"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F3F6FA"
textColor = "#1F2933"
font = "sans serif"
```
- Navy + white + one accent (#0B5394). Priority colors: Urgent #C62828, Review #EF8F00, Routine #2E7D32. Severity badges: strong red, moderate amber, weak grey, context blue-grey.
- Laptop-first (1366×768 minimum). No emojis except the priority dots and ✅/❌/⚠️ in tables.

---

## 12. Claims the UI may and may not make (MUST)

| Allowed | Never |
|---|---|
| "X indicators found; needs human review" | "Fraud detected", "cartel", "guilty", any probability of fraud |
| "Reviewers were X% faster on these test cases" (from timing data) | "Cuts procurement time by 50%" |
| "Potential savings under stated assumptions" | "Saved AED …" |

---

## 13. Error handling & performance

- Load data and run the engine with `@st.cache_data` keyed on `include_stretch`; target < 2 s first load, instant afterwards.
- If a CSV is missing or `engine.load` assertion fails: show `st.error` with the message and stop (`st.stop()`), never a stack trace.
- All SQLite access through `storage.py`; open a new connection per call (`check_same_thread=False` not needed then).
- Never log or display secrets.

---

## 14. Testing & acceptance (MUST)

1. `pytest -q` → the 11 given tests pass. Add tests for: `make_review_pack("T-104", ...)` contains BIDDER_RELATIONSHIP, PRICE_PATTERN_REVIEW, SHARED_RARE_PHRASE, DOC_METADATA_MATCH and the 2 pre-check findings; template filling never leaves `{` or `}` in output (EN and AR) for every alert in the dataset; storage round-trip (save decision → list → latest); LLM fact-check rejects an output containing a number not in the input and one containing "fraud".
2. Use `streamlit.testing.v1.AppTest` to load each page without exceptions.
3. Manual demo script (must work end to end in < 3 minutes):
   1. Dashboard shows 12 tenders; T-104 is first with 🔴 Urgent review.
   2. Bid Pre-check, T-104: C08 licence expired (2026-08-31); C11 missing bank guarantee.
   3. Integrity Radar, T-104: CV 0.027, gap 3.2%, relative distance 1.53; 4 reason codes (price strong, linked bidders strong, rare text moderate, same author weak).
   4. Bidder Connections, T-104: C04 — C05 red edge "owner O-17, not disclosed".
   5. Review Assistant: pack shows top-3 indicators; Evidence tab highlights "We will deliver 500 laptpos configured to the required build within 21 days of the purchase order" in B-013 and B-014, and greys out "The supplier shall provide three years of on-site warranty support."
   6. Decision: "Refer for internal review" with a note → appears on Audit Trail with timestamp.
   7. Switch to Arabic: all labels, the pack and the export switch to Arabic; layout is RTL.
   8. Turn stretch OFF: only T-104 remains above Routine.

---

## 15. Deployment (MUST)

1. Push the project to a public GitHub repo (no secrets, no `rasd.db`; add `.gitignore` with `rasd.db`, `.venv/`, `__pycache__/`, `.streamlit/secrets.toml`).
2. Streamlit Community Cloud → New app → repo, branch `main`, main file `app.py`, Advanced settings → Python 3.12.
3. Optional LLM keys go in the app's Secrets panel (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`).
4. Note in README: the cloud demo uses synthetic data only and SQLite resets when the app restarts; a production deployment would run on UAE-hosted infrastructure with read-only access to procurement systems.
5. README MUST include: one-paragraph description, screenshots, local run commands, test command, data disclaimer, citation of any research dataset used, team names.

---

## 16. Out of scope — do NOT build

Login/authentication, real government integrations, real company data, PDF upload/OCR, PDF export, email/SMS notifications, automatic blocking/award/cancellation, vendor blacklists, any "fraud score/probability", mobile app, admin panels, editing or deleting decisions, a machine-learning model inside the app (an optional offline notebook on public research data is separate and not part of this build).

---

## 17. Build order (follow in this order; app must run after each step)

1. Scaffold structure, `requirements.txt`, `.streamlit/config.toml`, `app.py` with navigation and empty pages, banner, language toggle, sidebar. Tests still pass.
2. `data_access.py` (cached load + run_all) and Page 1 Dashboard.
3. Page 2 Pre-check.
4. Page 3 Integrity Radar.
5. Page 4 Bidder Connections.
6. `templates.py`, `review_pack.py`, Page 5 (without LLM) + export.
7. `storage.py`, Decision tab, Page 6, timing.
8. `i18n.py` complete + RTL; verify every page in Arabic.
9. Page 7 Model Card + MODEL_CARD.md + README.
10. Optional `llm.py`.
11. New tests (section 14), AppTest smoke tests, manual demo script, deploy.

When finished, report: test results, the deployed URL, and any deviation from this spec with the reason.
