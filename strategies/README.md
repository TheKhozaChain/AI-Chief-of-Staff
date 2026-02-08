# Quant Strategies — RBI Loop

This folder contains trading strategy research, backtesting infrastructure, and the pipeline that drives all quant work.

## The RBI Loop

All strategy development follows **Research → Backtest → Implement**. Never skip phases.

```
  ┌───────────────────────────────────────────────────────────┐
  │                      THE RBI LOOP                         │
  │                                                           │
  │  RESEARCH          BACKTEST           IMPLEMENT           │
  │  ─────────         ─────────          ─────────           │
  │  Source ideas  →   Quick screen   →   Paper trade         │
  │  Papers, books     (30 min max)       (simulated)         │
  │  Other traders     ↓ pass?            ↓ 30 days ok?       │
  │  Market obs.       Full hypothesis    Micro-size live     │
  │  AI-generated      Walk-forward       ↓ 30 days ok?       │
  │                    OOS + costs        Scale up             │
  │                    ↓ pass?                                 │
  │                    Live readiness                          │
  │                    check (5/7)                             │
  │                                                           │
  │  ← ── ── ── archive + postmortem ── ── ── ── ── ←        │
  │        (failures feed back into research)                  │
  └───────────────────────────────────────────────────────────┘
```

**Target ratio:** 10 ideas researched → 3 quick-screened → 1 full hypothesis → rare live deployment.

## Structure

```
strategies/
├── RESEARCH_BACKLOG.md   # Living list of ideas to screen (R phase)
├── HYPOTHESIS_001.md     # London breakout (archived — PF 0.48)
├── HYPOTHESIS_002.md     # Mean reversion (archived — PF 0.69 after costs)
├── HYPOTHESIS_003.md     # 4H vol contraction breakout (scoped)
├── backtest/             # Backtesting framework
│   ├── data_loader.py    # Load CSV, resample to 4H/daily
│   ├── engine.py         # Backtest engine + walk-forward + OOS validation
│   ├── fetch_btc_data.py # Download BTCUSD data
│   ├── london_breakout.py # H001 strategy implementation (archived)
│   └── mean_reversion.py  # H002 strategy implementation (archived)
└── README.md
```

## RBI Workflow — Phase by Phase

### Phase R: Research

**Goal:** Fill the pipeline with testable ideas. Volume matters — most will die.

**Sources to scan:**
- Google Scholar (quantitative finance, crypto microstructure)
- Trading communities and forums
- YouTube strategy breakdowns
- Books (quantitative trading, market microstructure)
- AI-generated strategy concepts
- Market observation (anomalies, regime changes)

**Output:** Ideas added to `RESEARCH_BACKLOG.md` with:
- Source (where did the idea come from?)
- Core thesis (one sentence: what's the edge?)
- Testability (can we backtest this with our current data?)
- Priority (how promising does it look?)

**Cadence:** Aim for 2-3 new ideas per week minimum.

### Phase B: Backtest (Two-Tier)

**Tier 1 — Quick Screen (30 min max)**

Before writing a full hypothesis doc, do a rough validation:
1. Code a minimal version of the signal logic
2. Run on full data with 0% costs
3. Check gross PF — if < 1.5, kill it immediately
4. If it looks alive, check with 0.1% costs — if net PF < 1.0, kill it

Quick screens are disposable. No documentation needed for failures. Just log the idea as "screened — failed" in the research backlog and move on.

**Tier 2 — Full Hypothesis (only for survivors)**

If a quick screen shows promise (gross PF > 1.5, net PF > 1.2):
1. Write `HYPOTHESIS_XXX.md` with full thesis, parameters, edge rationale
2. Run baseline backtest with transaction costs
3. In-sample/out-of-sample split (70/30, PF degradation < 30%)
4. Walk-forward validation (5 windows, profitable in >= 3/5)
5. Live readiness check (pass 5/7 criteria)
6. Postmortem regardless of outcome (what was learned?)

### Phase I: Implement (Graduated Deployment)

**Stage 1 — Paper Trade:** Run the strategy in simulation for 30 days. Compare results to backtest expectations. Look for execution gaps.

**Stage 2 — Micro Live:** Smallest possible real position size for 30 days. Monitor slippage, fill quality, and psychological factors.

**Stage 3 — Scale:** If micro-live confirms the edge, increase size incrementally. Never jump to full allocation.

**Current status:** We are in R+B phases. Implementation is a future milestone. The system does not execute trades — this is deliberate.

## Hard Rules (Learned from Experience)

| Rule | Source | Rationale |
|------|--------|-----------|
| Gross PF > 1.3 for crypto | H002 postmortem | 0.1% costs destroy thin edges (PF 1.18 → 0.69 net) |
| Walk-forward is non-negotiable | H002 postmortem | Full-sample results are misleading |
| Design around cost floor | H001/H002 | Wide targets (4%+) not narrow (0.8%) |
| Don't import FX assumptions to crypto | H001 postmortem | Asian session is NOT range-bound for BTC |
| Time-of-day filtering matters | H002 refinement | Reduced trades 80%, improved every metric |
| One refinement iteration max | Operating principle | Don't endlessly optimize marginal edges |
| Kill fast, promote slow | RBI philosophy | 30 min to kill, 30+ days to promote to live |

## Getting Data

The backtest expects OHLCV data in CSV format:

```csv
datetime,open,high,low,close,volume
2024-01-01 00:00:00,1.1050,1.1055,1.1045,1.1052,1000
```

Current data: 3 years of BTCUSD (Feb 2023 — Feb 2026)
- `data/BTCUSD_15m.csv` — 105K bars
- `data/BTCUSD_1h.csv` — 26K bars

The data loader supports resampling:
- `resample_to_4h(data)` — 15m → 4H bars
- `resample_to_daily(data)` — intraday → daily bars

```bash
# Fetch fresh data
cd strategies/backtest
python fetch_btc_data.py              # All standard datasets
python fetch_btc_data.py --list       # Show existing data
python fetch_btc_data.py --interval 4h --days 1095  # Custom
```

## Running a Backtest

```bash
cd strategies/backtest

# Basic backtest
python mean_reversion.py ../../data/BTCUSD_15m.csv

# Full validation (backtest + OOS + walk-forward)
python mean_reversion.py ../../data/BTCUSD_15m.csv --validate
```

## Live Readiness Criteria (5/7 to pass)

1. Profit Factor >= 1.3
2. Win Rate >= 50%
3. Sharpe Ratio >= 1.0
4. Total Trades >= 100
5. Expectancy > 0
6. Beats Buy & Hold
7. Max Drawdown Duration < 30 days

## Constraints

- No live trading automation (recommendations only — for now)
- All strategies must have defined stops (prop-firm compliant)
- Keep it simple — no heavy ML or complex dependencies
- Transaction costs must be modeled (0.1% minimum for crypto)
- Risk agent must run before any future trade execution
