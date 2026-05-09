# Subagent Extraction (default path)

Delegate mechanical extractions to parallel Haiku subagents. This is the default path when the environment supports it — keeps the main session's context clean, cuts cost (Haiku vs Sonnet), and cuts wallclock (parallel vs sequential).

## Tool-availability check (run this first)

If the running environment exposes a Task/Agent tool with Haiku-class model selection (e.g., Claude Code's `Task` tool), use this path. If not (rare — some constrained skill harnesses), fall back to inline reading per the retrieval map in `pdf-slicing.md`. The skill must produce identical analysis either way; subagents are pure speedup, not a behavior change.

A single extraction (e.g., one CARO read) is rarely worth the schema/merge overhead — for a single section just read it inline. Use this path when the task involves 3+ of the extractions listed in §"What to delegate" below, which is true for any AR deep-dive or red-flags pass.

## What to delegate (tier-A extractions only)

These are mechanical "find every X" reads with structured output. Cheap-model territory.

| Extraction | Source extract(s) | Why delegate |
|---|---|---|
| **CARO findings** | `AR-*-caro.txt` | Listing clauses + adverse comments is enumeration, not synthesis |
| **RPT facts** | `AR-*-rpt.txt` | Pulling parties + amounts from a notes table is mechanical |
| **Contingent liabilities** | `AR-*-contingent-liab.txt` | Same — list the disputes + quantum + status |
| **AOC-1 subsidiaries** | `AR-*-aoc1.txt` | Tabular subsidiary list extraction |
| **ESOP / managerial remuneration** | `AR-*-esop.txt` | Pool size + top-N remuneration figures |
| **Auditor's Report KAMs** | `AR-*-auditor-report.txt` | Listing Key Audit Matters + management response |
| **Concall topic-keying** | each `qXX-*.txt` turn | Per-turn 3–5 word topic tags fed into `index.json` |

## What NOT to delegate

Keep these in the main session — they need cross-section synthesis a smaller model handles poorly:

- **MD&A reading + business model synthesis** — connects MD&A claims with segment trends and auditor flags
- **Concall management-quality read** — tone shifts, deflections, guidance vs delivery; pattern recognition across turns
- **Master report writing & verdict** — synthesis-heavy
- **Thesis / verdict / asymmetry call** — opinionated stance-taking

## Invocation pattern

For each delegated extraction, spawn one subagent with: (a) a Haiku-class model, (b) the extract file path, (c) the strict output schema below, (d) an instruction to return JSON only (no commentary).

Run the full set in parallel — one message with multiple subagent calls. Aggregate results when all return; on failure of any single subagent, fall back to inline reading for just that extraction.

### Standard subagent prompt skeleton

```
You are extracting structured facts from a single section of an Indian annual report.

Read the file at: <ABSOLUTE_PATH>
Extraction type: <CARO | RPT | ContingentLiab | AOC1 | ESOP | AuditorKAM | ConcallTopics>

Return JSON only, matching this schema exactly:
<SCHEMA_JSON>

Rules:
- Quote source values verbatim where applicable; do not paraphrase numbers
- If a field isn't present in the source, set it to null (do not invent)
- If a list is empty, return an empty array (do not omit the key)
- All amounts in INR Crores unless the source uses a different unit; if so, include the unit in a `unit` field
- No prose, no markdown — JSON only
```

## Output schemas

Schemas are strict — the main session validates the JSON before merging. Mismatched output is treated as a subagent failure and the main session retries inline.

### CARO findings

```json
{
  "audit_opinion": "clean | qualified | adverse | disclaimer",
  "kams": [
    {"matter": "string", "auditor_procedures": "string", "company_response": "string | null"}
  ],
  "emphasis_of_matter": ["string"],
  "caro_clauses_with_adverse_comment": [
    {"clause": "3(i) | 3(ii) | ...", "topic": "fixed assets | inventory | loans to related parties | deposits | statutory dues | term loan utilization | fund diversion | fraud | internal audit | ...", "finding": "string"}
  ],
  "auditor_change_last_3yr": {"changed": true | false, "reason": "string | null"}
}
```

### RPT facts

```json
{
  "year": "FY25 | FY24 | ...",
  "total_rpt_inr_cr": number | null,
  "total_rpt_pct_of_revenue": number | null,
  "total_rpt_pct_of_pat": number | null,
  "transactions": [
    {
      "party": "string",
      "relationship": "promoter entity | subsidiary | associate | KMP | KMP relative | joint venture | other",
      "nature": "sale of goods | purchase of goods | services rendered | services received | loan given | loan taken | royalty | brand fee | guarantee | other",
      "amount_inr_cr": number | null,
      "outstanding_balance_inr_cr": number | null
    }
  ],
  "notable_items": ["string"]
}
```

### Contingent liabilities

```json
{
  "year": "FY25 | FY24 | ...",
  "items": [
    {
      "type": "income tax | GST | customs | excise | service tax | legal claim | bank guarantee | performance guarantee | letter of credit | other",
      "description": "string",
      "amount_inr_cr": number | null,
      "status": "pending | under appeal | crystallized | dismissed | settled | unknown"
    }
  ],
  "total_inr_cr": number | null
}
```

### AOC-1 subsidiaries

```json
{
  "subsidiaries": [
    {
      "name": "string",
      "country": "string",
      "holding_pct": number | null,
      "revenue_inr_cr": number | null,
      "pat_inr_cr": number | null,
      "loss_making": true | false | null,
      "material": true | false
    }
  ],
  "total_subsidiaries": number,
  "material_threshold_used": "10pct of consolidated revenue or PAT"
}
```

### ESOP / managerial remuneration

```json
{
  "esop": {
    "pool_pct_of_paidup_capital": number | null,
    "outstanding_options_pct": number | null,
    "options_granted_during_year": number | null,
    "average_exercise_price_inr": number | null
  },
  "managerial_remuneration": {
    "top_executives": [
      {"name": "string", "role": "string", "total_inr_cr": number | null, "fixed_pct": number | null, "variable_pct": number | null, "esop_pct": number | null}
    ],
    "promoter_remuneration_pct_of_pat": number | null,
    "highest_paid_pct_of_pat": number | null
  }
}
```

### Auditor KAMs

(Subset of CARO schema if you want a separate call for KAMs only — usually folded into the CARO extraction.)

### Concall topic-keying

For each Q&A turn extract `qXX-*.txt`, return:

```json
{
  "q": number,
  "topics": ["string", "string", "string"]
}
```

Topics are 3–5 words each, 2–4 topics per turn. Examples: `"margin guidance FY27"`, `"capex Madhya Pradesh"`, `"working capital deterioration"`, `"USFDA inspection 483"`. The main session merges these into the `index.json` written by `scripts/slice_pdf.py`.

## Parallelism budget

Cap parallel subagents at 10 per message to avoid throttling. For a typical AR deep-dive that's:

- 1× CARO subagent
- 1× RPT subagent
- 1× Contingent-liab subagent
- 1× AOC-1 subagent
- 1× ESOP subagent

= 5 parallel subagents, all returning structured JSON in roughly one round-trip.

For concall topic-keying with 15 turns, batch them: 1 subagent per turn, capped at 10 in flight, second batch for the remaining 5.

For multi-AR comparisons (FY23/FY24/FY25 promise-vs-delivery), run the full 5-extraction set per AR in parallel — 15 subagents max — only if the environment has the headroom.

## Merge protocol

The main session is responsible for:

1. **Validating** each subagent's JSON against the schema. On invalid output, retry once; on second failure, fall back to inline reading for that specific extraction.
2. **Cross-referencing** structured output against the source extract for high-stakes items (auditor opinion, qualified clauses, RPT > 5% of revenue, contingent liab > 10% of net worth) by re-reading the relevant lines directly. Trust but verify.
3. **Merging** concall topics into `<TICKER>/extracts/<concall>-index.json` by `q` number.
4. **Persisting** the structured outputs as `<TICKER>/extracts/<source>-extracted.json` so future runs in the cache window don't re-spawn subagents.

## Caching

Structured extractions are valid as long as the source PDF hasn't changed. Cache rule:

- `<TICKER>/extracts/<source>-extracted.json` exists AND `INDEX.md` shows the source PDF was fetched ≤7 days ago → reuse cached JSON, skip subagent
- Otherwise → spawn subagents, write fresh `<source>-extracted.json`, update `INDEX.md`

This shares the 7-day cache window from `screener-auto-fetch.md` §9.

## Failure modes

- **Subagent tool unavailable** (e.g., claude.ai web skill): skip this file; main session reads extracts inline. The skill must work without subagents — this path is pure speedup.
- **Subagent returns invalid JSON**: retry once with the schema repeated; on second failure, fall back to inline read for that extraction.
- **Subagent reports the source extract is empty / off-target** (the slicer's boundaries were wrong): note it, and re-run `scripts/slice_pdf.py --dry-run` to inspect candidates per `pdf-slicing.md`.
- **Schema drift across companies**: don't tweak schemas per-ticker. If a recurring field is missing, propose a schema update in this file rather than ad-hoc fixes per run.
