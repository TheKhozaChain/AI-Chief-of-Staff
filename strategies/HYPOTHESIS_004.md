# Strategy Hypothesis 004: Volatility-Adjusted Trend Following

**Status:** PROMOTED — awaiting full validation  
**Created:** 2026-02-09  
**Research ID:** R007  
**Owner:** AI Chief of Staff

---

## Thesis (5 sentences)

Trend-following strategies suffer from constant position sizing, which creates asymmetric risk exposure — equal capital deployed during both calm trends and violent whipsaws. By scaling position size inversely to ATR (Average True Range), we risk the same dollar amount per unit of volatility, deploying larger size during stable trends and shrinking during chaos. A 30-period moving average identifies trend direction, while 20-period ATR measures current volatility for dynamic sizing. Wide stops (3× ATR) and targets (6× ATR) create a 2:1 reward-risk ratio that tolerates a 44-45% win rate while maintaining profitability. Operating on 1-hour timeframe with multi-day holding periods makes transaction costs (~0.1%) negligible relative to 3-6 ATR profit targets (typically 2-4% in calm markets, 6-12% in volatile markets).

---

## What's Different From Previous Hypotheses

| Factor | H001 (London Breakout) | H002 (Mean Reversion) | H003 (Vol Contraction) | **H004 (Vol-Adjusted Trend)** |
|--------|----------------------|---------------------|--------------------------|--------------------------|
| Timeframe | 15m | 15m | 4H | **1H** |
| Edge type | Session momentum | Fade extremes | Compression → expansion | **Adaptive trend** |
| Avg trade target | ~1.5% | 0.8% | 3-4% | **2-6% (volatility dependent)** |
| Expected trades/6mo | 48 | 289 | 30-60 | **40-50** |
| Cost as % of target | ~7% | ~12.5% | ~2.5-3.3% | **~2-5%** |
| Holding period | Hours | ~1.6 hours | 12-48 hours | **24-72 hours** |
| Position sizing | Fixed | Fixed | Fixed | **Inverse volatility** |

The core innovation: **risk-adjusted sizing** transforms a standard trend system into a volatility-adaptive strategy that automatically de-risks during dangerous periods.

---

## Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Instrument | BTCUSD | Tested on same instrument for consistency |
| Timeframe | 1-hour bars | 26,280 bars available (3 years) |
| MA period | 30 bars | 30 hours (~1.25 days) captures short-term trend without lag |
| ATR period | 20 bars | 20 hours captures recent volatility regime |
| Stop loss | 3.0 × ATR | Wide enough to survive normal noise (95th percentile of hourly moves) |
| Profit target | 6.0 × ATR | 2:1 reward-risk creates profitability at 44.8% win rate |
| Trend filter period | 80 bars | 80 hours (~3.3 days) longer-term trend alignment |
| Direction | Long only | Crypto native upward bias; eliminates short-side whipsaw |
| Position sizing | Base size × (ATR_baseline / ATR_current) | Normalize risk: 2× size when volatility halves, 0.5× when doubles |
| ATR baseline | Median ATR over full lookback | Fixed reference point for sizing calculations |

---

## Edge Hypothesis

**Core mechanism:** Volatility clustering creates predictable risk regimes. During low-volatility trends (ATR below median), price moves are more directional and less noisy — the optimal time to deploy maximum capital. During high-volatility periods (ATR above median), increased noise and mean reversion make trends less reliable — the optimal time to reduce exposure.

**Why it should work:**
1. **Regime adaptation:** Volatility persistence means today's calm predicts tomorrow's calm (autocorrelation ~0.6-0.7 in hourly ATR)
2. **Risk normalization:** Each trade risks the same ~1.5-2% regardless of volatility, preventing outsized losses during chaos
3. **Trend alignment:** 80-bar trend filter eliminates counter-trend trades, focusing only on dominant direction
4. **Asymmetric payoff:** 6:3 ATR target:stop with 44.8% win rate → expected value of +0.48 ATR per trade before costs

**Quick-screen validation:**
- Gross profit factor: 1.46 (significantly above 1.0 breakeven)
- 87 trades over test period (~29 trades/year on 3 years of data)
- 44.8% win rate with 2:1 target:stop validates payoff asymmetry
- Long-only design captures crypto's structural upward drift

---

## Validation Criteria

### Promotion Threshold (✓ PASSED in quick-screen)
- [x] Gross PF > 1.3 over full sample → **Achieved 1.46**
- [x] Win rate 40-50% range → **Achieved 44.8%**
- [x] Minimum 50 trades → **Achieved 87 trades**
- [x] Logical parameter values → **All parameters within reasonable ranges**

### Full Validation Requirements (next phase)

**Walk-forward analysis:**
- [ ] Divide 3-year dataset into 6 periods of 6 months each
- [ ] Rolling optimization: optimize on 12 months, test on next 6 months
- [ ] Net PF > 1.25 in at least 4 of 5 out-of-sample periods
- [ ] Median out-of-sample PF within 15% of in-sample median PF
- [ ] No catastrophic failure period (drawdown > 40% in any single 6-month window)

**Robustness tests:**
- [ ] Parameter sensitivity: PF > 1.2 for MA period ±20%, ATR period ±20%
- [ ] ATR multiplier stability: Test stop range [2.5, 3.5] and target range [5.0, 7.0]
- [ ] Trend filter range: Test [60, 100] bars without significant PF collapse
- [ ] Transaction cost stress: Net PF > 1.15 at 0.15% per side (50% cost increase)

**Statistical significance:**
- [ ] T-test on trade returns: p-value < 0.05 for mean > 0
- [ ] Permutation test: Strategy PF in top 5% of 1,000 random entry permutations
- [ ] Monte Carlo: 95% confidence interval for 6-month returns excludes zero

**Practical viability:**
- [ ] Maximum drawdown < 30% (at base 1.0× sizing)
- [ ] Longest losing streak ≤ 8 consecutive trades
- [ ] Minimum trade frequency: 20+ trades per year
- [ ] Average trade duration: 24-96 hours (allows manual oversight)

---

## Implementation Plan

### Phase 1: Walk-Forward Validation (Week 1)
**Objective:** Verify edge persists out-of-sample

**Tasks:**
1. Prepare 6 rolling windows on 26K 1H bars:
   - Train 1: 2023-Q1/Q2 → Test: 2023-Q3
   - Train 2: 2023-Q2/Q3 → Test: 2023-Q4
   - Train 3: 2023-Q3/Q4 → Test: 2024-Q1
   - Train 4: 2023-Q4/2024-Q1 → Test: 2024-Q2
   - Train 5: 2024-Q1/Q2 → Test: 2024-Q3
   - Train 6: 2024-Q2/Q3 → Test: 2024-Q4

2. For each window:
   - Re-optimize MA period [20, 40], ATR period [15, 25], multipliers [2.5-3.5, 5-7]
   - Record best in-sample parameters
   - Apply to out-of-sample test period
   - Calculate net PF, Sharpe, max DD with 0.10% transaction costs

3. **Success criteria:** 4+ out of 5 test periods with