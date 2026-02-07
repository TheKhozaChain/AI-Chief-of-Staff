# Weekly Review — Week Ending 2026-02-07

Generated at: 2026-02-07 (Saturday)  
Review period: Monday 2026-02-03 to Saturday 2026-02-07

---

### Week Summary

First full operational week for the AI Chief of Staff system. Built the entire infrastructure from scratch (GitHub Actions, email delivery, backtesting scaffold), then tested two trading hypotheses back-to-back. Both hypotheses were archived — one clearly negative, one marginally positive but destroyed by transaction costs. The week ended with system tooling mature and a clear next hypothesis scoped.

---

### What Got Done

- **AI Chief of Staff system operational** (Feb 3): GitHub Actions workflows, Anthropic API, Resend email delivery, morning brief system — all wired and working.
- **HYPOTHESIS_001 tested and archived** (Feb 3-4): London Session Momentum Breakout on BTCUSD 15m. Result: 33% win rate, PF 0.48. Clearly negative — institutional session breakout logic doesn't apply to crypto.
- **BTCUSD 15m data sourced** (Feb 4): 17,276 bars covering Aug 2025 — Feb 2026. Foundation for all strategy testing.
- **HYPOTHESIS_002 tested and refined** (Feb 4-6): Intraday Mean Reversion on BTCUSD 15m. Baseline PF 1.04 over 1,410 trades. Refined with time-of-day filter (20-23 UTC): PF 1.18, 55.4% WR, 289 trades.
- **Transaction cost modeling added to engine** (Feb 6): 0.1% round-trip cost support. Revealed H002's edge is a mirage — net PF 0.69.
- **Walk-forward and OOS validation built** (Feb 6): Rolling-window and in-sample/out-of-sample validation. H002 lost money in all 5 walk-forward windows.
- **HYPOTHESIS_002 archived** (Feb 6): Full postmortem written. Edge doesn't survive real-world friction.
- **Backtest code cleaned up** (Feb 6): Docstrings, readability improvements across engine, mean_reversion, and london_breakout modules.
- **Weekly review prompt created** (Feb 7): End-of-week reflection template added to PROMPTS/.
- **HYPOTHESIS_003 scoped** (Feb 7): 4H Volatility Contraction Breakout on BTCUSD. Designed to address the cost problem with wider targets (4% vs 0.8%) and fewer trades.
- **4H resampling utility added** (Feb 7): `resample_to_4h()` in data_loader.py — aggregates 15m bars to 4H for the new hypothesis.

---

### Key Decisions Made

| Decision | Reasoning | Still correct? |
|----------|-----------|---------------|
| Archive HYPOTHESIS_001 | PF 0.48, clearly negative. Session breakout doesn't work on crypto. | Yes — no ambiguity. |
| Refine HYPOTHESIS_002 (one more iteration) | PF 1.04 showed a structural edge existed even if marginal. Time-of-day filter had microstructure justification. | Yes — the refinement produced useful learnings even though the strategy was archived. |
| Archive HYPOTHESIS_002 | Net PF 0.69 after costs. Walk-forward: 0/5 profitable. | Yes — definitive. |
| Set PF 1.3 gross as minimum threshold | Any crypto strategy below this won't survive 0.1% round-trip costs. | Yes — this is now a hard constraint for all future work. |
| Move to 4H timeframe for H003 | Wider targets make costs negligible. Fewer trades = higher quality. | TBD — thesis is sound but untested. |

---

### What Didn't Happen

- **Evening review system not tested**: morning briefs are operational but evening workflow hasn't been validated end-to-end. Low priority but it's accumulating as debt.
- **No strategy postmortem CSV log**: The Feb 5 morning brief suggested appending each backtest run to a CSV for easy comparison. Didn't happen — results are in markdown instead. May not be needed if markdown postmortems are thorough enough.
- **No content/writing output**: The "build in public" secondary goal had zero progress this week. Expected — infrastructure week. But worth noting.

---

### Numbers That Matter

| Metric | H001 (London Breakout) | H002 Baseline | H002 Best (20-23 UTC) | H002 After 0.1% Costs |
|--------|----------------------|--------------|----------------------|----------------------|
| Trades | 48 | 1,410 | 289 | 289 |
| Win Rate | 33.3% | 47.0% | 55.4% | 55.4% |
| Profit Factor | 0.48 | 1.04 | 1.18 | 0.69 |
| Net P&L | -29.6% | +13.6% | +8.6% | -20.3% |
| Max Drawdown | $32,936 | $16,739 | $5,592 | $22,013 |

**System costs this week**: Minimal — GitHub Actions + Anthropic API + Resend. Well under $5.

---

### Learnings

1. **Gross PF < 1.3 on crypto = dead after costs.** This is now a hard filter. Don't waste time refining strategies below this threshold.
2. **Time-of-day filtering is meaningful.** Cut trade count by 80% while improving every quality metric. The 20-23 UTC window was best for mean reversion on BTCUSD — this carries forward.
3. **Asian session is NOT range-bound for crypto.** Don't import forex microstructure assumptions. BTCUSD has its own rhythm.
4. **Walk-forward validation is non-negotiable.** H002 looked "marginal" on full-sample but lost money in every sub-period. Full-sample results are misleading without temporal validation.
5. **Wider targets are the design constraint.** The 15m timeframe with 0.8% targets was fundamentally unable to absorb transaction costs. Future strategies must be designed around the cost floor, not optimized into it.

---

### Next Week's Focus

1. **Primary**: Implement and backtest HYPOTHESIS_003 (4H Volatility Contraction Breakout). The hypothesis is fully scoped — go straight to coding `vol_contraction.py` and running the baseline.
2. **Supporting**: Validate the `resample_to_4h()` utility against manual spot-checks. Bad aggregation = bad backtest = wasted time.
3. **Debt**: Test the evening review workflow end-to-end. It's been "not tested" since day one.

---

### Open Questions

1. **Is 6 months of 4H data (~1,080 bars) enough for statistical significance?** With an expected 30-60 trades, we're near the minimum. May need to source more history.
2. **Should squeeze detection be absolute or relative?** H003 proposes percentile-based (adaptive), but a fixed bandwidth threshold might be simpler and less prone to overfitting.
3. **When does it make sense to switch instruments instead of timeframes?** If H003 also fails, the problem might be BTCUSD itself, not the strategy approach.
