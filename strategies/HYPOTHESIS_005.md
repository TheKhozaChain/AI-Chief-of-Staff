# Strategy Hypothesis 005: Donchian Channel Breakout

**Status:** PROMOTED — awaiting full validation  
**Created:** 2024-01-XX  
**Promoted from:** Quick-screen R009 (PF 1.31 gross, 134 trades)  
**Owner:** AI Research Team

---

## Thesis (5 sentences)

Price breakouts from N-period high/low channels (Donchian Channels) capture the start of sustained trends in BTCUSD before the broader market recognizes the move. A 20-bar channel on the 1-hour timeframe represents 20 hours (~1 trading day) of price action, making breakouts statistically significant departures from recent consolidation. By taking only long positions when price exceeds the 20-bar high, we align with Bitcoin's long-term upward bias while avoiding the complexity of timing short entries in an asset prone to violent short squeezes. The 2% stop loss and 6% profit target create a 3:1 reward-to-risk ratio that tolerates a 33.6% win rate while maintaining profitability, with transaction costs (~0.1% × 2 = 0.2% round-trip) representing only 3.3% of the profit target. This simpler breakout logic eliminates the lag and whipsaw issues inherent in moving average crossover systems, entering decisively at defined price levels rather than waiting for indicator convergence.

---

## What's Different From Previous Hypotheses

| Factor | H001 (London) | H002 (Mean Rev) | H003 (Vol Contract) | H004 (MA Cross) | **H005 (Donchian)** |
|--------|---------------|-----------------|---------------------|-----------------|---------------------|
| Timeframe | 15m | 15m | 4H | 1H | **1H** |
| Edge type | Session momentum | Fade extremes | Compression | Trend following | **Range breakout** |
| Entry logic | Time-based | Oscillator | BB squeeze | MA crossover | **Price > N-bar high** |
| Directional | Long only | Long/short | Long/short | Long/short | **Long only** |
| Avg target | 1.5% | 0.8% | 3-4% | 2.0% | **6.0%** |
| Stop loss | 0.8% | 0.4% | 2.0% | 1.5% | **2.0%** |
| R:R ratio | 1.9:1 | 2:1 | 1.5-2:1 | 1.3:1 | **3:1** |
| Expected trades/6mo | 48 | 289 | 30-60 | 180 | **~65-70** |
| Setup complexity | Medium | Low | High | Medium | **Very low** |

The core design choice: **simplicity and asymmetry**. Single clear entry condition (new 20-bar high), no lagging indicators, long-only to capture Bitcoin's structural uptrend, and wide targets to make costs negligible.

---

## Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Instrument | BTCUSD | Same as all prior hypotheses — consistent test asset |
| Timeframe | 1-hour bars | Available in dataset (26K bars = ~3 years); balances signal quality vs. trade frequency |
| Channel period | 20 bars | 20 hours = ~1 trading day; optimal from screening across [10, 15, 20, 25, 30] |
| Entry trigger | Price closes above 20-bar high | Requires full hourly bar close to confirm breakout, reduces false signals |
| Direction | Long only | Bitcoin has positive skew; shorts prone to violent reversals |
| Stop loss | 2.0% from entry | Tested [1.5%, 2.0%, 2.5%]; 2.0% optimal balance of protection vs. noise |
| Profit target | 6.0% from entry | Tested [4%, 5%, 6%, 7%]; 6.0% maximized profit factor in screening |
| Position sizing | Fixed 1% account risk per trade | Stop distance = 2%, so position size = 1% / 2% = 0.5× account |
| Max concurrent | 1 position | Single-position simplicity; no pyramiding |

---

## Edge Hypothesis

**Primary edge:** Donchian breakouts identify the transition from consolidation (mean-reverting regime) to expansion (trending regime) before momentum indicators catch up. The 20-bar lookback is short enough to capture early trend initiation but long enough to filter intraday noise.

**Why this edge exists:**

1. **Information asymmetry:** Breakouts are visible to all participants, but most retail traders wait for "confirmation" (multiple bars, indicator alignment), by which time 20-40% of the move is complete. We enter on the first clean break.

2. **Structural Bitcoin bias:** BTC has exhibited long-term appreciation with periodic drawdowns. Long-only positioning captures 60-70% of historical Bitcoin regimes (uptrends and consolidations), avoiding only the 30-40% drawdown periods where stops protect capital.

3. **Asymmetric payoff:** The 3:1 R:R ratio means we only need to be right 25% of the time to break even (before costs). At 33.6% win rate, each 100 trades generates:
   - Wins: 33.6 × 6% = +201.6%
   - Losses: 66.4 × -2% = -132.8%
   - Gross: +68.8% (PF = 1.52 theoretical)
   - Costs: 100 trades × 0.2% = -20%
   - Net: +48.8% (PF = 1.37 net)

4. **Cost efficiency:** With 6% targets, the 0.2% round-trip cost is only 3.3% of gross profit per winner, compared to 13-20% in prior mean-reversion hypotheses.

**Why it might NOT exist:**

- Donchian breakouts are textbook signals; any inefficiency may have been arbitraged away by systematic funds.
- 1H timeframe may still be too fast for sustained trends; breakouts could be noise in a fundamentally ranging market.
- Long-only positioning incurs extended drawdowns during bear markets (e.g., 2022 -65% BTC decline).

---

## Validation Criteria

### Must pass ALL of the following:

1. **Walk-forward validation:**
   - Split 3 years into 6 periods (6-month chunks)
   - Train on first 12 months → test on next 6 months
   - Roll forward 6 months, repeat
   - **Pass:** Net PF > 1.20 in at least 4 of 5 test periods

2. **Transaction cost sensitivity:**
   - Test at costs: [0.05%, 0.10%, 0.15%, 0.20%]
   - **Pass:** Net PF > 1.15 at 0.15% costs (above expected maker/taker blended rate)

3. **Sharpe ratio:**
   - **Pass:** Annualized Sharpe > 0.8 on equity curve in walk-forward test periods

4. **Maximum drawdown:**
   - **Pass:** Max drawdown < 25% in any single test period

5. **Trade frequency stability:**
   - **Pass:** Number of trades per 6-month period stays within 40-100 range (no regime collapse)

6. **Win rate stability:**
   - **Pass:** Win rate in each test period between 25-45% (within 1.5 std dev of expected 33.6%)

### Strong signals (not required, but increase confidence):

- Monthly returns are positively skewed (median > mean)
- Strategy outperforms buy-and-hold during 2021-2022 drawdown period
- Profit factor improves when BTC 200-day MA is rising (confirming long bias edge)

---

## Implementation Plan

### Phase 1: Full Backtest (Week 1)
- [ ] Load 26K bars of BTCUSD 1H data (2021-2024)
- [ ] Implement Donchian channel calculation (rolling 20-bar high/low)
- [ ] Code entry logic: `if close > high_20 and no_position: enter_long()`
- [ ] Code exit logic: stop at entry - 2%, target at entry + 6%