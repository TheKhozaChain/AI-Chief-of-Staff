# Strategy Hypothesis 006: Daily Timeframe Trend

**Status:** PROMOTED — awaiting full validation  
**Created:** 2026-02-09  
**Promoted:** 2026-02-09  
**Owner:** AI Chief of Staff  
**Parent Research:** R006 (longer holds help), R011 (daily timeframe trend)

---

## Thesis (5 sentences)

BTCUSD exhibits persistent multi-week trends on the daily timeframe that are obscured by intraday noise on 15m and 1H charts. A simple dual moving average crossover with 5-day fast and 40-day slow periods captures intermediate-term directional shifts while filtering out false signals that plague shorter timeframes. By holding positions for weeks rather than hours, the strategy allows trends to develop fully while transaction costs (~0.1% per trade) become negligible relative to 24% profit targets. The 6% stop loss accommodates daily volatility (~3-5% typical range) without premature exits, while the 4:1 reward-to-risk ratio requires only 35% win rate for profitability—exactly what quick-screening delivered. This design directly addresses the core insight from R006: longer holding periods fundamentally change the cost/edge equation, transforming transaction drag from fatal (12.5% of target in H002) to trivial (0.4% of target here).

---

## What's Different From Previous Hypotheses

| Factor | H002 (Mean Reversion) | H003 (Vol Contraction) | **H006 (Daily Trend)** |
|--------|---------------------|----------------------|----------------------|
| Timeframe | 15m | 4H | **1D** |
| Edge type | Fade extremes | Compression breakout | **Trend following** |
| Avg trade target | 0.8% | 3-4% | **24%** |
| Avg stop loss | 0.4% | ~2% | **6%** |
| Expected trades/6mo | 289 | 30-60 | **~10** |
| Cost as % of target | ~12.5% | ~2.5-3.3% | **~0.4%** |
| Holding period | ~1.6 hours | 12-48 hours | **1-4 weeks** |
| Direction | Mean reversion | Bidirectional breakout | **Long only** |

The fundamental shift: **weekly holding periods** make this a position trade, not a day trade. Transaction costs become a rounding error.

---

## Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Instrument | BTCUSD | Consistent with all prior hypotheses |
| Timeframe | 1-day bars | Aggregated from 1H data (24 bars per daily candle) |
| Fast MA period | 5 days | 1 trading week — captures short-term momentum |
| Slow MA period | 40 days | ~8 trading weeks — defines intermediate trend |
| MA type | Simple (SMA) | Standard, interpretable, used in screening |
| Entry signal | Fast MA crosses above Slow MA | Classic bullish trend initiation |
| Exit - profit target | +24% from entry | 4:1 reward-to-risk; observed in quick-screen |
| Exit - stop loss | -6% from entry | 1 ATR on daily timeframe (~5-7% typical) |
| Position direction | Long only | Crypto native upward bias; simplifies first validation |
| Position sizing | Fixed 1 unit | Risk management applied in live deployment phase |

---

## Edge Hypothesis

**Core edge:** Multi-week crypto trends persist longer than participants expect because:

1. **Momentum cascade** — As daily trend establishes, it attracts algorithmic trend followers, creating self-reinforcing flow
2. **Information diffusion lag** — Fundamental catalysts (regulations, adoption, macro shifts) take weeks to fully price in, not hours
3. **Timeframe arbitrage** — Day traders and scalpers create intraday noise that obscures the cleaner directional signal visible on daily charts

**Why 35% win rate is sufficient:**
- Quick-screen: 20 trades, 7 winners (35%), PF 1.9 gross
- Math: With 4:1 R:R ratio, break-even WR = 20%. We have 15% cushion.
- Expected value per trade: (0.35 × 24%) + (0.65 × -6%) = 8.4% - 3.9% = **4.5% per trade**
- Even with 0.1% cost twice (entry + exit), net EV = 4.3% per trade

**Why parameter values make sense:**
- 5/40 MA combo: Fast enough to catch trend starts, slow enough to avoid whipsaws
- 24% target: Represents a significant crypto move (~2-3 week sustained trend)
- 6% stop: Wider than daily noise (3-5%), tighter than trend invalidation (10%+)

---

## Validation Criteria

### Must Pass (Walk-Forward)

| Metric | Threshold | Quick-Screen Result | Rationale |
|--------|-----------|-------------------|-----------|
| Gross Profit Factor | > 1.5 | **1.9** ✓ | Core edge must survive all time periods |
| Win Rate | > 30% | **35%** ✓ | With 4:1 R:R, 30% is mathematical minimum |
| Net Profit Factor (after costs) | > 1.3 | TBD | 0.2% round-trip cost per trade |
| Total trades (3 years) | > 40 | Est. 60-70 | Need statistical sample size |
| Max consecutive losses | < 10 | TBD | Risk of ruin check |
| Worst drawdown | < 40% | TBD | Must be recoverable psychologically |

### Performance Stability

- **Consistency across years:** PF must be > 1.3 in at least 2 of 3 annual periods
- **Walk-forward degradation:** Out-of-sample PF must be > 80% of in-sample PF
- **Parameter sensitivity:** Varying fast MA ±1 day and slow MA ±5 days should maintain PF > 1.3

### Regime Analysis

Test performance separately across:
- **Bull markets** (BTC +20% over 90 days): Expect 40%+ WR
- **Bear markets** (BTC -20% over 90 days): Long-only should flat-line (few signals)
- **Sideways** (BTC ±10% over 90 days): Critical test — avoid whipsaw losses

---

## Data Requirements

**Available:**
- 3 years BTCUSD 1H data: 26,000 bars → aggregates to ~1,095 daily bars
- 3 years BTCUSD 15m data: 105,000 bars → can validate daily aggregation

**Aggregation method:**
```
Daily bar = {
  Open: first 1H open of 00:00-23:00 UTC day
  High: max of 24 × 1H highs
  Low: min of 24 × 1H lows  
  Close: last 1H close of 23:00 UTC
  Volume: sum of 24 × 1H volumes
}
```

**Walk-forward structure:**
- Year 1 (365 days): In-sample optimization/validation of 5/40 parameters
- Year 2 (365 days): Out-of-sample test (frozen parameters)
- Year 3 (365 days): Out-of-sample confirmation
- Total: ~1,095 daily bars (adequate for 40-bar slow MA with warmup)

---

## Implementation Plan

### Phase 1: Full Validation (Week 1)
- [ ] Aggregate 1H data to daily bars (verify OHLC alignment)
- [ ] Implement 5/40 SMA crossover logic with 6%/-24% exits
- [ ] Run walk-forward backtest with 0.2% round-trip costs
- [ ] Generate equity curve, trade log, and drawdown chart
- [ ] Calculate all validation metrics from table above
- [ ] **Decision gate:** If Net PF < 1.3 in any year → ARCHIVE

### Phase 2: Robustness Testing (Week 1)
- [ ] Parameter sweep: Fast MA [4,5,6], Slow MA [35,40,45]
- [ ] Stop loss sensitivity: [4%, 