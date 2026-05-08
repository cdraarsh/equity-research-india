# Valuation math (basic)

Read this when the user asks "is it cheap?", "what's a fair price?", "should I buy at ₹X?", or after the qualitative thesis is done and they want to know whether the current price makes sense.

The philosophy is **disciplined ratio analysis with scenario bands** — Peter Lynch / Phil Fisher style, not Damodaran-style DCF. The goal is to bracket fair value with a range that honestly reflects uncertainty, not to compute a single-point intrinsic value that pretends to know the future.

## What this gives you, what it doesn't

**In scope:**
- Trailing and forward multiples (PE, EV/EBITDA, P/B)
- Forward EPS scenarios (bear / base / bull)
- Implied price band per scenario
- Quality-of-earnings adjustment (cash earnings vs accounting earnings)
- Asymmetry assessment vs current price

**Out of scope:**
- DCF / DDM / single-point intrinsic value
- "Buy at exactly ₹X" target price
- Position sizing / portfolio construction advice
- Technical / chart-based timing

## Inputs required before starting

Always require these. Don't guess them.
1. **Current market price (CMP)**
2. **Total shares outstanding** — post all dilutions: bonus, rights, QIP, ESOP. SME companies often dilute meaningfully near listing; pre-dilution share counts are a common source of error.
3. **Total debt** (short + long term)
4. **Cash & equivalents**
5. **Latest 4-quarter PAT trail and EBITDA trail**

`screener.in/company/<TICKER>/` is the canonical source — most fields cleanly available. If anything is missing or stale, ask the user to paste it.

---

## The 6-step framework

### Step 1 — Translate fundamentals to per-share

| Item | Value |
|---|---|
| TTM PAT | ₹X cr |
| TTM EBITDA | ₹Y cr |
| Shares outstanding (post-dilution) | Z cr |
| TTM EPS | PAT ÷ shares |
| Book value/share | Net worth ÷ shares |
| Net debt | Debt − Cash |
| Enterprise value | Mkt Cap + Net debt |

Use the post-dilution share count even if the dilution just happened. Always.

### Step 2 — Compute the four core ratios

| Ratio | Formula | When it dominates |
|---|---|---|
| Trailing PE | Mkt Cap ÷ TTM PAT | Stable earners, low debt |
| Forward PE | Mkt Cap ÷ FY+1 PAT estimate | Companies with a clear guidance trail |
| EV/EBITDA | EV ÷ EBITDA | Capital-structure-heavy companies (D/E > 0.5) |
| P/B | Mkt Cap ÷ Net Worth | Banks, NBFCs, asset-heavy commodity businesses |

Sector-specific overrides:
- **NBFCs / banks:** P/B + ROE drive everything; PE is secondary.
- **Real estate:** P/Sales > PE because earnings are lumpy on revenue recognition timing.
- **Capital goods on long projects:** EV/EBITDA + book-to-bill matter more than PE.
- **Early-stage / loss-making:** drop PE; use P/Sales + EV/EBITDA + path-to-profitability narrative.
- **Mid-cap industrials / converters / consumer:** EV/EBITDA + Forward PE matter most.

### Step 3 — Generate forward EPS scenarios

Three scenarios, each anchored to a defensible input.

| Scenario | Revenue anchor | Margin anchor |
|---|---|---|
| Bear | Lower bound of recent guidance × 0.8 (delivery slippage) | Lower bound of last 4 quarters |
| Base | Midpoint of recent guidance | Average of last 4 quarters |
| Bull | Upper bound of recent guidance | Highest of last 4 quarters — only if structurally repeatable, not a one-off (e.g., inventory gain) |

For each scenario, walk the P&L explicitly — don't shortcut with "Revenue × PAT margin":

```
Revenue × EBITDA margin = EBITDA
Less: D&A (latest year, scaled if capex changed)
Less: Finance cost (scale with debt change)
= PBT
Less: Tax (use blended rate from latest year)
= PAT
÷ Post-dilution share count
= Forward EPS
```

Finance cost and tax dynamics matter at small/mid scale — a 2 pp jump in finance cost can move PAT by 5–10%. Don't flatten this.

### Step 4 — Pick the multiple band, generate implied prices

The multiple band is the most subjective step. Anchor explicitly to three things:

**Anchor 1 — Sector peers.** Pull peer multiples from Screener's peer comparison. Note the median; apply discount/premium based on relative quality.

**Anchor 2 — Growth rate (PEG).** Rough rule:
- PEG = 1 (PE ≈ growth rate %): fair for steady growers
- PEG = 0.7: conservative-cheap; opportunity if growth is real
- PEG = 1.5: starting to look expensive
- For 50%+ growth companies, ignore PEG = 1; that produces absurd multiples. Cap base PE at sector median + growth premium.

**Anchor 3 — Quality discounts/premia (apply to sector median):**

| Factor | Adjustment |
|---|---|
| SME platform listing | −15% to −25% |
| Single product / single facility | −10% |
| Negative operating cash flow (working-capital-intensive) | −10% to −20% |
| Governance flag (promoter pledging, RPT-heavy, CFO=Chairman, etc.) | −10% to −20% |
| Founder-led, multi-decade clean track record | +10% to +20% |
| Net cash, recurring revenue, low capex intensity | +10% to +20% |
| Promoter aggressively buying from open market | +5% to +10% |

**Output a band, not a point:**
- Bear multiple: e.g., 10–13x
- Base multiple: e.g., 16–20x
- Bull multiple: e.g., 22–28x

Then compute the cross product with EPS:

| Scenario | Multiple | EPS | Implied price |
|---|---|---|---|
| Bear (low) | 10x | bear EPS | … |
| Base (centre) | 18x | base EPS | … |
| Bull (high) | 28x | bull EPS | … |

### Step 5 — Quality-of-earnings adjustment

This is the step retail investors skip and the one that separates a real value call from a multiple-arbitrage trap.

**Reconstruct owner's earnings (rough Buffett-style):**

```
PAT
+ D&A
− Δ Receivables (if growing)
− Δ Inventory (if growing)
+ Δ Payables (if growing)
− Maintenance capex (≈ D&A for steady-state businesses)
= Owner's earnings
```

If owner's earnings is materially below PAT (>30% gap), the headline PE is misleading — the real PE is much higher. Apply an additional 20–30% multiple haircut in step 4 until the gap closes.

For working-capital-intensive businesses (converters, distributors, capital-goods on long projects, contract manufacturers), this gap can absorb the entire profit. Growth is real on paper, but cash isn't there until growth slows. Always flag this — it's the single most common quality-of-earnings problem in Indian small/mid caps.

For asset-light businesses with prompt receivable cycles (FMCG, SaaS, brokerage, asset managers): PAT ≈ owner's earnings; no adjustment usually needed.

### Step 6 — Asymmetry vs current price

Compute three numbers:
- **Bull-case price as % above CMP** (max upside)
- **Bear-case price as % below CMP** (max downside)
- **Probability-weighted return:** (P_bull × bull return) + (P_base × base return) − (P_bear × |bear return|)

Don't fake the probabilities. If the bull case requires four things to play out, P_bull is not 50%. Common assignments for an honest range:

| Conviction | P_bear / P_base / P_bull |
|---|---|
| High conviction in story | 15 / 60 / 25 |
| Standard | 25 / 50 / 25 |
| Low conviction (uncertain story) | 35 / 50 / 15 |
| Bear-leaning | 50 / 35 / 15 |

**Asymmetry decision rules:**

| Upside : Downside ratio | Read |
|---|---|
| > 3:1 with reasonable base case conviction | Genuine starter position |
| 1.5:1 to 3:1 | Smaller starter, add on confirmation event |
| 1:1 to 1.5:1 | Watchlist, not buy |
| < 1:1 (downside > upside) | Avoid — math is not in your favour |

If the bear-case price is < 70% of CMP **without** strong conviction in the bull case, that's a value-trap signal. Don't buy.

---

## When the math contradicts the qualitative thesis

If qualitative says "Watchlist" or "Avoid" but the math says cheap, the resolution is usually one of three things:

1. **The market is pricing in something the thesis missed.** Re-read the red flags section. Often there's a known issue (litigation, accounting flag, competitive threat) that the qualitative read underweighted.
2. **The market is mis-pricing illiquidity / SME discount.** Real arb opportunity — but only if your thesis is robust.
3. **Earnings quality is poor.** Re-do step 5 properly. Often the headline PE is hiding a working-capital trap.

Either way, **name the disagreement explicitly in the output**. Don't paper over it.

If qualitative says **"Pass — structural concerns"** but the math says cheap, **trust the qualitative.** Cheap value-traps with broken governance stay cheap. Don't override a structural call with a multiple call.

---

## Output format for the valuation snapshot section

When this is included in the master report, format as:

```markdown
### 8. Valuation snapshot

**Inputs** (as of [date], source: Screener / [other]):
- CMP: ₹X
- Market Cap: ₹Y cr
- Shares (post-dilution): Z cr
- Net debt: ₹A cr
- TTM PAT: ₹P cr / TTM EBITDA: ₹E cr

**Trailing ratios:**

| Ratio | Value | vs sector median |
|---|---|---|
| Trailing PE | X.Xx | (sector ~Yx) |
| EV/EBITDA | X.Xx | (sector ~Yx) |
| P/B | X.Xx | — |
| ROCE | X% | — |
| ROE | X% | — |

**Forward EPS scenarios (FY+1):**

| Scenario | Revenue | EBITDA% | PAT | EPS |
|---|---|---|---|---|
| Bear | | | | |
| Base | | | | |
| Bull | | | | |

**Multiple band reasoning:** [one short paragraph anchoring multiples to peers + growth + quality adjustments]

**Implied price band:**

| Scenario | Multiple | EPS | Implied price | vs CMP |
|---|---|---|---|---|
| Bear | | | | −X% |
| Base | | | | +X% |
| Bull | | | | +X% |

**Quality of earnings:** [one short paragraph — reconstruct owner's earnings; flag any material PAT-vs-cash gap; note any haircut already applied to multiples]

**Asymmetry call:** [one or two sentences — what the math says about price vs fundamentals. This is separate from the business-quality verdict in section 10. A great business at a bad price is still "Watchlist."]
```

When the user asks **only** for valuation ("is it cheap", "fair value at X"), produce just this section, prefaced with a 2-line snapshot of the company so the inputs aren't free-floating.

---

## Common mistakes to avoid

- **Anchoring on a single-point fair value.** Always produce a band. Single-point fair values lie about precision.
- **Pre-dilution share count.** Always use post-Rights / post-QIP / post-bonus share count, even if dilution just happened.
- **Ignoring net debt.** Comparing pure PE on a leveraged company to PE on a debt-free peer is wrong. Use EV/EBITDA when D/E > 0.5.
- **Lazy P&L walk.** "Revenue × PAT margin" misses finance cost and tax dynamics. Walk the full income statement.
- **Forgetting quality discounts.** SME, single product, governance, working-capital intensity all warrant explicit haircuts. Don't apply sector median multiples blindly.
- **Comparing across the value chain.** A Tier-1 commodity producer (Hindalco) and a Tier-2 converter (e.g., GSM Foils) shouldn't share a PE. Check what stage of the value chain the peer is at.
- **Using sector median uncritically.** If the sector itself is in a bubble (e.g., chemicals 2022) or trough (e.g., real estate 2018), the median is the wrong anchor. Adjust.
- **Skipping the quality-of-earnings adjustment.** Especially fatal for working-capital-heavy businesses where reported PAT may be 2x cash earnings.
- **Letting the math override a "Pass" qualitative verdict.** Cheap broken governance stays cheap. The math doesn't fix structural concerns.
- **Confusing the verdict bucket with the price call.** Section 10's "Interesting / Watchlist / Avoid / Pass" verdict is about the **business**. Section 8's asymmetry call is about the **price**. They can disagree, and when they do, you say so.
