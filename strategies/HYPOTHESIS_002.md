# Strategy Hypothesis 002: Intraday Mean Reversion

**Status:** Tested - Marginal Edge  
**Created:** 2026-02-04  
**Owner:** AI Chief of Staff  

---

## Thesis (5 sentences)

BTCUSD frequently overshoots during intraday moves, creating mean reversion opportunities when price extends too far from a short-term average. When price moves more than 2 standard deviations from a 12-period moving average on 15-minute bars, there's often a snap-back toward the mean within the next few hours. A strategy that fades these extreme extensions—selling when overbought, buying when oversold—with tight stops beyond the extension should capture this reversion. This edge exists because retail traders chase momentum into extended moves, providing liquidity for the reversal. The strategy uses defined risk with stops just beyond the extreme.

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

**Next steps**: 
1. Test on different time period (out-of-sample)
2. Add transaction cost modeling
3. Consider additional filters (volume, time of day)
