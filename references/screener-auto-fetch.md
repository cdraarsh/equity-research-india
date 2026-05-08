# Screener Auto-Fetch Playbook

When the user names an Indian listed stock (by name or ticker) without uploading PDFs, **do not ask for uploads**. Auto-fetch the right set of filings from `screener.in/company/<TICKER>/` instead. This file is the standing playbook for what to pull, in what order, and how to adapt by company profile.

## 1. Trigger

Apply this playbook whenever:
- The user names an Indian listed company by ticker or name AND
- No PDFs are attached to the conversation AND
- The ask is substantive enough to warrant the skill (thesis, deep dive, red flags, management read, "should I invest", peer compare, etc.)

If the user has already uploaded files, skip this playbook and use the uploads — they took the trouble to attach for a reason.

## 2. Confirmation rule (always confirm before fetching)

Before pulling any PDFs, list what you're about to fetch and wait for the user's go-ahead. Format:

> Fetching from `screener.in/company/<TICKER>/`:
> - FY25 Annual Report
> - FY24 Annual Report
> - Last 4 concall transcripts (May 2025 → Apr 2026)
> - Q4 FY26 investor presentation
> - Screener page scrape (10-yr financials, quarterly trend, shareholding)
>
> Proceed? Or adjust the set?

Reasons to confirm rather than silent-fetch:
- Saves wasted fetches if the user wants a narrower scope ("just red flags" → don't pull 4 concalls)
- Lets the user add a peer ticker before you start
- Surfaces the Tier-3 judgment calls (e.g. "should I also pull the DRHP?") explicitly

## 3. Fetch sequence

1. `WebFetch` the Screener page first to enumerate available files. The page lists ARs, concall transcripts, investor presentations, and announcements with their actual URLs (which point to NSE/BSE archives).
2. Decide the tier set based on company profile (§5).
3. `WebFetch` each PDF in the set. If a fetch fails or 404s, note it in the output's source-of-inputs line and continue — do not block.
4. Scrape the Screener page itself for the 10-yr quant tables (P&L, BS, CF, ratios, quarterly trend, shareholding). No login needed — these are rendered in the public HTML.

## 4. The standard set

### Tier 1 — always fetch

- **Latest Annual Report** (richest single document)
- **Latest concall transcript** (most recent management voice + analyst Q&A)
- **Latest investor presentation** (the curated narrative — what management wants you to see)
- **Screener page scrape** — 10-yr P&L/BS/CF, quarterly trend, ratios, shareholding pattern. No file download; just `WebFetch` the company URL.

### Tier 2 — fetch when company has the history

- **Prior-year AR** (promise-vs-delivery check — single highest-signal management test)
- **Up to 3 prior concall transcripts** (narrative consistency over time, guidance vs delivery)

### Tier 3 — fetch only when relevant

- **Promoter lock-in / SDD updates** — only if listed <2 years OR on SME board (lock-in expiry can create supply overhang)
- **Monthly/quarterly business updates** — only for cyclicals or commodity-linked names where near-term momentum matters
- **DRHP / RHP** — only for IPOs of the last ~24 months (richer than the limited AR history available)
- **Specific announcements** — auditor change, RPT-heavy disclosures, regulatory actions — only pull if Tier 1 reading flagged a concern that needs documentary backing

## 5. Size-adaptive weighting

The standard set adapts to the company's profile. This is the core "no matter the size" rule:

| Profile | Adjustments |
|---|---|
| **Mature large-cap** (10+ yrs listed, well-tracked) | AR-arc heavy: 3 ARs (latest + T-1 + T-2), 4 concalls. Skip lock-in/monthly noise. |
| **Mid-cap** (5–10 yrs listed) | Standard Tier 1 + Tier 2. DRHP irrelevant. |
| **Recent IPO / SME** (≤2 yrs listed) | Pull DRHP from BSE/NSE archives (richer than the thin AR history). Lean concall-heavy — that *is* the management track record. Lock-in update matters. |
| **Cyclical / commodity** (cement, steel, sugar, chemicals, agri) | Add monthly sales updates and last 6 quarters of QRs. AR history less informative than near-term trend. |
| **Banks / NBFCs** | Investor presentation matters more than usual (asset-quality slides, CAR, NIM walk). Add latest credit rating rationale if Screener links it. |
| **Pharma** | Add USFDA inspection disclosures filed with exchanges (483s, warning letters) when present. |

If the sector isn't on this list, default to standard Tier 1 + Tier 2 and adjust during reading.

## 6. Skip list (don't waste a fetch)

These appear on Screener but rarely add signal:
- Structural Digital Database (SDD) certificates
- Notice of AGM, postal ballot, proxy forms
- Voting results (unless contested)
- Routine board meeting intimations
- Compliance certificates under standard SEBI regulations
- Newspaper publication of results
- Trading window closure notifications

Pull them only if a specific thesis question requires the documentary trail.

## 7. Budget & failure modes

- **Cap at ~8 PDFs per analysis.** Signal-density flattens fast — beyond 8 documents you're re-reading the same story.
- **If Screener returns nothing useful** (rare — usually only for very illiquid SMEs), fall back to BSE corporate filings or the company's investor relations page. Note the substitution.
- **If a fetch fails**, name it in the report's source-of-inputs line. Do not silently substitute a web search for what should have been a primary filing.
- **If the company is not on Screener at all** (extremely rare), tell the user and ask whether they want to provide files manually.

## 8. Source-labeling rule

Every claim in the final report must trace to a source. Use these tags inline or in a short legend at the top of the report:

- `[AR-FY25]` — Annual Report for the fiscal year noted
- `[Concall-Q4FY26]` — Concall transcript for the quarter noted
- `[IP-Q3FY26]` — Investor presentation for the quarter noted
- `[Screener-quant]` — 10-yr table or ratio scraped from the Screener page
- `[Web-search]` — Used only for very recent news/regulatory actions postdating the latest filing
- `[Inferred]` — Analytical inference, not directly stated in any source

This preserves the existing operating principle that the user always knows what came from primary filings vs. derived analysis.

## 9. Folder structure & caching

Save fetched files to a per-ticker folder so repeat analyses don't re-fetch.

### Location

`~/Documents/equity-research/<TICKER>/`

### Layout

```
~/Documents/equity-research/<TICKER>/
├── INDEX.md
├── screener-snapshot.md          # scraped 10-yr financials, ratios, shareholding
├── annual-reports/
│   ├── AR-FY25.pdf
│   └── AR-FY24.pdf
├── concalls/
│   ├── concall-Q4FY26-2026-04-27.pdf
│   └── concall-Q3FY26-2026-02-06.pdf
├── presentations/
│   ├── IP-Q4FY26-2026-04-21.pdf
│   └── IP-Q3FY26-2026-01-30.pdf
└── announcements/
    ├── promoter-lockin-2026-04-25.pdf
    └── monthly-sales-2026-04.pdf
```

### Naming conventions

- ARs: `AR-FY<YY>.pdf`
- Concalls: `concall-Q<N>FY<YY>-<YYYY-MM-DD>.pdf` (date = filing/call date)
- Presentations: `IP-Q<N>FY<YY>-<YYYY-MM-DD>.pdf`
- Announcements: `<short-type>-<YYYY-MM-DD>.pdf`
- Screener page scrape: `screener-snapshot.md` (always overwrite — latest pull wins)

### INDEX.md

A markdown index at the ticker root, regenerated on every fetch. Minimum content:

```
# <Company> (<TICKER>) — File Index
Last fetched: <YYYY-MM-DD>
Screener URL: https://www.screener.in/company/<TICKER>/

| File | Source URL | Source tag |
|---|---|---|
| annual-reports/AR-FY25.pdf | <NSE archive URL> | [AR-FY25] |
| concalls/concall-Q4FY26-2026-04-27.pdf | <NSE archive URL> | [Concall-Q4FY26] |
| ...
```

INDEX.md is the source of truth for what's been pulled — use it (not a directory listing) to decide cache state.

### Caching behavior

Before any fetch, check `~/Documents/equity-research/<TICKER>/INDEX.md`:

- **Exists & `Last fetched` ≤7 days old** → use cached files. Tell the user *"Using files cached on <date>; re-fetch?"* and only re-pull if asked or if Screener now lists a filing newer than the latest in INDEX.
- **Exists & >7 days old** → re-list the Screener page, delta-fetch only what's new, update INDEX.
- **Doesn't exist** → full fetch per §3, then create the folder structure and write INDEX.md.

The 7-day window is heuristic — Indian listed companies file rarely outside results season, so day-to-day staleness is unlikely. Override on explicit user request ("re-fetch", "use latest").
