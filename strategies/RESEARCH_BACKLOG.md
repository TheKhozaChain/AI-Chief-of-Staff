# Research Backlog

> The R in RBI. This is the pipeline feeder. Ideas come in wide, get screened fast, and only survivors become full hypotheses.

Last updated: 2026-02-08 (3 screens run, 3 killed, 3 new ideas added)

## Status Key

| Status | Meaning |
|--------|---------|
| `new` | Sourced but not yet screened |
| `screening` | Currently being quick-screened (30 min) |
| `promoted` | Passed screen → promoted to full HYPOTHESIS_XXX.md |
| `killed` | Failed screen — logged here for reference |
| `parked` | Interesting but not testable with current data/tools |

---

## Active Pipeline

| # | Idea | Source | Core Thesis | Status | Notes |
|:-:|------|--------|-------------|--------|-------|
| R001 | 4H Vol Contraction Breakout | Internal (H001/H002 learnings) | Tight range → breakout with momentum, wider targets absorb costs | killed | → H003: PF 0.98 gross. Squeeze predicts magnitude not direction. |
| R002 | Funding Rate Mean Reversion | Market observation | Extreme funding rates predict short-term reversals in perps | parked | Needs funding rate data (not in current dataset) |
| R003 | Volume Profile Breakout | Academic (market microstructure) | Price breaks from high-volume nodes with directional momentum | new | Testable but complex — needs volume profiling logic |
| R004 | Multi-Timeframe Momentum | Quantitative trading literature | Align daily trend with 4H entry for higher-probability trades | killed | Gross PF 1.06. Directional filter adds tiny edge, not enough. |
| R005 | Weekend Gap Fade | Market observation | Crypto weekend gaps tend to fill within 24-48 hours | killed | Gross PF 0.73. Crypto gaps extend, not revert. |
| R006 | Trend Following (Long Bias) | H003/R004 postmortem insight | BTC structural uptrend (+203% 3yr). Ride the trend, don't fight it. | killed | **BEST RESULT: PF 1.26 gross** (20/80 MA, 3%/9%). Below 1.3 but only positive-expectancy strat found. |
| R007 | Volatility-Adjusted Trend | Academic (adaptive strategies) | Scale position size inversely with volatility. Bigger in calm trends, smaller in chaos. | new | Testable. Could improve R006's best variant. |
| R008 | Long Dip Buy (uptrend MR) | Combined H002+R006 insight | Buy oversold z-score dips within confirmed uptrend. Long-only. | killed | PF 0.81 gross. Dip-buying catches falling knives. |
| R009 | Donchian Channel Breakout | Classic trend following | Enter on N-bar high/low breakout. Long only. Simpler entry than MA crossover. | new | Testable. Alternative to R006's MA-based entry. |
| R010 | Multi-Asset Momentum | Portfolio theory | Rotate between BTC/ETH/SOL — go long the strongest, avoid the weakest. | parked | Needs ETH/SOL data. |
| R011 | Daily Timeframe Trend | R006 insight: longer holds help | Move to daily bars. Hold for weeks, not days. Reduce trade frequency, increase target. | new | Testable with current data. |

---

## Killed Ideas (Archive)

| # | Idea | Screen Result | Lesson |
|:-:|------|--------------|--------|
| K001 | London Session Breakout (BTC) | PF 0.48, 33% WR | FX session patterns don't transfer to crypto. Was H001. |
| K002 | 15m Mean Reversion (BTC) | Net PF 0.69 after costs | Edge too thin for crypto transaction costs. Was H002. |
| K003 | 4H Vol Contraction Breakout (BTC) | Gross PF 0.98, 26.8% WR | Squeeze predicts expansion magnitude, not direction. Was H003. |
| K004 | Multi-Timeframe Momentum (BTC) | Gross PF 1.06, 28% WR | Daily trend filter adds tiny edge, not enough for viability. R004. |
| K005 | Weekend Gap Fade (BTC) | Gross PF 0.73, 49.3% WR | Crypto gaps extend rather than revert. Don't import FX gap logic. R005. |
| K006 | Trend Following Long (BTC 4H) | **Gross PF 1.26**, 32.4% WR | Best result so far but below 1.3 threshold. Entry timing is the bottleneck. R006. |
| K007 | Long Dip Buy (BTC 4H) | Gross PF 0.81, 33.3% WR | Mean reversion entry within uptrend catches falling knives. R008. |

---

## Research Sources to Scan

Regular sources for new ideas:

- **Academic:** Google Scholar — "cryptocurrency trading strategy", "bitcoin microstructure", "quantitative crypto"
- **Books:** Quantitative Trading (Chan), Algorithmic Trading (Chan), Advances in Financial ML (de Prado)
- **Communities:** Trading forums, strategy discussions, open-source strategy repos
- **Market Data:** Anomalies observed in our own backtests, regime changes, correlation breaks
- **AI-Generated:** Use LLMs to generate strategy concepts from market structure observations

---

## Adding Ideas

When sourcing a new idea, add a row to the Active Pipeline with:
1. Sequential R-number
2. Descriptive name
3. Where the idea came from
4. One-sentence edge thesis
5. Status: `new`
6. Any notes about data requirements or feasibility

**Target: 2-3 new ideas per week.** Not all will be testable. That's fine — the funnel is supposed to be wide.
