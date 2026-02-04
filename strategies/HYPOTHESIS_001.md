# Strategy Hypothesis 001: London Session Momentum Breakout

**Status:** Research  
**Created:** 2026-02-03  
**Owner:** AI Chief of Staff  

---

## Thesis (5 sentences)

BTCUSD exhibits predictable volatility expansion at the London open (08:00 GMT) as European institutional flow enters the market. The Asian session range often acts as a consolidation zone that gets broken with directional momentum when London traders initiate positions. A breakout strategy that enters on a clean break of the Asian high/low, with stops at the opposite boundary and targets at 1.5-2x the Asian range, should capture this institutional flow. This edge exists because retail traders are often caught on the wrong side of these moves, providing liquidity for the breakout. The strategy uses defined stops and clear risk parameters.

---

## Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Instrument | BTCUSD | High liquidity crypto pair, 24/7 trading |
| Timeframe | 15-minute bars | Balances noise filtering with timely entries |
| Session | Asian range: 00:00-08:00 GMT | Defines consolidation zone |
| Entry window | 08:00-12:00 GMT | London session momentum period |
| Entry trigger | Close above/below Asian high/low | Confirms breakout vs. wick |
| Stop loss | Opposite side of Asian range | Defined risk |
| Take profit | 1.5x Asian range OR trail at 1x | Captures expansion without overstaying |
| Filters | Skip if Asian range > 3% of price | Avoid extended ranges with no room to run |

---

## Edge Hypothesis

- **Why it might work:** Institutional order flow at London open creates directional momentum. Asian consolidation provides clear levels. The pattern repeats because of time-zone-driven liquidity cycles.
  
- **Why it might fail:** Choppy days with no follow-through. Major news events mid-session. Spread widening at open eating into edge.

---

## Validation Criteria

- [ ] Win rate > 45% over 100+ trades
- [ ] Profit factor > 1.3
- [ ] Max drawdown < 10% of account
- [ ] Consistent performance on BTCUSD
- [ ] Holds up in 2024-2025 data (out-of-sample)

---

## Next Steps

1. Source historical 15-min OHLC data for BTCUSD (2023-2025)
2. Implement basic backtest logic
3. Run initial backtest and document results
4. If promising, refine parameters; if not, archive and move to next hypothesis

---

## Notes

*This is a starting hypothesis, not a proven strategy. The goal is to test quickly and either validate or discard.*
