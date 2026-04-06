# Dedup Decision Log — 2026-04-06

## Context
The research backlog had 61 `new` ideas (R068-R128) that were auto-sourced but never curated.
Analysis revealed massive duplication: most ideas were trivial variants of archetypes already
in paper trading or already killed.

## Method
Clustered all `new` ideas by archetype. For each archetype, checked whether:
1. A hypothesis is already paper trading (covered — kill all new variants)
2. The archetype failed in paper trading (dead — kill all variants)
3. A validated/promoted idea already exists (covered — kill duplicates)

## Decisions

### Archetypes CONFIRMED DEAD (failed in paper trading)
| Archetype | Paper Result | New Ideas Killed |
|-----------|-------------|-----------------|
| volume_breakout | H011 PF 0.00, H022 PF 0.55 | R069,R072,R076,R082,R087,R102,R117 (7) |
| dual_momentum_consensus | H019 PF 0.00 | R079,R093,R108,R122 (4) |
| momentum_exhaustion_reversal | R022 val-failed | R084,R099,R112,R114,R125 (5) |

### Archetypes COVERED (already paper trading)
| Archetype | Active Hypothesis | New Ideas Killed |
|-----------|------------------|-----------------|
| range_compression_expansion | H017 | R073,R074,R075,R078,R080,R086,R101,R116 (8) |
| acceleration_breakout | H009 | R070,R071,R088,R103,R118 (5) |
| trend_pullback | H014 | R068,R083,R098,R113,R128 (5) |
| trend_strength_breakout | H013 | R081,R090,R105,R119 (4) |
| consecutive_momentum | H016 | R091,R106,R120 (3) |
| atr_regime_adaptive | H015+H020 | R085,R100,R115 (3) |
| adaptive_momentum_burst | H008 | R092,R107,R124 (3) |

### Archetypes PROMOTED (awaiting validation)
| Archetype | Promoted Idea | New Ideas Killed |
|-----------|--------------|-----------------|
| mtf_breakout | R055 (PF 1.48) | R077,R094,R109,R121,R123,R127 (6) |

### Intra-archetype duplicates
| Kept | Killed | Reason |
|------|--------|--------|
| R097 (both-dir MA crossover), R110 (long MA crossover) | R095, R126 | Same archetype, keeping canonical reps |
| R089 (donchian w/ trend gate) | R104 | Same concept, R089 more distinct |

## Survivors (5 genuinely new ideas)
| # | Idea | Archetype | Why kept |
|---|------|-----------|----------|
| R089 | Extended Donchian with Trend Gate | donchian_breakout | New archetype combo, not yet tested |
| R096 | Donchian Breakdown Short | donchian_breakout (short) | Short-side coverage needed |
| R097 | Slow Death Cross Trend Reversal | ma_crossover (both) | New archetype, both directions |
| R110 | MA Crossover Long-Bias | ma_crossover (long) | New archetype for pipeline |
| R111 | Breakdown Momentum Short | consecutive_momentum (short) | Short-side momentum coverage |

## Totals
- **56 ideas killed** (R068-R128 minus 5 survivors)
- **5 ideas remain `new`** for future screening
- **3 ideas remain `promoted`** (R046/R048/R055) — flagged below

## FLAG: Promoted queue vs PF threshold
The PF threshold was raised to 1.5 on 2026-03-05, but three promoted strategies are below it:
- R046 (PPAS): PF 1.30 — below 1.5
- R048 (MLMC): PF 1.39 — below 1.5
- R055 (MTF Alignment): PF 1.48 — below 1.5

**Recommendation:** Kill R046 and R048 (well below 1.5). R055 is borderline at 1.48 — could either validate or kill.

## FLAG: Paper trading overdue
H004, H008, H009, H013, H014, H015, H016 all started 2026-02-15 (50 days ago).
max_days is 45. These should have been auto-killed or graduated. Auto-kill may be broken.
