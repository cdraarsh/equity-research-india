# PDF Slicing & Section Extraction

After fetching a PDF, slice it into the analytically relevant sections **before** feeding anything to the model. A 300-page AR is 50–80k tokens; the actually-useful content is closer to 10k. Slice once at fetch time, save to disk, retrieve only what the current question needs.

## Why slice at all

- **Cost**: feeding the full AR every query reads the same 80% of irrelevant boilerplate every time.
- **Signal-to-noise**: notice of AGM, board photos, glossy CSR sections drown out MD&A and audit notes.
- **Retrieval discipline**: when the question is "what does the auditor say about CARO clause 3(xi)", you don't need the segment trends.

## The primary path: `scripts/slice_pdf.py`

Run the helper script on every PDF >30 pages. It handles `pdftotext` conversion, heading detection, section extraction for ARs, and Q&A turn splitting + indexing for concalls.

```bash
# AR / RHP / DRHP — auto-detected from filename
python scripts/slice_pdf.py ~/Documents/equity-research/<TICKER>/annual-reports/AR-FY25.pdf

# Concall — auto-detected from filename
python scripts/slice_pdf.py ~/Documents/equity-research/<TICKER>/concalls/concall-Q4FY26-2026-04-27.pdf

# Force the type if filename doesn't make it obvious
python scripts/slice_pdf.py ~/Downloads/some-file.pdf --type ar

# Dry-run to inspect boundary candidates without writing files (recommended first pass)
python scripts/slice_pdf.py <pdf> --dry-run
```

The script prints a JSON summary to stdout listing every section it wrote, the line ranges, whether each match was a confident heading-shaped hit (`heading_match: true`) or a fallback to last text mention (`heading_match: false`), the header text it landed on, and any sections that were missing or look suspicious (oversized).

**Always check `sections_suspicious` and `sections_missing` in the output.** When something is suspicious or a critical section is missing, fall back to the manual flow below for that section only.

## Required tools

- `pdftotext` (poppler-utils): `brew install poppler` — required by the script
- `pdfplumber` (Python, optional): `pip install pdfplumber` — fallback for table-heavy notes (not used by the script today; helpful when you need clean financial-table extracts)
- `ocrmypdf` (optional): `brew install ocrmypdf` — for image-based scans; the script tells you when this is needed

## When to skip slicing entirely

Don't slice every PDF — the fixed cost isn't worth it for short documents.

- **< 30 pages**: feed whole. Most concalls at the short end, single-quarter QR press releases, IPs.
- **First-pass inventory**: a 1–2 page sample is fine to identify what the document IS. Slice properly only before the deep read.
- **Single-question asks** (e.g., "what's the dividend?"): grep the answer directly, don't slice the whole AR.

Slice when: AR (always), DRHP/RHP (always), 100+ page concalls (rare but exists), credit rating rationale bundles.

## Manual fallback (when the script's boundaries look wrong)

The script's heading detector is good but not perfect — Indian AR conventions vary, and RHPs/DRHPs especially have non-standard structure. When `sections_suspicious` flags a section or you need to find one the script missed, drop down to the manual flow.

## Annual Report slicing

### Step 1: convert to text with layout preserved

```bash
TICKER=GRSE
SRC=~/Documents/equity-research/$TICKER/annual-reports/AR-FY25.pdf
OUT=~/Documents/equity-research/$TICKER/extracts
mkdir -p $OUT

pdftotext -layout "$SRC" "$OUT/AR-FY25.txt"
```

`-layout` preserves table column alignment. Page boundaries are marked with form-feed (`\f`) — you can compute a line→page map from those if needed.

If the output is gibberish/empty, the PDF is image-based (common for pre-2015 ARs and some BSE archive scans). Run OCR first:

```bash
ocrmypdf "$SRC" "${SRC%.pdf}-ocr.pdf" && pdftotext -layout "${SRC%.pdf}-ocr.pdf" "$OUT/AR-FY25.txt"
```

### Step 2: locate section boundaries with grep

ARs vary heavily in heading conventions. Use a single multi-pattern grep to map all sections at once:

```bash
grep -niE \
  'management.{0,5}discussion|director.{0,2}s.{0,3}report|board.{0,2}s.{0,3}report|independent auditor.{0,3}s.{0,3}report|\bCARO\b|annexure.{0,5}auditor|related party|contingent liab|operating segments?|segment reporting|form aoc.?1|borrowings|managerial remuneration|employee stock option|esop' \
  "$OUT/AR-FY25.txt"
```

Output is `<line>:<text>`. Pair each match with the next to derive section ranges. **Skip the first match for any heading** — it's usually the table of contents (within first ~30 pages); the second match is the real section.

Common heading mappings:

| Section | Patterns to match |
|---|---|
| MD&A | `management.{0,5}discussion`, `\bMD&A\b` |
| Director's Report | `director.{0,2}s.{0,3}report`, `board.{0,2}s.{0,3}report` |
| Auditor's Report | `independent auditor.{0,3}s.{0,3}report` |
| CARO 2020 | `\bCARO\b`, `annexure.{0,5}auditor` |
| Segment reporting | `operating segments?`, `segment reporting` |
| Related Party | `related party transactions?` |
| Contingent Liab | `contingent liabilities?` |
| Borrowings | `^.{0,10}borrowings\b` |
| Subsidiary list | `form aoc.?1`, `salient features.*subsidiar` |
| ESOP / Remuneration | `employee stock option`, `managerial remuneration` |

### Step 3: extract each section to its own file

For each section pair (`<start_line>` → `<end_line>` = next section's start - 1), use `awk`:

```bash
awk 'NR >= 1247 && NR <= 1893' "$OUT/AR-FY25.txt" > "$OUT/AR-FY25-mdna.txt"
awk 'NR >= 1894 && NR <= 2210' "$OUT/AR-FY25.txt" > "$OUT/AR-FY25-directors-report.txt"
# ... etc
```

Target layout per ticker:

```
~/Documents/equity-research/<TICKER>/extracts/
├── AR-FY25.txt                       # full text dump (kept for re-slicing)
├── AR-FY25-mdna.txt
├── AR-FY25-directors-report.txt
├── AR-FY25-auditor-report.txt
├── AR-FY25-caro.txt
├── AR-FY25-segments.txt
├── AR-FY25-rpt.txt
├── AR-FY25-contingent-liab.txt
├── AR-FY25-borrowings.txt
├── AR-FY25-aoc1.txt
└── AR-FY25-esop.txt
```

### Step 4: skip these sections (don't slice, don't read)

- Notice of AGM, proxy form, attendance slip, ballot
- Board / KMP profile pages with photos and bios
- Cover, contents, glossy marketing pages, awards & certifications
- CSR / sustainability section (unless thesis specifically calls for it)
- Five-year highlights graphics (Screener-quant supersedes — the data is cleaner there)
- Standalone statutory compliance certificates

### Step 5: tables — when to use pdfplumber

`pdftotext -layout` mostly handles tables, but for note-heavy financial grids (segment revenue over 5 years, complex RPT tables), columns can drift. Fallback:

```python
import pdfplumber, json, sys
pdf_path, pg_start, pg_end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
with pdfplumber.open(pdf_path) as pdf:
    for i in range(pg_start - 1, pg_end):
        for table in pdf.pages[i].extract_tables():
            print(json.dumps({"page": i + 1, "table": table}))
```

Use only when the rough text has lost column alignment.

## Concall transcript indexing

Concalls (typically 20–50 pages) need a different cut: opening remarks vs Q&A, then per-question turns within Q&A.

### Step 1: convert and split at the Q&A boundary

```bash
pdftotext -layout concall-Q4FY26-2026-04-27.pdf "$OUT/concall-Q4FY26.txt"

grep -niE '^moderator|question.{0,5}(and|&).{0,5}answer|q.?\s*&\s*a\s*session|first question|interactive session' "$OUT/concall-Q4FY26.txt" | head -5
```

Concalls almost always have an explicit "Q&A session" or "first question" / "Moderator" marker. Split the file at that line:

- `concall-Q4FY26-opening-remarks.txt` (lines 1 → boundary)
- `concall-Q4FY26-qa.txt` (boundary → end)

### Step 2: split Q&A into per-question turns

Each analyst's first question opens a turn (the moderator usually announces the analyst + firm):

```bash
grep -niE '^(moderator|analyst|operator).{0,2}[:.]|next question.{0,3}from|question.{0,5}from.{0,5}line' "$OUT/concall-Q4FY26-qa.txt"
```

Save each turn separately, named by analyst + firm:

```
extracts/
├── concall-Q4FY26-opening-remarks.txt
├── concall-Q4FY26-qa/
│   ├── q01-Sneha-Jain-Nomura.txt
│   ├── q02-Rohit-Gupta-Emkay.txt
│   └── ...
└── concall-Q4FY26-index.json
```

### Step 3: fill in topics inline (the running model's job)

`scripts/slice_pdf.py` writes the `index.json` with the structural fields filled in (q number, analyst, firm, file path, line range) but leaves `topics` as an empty array per turn. Topics are written by the running Claude session — there's no separate API call, just one inline pass.

If subagent tools are available in the environment, the topic pass can be parallelized — one Haiku subagent per turn, returning `{q, topics}` JSON. See `references/subagent-extraction.md` § "Concall topic-keying" for the invocation pattern and merge protocol. Otherwise, do it inline as below.

After the script runs (or after the parallel topic batch returns), each entry in `index.json` should have a 3–5-word `topics` list:

```json
[
  {"q": 1, "analyst": "Sneha Jain", "firm": "Nomura", "topics": ["margin guidance FY27", "capex plan"], "file": "...q01-Sneha-Jain-Nomura.txt"},
  {"q": 2, "analyst": "Rohit Gupta", "firm": "Emkay", "topics": ["promoter pledge", "subsidiary loans"], "file": "...q02-Rohit-Gupta-Emkay.txt"}
]
```

Topics are the lookup keys for retrieval (§ Retrieval rules below). Each turn is ~500 tokens, so reading all 12–20 turns of a typical concall costs ~10k tokens once and saves orders of magnitude on every subsequent retrieval.

This is a one-time pass per concall — re-do it only when the source PDF is re-fetched.

## Retrieval rules — pull only what the question needs

When the model needs content for a specific master-report section, retrieve from the sliced extracts, not raw PDFs.

| Master report section | Pull from extracts/ |
|---|---|
| Snapshot, business model, segments | `AR-*-mdna.txt`, `AR-*-segments.txt`, `IP-*.pdf` (whole if short) |
| Growth drivers, capex | `AR-*-mdna.txt`, `AR-*-directors-report.txt`, concall opening remarks, Q&A turns matching `["capex", "guidance", "expansion"]` |
| Management assessment | concall Q&A turns by topic (recent + 1–2 prior concalls), tone-shift comparison |
| Financial trajectory | `AR-*-segments.txt`, `AR-*-borrowings.txt`, `screener-snapshot.md` |
| Red flags | `AR-*-auditor-report.txt`, `AR-*-caro.txt`, `AR-*-rpt.txt`, `AR-*-contingent-liab.txt`, `AR-*-aoc1.txt`, `AR-*-esop.txt` |
| Investment thesis, verdict | synthesize from prior sections — don't re-read raw |

For concalls specifically: search `concall-*-index.json` topics first, pull only matching Q&A turns (typically 2–4 turns × ~500 tokens). For broader management-tone reads, pull opening remarks + a sampled cross-topic subset of turns.

## Failure modes

- **Image-based PDF**: `pdftotext` returns empty / garbage. Run `ocrmypdf` first, then continue. Common for old ARs (pre-2015) and some BSE-archived concalls.
- **No standard headings** (small/SME ARs): grep returns sparse hits. Open the PDF in Preview, find page numbers visually, then `pdftotext -f <start> -l <end>` to extract by page range directly.
- **Section spans mid-page**: `pdftotext` linearizes anyway — work in line numbers, not page numbers.
- **Heading appears twice (TOC + actual section)**: skip the first match; second is the real one. Validate by checking it's past line ~3000 (i.e., past the first ~50 pages).
- **Q&A turn boundaries unclear** (some concalls don't label cleanly): fall back to splitting on speaker-change patterns — `^[A-Z][a-z]+\s+[A-Z][a-z]+:` (Name Surname:).

## INDEX.md update

After slicing, add an `Extracts` section to the ticker's `INDEX.md` so future runs know slicing was done:

```
## Extracts (sliced sections)
| Source PDF | Extract files | Sliced on |
|---|---|---|
| AR-FY25.pdf | extracts/AR-FY25-mdna.txt, ...-caro.txt, ...-rpt.txt, ...-segments.txt, ...-aoc1.txt | 2026-05-09 |
| concall-Q4FY26-2026-04-27.pdf | extracts/concall-Q4FY26-opening-remarks.txt, qa/ (12 turns), index.json | 2026-05-09 |
```

Re-slice only when the source PDF is re-fetched or when a new heading pattern is needed for a thesis question.
