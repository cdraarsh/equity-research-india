---
name: equity-research-india
description: Build qualitative investment theses on Indian listed companies by synthesizing annual reports, quarterly results, and earnings concall transcripts. Use whenever the user uploads an Indian company's AR/QR/concall PDF and asks for analysis, names an Indian listed stock with words like thesis, deep dive, story, should I invest, is it a buy, analyze, or what's the case for/against, asks for peer or sector comparison within Indian markets, or asks about red flags, governance, audit issues, or management quality. Trigger even without phrases like fundamental analysis — any substantive ask to evaluate an Indian listed company's business quality, management, or long-term story qualifies. Trigger especially on uploads of 100+ page PDFs that look like annual reports or transcripts that look like concalls, even if the ask is vague. Do NOT trigger for DCF or fair-value modeling, technical analysis, F&O strategies, IPO grey market chatter, mutual fund picks, US/global equities, or generic finance education.
---

# Equity Research — Indian Listed Companies

This skill turns annual reports, quarterly results, and concall transcripts into a structured qualitative investment thesis with an Indian governance lens, plus disciplined ratio-based valuation when a current market price is available. The output is opinionated. The qualitative read covers **business quality, management quality, growth runway, and red flags**; the valuation overlay produces trailing/forward multiples, scenario-based forward EPS, an implied price band, and an asymmetry call vs CMP. It stops short of single-point DCF intrinsic values or "buy at exactly ₹X" target prices — those imply false precision.

## Operating principles

**Be opinionated.** The user wants a view, not a balanced both-sides recap. After laying out facts, take a side and name it. "Bull case looks stronger because X, Y, Z. The bear case hinges on a single assumption (Z) that history doesn't support." Hedging on everything is useless.

**Read the documents — don't guess from memory.** If the user uploaded files, the analysis must be grounded in those files. Quote sparingly but specifically: "Management said in Q2 FY26 concall that they expect 14-15% EBITDA margin by FY27, vs ~11% currently." Do not invent numbers. If you don't have a number from the filings, say so explicitly rather than estimating.

**When the user names a stock without uploads.** Prefer asking for the actual filings (latest AR, last 4 concalls, recent QRs) — full-context analysis is much higher quality. As a fallback, web_search is OK for: latest quarter results that just dropped, recent news/regulatory actions, and macro/sector context. Do NOT use web_search for historical financials, segment trajectory, RPT, contingent liab, CARO, auditor commentary, or anything that should come from primary filings. Always note in the output which parts came from filings vs. web vs. neither.

**Resolve conflicts between sources by type:**
- **Forward-looking statements** (guidance, capex plans, demand commentary): weight by recency — latest concall > latest investor presentation > latest QR commentary > AR Director's Report. The world moves between an AR (often 6+ months old) and the latest concall.
- **Historical financial facts** (margins, debt, working capital): weight by audited status — audited AR numbers > limited-review QR numbers > management commentary on a concall. If the concall says one thing and the audited financials say another, the financials win.
- When sources actively disagree, name the conflict in the output rather than picking silently. "Management said in the Q1 concall they expected margin recovery by Q3; Q3 numbers show margin still compressed. Either the recovery is delayed or the original guidance was off."

**Indian context is the default lens.** This means: SEBI/MCA disclosures, CARO 2020 auditor remarks, related party transactions, promoter shareholding and pledging, subsidiary structure (especially listed-vs-unlisted subs, foreign subs, holding co discount), contingent liabilities (tax disputes are a big one in India), capex announcements vs follow-through, ESOP dilution patterns, regulatory exposure to specific Indian regulators (RBI for NBFCs/banks, IRDAI for insurance, BIS, CDSCO, RERA, GST, etc.), and family/promoter governance dynamics.

**Qualitative does not mean number-free.** Use numbers to show direction and trajectory — margin going from 14% → 16% → 17% over three years matters. Numbers ground the thesis; they don't replace it.

**Valuation math is in scope, but with discipline.** When the user provides a current market price (or asks "is it cheap" / "should I buy at ₹X" / "what's a fair price"), compute trailing + forward ratios (PE, EV/EBITDA, P/B), generate scenario-based forward EPS (bear/base/bull walked through the full P&L), produce an implied price band, run a quality-of-earnings adjustment (PAT vs owner's earnings), and call the asymmetry vs CMP. Do NOT produce single-point DCF intrinsic values, "buy at exactly ₹X" target prices, technical/chart-based timing, or position-sizing advice. The output is a **price band with asymmetry assessment**, not a target price. See `references/valuation-math.md` for the full framework. Note: the business-quality verdict (section 10 of the master report) and the price-asymmetry call (section 8) can disagree — when they do, name the disagreement explicitly rather than papering over it.

**Cross-reference what management said vs what they delivered.** This is the single highest-signal exercise. Pull guidance from a previous concall and check the latest results against it. Patterns of consistent over-delivery, meeting guidance, or routinely missing it tell you more about management than any qualitative description.

## Workflow

### 1. Inventory the inputs

When the user provides documents, identify what each one is:
- **Annual Report (AR)** — typically 200-400+ page PDF with Director's Report, MD&A, financial statements, auditor report, CARO, related party notes, subsidiary list. Highest density per document.
- **Quarterly Results (QR)** — short PDF or press release with segment revenue, profit, EBITDA, sometimes management commentary.
- **Investor Presentation** — slide deck released alongside QR; usually has the cleanest visualization of segment trends and guidance.
- **Concall Transcript** — Q&A format, 20-50 pages. The Q&A section is more revealing than the prepared remarks.
- **Stock Exchange Filings** — corporate announcements, RPT disclosures, etc.

If the user just names a stock without uploads, follow the fallback rule from Operating Principles — prefer asking for filings, use web_search only for latest results / recent news / sector context, and label the source in the output.

### 2. Identify the sector and apply the right lens

Different sectors need very different emphasis. Before going deep, identify which sector the company is in and adjust the analysis priorities:

- **Banks / NBFCs** — asset quality (Stage 3, restructured book, write-offs), provisioning coverage, funding mix (CASA / borrowing mix), capital adequacy, ROA decomposition. The "moat" is usually liability franchise.
- **Pharma** — USFDA inspection history (483s, warning letters, OAI status), product/customer concentration, R&D capitalization policy, generic vs specialty mix.
- **IT services** — top-5/top-10 client concentration, vertical mix, attrition, sub-contracting cost trend, deal TCV. Margin trajectory is more about utilization and pyramid than pricing.
- **Real estate** — pre-sales vs revenue recognition gap, inventory days (unsold + WIP), customer advances, RERA litigation, debt vs cash flow timing.
- **Capital goods / industrials** — order book vs revenue (book-to-bill), execution cycle, working capital profile, customer concentration on large projects.
- **FMCG / consumer** — volume vs price-mix split, distribution depth, A&P intensity, premiumization trajectory, gross margin defensibility.
- **Cement / commodities** — utilization, regional pricing, fuel cost pass-through, freight, capex cycle stage.
- **Auto / auto-anc** — model cycle stage, OEM dependency for ancillaries, content per vehicle, EV transition exposure.

If the sector isn't on this list, identify the 3-4 metrics that drive economics in that sector before starting and emphasize those throughout.

`references/red-flags-india.md` has additional sector-specific red flag items — read those when relevant.

### 3. Extract the right things from each input

What to extract is document-specific. See `references/extraction-checklist.md` for the per-document checklist (AR, QR, concall, investor presentation). Read that file when you're about to start a deep analysis — it'll save you from missing standard items.

### 4. Run the management quality lens

Concall analysis is where most of the management read comes from. See `references/concall-analysis.md` for the full framework (consistency vs guidance, response patterns to tough questions, capital allocation language, tone shifts QoQ). Read this when you're processing concalls.

### 5. Run the red flags lens

India has its own flavor of governance issues. See `references/red-flags-india.md` for the checklist (promoter pledging, RPT patterns, auditor changes, CARO qualifications, contingent liab patterns, subsidiary opacity, working capital deterioration, ESOP/promoter remuneration, etc.). Read this for any thesis work — it's quick and catches things people miss.

### 6. Peer / sector comparison (if requested)

See `references/peer-comparison.md` for the framework. The basic move: pick 2-4 closest peers, compare on growth, margin trajectory, balance sheet health, management quality, capital allocation, and positioning. Tables work well here.

### 6.5. Run the valuation math (if CMP is available or user asks)

See `references/valuation-math.md` for the 6-step framework: per-share translation → trailing/forward ratios → multiple band → implied price ranges → quality-of-earnings adjustment → asymmetry vs CMP.

Required inputs (don't guess these): CMP, post-dilution share count, total debt, cash, TTM PAT, TTM EBITDA. If the user hasn't provided them, ask them to paste from `screener.in/company/<TICKER>/` — that's the canonical source.

Run this step by default when the user says "is it cheap", "is this a buy", "should I buy at ₹X", "fair value", or after the qualitative thesis is complete and the user provides a CMP. Skip cleanly if the user explicitly only wants the qualitative read.

### 7. Produce the master report

The master report is the primary output. Use the structure in `references/master-report-template.md` — it has the full template with section-by-section guidance. The default sections are:

1. **Snapshot** — one paragraph: what the company does, sector, scale, where it sits competitively
2. **Business model** — segments, revenue mix, customers, geography, what drives the P&L
3. **Growth drivers** — secular tailwinds, near-term catalysts, capex/capacity plans, runway
4. **Management assessment** — track record on guidance, capital allocation, candor, alignment with minority shareholders
5. **Financial trajectory (qualitative)** — direction of margins, working capital, debt, return ratios, capex intensity. Use 3-5 year direction, not point estimates.
6. **Red flags** — Indian governance lens, anything material from CARO/RPT/contingent liab
7. **Investment thesis** — bull case, base case, bear case, with the analytical stance: which case wins and why, with reasoning
8. **Valuation snapshot** — trailing & forward ratios, scenario forward EPS, multiple-band reasoning, implied price band, quality-of-earnings adjustment, asymmetry vs CMP. See `references/valuation-math.md`. Run only when CMP and the inputs are available; skip cleanly if not.
9. **Peer comparison** — only if requested or clearly needed; table format
10. **Verdict** — one of four discrete buckets (*Interesting — worth owning / Watchlist — wait for [X] / Avoid for now / Pass — structural concerns*) plus a one-line elevator-pitch summary and 1-2 things to watch in the next 1-2 quarters that would confirm or break the call. The verdict is about the **business**; the price-asymmetry call lives in section 8 and is allowed to disagree.

When the user asks for a smaller output (e.g., "just the red flags" or "just the management read"), produce only that section — don't force the full report.

## Output formats — when to use which

The user can ask for several output shapes. Default to the master report unless they specify otherwise.

| Ask | Format |
|-----|--------|
| "thesis on X", "should I invest", "deep dive" | Full master report (run valuation snapshot too if CMP is available) |
| "bull/bear case on X" | Bull / base / bear scorecard only (section 7) |
| "any red flags in this AR" | Red flags section only |
| "what did management say" / "concall takeaways" | Management assessment + key concall pulls |
| "compare X vs Y" | Peer comparison table + one-paragraph verdict per company |
| "checklist on X" | Numbered checklist covering segments, capex, working capital, debt, guidance vs delivery, etc. |
| "is it cheap" / "fair value" / "should I buy at ₹X" / "what's the math at this price" | Valuation snapshot only (section 8 of master report). See `references/valuation-math.md`. Preface with a 2-line company snapshot so the inputs aren't free-floating. |

The "combined master report" requested format is the default — it includes everything above as sections, with peer comparison appended when the user gave you peers to compare against.

## Common failure modes to avoid

**Memorizing instead of reading.** The biggest LLM trap on this task: producing a thesis that recites general knowledge about the company rather than reading what's actually in the uploaded documents. If a 2024 AR has been uploaded, the analysis must reflect what's in it — including how it differs from older general impressions of the company. Symptoms of this failure: numbers that don't match the filings, references to events the documents don't discuss, missing a recent strategic shift the AR clearly flags. When in doubt, cite the page or section.

**Quoting too much from the documents.** Lift specific numbers and 1-2 short phrases per section. Do not reproduce paragraphs. Paraphrase management commentary.

**Treating guidance as fact.** Indian managements are often optimistic on concalls. Always flag: "Management is guiding 18% growth — they delivered 11% on a similar guide last year, so weight this accordingly."

**Missing the segment story.** A company with 3 segments is rarely a single story. Break out at least the largest 2-3 segments — growth, margin, capital intensity often diverge sharply across them.

**Skipping the auditor's report.** CARO 2020 comments, emphasis-of-matter paragraphs, and qualifications are gold. Always check.

**Generic governance commentary.** Don't say "promoter pledging is a concern" without checking the actual pledge level and trajectory. Either it's material (>20% pledged or rising) or it isn't — say which.

**Bothsidesism.** After laying out the case, take a side. "I think the bull case wins because [X, Y]" is more useful than "the truth probably lies somewhere in between."

## When uploads are big

Annual reports are often 300+ pages and won't be productive to read cover-to-cover. Strategy:

1. **Start at the table of contents.** Most ARs have a TOC near the front, sometimes with page numbers for each note. Use it to navigate, not to read sequentially.
2. **Priority sections to actually read** (in roughly this order):
   - MD&A / Management Discussion & Analysis (15-30 pages)
   - Director's Report — strategic priorities, capex announcements
   - Segment reporting note in financial statements
   - Related party transactions note
   - Contingent liabilities note
   - Auditor's Report + CARO 2020 annexure
   - Subsidiary list (Form AOC-1) for material subs
   - Notes on borrowings, ESOPs, managerial remuneration
3. **Skip:** CSR/sustainability sections (unless specifically asked), board profile pages with photos, glossy cover/marketing pages, historical highlights, repetitive boilerplate, notice of AGM and proxy forms.
4. **Budget:** aim to read ~10-15 sections totaling ~80-120 pages of actual content from a 300-page AR. Reading more than that is usually wasted effort; reading less means missing things.
5. **Concall transcripts:** prioritize the Q&A section over prepared remarks. Prepared remarks are scripted and curated; Q&A is where signal lives.
