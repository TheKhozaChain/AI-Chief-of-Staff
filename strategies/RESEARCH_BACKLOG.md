# Research Backlog

> The R in RBI. This is the pipeline feeder. Ideas come in wide, get screened fast, and only survivors become full hypotheses.

Last updated: 2026-02-16 (statuses updated: R007-R020 now show validated/failed state, R021-R023 new)

## Status Key

| Status | Meaning |
|--------|---------|
| `new` | Sourced but not yet screened |
| `screening` | Currently being quick-screened (30 min) |
| `promoted` | Passed screen → promoted to full HYPOTHESIS_XXX.md |
| `validated` | Walk-forward validated → now paper trading as HXXX |
| `val-failed` | Walk-forward validation failed → killed |
| `killed` | Failed screen — logged here for reference |
| `parked` | Interesting but not testable with current data/tools |

---

## Active Pipeline

| # | Idea | Source | Core Thesis | Status | Notes |
|:-:|------|--------|-------------|--------|-------|
| R001 | 4H Vol Contraction Breakout | Internal (H001/H002 learnings) | Tight range → breakout with momentum, wider targets absorb costs | killed | → H003: PF 0.98 gross. Squeeze predicts magnitude not direction. |
| R002 | Funding Rate Mean Reversion | Market observation | Extreme funding rates predict short-term reversals in perps | parked | Needs funding rate data (not in current dataset) |
| R003 | Volume Profile Breakout | Academic (market microstructure) | Price breaks from high-volume nodes with directional momentum | killed | PF 1.02 gross, 129 trades, 37.2% WR. Best of 8 param combos. Volume profile approximated via BB squeeze (no volume profile data). |
| R004 | Multi-Timeframe Momentum | Quantitative trading literature | Align daily trend with 4H entry for higher-probability trades | killed | Gross PF 1.06. Directional filter adds tiny edge, not enough. |
| R005 | Weekend Gap Fade | Market observation | Crypto weekend gaps tend to fill within 24-48 hours | killed | Gross PF 0.73. Crypto gaps extend, not revert. |
| R006 | Trend Following (Long Bias) | H003/R004 postmortem insight | BTC structural uptrend (+203% 3yr). Ride the trend, don't fight it. | killed | **BEST RESULT: PF 1.26 gross** (20/80 MA, 3%/9%). Below 1.3 but only positive-expectancy strat found. |
| R007 | Volatility-Adjusted Trend | Academic (adaptive strategies) | Scale position size inversely with volatility. Bigger in calm trends, smaller in chaos. | validated | → H004 (paper trading). PF 1.46 gross, OOS PF 1.09. |
| R008 | Long Dip Buy (uptrend MR) | Combined H002+R006 insight | Buy oversold z-score dips within confirmed uptrend. Long-only. | killed | PF 0.81 gross. Dip-buying catches falling knives. |
| R009 | Donchian Channel Breakout | Classic trend following | Enter on N-bar high/low breakout. Long only. Simpler entry than MA crossover. | val-failed | → H005 (killed). Net PF 1.23, edge too thin after costs. |
| R010 | Multi-Asset Momentum | Portfolio theory | Rotate between BTC/ETH/SOL — go long the strongest, avoid the weakest. | validated | → H007 (paper trading). PF 1.62 gross, OOS PF 1.04, decay warning -42.7%. |
| R011 | Daily Timeframe Trend | R006 insight: longer holds help | Move to daily bars. Hold for weeks, not days. Reduce trade frequency, increase target. | val-failed | → H006 (killed). Only 20 trades over 3yr — insufficient sample. |
| R012 | Adaptive Momentum Burst (AMB) | Combining learnings from R007 (volatility-adjusted edges work) and R001 (squeeze predicts magnitude). Bitcoin exhibits periods of compressed volatility followed by explosive directional moves that persist. | Enter breakouts from volatility compression zones ONLY when price simultaneously breaks above a rising medium-term MA, capturing the directional momentum that follows squeeze releases in an uptrending market. | validated | → H008 (paper trading). PF 1.66 gross, OOS PF 1.13, decay warning -48.8%. |
| R013 | Acceleration Breakout Filter (ABF) | R006 and R011 show trend-following works; R009 shows breakouts work. Bitcoin's strongest moves exhibit price acceleration (increasing rate of change) before breakout, filtering out false breaks that lack momentum conviction. | Only take Donchian breakouts when recent ROC (rate of change) is accelerating upward over multiple lookback periods, ensuring we catch breakouts with genuine momentum thrust rather than slow grinds that fail. | validated | → H009 (paper trading). PF 2.34 gross, OOS PF 2.50 — **STRONGEST batch 1**, 4/4 pass. |
| R014 | Multi-Timeframe Breakout Confluence (MTBC) | R011's daily timeframe success (PF 1.9) plus R009's hourly breakout success (PF 1.31) suggest combining timeframes. Requiring alignment across timeframes should filter false signals while maintaining edge. | Enter only when BOTH 1H Donchian breakout occurs AND daily timeframe shows simultaneous uptrend (price > daily MA), capturing high-conviction moves where intraday breakout aligns with daily momentum structure. | val-failed | → H010 (killed). Failed walk-forward validation. |
| R015 | Volume-Confirmed Breakout (VCB) | None of R001-R014 used volume data. Volume spikes at breakout confirm real buying pressure vs. low-volume false breaks. | Only enter Donchian breakouts when current bar volume exceeds the rolling average by a multiplier, filtering out low-conviction breakouts. | validated | → H011 (paper trading). PF 1.41 gross, OOS PF 1.18. |
| R016 | Dual Momentum Consensus (DMC) | H009's acceleration filter was standout performer. Multi-period momentum consensus should be more robust than single-period acceleration. | Require positive ROC across 3 lookback periods (fast/med/slow) before entering breakout — all timeframes must agree momentum is positive. | val-failed | → H012 (killed). Failed walk-forward validation. |
| R017 | Trend Strength Breakout (TSB) | Academic (ADX/directional movement literature). Choppy markets kill breakout strategies — ADX filters them out. | Only enter Donchian breakouts when ADX-like directional movement measure exceeds threshold, filtering out range-bound, choppy environments. | validated | → H013 (paper trading). PF 1.59 gross, OOS PF 1.54 — **STRONGEST batch 2**, 4/4 pass. |
| R018 | Trend Pullback Entry (TPE) | H004 and H009 both buy extended breakouts. Pullback entries capture the same trend at better prices with tighter risk. | Buy when price pulls back to a rising trend MA and bounces with positive short-term momentum — trend continuation, not mean reversion. | validated | → H014 (paper trading). PF 2.65 gross, OOS PF 4.61 (only 26 trades — sample concern). |
| R019 | ATR Regime Adaptive (ARA) | H004 proved volatility adjustment works. This extends it with dynamic regime detection — scaling stops by ATR percentile relative to history. | Trend following with ATR-percentile-based stop scaling: wider stops in high-vol regimes (avoid noise), tighter in low-vol (lock in gains). | validated | → H015 (paper trading). PF 1.38 gross, OOS PF 0.76, decay -57% — overfitting warning. |
| R020 | Consecutive Momentum Filter (CMF) | Novel filter dimension. Consecutive positive bars indicate sustained buying pressure, not just a single spike. | Only enter Donchian breakouts when N consecutive prior bars have positive close-to-close returns, confirming sustained buying momentum. | validated | → H016 (paper trading). PF 1.74 gross, OOS PF 1.94 — **robust**. |
| R021 | Range Compression Expansion (RCE) | R001/R012 showed squeeze predicts magnitude but not direction. Rather than predict direction, trade the expansion itself with dual-sided breakouts and quick directional confirmation. | After extreme range compression (ATR at multi-week lows), the eventual breakout in EITHER direction tends to continue due to accumulated volatility release and position unwinding. | new | Archetype: custom. {'atr_period': 20, 'atr_lookback': 60, 'compression_percentile': 10, 'breakout_atr_mult': 1.5, 'confirmation_bars': 2, 'stop_pct': 3.0, 'target_pct': 9.0, 'long_only': True} |
| R022 | Momentum Exhaustion Reversal to Trend (MERT) | R006/R018 show trend-following works, R008 shows dip-buying fails. Combine: wait for short-term momentum exhaustion (RSI <30) WITHIN an established uptrend, then enter on the first bounce bar. | Oversold conditions in strong uptrends create asymmetric risk-reward as weak hands capitulate near temporary bottoms, but the structural trend reasserts quickly. | new | Archetype: custom. {'ma_period': 50, 'rsi_period': 14, 'rsi_threshold': 30, 'bounce_min_pct': 0.5, 'stop_pct': 3.0, 'target_pct': 9.0, 'long_only': True} |
| R023 | Gap-and-Go Continuation (GGC) | R005 showed gaps extend rather than revert. Opposite insight: trade WITH gaps that occur in trend direction during high-momentum regimes. | Price gaps above recent range highs during established uptrends signal institutional accumulation or news-driven momentum that continues for 1-2 sessions as FOMO kicks in. | new | Archetype: custom. {'ma_period': 50, 'gap_min_pct': 1.0, 'lookback_period': 20, 'roc_period': 10, 'min_roc': 2.0, 'entry_delay_bars': 1, 'stop_pct': 2.0, 'target_pct': 6.0, 'long_only': True} |

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
| K008 | Volume Profile Breakout (BTC 4H) | Gross PF 1.02, 37.2% WR | Gross PF 1.02 — positive expectancy but below 1.3 threshold. |

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
