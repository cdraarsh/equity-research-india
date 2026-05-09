# equity-research-india

A [Claude Code](https://docs.claude.com/en/docs/claude-code) skill for building qualitative investment theses on Indian listed companies — annual reports, quarterly results, and earnings concall transcripts in, structured opinion out, with an Indian governance lens (SEBI/MCA disclosures, CARO 2020, related party transactions, promoter pledging, contingent liabilities, etc.).

The qualitative core covers **business quality, management quality, growth runway, and red flags**. An optional **valuation overlay** runs disciplined ratio-based math (PE, EV/EBITDA, P/B, scenario-based forward EPS, implied price band, quality-of-earnings adjustment, asymmetry vs CMP) when a current market price is provided. It stops short of single-point DCF intrinsic values or "buy at exactly ₹X" targets — those imply false precision.

---

## Table of contents

- [What it does](#what-it-does)
- [What it does NOT do](#what-it-does-not-do)
- [Installation](#installation)
- [Setup (helper scripts)](#setup-helper-scripts)
- [When the skill triggers](#when-the-skill-triggers)
- [Architecture](#architecture)
- [The fetch & analysis pipeline](#the-fetch--analysis-pipeline)
- [Helper scripts](#helper-scripts)
  - [`scripts/parse_screener.py`](#scriptsparse_screenerpy)
  - [`scripts/slice_pdf.py`](#scriptsslice_pdfpy)
- [Subagent extraction (parallel Haiku)](#subagent-extraction-parallel-haiku)
- [Output](#output)
- [Source labels](#source-labels)
- [Repo structure](#repo-structure)
- [Example prompts](#example-prompts)
- [Caveats & known limits](#caveats--known-limits)
- [License](#license)

---

## What it does

- **Auto-fetches filings from Screener.in when given a ticker** — annual reports, concall transcripts, investor presentations, and a structured 10-yr financials parse. No PDF uploads required. Tier-based selection adapts to company size (mature large-cap → recent SME IPO).
- **Falls back through 3 source tiers** if Screener doesn't list a filing: Screener → official BSE/NSE search → third-party aggregators (clearly labeled).
- **Slices PDFs into per-section extracts** before reading, so the model isn't fed 50–80k tokens of boilerplate every query.
- **Extracts in parallel via Haiku subagents** (when available) for the mechanical reads — CARO findings, RPT facts, contingent liabilities, AOC-1 subsidiaries, ESOP/managerial remuneration, concall topic-keying.
- **Cross-references what management said vs what they delivered** — pulls guidance from prior concalls and checks against the latest results.
- **Flags governance issues** through an Indian lens — RPT patterns, auditor remarks, CARO qualifications, contingent liab trajectory, promoter pledging, subsidiary opacity, ESOP dilution, working capital deterioration, auditor changes.
- **Produces an opinionated bull/bear thesis** with explicit conviction level (Interesting / Watchlist / Avoid / Pass).
- **Source-labels every claim** so the user always knows what came from primary filings vs. derived analysis.
- **Caches per-ticker** for 7 days to avoid re-fetching during iterative work.
- **Optional valuation snapshot** when CMP is provided: trailing & forward multiples, scenario-based forward EPS (full P&L walk), multiple-band reasoning anchored to peers/growth/quality discounts, implied price band, owner's-earnings reconstruction, asymmetry call vs CMP.

## What it does NOT do

- DCF / DDM / single-point intrinsic value modeling
- "Buy at exactly ₹X" target prices or position-sizing advice
- Technical analysis or F&O strategies
- IPO grey market chatter or mutual fund picks
- US / global equities (Indian listed companies only)

---

## Installation

Drop the folder into your Claude Code skills directory:

```bash
git clone https://github.com/cdraarsh/equity-research-india.git ~/.claude/skills/equity-research-india
```

Or, if `~/.claude/skills/` already exists:

```bash
cd ~/.claude/skills
git clone https://github.com/cdraarsh/equity-research-india.git
```

Restart Claude Code (or start a new session) and the skill will auto-trigger on relevant prompts.

## Setup (helper scripts)

The skill itself works as a pure markdown skill — no setup required. The two helper scripts (`parse_screener.py`, `slice_pdf.py`) are technically optional but **strongly recommended** for non-trivial deep-dives. Without them, the skill falls back to slower, more expensive markdown-based extraction.

### One-time install

```bash
cd ~/.claude/skills/equity-research-india

# Python venv with beautifulsoup4 (for scripts/parse_screener.py)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# pdftotext (for scripts/slice_pdf.py) — macOS
brew install poppler

# Optional: ocrmypdf — for scanned/image-based PDFs (older ARs, some BSE archive scans)
brew install ocrmypdf
```

The scripts then run as:

```bash
.venv/bin/python scripts/parse_screener.py <TICKER>
.venv/bin/python scripts/slice_pdf.py <pdf>
```

When the skill auto-runs them via the workflow, it picks up the venv automatically from the repo's `.venv/`.

---

## When the skill triggers

The skill activates when you:

- Upload an Indian company's AR / QR / concall PDF and ask for analysis
- Name an Indian listed stock with words like *thesis*, *deep dive*, *should I invest*, *is it a buy*, *analyze*, *what's the case for / against*
- Ask for peer or sector comparison within Indian markets
- Ask about red flags, governance, audit issues, or management quality
- Drop a 100+ page PDF that looks like an annual report or concall transcript (heuristic match)

---

## Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │  User: "Thesis on ABREL"                    │
                    └──────────────────┬──────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │  Step 0: confirm file set                           │
            │  Step 1: fetch (3-tier source fallback)             │
            │     Tier 1: screener.in/company/<TICKER>/           │
            │     Tier 2: WebSearch site:bseindia.com / nseindia  │
            │     Tier 3: WebSearch trendlyne, marketscreener     │
            └──────────────────────────┬──────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │  scripts/parse_screener.py <TICKER> --save          │
            │     → ~/Documents/equity-research/<TICKER>/         │
            │       screener-data.json                            │
            │       (top ratios, P&L/BS/CF, shareholding,         │
            │        AR URLs, concall URLs, ratings, news, ...)   │
            └──────────────────────────┬──────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │  Step 2: download PDFs (curl)                       │
            │     ARs, concalls, investor presentations           │
            └──────────────────────────┬──────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │  Step 3: scripts/slice_pdf.py <pdf>                 │
            │     → extracts/AR-FY25-mdna.txt, -caro.txt,         │
            │       -rpt.txt, -contingent-liab.txt, -aoc1.txt,    │
            │       -esop.txt, -segments.txt, -borrowings.txt     │
            │     → concall-Q4FY26-opening-remarks.txt            │
            │       concall-Q4FY26-qa/qXX-Analyst-Firm.txt        │
            │       concall-Q4FY26-index.json                     │
            └──────────────────────────┬──────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │  Step 4: structured extraction                      │
            │     Default: parallel Haiku subagents               │
            │       → CARO, RPT, contingent-liab, AOC-1, ESOP,    │
            │         concall topic-keying (returns strict JSON)  │
            │     Fallback: main session reads extracts inline    │
            └──────────────────────────┬──────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │  Step 5: synthesis (main session)                   │
            │     Sector lens → red flags → management quality    │
            │     → financial trajectory → bull/bear thesis       │
            │     → optional valuation snapshot if CMP provided   │
            └──────────────────────────┬──────────────────────────┘
                                       │
                                       ▼
                              Master report
            (snapshot, business model, growth drivers,
             management assessment, red flags, thesis,
             valuation snapshot, peer comparison, verdict)
```

## The fetch & analysis pipeline

### 1. Confirmation step

The skill always lists what it's about to fetch and waits for go-ahead — it never silent-fetches. This catches narrow asks ("just red flags" → skip 4 concalls) and surfaces Tier-3 judgment calls (DRHP for recent IPOs).

### 2. Tier-based file selection

What gets pulled depends on company profile (`references/screener-auto-fetch.md`):

| Profile | Adjustments |
|---|---|
| Mature large-cap (10+ yrs listed, well-tracked) | AR-arc heavy: 3 ARs (latest + T-1 + T-2), 4 concalls. Skip lock-in/monthly noise. |
| Mid-cap (5–10 yrs listed) | Standard Tier 1 + Tier 2. DRHP irrelevant. |
| Recent IPO / SME (≤2 yrs listed) | Pull DRHP from BSE/NSE archives. Lean concall-heavy. Lock-in updates matter. |
| Cyclical / commodity (cement, steel, sugar, chemicals, agri) | Add monthly sales updates and last 6 quarters of QRs. |
| Banks / NBFCs | Investor presentation matters more (asset-quality, CAR, NIM walk). Add credit rating rationale. |
| Pharma | Add USFDA inspection disclosures (483s, warning letters) when present. |

### 3. Source fallback (when Screener doesn't list a file)

The 3-tier fallback (`references/screener-auto-fetch.md` §3a):

- **Source Tier 1**: `screener.in/company/<TICKER>/consolidated/` → standalone if consolidated 404s
- **Source Tier 2**: `WebSearch` restricted to `bseindia.com`, `nseindia.com`, company IR page; labeled `[BSE-direct]` / `[NSE-direct]`
- **Source Tier 3**: `WebSearch` against trendlyne, marketscreener, alphaspread, gurufocus; mandatory `[Third-party]` label

### 4. Per-ticker folder layout

```
~/Documents/equity-research/<TICKER>/
├── INDEX.md                              # Source-of-truth file list + cache date
├── screener-data.json                    # Structured Screener parse (primary)
├── screener-snapshot.md                  # Legacy markdown (fallback only)
├── annual-reports/
│   ├── AR-FY25.pdf
│   └── AR-FY24.pdf
├── concalls/
│   ├── concall-Q4FY26-2026-04-27.pdf
│   └── concall-Q3FY26-2026-02-06.pdf
├── presentations/
│   ├── IP-Q4FY26-2026-04-21.pdf
│   └── IP-Q3FY26-2026-01-30.pdf
├── announcements/
│   └── auditor-change-2026-05-08.pdf
└── extracts/                             # Output of slice_pdf.py
    ├── AR-FY25-mdna.txt
    ├── AR-FY25-caro.txt
    ├── AR-FY25-rpt.txt
    ├── AR-FY25-contingent-liab.txt
    ├── AR-FY25-aoc1.txt
    ├── AR-FY25-esop.txt
    ├── AR-FY25-segments.txt
    ├── concall-Q4FY26-opening-remarks.txt
    ├── concall-Q4FY26-qa/
    │   ├── q01-Sneha-Jain-Nomura.txt
    │   ├── q02-Rohit-Gupta-Emkay.txt
    │   └── ...
    └── concall-Q4FY26-index.json
```

### 5. Caching

7-day cache window, controlled by `Last fetched:` in `INDEX.md`. Override on explicit user request ("re-fetch", "use latest").

---

## Helper scripts

### `scripts/parse_screener.py`

Generic deterministic HTML parser for `screener.in/company/<TICKER>/`. Works across all sectors (tested on Realty, IT, Banks, Industrial Minerals, manufacturing). Stdlib + `beautifulsoup4`.

```bash
.venv/bin/python scripts/parse_screener.py ABREL --save
# → writes ~/Documents/equity-research/ABREL/screener-data.json (~33KB)

.venv/bin/python scripts/parse_screener.py TCS --standalone --out tcs.json
.venv/bin/python scripts/parse_screener.py --html /tmp/local.html  # parse local file (testing)
```

**Output shape (16 top-level keys):**

```json
{
  "ticker": "ABREL",
  "company_id": "613",
  "is_consolidated": true,
  "meta": {
    "name": "Aditya Birla Real Estate Ltd",
    "sector_taxonomy": {
      "broad_sector": "Consumer Discretionary",
      "sector": "Realty",
      "broad_industry": "Realty",
      "industry": "Residential, Commercial Projects"
    },
    "benchmarks": ["BSE 500", "Nifty 500", "Nifty Realty", "Nifty Smallcap 100", ...],
    "exchange_codes": {"bse": "500040", "nse": "ABREL"},
    "website": "http://www.centurytextind.com",
    "about": "...",
    "key_points": "..."
  },
  "key_ratios": {
    "market_cap":     {"value": 16596, "unit": "inr_cr", "raw": "₹ 16,596 Cr."},
    "current_price":  {"value": 1486,  "unit": "inr"},
    "high_low":       {"value": 2538, "value_2": 1080, "unit": "inr"},
    "stock_p_e":      {"value": null, "unit": null},
    "book_value":     {"value": 331,   "unit": "inr"},
    "dividend_yield": {"value": 0.13,  "unit": "pct"},
    "roce":           {"value": -4.26, "unit": "pct"},
    "roe":            {"value": -7.43, "unit": "pct"},
    "face_value":     {"value": 10.0,  "unit": "inr"}
  },
  "pros_cons": {
    "pros": ["Company has been maintaining a healthy dividend payout of 23.2%"],
    "cons": [
      "Stock is trading at 4.48 times its book value",
      "Working capital days have increased from 1,675 days to 3,916 days",
      ...
    ]
  },
  "compounded_growth": {
    "compounded_sales_growth": {"10_years": null, "5_years": -31, "3_years": -53, "ttm": -67},
    "stock_price_cagr":        {"10_years": 18, "5_years": 26, "3_years": 24, "1_year": -19},
    "return_on_equity":        {"10_years": 20, "5_years": 0, "3_years": -3, "last_year": -7},
    ...
  },
  "quarterly":            { "dates": [...13 quarters...], "rows": {"Sales": [...], "OPM %": [...], ...} },
  "pl_yearly":            { "dates": [...10 years...],   "rows": {...} },
  "balance_sheet_yearly": { "dates": [...10 years...],   "rows": {"Equity Capital": [...], "Reserves": [...], "Borrowings": [...], ...} },
  "cash_flow_yearly":     { "dates": [...10 years...],   "rows": {"Cash from Operating Activity": [...], "Free Cash Flow": [...], ...} },
  "ratios_yearly":        { "dates": [...10 years...],   "rows": {"Debtor Days": [...], "Cash Conversion Cycle": [...], "ROCE %": [...]} },
  "shareholding_quarterly": { "dates": [...12 q...], "rows": {"Promoters": [...], "FIIs": [...], "DIIs": [...], ...} },
  "shareholding_yearly":    { same shape },
  "annual_reports": [
    {"fy": 2025, "url": "https://www.bseindia.com/...", "source": "BSE"},
    {"fy": 2024, "url": "...", "source": "BSE"},
    ...15 entries
  ],
  "concalls": [
    {
      "date": "Feb 2026",
      "transcript_url": "https://www.bseindia.com/...",
      "ppt_url": "https://www.bseindia.com/...",
      "ai_summary_url": "https://www.screener.in/concalls/summary/23081792/",
      "recording_url": "https://youtu.be/..."
    },
    ...
  ],
  "credit_ratings": [
    {"agency": "CARE",   "date_text": "10 Apr from care",   "url": "https://www.careratings.com/..."},
    {"agency": "CRISIL", "date_text": "4 Mar from crisil", "url": "https://www.crisil.com/..."}
  ],
  "announcements": [
    {
      "title": "Announcement under Regulation 30 (LODR)-Appointment of Statutory Auditor/s",
      "summary": "Board recommends Singhi & Co. as statutory auditor for FY2026-27 to FY2030-31.",
      "url": "https://www.bseindia.com/...",
      "days_ago": 2
    },
    ...
  ]
}
```

**Why deterministic parsing matters:**
- Numbers are exact (no rounding from markdown extraction)
- 10× cheaper than re-running an LLM extraction every session
- Sector taxonomy auto-fires the right analytical lens
- All 15 years of AR URLs available without re-fetch
- Recent announcements with AI-generated summaries surface auditor changes / dividend events without web search
- Pros/cons block gives Screener's own machine-generated red flags as a free baseline

**Failure modes:**
- HTML structure changes → script degrades gracefully (failed sections become null, others still populate)
- Premium-gated sections (the "Insights" block with the "Log in to view" placeholder) → skipped
- Network failure / 404 → falls back to `WebFetch` markdown extraction per the playbook

### `scripts/slice_pdf.py`

Stdlib-only (no pip deps) PDF slicer. Auto-detects AR vs concall from filename.

```bash
.venv/bin/python scripts/slice_pdf.py ~/Documents/equity-research/ABREL/annual-reports/AR-FY25.pdf
.venv/bin/python scripts/slice_pdf.py <pdf> --type concall    # force type
.venv/bin/python scripts/slice_pdf.py <pdf> --dry-run         # preview boundaries without writing
```

**For ARs** — runs `pdftotext -layout`, finds heading-shaped lines for ~10 standard sections (MD&A, Director's Report, Auditor Report, CARO, Segments, RPT, Contingent Liabilities, Borrowings, AOC-1, ESOP/Remuneration), `awk`-extracts each to `<TICKER>/extracts/AR-FY25-<section>.txt`. Always emits a JSON summary listing every section written, line ranges, whether each match was a confident heading-shaped hit (`heading_match: true`) or a fallback to last text mention, and any `sections_suspicious` (oversized) or `sections_missing` so you know where to verify.

**For concalls** — splits at the Q&A boundary, then per-analyst turns. Builds a topic-keyed `index.json` with empty `topics` arrays that the running model fills in by reading each turn (~500 tokens × 15 turns = one cheap pass).

**Skip rules** — anything <30 pages is fed whole; slicing isn't worth the overhead. Single-quarter QRs and most investor presentations don't need slicing.

---

## Subagent extraction (parallel Haiku)

When the running environment exposes a Task/Agent tool with Haiku-class model selection (e.g., Claude Code), the skill defaults to delegating mechanical extractions to parallel subagents — strict JSON schemas in, structured facts out. See `references/subagent-extraction.md` for full schemas, parallelism cap (10 in flight), retry logic, and merge protocol.

**Delegated:**
- CARO findings (audit opinion, KAMs, qualified clauses, auditor changes)
- RPT facts (parties, relationships, amounts, % of revenue/PAT)
- Contingent liabilities (disputes, quantum, status)
- AOC-1 subsidiaries (name, country, holding %, financials, materiality)
- ESOP / managerial remuneration (pool size, top-N pay, promoter % of PAT)
- Concall topic-keying (per-turn 3–5 word tags)

**Kept in main session** (synthesis-heavy, smaller models do this poorly):
- MD&A reading + business model synthesis
- Concall management-quality read (tone shifts, deflections, guidance vs delivery)
- Master report writing & verdict
- Bull / base / bear thesis stance

**Falls back to inline reading** when the Task tool isn't available, or when a subagent returns invalid JSON twice for a specific extraction.

---

## Output

The default output is the **master report** (template in `references/master-report-template.md`), with these sections:

1. **Snapshot** — what the company does, sector, scale, competitive position
2. **Business model** — segments, revenue mix, customers, geography, P&L drivers
3. **Growth drivers** — secular tailwinds, near-term catalysts, capex/capacity, runway
4. **Management assessment** — track record on guidance, capital allocation, candor
5. **Financial trajectory (qualitative)** — direction of margins, working capital, debt, return ratios
6. **Red flags** — Indian governance lens; CARO, RPT, contingent liab, ESOP, pledging
7. **Investment thesis** — bull / base / bear, with explicit stance
8. **Valuation snapshot** (when CMP available) — trailing & forward ratios, scenario forward EPS, multiple-band reasoning, implied price band, quality-of-earnings adjustment, asymmetry vs CMP
9. **Peer comparison** (when requested or clearly needed)
10. **Verdict** — *Interesting / Watchlist / Avoid / Pass* + 1-line elevator pitch + 1–2 things to watch in the next 1–2 quarters

For narrower asks (just red flags, just management read, just valuation), the skill produces only that section instead of the full report.

## Source labels

Every claim in the final report traces to a source via inline tags:

| Tag | Meaning |
|---|---|
| `[AR-FY25]` | Annual Report for the fiscal year noted |
| `[Concall-Q4FY26]` | Concall transcript for the quarter noted |
| `[IP-Q3FY26]` | Investor presentation for the quarter noted |
| `[Screener-quant]` | 10-yr table or ratio from `screener-data.json` |
| `[BSE-direct]` / `[NSE-direct]` | Filing found via exchange search (Source Tier 2) |
| `[Third-party]` | Filing sourced from trendlyne, marketscreener, etc. (Source Tier 3) — weight lower |
| `[Web-search]` | Recent news / regulatory action postdating the latest filing |
| `[Inferred]` | Analytical inference, not directly stated in any source |

This preserves the operating principle: the user always knows what came from primary filings vs. derived analysis.

---

## Repo structure

```
equity-research-india/
├── SKILL.md                          # Main skill file (operating principles, workflow, output format)
├── README.md                         # This file
├── LICENSE                           # MIT
├── requirements.txt                  # Python deps (beautifulsoup4)
├── .gitignore                        # Excludes .venv/, __pycache__/, .DS_Store
├── scripts/
│   ├── parse_screener.py             # Generic screener.in HTML → structured JSON
│   └── slice_pdf.py                  # AR/concall slicer (pdftotext + heading detection)
└── references/
    ├── extraction-checklist.md       # What to pull from each filing type
    ├── concall-analysis.md           # How to read concalls (prepared remarks vs Q&A)
    ├── peer-comparison.md            # Indian peer/sector comparison frame
    ├── red-flags-india.md            # Indian-specific governance red flags
    ├── valuation-math.md             # 6-step ratio-based valuation framework with scenario bands
    ├── screener-auto-fetch.md        # Ticker-only flow: 3-tier source fallback, folder layout, cache
    ├── pdf-slicing.md                # How to slice PDFs (script + manual fallback + retrieval map)
    ├── subagent-extraction.md        # Default path: parallel Haiku for mechanical extractions
    └── master-report-template.md     # Output template for the final thesis
```

---

## Example prompts

| Prompt | What happens |
|---|---|
| *"Thesis on GSM Foils."* | Triggers Screener auto-fetch; skill confirms file set, downloads ARs / concalls / IP, parses screener page, slices, extracts in parallel, writes master report |
| *"Here's the Asian Paints FY25 annual report. Build me a thesis."* | Uploaded PDF short-circuits auto-fetch; goes straight to slicing + extraction |
| *"Should I invest in Bajaj Finance? Pull the last 4 concalls and tell me the case for and against."* | Bull/base/bear scorecard with the concall-heavy fetch profile |
| *"What are the red flags in this Adani Ports AR?"* | Red flags section only — CARO + RPT + contingent liab + AOC-1 + ESOP via parallel Haiku |
| *"Compare Tata Motors and Mahindra & Mahindra on capital allocation."* | Peer comparison table + verdict per company |
| *"Is GSM Foils cheap at ₹205?"* | Triggers the valuation snapshot — auto-fetches CMP/financials from screener, runs the 6-step ratio framework |
| *"Track record of HUL management's guidance vs delivery over the last 3 years."* | Pulls 3 years of concalls, extracts guidance, checks against actuals from `screener-data.json` |

---

## Caveats & known limits

- **The `slice_pdf.py` heading detector is reasoned, not battle-tested across every Indian AR convention.** First real run on a new ticker may surface where the regex misses a heading; the script's `sections_suspicious` / `sections_missing` JSON output makes this visible. Tune `AR_SECTIONS` patterns in `scripts/slice_pdf.py` if you find a recurring miss.
- **`parse_screener.py` is brittle to Screener's HTML changes.** If they rename `#top-ratios` or `data-result-table`, sections fail to populate. The skill falls back to markdown extraction in that case, but the parser would need an update.
- **RHPs/DRHPs are handled awkwardly today** — they don't have CARO or AOC-1 (pre-listing), so those sections are correctly reported as missing. A focused `indian-ipo-analyzer` skill is a planned v2 split-out for proper IPO analysis (lock-in expiry, OFS vs fresh issue, peer-multiple framing).
- **The Insights premium block** ("Pulp and Paper Installed Capacity", "Real Estate Booking Value", etc.) is Screener-paid — the parser deliberately skips the gated cells. The Pros/Cons block is the public version, which is enough.
- **Banks and NBFCs use different P&L row labels** ("Revenue" / "Financing Profit" / "Financing Margin %" instead of "Sales" / "Operating Profit" / "OPM %"). The parser captures them as-is; the skill's sector lens applies the right normalization.
- **Subagent path requires a Task/Agent tool** in the running environment. claude.ai web skills without subagent tools fall back to inline reading — the skill produces identical analysis either way; subagents are pure speedup.

---

## License

MIT — use it, fork it, modify it.
