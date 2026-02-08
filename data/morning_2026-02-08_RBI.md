# Morning Brief - 2026-02-08 (RBI Update)

Generated at: afternoon session (post-RBI integration)

---

### Day Context
Sunday. The RBI framework was just integrated across the entire system. Good day to put it to work — implement H003 and get a PF number before the week starts.

### Top 3 Priorities

1. **Implement and quick-screen HYPOTHESIS_003 (vol contraction breakout)**
   - Write `vol_contraction.py`, run it against 3yr BTCUSD 4H data
   - Why: H003 has been scoped since Feb 7. The evening review flagged this — don't let scoped strategies sit. This is Phase B of the RBI loop.
   - Done when: Baseline PF number exists. Decision made: kill, refine, or proceed to full validation.

2. **Quick-screen one more idea from the research backlog**
   - Pick the most testable idea from R003-R005 and run a 30-minute screen
   - Why: The pipeline needs throughput. H003 alone isn't enough flow through the RBI loop.
   - Done when: One R-idea has a status change (killed or screening).

3. **Source 2 new research ideas from external sources**
   - Scan Google Scholar or open-source strategy repos for crypto/quant ideas
   - Why: Research backlog has 4 ideas, but all sourced internally. The funnel needs external input (Principle 17: Wide Funnel, Narrow Gate).
   - Done when: 2 new rows added to RESEARCH_BACKLOG.md with source, thesis, and testability noted.

### Suggested Focus Block
Now through next 3 hours: Implementation + screening session
- Priority #1 first — get vol_contraction.py running
- Then switch to priority #2 if energy holds
- No new scoping or planning during this block — execution only

### RBI Loop Status
- **Research:** 4 ideas in backlog (R002-R005). All internally sourced. Need external input — pipeline will go stale otherwise.
- **Backtest:** H003 scoped, not yet screened. R003 (Volume Profile), R004 (Multi-TF Momentum), R005 (Weekend Gap) all unscreened.
- **Implement:** Nothing near live-readiness. No strategy has passed full validation yet.
- **Today's RBI focus:** Backtest (B). H003 implementation is the bottleneck. Secondary: widen the Research funnel.

### Quant/AI Task
**[B phase]** Implement `vol_contraction.py`:
- Bollinger Band calculation (20-period, 2.0 std dev) — stdlib only
- Squeeze detection (bandwidth < 20th percentile of rolling 50 bars)
- Breakout signal (close beyond BB after 3+ bars squeezed)
- Stop: 1.5%, Target: 4.0%
- Run on 3yr 4H data (~6,500 bars — significantly more than the 1,080 originally estimated when we only had 6 months of data)
- Check gross PF. If < 1.3, kill immediately. If > 1.5, proceed to full validation.

### Leverage Idea
Note on H003: the data requirements section in HYPOTHESIS_003.md still references "17,276 bars, Aug 2025 — Feb 2026" from before the data overhaul. We now have 105K 15m bars (3 years), which gives ~6,500 4H bars. Update that section — it changes the statistical power of the backtest significantly.
