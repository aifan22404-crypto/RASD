## Purpose

Rasd is a pre-award review aid for government procurement teams. It checks bids for missing documents and expired licences, raises explained **warning signs** (reason codes) that may point to bid-rigging or overpricing, and assembles an Evidence Review Pack so that a human reviewer can decide quickly. It does not decide anything itself and it never produces a "fraud score" or probability.

## Data

- **Demo data is fully synthetic**: 12 tenders, 15 companies, 45 bids, 45 proposals and 6 benchmark prices. Every company name ends with "(Synthetic)". No real company names, personal data or identifiers are used.
- No external research dataset is used by this app. If the team uses a public research dataset for an offline experiment, it is cited in the README and is not part of this build.

## Detectors

Thresholds are demo values chosen for the synthetic data, **not** proven collusion thresholds. The live values used by the engine are shown in the table below this card.

| Code | What it looks at | Severity |
|---|---|---|
| PRICE_PATTERN_REVIEW | Coefficient of variation of bids (≥ 3 bids) and relative distance of the lowest bid (≥ 4 bids) | strong if both screens hit, moderate if one; weak if the product is standardized |
| BIDDER_RELATIONSHIP | Two bidders in one tender share an owner, phone or address in the registry | strong (undisclosed owner), context (disclosed group), moderate (phone / address), weak (business-centre address) |
| SHARED_RARE_PHRASE | Two proposals share a sentence that is not tender wording and appears in at most 2 proposals overall | moderate |
| DOC_METADATA_MATCH | Two proposals list the same document author | weak |
| BENCHMARK_GAP *(stretch)* | Lowest unit price compared with the median of ≥ 3 comparable purchases | moderate |
| REPEATED_WIN_SEQUENCE *(stretch)* | Same group of ≥ 3 bidders in ≥ 5 awarded tenders of one category, winners taking turns | moderate |

Stretch detectors can be switched off in the sidebar.

## What each priority means

Severity points: strong 3, moderate 2, weak 1, context 0.

- **Urgent review** — at least one strong indicator and 5 or more points. Look at this tender first.
- **Review** — 2 or more points.
- **Routine** — fewer than 2 points. Ordinary procurement checks still apply.

Priority orders the review queue. It is never a legal status.

## Known limitations

- Small bid counts make price statistics noisy; close prices are normal for well-defined products.
- Registry data can be outdated; shared phones and business-centre addresses are common for unrelated firms.
- Shared wording can come from a common consultant or template; default document author names can match innocently.
- Benchmarks only help when specification, quantity, timing and delivery terms genuinely match.
- Alternation of winners can happen by chance in small markets.
- Pre-check verifies completeness and dates only, not identities or document authenticity.
- Thresholds were tuned on synthetic data and have not been validated on real procurement records.

## Claims we do and do not make

| Allowed | Never |
|---|---|
| "X indicators found; needs human review" | "Fraud detected", "cartel", "guilty", any probability of fraud |
| "Reviewers were X% faster on these test cases" (from timing data) | "Cuts procurement time by 50%" |
| "Potential savings under stated assumptions" | "Saved AED …" |

## Human-in-the-loop rules

1. A human makes every decision: *Clear*, *Needs more information* or *Refer for internal review*.
2. Rasd never rejects, blacklists, cancels or awards automatically.
3. Every indicator links to the exact source records and shows its limitation text.
4. Every decision is logged with reviewer, reason, priority, alert codes, engine version and timestamp, and cannot be edited or deleted.
5. The optional AI summary is off by default, only rewrites already-filled template sentences, and is fact-checked against them.

## Version

Engine `rasd-engine-1.0` · App v1.0 · 28 Oct 2026
