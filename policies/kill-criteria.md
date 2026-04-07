# Kill Criteria

Decision policy for when to kill a strategy. Applied at screening, validation,
and paper trading stages. Each stage has its own thresholds — a strategy must
survive every gate it reaches.

---

## Screening (Quick Screen)

| Criterion | Threshold | Action |
|-----------|-----------|--------|
| Gross PF below minimum | < 1.5 | Kill immediately |
| Positive but below threshold | 1.0 - 1.5 | Kill (edge too thin to survive costs) |
| Negative expectancy | < 1.0 | Kill immediately |
| Insufficient trades | < 20 | Park (not enough data to judge) |
| Regime coverage fails | Any regime missing | Park (strategy too narrow) |

**Why 1.5 and not 1.3:** Raised from 1.3 on 2026-03-05. Strategies at 1.3-1.35
gross PF rarely survive validation + transaction costs. H005 taught us: gross PF
1.31 becomes net PF 1.23 after costs — barely viable and usually fails OOS.

---

## Validation (Walk-Forward)

| Criterion | Threshold | Action |
|-----------|-----------|--------|
| OOS PF below minimum | < 1.0 | Kill (instant, quick-screen gate) |
| OOS PF decay from IS | > 50% | Kill (instant, overfitting signal) |
| Full OOS PF | < 1.2 | Kill |
| Full OOS PF decay | > 30% | Kill (overfitting warning — H004: -37.9%, H006: -41.0%) |
| Walk-forward windows profitable | < 60% | Kill |
| Walk-forward mean PF | < 1.1 | Kill |
| Sensitivity variants PF > 1.0 | < 80% | Kill |
| Worst sensitivity variant PF | < 0.9 | Kill |
| Cost stress test PF (0.15%) | < 1.15 | Kill |
| Overall tests passed | < 3 of 4 | Kill |

---

## Paper Trading

| Criterion | Threshold | Action |
|-----------|-----------|--------|
| Net PF clearly failing | < 0.8 (with 5+ trades) | Kill early |
| Zero trades, no position | 30+ days | Kill (zero trade production) |
| Zero completed trades, stuck in position | 45+ days | Kill (limbo state, H004 lesson) |
| Insufficient trades past max days | < 5 trades after 45 days | Kill |
| Extended period, not graduating | 45+ days with 5+ trades, criteria unmet | Kill |

### Staleness (warnings before kill)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| No trades, no position | 14+ days | Stale warning (email once) |
| Had trades but went silent | 30+ days since last signal | Stale warning (email once) |

---

## Hard Lessons (do not forget)

- **H005:** Gross PF 1.31 -> net PF 1.23. The 1.3 threshold barely survives costs.
- **H006:** 20 trades over 3yr is NOT enough. Need 50+ for statistical significance.
- **H004/H006:** OOS PF decay > 30% = overfitting (H004: -37.9%, H006: -41.0%).
- **H007:** Auto-killed after 0 trades in 30 days. Zero trade production is a valid kill.
- **H004:** Stuck in open position for 49+ days with 0 completed trades. Force-kill limbo states.
- **General:** One refinement iteration max, then archive and move on.
- **General:** Transaction costs (0.1% minimum) must be modeled from day one.
