# Peer Comparison Framework

When the user wants comparison across an Indian sector / set of peers, the goal is to surface **relative positioning** — not to crown one absolute winner. Companies in the same sector often play different games (premiumization vs scale, B2B vs B2C, organized vs hybrid).

## Picking the comparison set

Default to 2-4 peers, including the company in question. Pick them based on:
- **Same business model** (don't compare a manufacturer to a brand-only player)
- **Same scale band** (large-caps vs mid-caps usually have different ROEs and growth profiles for structural reasons)
- **Same geographic exposure** where relevant

If the user specifies the peers, use those. If they don't, propose 2-3 obvious comparables and confirm before going deep.

## What to compare on

### Growth (last 3-5 years, qualitative direction)
- Revenue CAGR
- Volume vs price contribution if separable
- Whether growth is broad-based or concentrated in 1-2 products/geographies

### Profitability trajectory
- Gross margin direction
- EBITDA margin direction
- Operating leverage — is margin expanding with scale, or stuck?

### Balance sheet health
- Net debt / equity direction
- Cash conversion (OCF / EBITDA)
- Working capital days trend

### Capital allocation
- Capex intensity (capex / revenue)
- ROCE / ROE direction
- Dividend payout vs retention pattern
- M&A history — value-creating or value-destroying?

### Management quality
- Guidance vs delivery track record (across all peers)
- Concall candor relative to peers
- Promoter governance signals

### Strategic positioning
- Where does each player sit on the value chain?
- Premium vs mass positioning
- Distribution moat, brand moat, scale moat, regulatory moat — which one (if any)?
- What's their stated long-term play?

## Output format for peer comparison

The cleanest format is usually a comparison table followed by a short verdict on each company.

Example structure:

```
| Dimension          | Company A          | Company B          | Company C          |
|--------------------|--------------------|--------------------|--------------------|
| Revenue 3Y CAGR    | ~14%               | ~22% (lumpy)       | ~9%                |
| EBITDA margin trend| 14% → 17% (rising) | 8% → 10% (slow)    | 18% → 17% (slip)   |
| Net debt / equity  | 0.2 (improving)    | 0.8 (rising)       | Net cash           |
| ROCE direction     | 18% → 22%          | 9% → 11%           | 24% → 21%          |
| Capex intensity    | 3-4% of revenue    | 12% (heavy)        | 2%                 |
| Mgmt guidance hit  | 3 of last 4 quarters | Inconsistent     | Consistently met   |
| Key risk           | Customer concentration | Capex digestion | Saturation        |
```

Then a one-paragraph verdict on each:

> **Company A** — best margin trajectory in the set with a believable growth runway. Customer concentration is the main risk but management is actively diversifying (3 new logos last year). Strongest base-case story in the set.

> **Company B** — capex-heavy bet on a structural opportunity. Returns will lag for 2-3 years. Story is real but story stocks can drift sideways for years.

> **Company C** — best return profile but margin slippage and slowing growth suggest the easy gains are behind. Look for catalysts before re-rating.

## Common mistakes to avoid

- **Forcing identical metrics across different business models.** A capital-light brand company will always look better on ROCE than a capex-heavy manufacturer; that doesn't mean it's a "better" company.
- **Ignoring cycle stage.** Comparing a company at peak margin to one at trough margin and concluding the first is "better" is misleading.
- **Single-period snapshots.** A 3-5 year direction matters more than the latest quarter's number.
- **Picking peers the company itself names.** Companies often pick flattering peer sets in their investor presentations. Use independent judgment.
