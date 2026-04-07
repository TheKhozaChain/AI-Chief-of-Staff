# Promotion Criteria

Decision policy for when to promote a strategy to the next stage.
Promotion is slow and deliberate — the bar rises at each stage.

---

## Screening -> Promoted (to validation queue)

All of the following must be true:

| Criterion | Threshold |
|-----------|-----------|
| Gross Profit Factor | >= 1.5 |
| Total trades | >= 20 |
| Regime coverage | Pass (profitable in bull + bear + sideways) |
| Transaction cost modeled | 0.1% minimum from day one |
| Archetype not saturated | < 3 promoted/validated entries for same archetype |
| No duplicate params | Not identical archetype + params already promoted |

**Screening timeframe must match validation timeframe.** R007/R009 were screened
at 4H, not 1H. Mismatched timeframes invalidate the screen.

---

## Promoted -> Validated (full walk-forward)

Must pass 3 of 4 validation tests:

| Test | Pass Criteria |
|------|--------------|
| Walk-forward | 60%+ windows profitable AND mean PF > 1.1 |
| Out-of-sample | OOS PF >= 1.2 AND PF decay < 30% from in-sample |
| Parameter sensitivity | 80%+ variants PF > 1.0 AND worst variant PF > 0.9 |
| Cost stress test | PF >= 1.15 at 0.15% transaction costs |

---

## Validated -> Paper Trading

Strategy enters paper trading when it passes validation. Configuration:

| Parameter | Default |
|-----------|---------|
| Minimum days | 30 |
| Minimum trades for evaluation | 5 |
| Cost percentage | 0.1% |

---

## Paper Trading -> Graduation (ready for live)

All of the following must be true:

| Criterion | Threshold |
|-----------|-----------|
| Days active | >= 30 |
| Completed trades | >= 5 |
| Net Profit Factor | >= 1.0 |
| Max drawdown | <= 25% |

**Graduation = ready for live review.** This is the one human-in-the-loop gate.
The system flags graduation; Sipho decides whether to deploy.

---

## Live Readiness Checklist (reference, from validation baseline)

These are checked during validation baseline but documented here for completeness:

| Criterion | Target |
|-----------|--------|
| Profit Factor | >= 1.3 |
| Win Rate | >= 50% |
| Sharpe Ratio | >= 1.0 |
| Total Trades | >= 100 |
| Expectancy | > 0 |
| Beats Buy & Hold | Yes |
| Max Drawdown Duration | < 30 days |

Pass 5 of 7 for live readiness.

---

## Pipeline Throughput Rules

| Rule | Value |
|------|-------|
| Idea sourcing | ~3/week (Mon/Wed/Fri) |
| Screening cadence | Daily (03:00 UTC / 14:00 AEDT) |
| Archetype saturation cap | 3 promoted/validated per archetype |
| Max refinement iterations | 1 (then archive and move on) |
| Target funnel | 10 ideas -> 3 screened -> 1 hypothesis |
