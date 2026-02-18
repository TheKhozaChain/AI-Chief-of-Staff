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
| R021 | Range Compression Expansion (RCE) | R001/R012 showed squeeze predicts magnitude but not direction. Rather than predict direction, trade the expansion itself with dual-sided breakouts and quick directional confirmation. | After extreme range compression (ATR at multi-week lows), the eventual breakout in EITHER direction tends to continue due to accumulated volatility release and position unwinding. | promoted | **PROMOTED**: PF 2.49 gross, 48 trades, 43.8% WR. Best params: {'atr_period': 20, 'atr_lookback': 60, 'compression_percentile': 10, 'breakout_atr_mult': 1.5, 'confirmation_bars': 2, 'stop_pct': 2.0, 'target_pct': 6.0, 'long_only': True}. |
| R022 | Momentum Exhaustion Reversal to Trend (MERT) | R006/R018 show trend-following works, R008 shows dip-buying fails. Combine: wait for short-term momentum exhaustion (RSI <30) WITHIN an established uptrend, then enter on the first bounce bar. | Oversold conditions in strong uptrends create asymmetric risk-reward as weak hands capitulate near temporary bottoms, but the structural trend reasserts quickly. | promoted | **PROMOTED**: PF 1.61 gross, 29 trades, 31.0% WR. Best params: {'ma_period': 50, 'rsi_period': 14, 'rsi_threshold': 30, 'bounce_min_pct': 1.0, 'stop_pct': 2.0, 'target_pct': 6.0, 'long_only': True}. |
| R023 | Gap-and-Go Continuation (GGC) | R005 showed gaps extend rather than revert. Opposite insight: trade WITH gaps that occur in trend direction during high-momentum regimes. | Price gaps above recent range highs during established uptrends signal institutional accumulation or news-driven momentum that continues for 1-2 sessions as FOMO kicks in. | parked | Insufficient trades (0). Need 20+ for meaningful screen. |
| R024 | Volatility Regime Breakout (VRB) | R021's 2.49 PF shows compression→expansion works; extend this to identify low-vol regimes that precede large directional moves | After sustained low volatility periods (20+ bars below 30th percentile ATR), breakouts have higher follow-through because volatility mean-reverts explosively in crypto, and the first break direction tends to persist. | parked | No strategy mapping found. Add to IDEA_ARCHETYPE_MAP or include "Archetype: <name>" in notes. |
| R025 | Momentum Exhaustion Reversal (Long-Only) | R006 trend-following works (PF 1.26); flip the concept—wait for sharp UP moves to exhaust, then enter LONG on the retrace into still-bullish trend | In a structural uptrend, violent 6-8% rallies on 4H often pull back 2-3% within 24 hours before resuming; buying the first retrace after momentum exhaustion (RSI>75) captures the continuation leg with better entry than chasing. | new | Archetype: custom. {'trend_ma_period': 100, 'momentum_lookback': 12, 'rsi_period': 14, 'rsi_exhaustion': 75, 'retrace_pct': 2.0, 'max_retrace_pct': 4.0, 'entry_timeout_bars': 16, 'stop_pct': 3.0, 'target_pct': 6.0, 'long_only': True} |
| R026 | Two-Timeframe Breakout Confirmation (2TBC) | R004 multi-TF momentum added tiny edge; R006 trend-following works—combine them with breakout timing: 1H breakout + 4H trend alignment | 1H Donchian breakouts fail frequently, but when a 1H breakout occurs while 4H is also breaking above its own 20-bar high AND 4H ATR is expanding, it signals institutional-scale momentum that sustains 5-8% moves. | parked | No strategy mapping found. Add to IDEA_ARCHETYPE_MAP or include "Archetype: <name>" in notes. |
| R027 | Volatility Breakout with Momentum Confirmation (VBMC) | R021 (RCE) showed 2.49 PF with compression/expansion. Combining with directional momentum filter may improve win rate while preserving edge. | After ATR compression, breakouts that align with multi-period momentum consensus have higher follow-through probability than raw compression breakouts. | new | Archetype: dual_momentum_consensus. {'lookback_period': 30, 'breakout_threshold': 1.8, 'roc_periods': [3, 5, 10], 'consensus_threshold': 0.67, 'atr_period': 20, 'compression_lookback': 60, 'compression_percentile': 15, 'stop_pct': 2.5, 'target_pct': 7.0, 'long_only': True} |
| R028 | Trend Acceleration Breakout (TAB) | R006 trend following (PF 1.26) + acceleration concept. BTC's structural uptrend suggests accelerating trends (not decelerating bounces) have strongest edge. | Donchian breakouts that occur when price is accelerating above its trend (positive and increasing ROC) capture the highest-conviction momentum moves in an uptrending asset. | new | Archetype: acceleration_breakout. {'donchian_period': 40, 'ma_period': 100, 'roc_period': 10, 'roc_threshold': 2.0, 'roc_acceleration_bars': 3, 'stop_pct': 3.0, 'target_pct': 8.0, 'long_only': True} |
| R029 | High ATR Regime Trend Following (HARTF) | R021 showed ATR percentile detection works (2.49 PF). Inverse approach: instead of low ATR compression, trade when ATR is HIGH (volatility expansion already occurring = sustained trends). | When ATR is in top percentile (high volatility regime), breakouts represent established trends with momentum rather than false breakouts, justifying wider stops for larger moves. | new | Archetype: atr_regime_adaptive. {'ma_fast': 20, 'ma_slow': 80, 'atr_period': 20, 'atr_lookback': 60, 'regime_percentile_high': 75, 'regime_percentile_low': 25, 'high_regime_stop_mult': 3.0, 'low_regime_stop_mult': 1.5, 'target_pct': 8.0, 'long_only': True} |
| R030 | Volatility Breakout with Momentum Confirmation (VBMC) | R021's success (PF 2.49) shows compressed volatility predicts expansions. R006 shows MA filters improve directional accuracy. Combining both: use volatility compression to time entry, but require price momentum alignment. | Volatility compressions predict expansion magnitude, but adding short-term momentum confirmation (price above fast MA + positive ROC) filters for directional bias, capturing explosive trending moves while avoiding false breakouts. | new | Archetype: adaptive_momentum_burst. {'atr_period': 20, 'atr_lookback': 60, 'compression_percentile': 15, 'breakout_atr_mult': 1.5, 'trend_ma_period': 20, 'roc_period': 5, 'roc_threshold': 1.0, 'stop_pct': 2.5, 'target_pct': 6.0, 'long_only': True} |
| R031 | Acceleration Surge After Consolidation (ASAC) | R021 shows consolidation predicts moves. R004 showed ROC adds weak directional edge. Instead of using ROC as filter, use it as trigger: after price consolidates in narrow range, enter on acceleration spike (ROC crossing above threshold) rather than simple breakout. | After range consolidation, the first acceleration surge (measured by ROC) signals institutional accumulation completing and trend initiation, capturing the early phase of momentum expansion with better timing than static breakouts. | new | Archetype: acceleration_breakout. {'lookback_period': 40, 'breakout_percentile': 90, 'roc_period': 10, 'roc_threshold': 2.0, 'stop_pct': 2.5, 'target_pct': 6.0, 'long_only': True} |
| R032 | Multi-Bar Persistence Breakout (MBPB) | R006 trend-following worked (PF 1.26). Single-bar breakouts (Donchian) risk noise. Require N consecutive closes above breakout level to confirm persistence before entry, filtering whipsaws while catching sustained moves. | In crypto's high-noise environment, requiring 2-3 consecutive closes above resistance after breakout filters false breaks and captures only persistent institutional flows, improving win rate at cost of slightly delayed entry but better risk-adjusted returns. | new | Archetype: consecutive_momentum. {'lookback_period': 30, 'consecutive_bars': 3, 'min_breakout_pct': 1.0, 'stop_pct': 2.5, 'target_pct': 6.0, 'long_only': True} |

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
