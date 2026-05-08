# Master Report Template

This is the default output structure for a full thesis. Treat it as a frame, not a rigid form — if a section has nothing material to say for a particular company, condense it; if a section has unusual depth, expand it.

The report is opinionated. The qualitative core (sections 1–7, 9, 10) doesn't do DCF or single-point fair value. Section 8 (Valuation snapshot) does basic ratio-based valuation with scenario bands when a CMP and the required inputs are available — it produces a price band and asymmetry call, not a target price. Skip section 8 cleanly if no CMP is available.

## Format

Markdown. Use H2 (`##`) for sections. Tables for comparisons and trajectory. Keep section lengths roughly proportional to importance (don't write 3 paragraphs on Snapshot and 1 paragraph on Investment Thesis).

## Section template

---

### 1. Snapshot

One paragraph. What the company does, sector, rough scale (small/mid/large cap qualitatively or by revenue scale), competitive position in 1-2 sentences. End with the one-line essence of why this name is interesting (or not).

---

### 2. Business model

What drives the P&L. Cover:
- Segments and their revenue mix (% of total)
- Customer profile (B2B/B2C, concentrated/diversified, domestic/export)
- What they actually sell, in plain English
- Capital intensity of the model
- Where the moat is (or isn't): brand, distribution, scale, switching cost, regulatory, network effect

If the company has 3+ segments, briefly characterize each — they often have very different economics.

---

### 3. Growth drivers

Forward-looking section, but grounded in management commentary and observable trends. Cover:
- Secular tailwinds the business is exposed to (and how directly)
- Near-term catalysts: new capacity coming online, new product launches, new geographies, regulatory tailwinds
- Multi-year levers: premiumization, distribution expansion, market share gain in fragmented industry, etc.
- How much of the growth is in management's control vs dependent on cycles / external factors
- Realistic vs aspirational separation — flag any stated runway that looks unrealistic

---

### 4. Management assessment

The qualitative read of the people running the business. Cover:
- Guidance vs delivery track record over last 4-8 quarters (cite specific examples)
- Capital allocation history — what have they done with cash? Was it value-creating?
- Candor on concalls — how do they handle tough questions, do they own misses?
- Compensation alignment with minority shareholders
- Promoter shareholding behavior (selling/buying/pledging)
- Family/governance dynamics if relevant

Take a clear stance: "Management is high quality" or "Management is a meaningful concern" or "Mixed — strong on operations, weak on capital allocation." Don't hedge.

---

### 5. Financial trajectory (qualitative)

Direction over the last 3-5 years on:
- Revenue growth (and what's driving it — volume, price, mix)
- Gross margin trajectory
- EBITDA margin trajectory
- Operating cash flow vs profit (earnings quality)
- Debt direction
- Working capital days
- Return ratios (ROCE, ROE) direction
- Capex intensity

A simple table works well here:

| Metric           | FY22 → FY26 direction       | Comment                           |
|------------------|-----------------------------|-----------------------------------|
| Revenue growth   | Steady ~12-14%              | Volume-led, price taken once      |
| EBITDA margin    | 14% → 18% (steadily up)     | Operating leverage + premium mix  |
| Net debt/equity  | 0.4 → 0.1                   | FCF used to pay down              |
| ROCE             | 16% → 24%                   | Both margin and turnover up       |

No future projections — just direction-of-travel from disclosed numbers.

---

### 6. Red flags

Material governance / quality issues only. For each:
- The specific issue (with quantum from the filings)
- Materiality (% of revenue, profit, or net worth as applicable)
- Trajectory (one-time, recurring, escalating?)
- What would resolve it / what to watch

If there's nothing material, say so explicitly: "No material red flags identified. Routine items: [list briefly], none of which are concerning at current quanta." Don't manufacture concerns.

---

### 7. Investment thesis

The opinionated section — the analytical stance with full reasoning. Three subsections plus the stance:

**Bull case.** What has to be true for this to be a great investment over 3-5 years. List the 2-4 things that need to play out, with how much weight each carries.

**Base case.** What's most likely given everything above. Often the bull case adjusted for realistic delivery rates, with one or two of the upside items not playing out.

**Bear case.** What breaks the story. Specific, not generic. "Customer concentration risk if top 2 clients renegotiate terms" beats "macro slowdown."

**The analytical stance.** End with which case you lean toward and the reasoning — typically a paragraph or two. Take a side. Identify what evidence pushed you there. Note what specific developments would force you to update toward another case. This is the long-form reasoned stance; section 10's verdict will compress it into a discrete bucket.

---

### 8. Valuation snapshot (only if CMP and the required inputs are available)

Use the framework in `valuation-math.md`. Skip cleanly if the user hasn't provided a current market price and the input fundamentals (debt, cash, share count post-dilution, TTM PAT/EBITDA), or if the user explicitly only wants the qualitative read.

When run, this section produces:
- An inputs block (CMP, market cap, shares post-dilution, debt, cash, TTM PAT/EBITDA, with date and source)
- Trailing ratios table (PE, EV/EBITDA, P/B, ROCE, ROE, with sector median where useful)
- Forward EPS scenarios (bear / base / bull) with the full P&L walk for each — Revenue × EBITDA% → EBITDA → less D&A and Finance cost → PBT → less Tax → PAT → ÷ shares
- Multiple band reasoning (one paragraph anchoring multiples to peers + growth + quality discounts)
- Implied price band table (multiple × EPS for each scenario, with % vs CMP)
- Quality-of-earnings adjustment (reconstruct owner's earnings; flag any material PAT-vs-cash gap)
- Asymmetry call (one or two sentences — what the math says about price vs fundamentals)

The asymmetry call here is about **price** and is allowed to disagree with section 10's **business** verdict. When they disagree, name the disagreement explicitly — that nuance is often the most valuable part of the analysis.

---

### 9. Peer comparison (only if requested or clearly needed)

Use the framework in `peer-comparison.md`. Table + one-paragraph verdict per company.

---

### 10. Verdict

The compressed elevator-pitch version of section 7, focused on the **business** call (not the price call — that lives in section 8). Two parts:

**The bucket.** Pick exactly one — these are deliberately discrete to force a stance:

- **Interesting — worth owning.** Conviction that the bull/base case is sound. Story is real, management is delivering, no structural concerns.
- **Watchlist — wait for [X].** The story has merit but a specific catalyst or de-risking event needs to play out first. Always name the [X] (e.g., "wait for capex digestion to show in FY27 numbers", "wait for resolution of GST dispute", "wait for next 2 concalls to confirm margin trajectory").
- **Avoid for now.** Story is unconvincing or the bear case is more probable than the bull case at present, but no permanent disqualifiers — could become interesting if the situation changes.
- **Pass — structural concerns.** Governance, business model, or capital allocation issues that don't get fixed by a quarter or two. A skip regardless of price.

**The one-line story.** A single sentence capturing what this company is and the essence of the call. Then 1-2 specific things to watch over the next 1-2 quarters that would confirm or break the verdict.

Example:

> **Watchlist — wait for the FY27 capex digestion cycle.**
>
> A high-quality consumer franchise mid-way through a heavy capex cycle that will compress returns for 6-8 quarters before the new capacity contributes. Watch: (1) capex spend pace vs. the Rs 1,200 cr guidance for FY27, and (2) gross margin stability through input cost volatility — anything below 38% would be a yellow flag.

---

### One-line caveat (always include at the end)

End the report with this exact line, on its own:

> *This is qualitative analysis based on disclosed filings, not investment advice or a fair-value call. Do your own work before acting.*

---

## Avoiding hallucinated numbers

The single biggest failure mode in producing a report like this is making up numbers that sound plausible. Rules:

- Every number in the report should trace to a specific filing or commentary you actually read. If you can't say which filing it came from, drop it.
- "Approximately" and rounded numbers from the actuals are fine ("revenue around Rs 12,000 cr"). Inventing precise numbers ("revenue of Rs 12,347 cr") because it sounds authoritative is not.
- If you remember a number from general knowledge but the documents don't confirm it, flag it: "general impression is around 15% margin, but the uploaded AR doesn't break this out cleanly — would need the latest QR for confirmation."
- Direction-of-travel claims ("margin has been expanding") need at least 2 data points from the filings to support. One-point claims are usually unsupported.

---

## Length guidance

A full master report on a single company typically lands around 1500-3000 words. With peer comparison added, 2500-4500 words. Don't pad — if the analysis is concise, that's a feature.

If the user asks for a shorter version ("quick take", "tl;dr", "in 500 words"), produce the Verdict section + Investment Thesis section only.
