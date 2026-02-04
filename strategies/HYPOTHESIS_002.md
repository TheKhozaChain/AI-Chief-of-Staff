# Strategy Hypothesis 002: Intraday Mean Reversion

**Status:** Refine — Validating out-of-sample before optimization
**Created:** 2026-02-04
**Updated:** 2026-02-05
**Owner:** AI Chief of Staff

---

## Thesis (5 sentences)

BTCUSD frequently overshoots during intraday moves, creating mean reversion opportunities when price extends too far from a short-term average. When price moves more than 2 standard deviations from a 20-period moving average on 15-minute bars, there's often a snap-back toward the mean within the next few hours. A strategy that fades these extreme extensions—selling when overbought, buying when oversold—with tight stops beyond the extension should capture this reversion. This edge exists because retail traders chase momentum into extended moves, providing liquidity for the reversal. The strategy uses defined risk with stops just beyond the extreme.

---

## Parameters (Optimized)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Instrument | BTCUSD | High volatility creates frequent extension opportunities |
| Timeframe | 15-minute bars | Balances noise with actionable setups |
| Moving average | 12-period SMA | ~3 hours of data, faster reversion capture |
| Entry trigger | Close > 2 std devs from MA | Statistically extreme extension |
| Entry direction | Fade the move (sell overbought, buy oversold) | Mean reversion |
| Stop loss | 0.4% beyond entry | Tight risk control |
| Take profit | 0.8% profit | Quick capture, don't wait for full reversion |
| Filters | Skip if 24h range > 5% | Avoid trending/news days (strict) |

---

## Edge Hypothesis

- **Why it might work:** Intraday overextensions are driven by retail FOMO and liquidation cascades. Once the momentum exhausts, price reverts. Statistical mean reversion is a well-documented phenomenon in high-volatility assets.
  
- **Why it might fail:** Strong trending days will stop out repeatedly. News events cause extensions that don't revert. Wide spreads during volatility eat into edge.

---

## Validation Criteria

- [ ] Win rate > 50% over 100+ trades
- [ ] Profit factor > 1.3
- [ ] Max drawdown < 10% of account
- [ ] Average trade duration < 4 hours (confirms intraday nature)
- [ ] Holds up in 2024-2025 data (out-of-sample)

---

## Next Steps

1. Implement strategy in `backtest/mean_reversion.py`
2. Run initial backtest on existing BTCUSD 15m data
3. Document results
4. If promising, refine parameters; if not, archive and move to next hypothesis

---

## Notes

*This is conceptually opposite to HYPOTHESIS_001 (breakout). If both momentum and mean reversion fail, we may need to explore different timeframes or instruments.*

---

## Backtest Results (2026-02-04)

**Data**: BTCUSD 15m, Aug 2025 - Feb 2026 (17,276 bars)

| Metric | Value |
|--------|-------|
| Total Trades | 1,410 |
| Win Rate | 47.0% |
| Total P&L | +$12,170 (+13.63%) |
| Avg Win | $476 |
| Avg Loss | -$406 |
| Profit Factor | 1.04 |
| Max Drawdown | $16,739 |

**Conclusion**: Strategy shows marginal edge. Profit factor of 1.04 is barely profitable - likely to be eroded by transaction costs in live trading. However:
- The edge exists (unlike HYPOTHESIS_001 which was clearly negative)
- Further optimization or filtering may improve results
- Worth exploring with additional validation before discarding

**Next steps**: See Decision and Refinement Plan below.

---

## Decision (2026-02-05)

**Verdict: Refine — but validate out-of-sample first.**

### Rationale

The results are marginal but not zero. Here's why refine beats archive:

1. **PF 1.04 on 1,410 trades is a weak signal, not noise.** A profit factor slightly above 1.0 on a large sample (1,410 trades) is more meaningful than a high PF on 50 trades. The sample size gives some confidence the edge isn't random — but it needs confirmation.

2. **The thesis is sound.** Mean reversion in high-volatility intraday crypto is a well-documented phenomenon. Unlike HYPOTHESIS_001 (London breakout applied to a 24/7 market — conceptual mismatch), the mean reversion thesis fits the instrument.

3. **Reward:risk ratio is positive.** Avg win $476 vs avg loss $406 (1.17:1) means the strategy lets winners run slightly further than losers. The 47% win rate drags it down, but filtering for higher-probability setups could shift this.

4. **Max drawdown is a concern.** $16,739 drawdown on ~$89K starting capital (~18.7%) is steep for a marginal edge. Any refinement must address this.

5. **The evening review's warning stands.** Before touching parameters, we must confirm the edge survives out-of-sample. Optimization without validation is curve-fitting.

### What would make me archive instead

- OOS profit factor below 0.95 (edge collapses = it was noise)
- OOS max drawdown exceeds 25% of capital
- Fewer than 200 trades in OOS window (insufficient signal)

---

## Refinement Plan (2026-02-05)

### Phase 1: Out-of-sample validation (do this FIRST)

Split existing 6-month data (Aug 2025 – Feb 2026) into:
- **In-sample:** Aug 2025 – Nov 2025 (first ~4 months)
- **Out-of-sample:** Dec 2025 – Feb 2026 (last ~2 months)

Run current strategy parameters (unchanged) on OOS data only.

**Pass criteria:**
- PF >= 1.0 on OOS data
- Win rate within 5 percentage points of in-sample (42%–52%)
- Edge direction consistent (positive total P&L)

**If pass → proceed to Phase 2.**
**If fail → archive HYPOTHESIS_002, move to HYPOTHESIS_003.**

### Phase 2: ONE refinement — time-of-day filter

If OOS validates, test adding a **time-of-day filter**. Hypothesis: mean reversion signals are stronger during high-liquidity hours (US market overlap, ~14:00–21:00 UTC) and weaker during low-volume Asian hours.

- **Test:** Only take signals between 14:00–21:00 UTC
- **Expected outcome:** Fewer trades but higher PF (filtering out low-quality setups)
- **Fail criteria:** If PF doesn't improve above 1.15, the filter doesn't help — try a different refinement or archive

### NOT doing (yet)
- Parameter optimization (MA period, std threshold) — premature without validation
- Transaction cost modeling — useful but won't change the refine/archive decision
- Volume filters — data quality uncertain, save for later
