# Strategy Hypothesis 003: 4H Volatility Contraction Breakout

**Status:** ARCHIVED — Gross PF 0.98, no edge
**Created:** 2026-02-07
**Archived:** 2026-02-08
**Owner:** AI Chief of Staff

---

## Thesis (5 sentences)

BTCUSD alternates between periods of low volatility (compression) and high volatility (expansion) on the 4-hour timeframe. When Bollinger Band bandwidth contracts below a threshold, it signals an imminent directional move. Entering on the first clean breakout from a compression zone — long above the upper band, short below the lower band — captures the expansion phase before it becomes crowded. By operating on 4H bars with wider profit targets (3-4%), transaction costs (~0.1%) become negligible relative to expected profit per trade (~2-5% of target). This directly addresses the fatal flaw of HYPOTHESIS_002, where 0.1% costs destroyed a thin edge on narrow 0.8% targets.

---

## What's Different From Previous Hypotheses

| Factor | H001 (London Breakout) | H002 (Mean Reversion) | **H003 (Vol Contraction)** |
|--------|----------------------|---------------------|--------------------------|
| Timeframe | 15m | 15m | **4H** |
| Edge type | Session momentum | Fade extremes | **Compression → expansion** |
| Avg trade target | ~1.5% | 0.8% | **3-4%** |
| Expected trades/6mo | 48 | 289 | **30-60** |
| Cost as % of target | ~7% | ~12.5% | **~2.5-3.3%** |
| Holding period | Hours | ~1.6 hours | **12-48 hours** |

The core design choice: **fewer, wider trades** to make transaction costs irrelevant.

---

## Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Instrument | BTCUSD | Same instrument — isolate timeframe as the variable |
| Timeframe | 4-hour bars | Aggregated from existing 15m data (16 bars per 4H candle) |
| BB period | 20 | 20 × 4H = 80 hours (~3.3 days) of lookback |
| BB std dev | 2.0 | Standard Bollinger Band width |
| Squeeze threshold | Bandwidth < 20th percentile of rolling 50-bar bandwidth | Relative compression, adapts to regime |
| Entry trigger | Close beyond BB after squeeze period (min 3 bars squeezed) | Confirms expansion, not a wick |
| Stop loss | 1.5% beyond entry | Wide enough for 4H noise, tight enough for risk control |
| Take profit | 4.0% from entry | ~2.7:1 reward/risk ratio |
| Trailing stop | Optional: move stop to breakeven after 2% unrealized profit | Protect runners |
| Max position hold | 20 bars (80 hours / ~3.3 days) | Force exit on stale trades |
| Filters | None initially — add only if baseline shows clear failure mode | Learn first, filter second (lesson from H002) |

---

## Edge Hypothesis

- **Why it might work:** Volatility clustering is one of the most robust phenomena in financial markets. Low-vol periods reliably precede high-vol periods. On 4H BTCUSD, these compressions often align with institutional accumulation/distribution before large moves. The wider targets mean we only need ~40% win rate at 2.7:1 R:R to be profitable (breakeven PF = 1.0 at 37% WR).

- **Why it might fail:** Squeezes may resolve with a false breakout (break one direction, then reverse). 4H BTCUSD may not have enough squeeze events in 6 months of data to be statistically meaningful. The stop at 1.5% might be too tight for 4H candle wicks. Or the squeeze detection threshold may be hard to calibrate without overfitting.

---

## Key Assumptions to Test

1. **Volatility clustering exists on 4H BTCUSD** — Do squeezes actually precede expansions? (Measure: average move size in the 5 bars after a squeeze vs. random 5-bar moves)
2. **Direction is predictable at squeeze breakout** — Does the breakout direction hold? (Measure: % of breakouts that reach 4% in breakout direction before hitting 1.5% stop)
3. **Enough events to be meaningful** — Do we get >= 30 trades in 6 months? Below that, the sample is too small.
4. **Transaction costs are survivable** — At 0.1% round-trip, does net PF stay above 1.3? (With 3-4% targets, this should be trivially true if gross edge exists)

---

## Validation Criteria

- [ ] Gross profit factor > 1.3 (hard threshold from H002 postmortem)
- [ ] Net profit factor > 1.2 after 0.1% transaction costs
- [ ] Win rate > 35% (lower threshold acceptable given wider R:R)
- [ ] Total trades >= 30 over test period
- [ ] Walk-forward: profitable in >= 3 of 5 windows
- [ ] Out-of-sample PF degradation < 30%
- [ ] Max drawdown < 15% of starting capital

---

## Implementation Plan

### Step 1: Data Preparation
- Add `resample_to_4h()` function to `data_loader.py`
- Verify aggregation: 16 × 15m bars → 1 × 4H bar (aligned to 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)
- Validate OHLCV correctness: open = first bar's open, high = max of all highs, low = min of all lows, close = last bar's close, volume = sum

### Step 2: Strategy Implementation
- Create `strategies/backtest/vol_contraction.py`
- Implement Bollinger Band calculation (no external deps — use stdlib statistics)
- Implement squeeze detection (rolling bandwidth percentile)
- Implement signal generation (breakout from squeeze)
- Wire up to existing `engine.py` Backtest class

### Step 3: Baseline Backtest
- Run on full BTCUSD 15m→4H data with 0% cost
- Run with 0.1% cost
- Log results in this document

### Step 4: Validation (if baseline passes)
- In-sample / out-of-sample split (70/30)
- Walk-forward (5 rolling windows)
- Live readiness check

### Step 5: Decision
- Archive if net PF < 1.2 or walk-forward < 3/5 windows profitable
- Proceed to refinement only if baseline is close (PF 1.1-1.2) with a clear, justified filter

---

## Data Requirements

- **Source**: Existing `data/BTCUSD_15m.csv` (17,276 bars, Aug 2025 — Feb 2026)
- **Aggregation**: 15m → 4H = ~1,080 bars (17,276 / 16)
- **Lookback needed**: 20 bars BB + 50 bars bandwidth percentile = 70 bars warm-up
- **Effective test period**: ~1,010 bars (~168 days / ~5.6 months)
- **No new data needed** — this is entirely doable with existing infrastructure

---

## Risk Budget

At 1.5% stop loss per trade with ~30-60 trades expected:
- Worst case (all losses): 45-90% drawdown — unrealistic but sets the ceiling
- Realistic worst case (~5 consecutive losses): 7.5% drawdown
- Target max drawdown: < 15%

This is well within the backtest engine's tracking capability.

---

## Notes

*This hypothesis directly addresses the transaction cost problem that killed H002. The strategy is designed around the constraint: targets must be wide enough that 0.1% costs are noise, not signal. If volatility contraction breakouts don't work on 4H BTCUSD, the next direction should be a different instrument (forex or ETH) rather than further BTCUSD optimization.*

---

## Backtest Results (Quick Screen — 2026-02-08)

| Metric | Gross (0% costs) | Net (0.1% costs) |
|--------|-------------------|-------------------|
| Total Trades | 149 | 149 |
| Win Rate | 26.8% | 26.8% |
| Profit Factor | 0.98 | 0.89 |
| Net P&L | -$2,314 (-3.5%) | -$12,343 (-18.4%) |
| Avg Win | $2,693 | $2,626 |
| Avg Loss | -$1,009 | -$1,077 |
| Expectancy | -$15.53/trade | -$82.84/trade |
| Max Drawdown | $18,468 | $23,480 |
| Max DD Duration | 408 days | 408 days |
| Sharpe | -0.07 | -0.36 |
| Buy & Hold | +$47,040 (+203%) | +$47,040 (+203%) |
| Live Readiness | 1/7 | 1/7 |

Data: 6,571 4H bars (3 years, Feb 2023 — Feb 2026).

**Decision: KILL.** Gross PF < 1.0. No edge exists.

---

## Postmortem

1. **Expected:** Squeeze → expansion with directional predictability. ~40% WR at 2.67:1 R:R would yield PF ~1.4. Wider targets (4%) would make costs negligible.

2. **What happened:** Squeeze detection worked (149 trades, reasonable frequency). R:R worked (avg win $2,693 vs avg loss $1,009 = 2.67:1). But win rate was 26.8% — the breakout direction after a squeeze is essentially random. Gross PF 0.98 means no edge before costs.

3. **Learned:**
   - **Volatility contraction predicts expansion magnitude, not direction.** This is a known property of squeeze-based strategies. The squeeze tells you a big move is coming, but NOT which way.
   - **The R:R ratio was correctly designed** — avg win/loss confirmed the 2.67:1 target. The problem was entirely in direction prediction.
   - **Fix the direction problem.** If we could predict direction even slightly (35%+ WR), the existing R:R structure would be profitable. This suggests combining squeeze detection with a directional filter (trend, momentum, order flow).
   - **Quick screen worked as intended.** 30 minutes, clear result, no wasted effort on full validation.
