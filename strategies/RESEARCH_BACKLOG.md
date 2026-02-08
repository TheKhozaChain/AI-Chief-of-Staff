# Research Backlog

> The R in RBI. This is the pipeline feeder. Ideas come in wide, get screened fast, and only survivors become full hypotheses.

Last updated: 2026-02-08

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
| R001 | 4H Vol Contraction Breakout | Internal (H001/H002 learnings) | Tight range → breakout with momentum, wider targets absorb costs | promoted | → HYPOTHESIS_003 |
| R002 | Funding Rate Mean Reversion | Market observation | Extreme funding rates predict short-term reversals in perps | new | Needs funding rate data |
| R003 | Volume Profile Breakout | Academic (market microstructure) | Price breaks from high-volume nodes with directional momentum | new | Testable with current OHLCV + volume |
| R004 | Multi-Timeframe Momentum | Quantitative trading literature | Align daily trend with 4H entry for higher-probability trades | new | Testable with current data |
| R005 | Weekend Gap Fade | Market observation | Crypto weekend gaps tend to fill within 24-48 hours | new | Testable with current data |

---

## Killed Ideas (Archive)

| # | Idea | Screen Result | Lesson |
|:-:|------|--------------|--------|
| K001 | London Session Breakout (BTC) | PF 0.48, 33% WR | FX session patterns don't transfer to crypto. Was H001. |
| K002 | 15m Mean Reversion (BTC) | Net PF 0.69 after costs | Edge too thin for crypto transaction costs. Was H002. |

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
