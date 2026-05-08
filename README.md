# equity-research-india

A [Claude Code](https://docs.claude.com/en/docs/claude-code) skill for building qualitative investment theses on Indian listed companies.

The skill turns annual reports, quarterly results, and earnings concall transcripts into a structured opinion on **business quality, management quality, growth runway, and red flags** — through an Indian governance lens (SEBI/MCA disclosures, CARO 2020, related party transactions, promoter pledging, contingent liabilities, etc.).

Output is opinionated. The qualitative core covers business / management / red flags; an optional **valuation overlay** runs disciplined ratio-based math (PE, EV/EBITDA, P/B, scenario-based forward EPS, implied price band, quality-of-earnings adjustment, asymmetry vs CMP) when a current market price is provided. It stops short of single-point DCF intrinsic values or "buy at exactly ₹X" target prices — those imply false precision.

## What it does

- **Auto-fetches filings from Screener.in when you give it a ticker** — annual reports, concall transcripts, investor presentations, plus a 10-yr financials scrape. No PDF uploads required. Tier-based selection adapts to company size (large-cap → SME). Saves to `~/Documents/equity-research/<TICKER>/` and caches for 7 days.
- Inventories filings (AR, QR, investor decks, concall transcripts) and reads them rather than guessing from memory
- Extracts segment trajectory, margin direction, capex follow-through, working capital trends
- Cross-references **what management said vs what they delivered** across past concalls
- Flags governance issues: RPT patterns, auditor remarks, contingent liabilities, ESOP dilution, promoter pledging, subsidiary opacity
- Produces an opinionated bull/bear thesis with explicit conviction level
- Source-labels every claim (`[AR-FY25]`, `[Concall-Q4FY26]`, `[Screener-quant]`, `[Web-search]`, `[Inferred]`) so primary filings vs. derived analysis are always distinguishable
- When a CMP is provided: trailing/forward multiples, scenario-based forward EPS (full P&L walk), multiple-band reasoning anchored to peers/growth/quality discounts, implied price band, owner's-earnings reconstruction, asymmetry call vs CMP

## What it does NOT do

- DCF / DDM / single-point intrinsic value modeling
- "Buy at exactly ₹X" target prices or position-sizing advice
- Technical analysis or F&O strategies
- IPO grey market chatter or mutual fund picks
- US/global equities (Indian listed companies only)

## Installation

Drop the folder into your Claude Code skills directory:

```bash
git clone https://github.com/cdraarsh/equity-research-india.git ~/.claude/skills/equity-research-india
```

Or, if you already have a `~/.claude/skills/` directory:

```bash
cd ~/.claude/skills
git clone https://github.com/cdraarsh/equity-research-india.git
```

Restart Claude Code (or start a new session) and the skill will auto-trigger on relevant prompts.

## When it triggers

The skill activates when you:

- Upload an Indian company's AR / QR / concall PDF and ask for analysis
- Name an Indian listed stock with words like *thesis*, *deep dive*, *should I invest*, *is it a buy*, *analyze*, *what's the case for/against*
- Ask for peer or sector comparison within Indian markets
- Ask about red flags, governance, audit issues, or management quality

It triggers especially on uploads of 100+ page PDFs that look like annual reports.

## Repo structure

```
equity-research-india/
├── SKILL.md                          # Main skill file (operating principles, workflow, output format)
└── references/
    ├── extraction-checklist.md       # What to pull from each filing type
    ├── concall-analysis.md           # How to read concalls (prepared remarks vs Q&A)
    ├── peer-comparison.md            # Indian peer/sector comparison frame
    ├── red-flags-india.md            # Indian-specific governance red flags
    ├── valuation-math.md             # 6-step ratio-based valuation framework with scenario bands
    ├── screener-auto-fetch.md        # Ticker-only flow: tier-based file selection, folder layout, cache
    └── master-report-template.md     # Output template for the final thesis
```

## Example prompts

- *"Thesis on GSM Foils."* — ticker alone triggers Screener auto-fetch (skill confirms the file set, downloads ARs / concalls / IP, then reads them)
- *"Here's the Asian Paints FY25 annual report. Build me a thesis."* — uploaded PDFs short-circuit the auto-fetch
- *"Should I invest in Bajaj Finance? Pull the last 4 concalls and tell me the case for and against."*
- *"What are the red flags in this Adani Ports AR?"*
- *"Compare Tata Motors and Mahindra & Mahindra on capital allocation."*
- *"Is GSM Foils cheap at ₹205?"* (triggers the valuation snapshot — auto-fetches CMP/financials from `screener.in/company/<TICKER>/`)

## License

MIT — use it, fork it, modify it.
