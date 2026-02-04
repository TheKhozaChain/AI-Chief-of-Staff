# Quant Strategies

Trading strategy research and backtesting infrastructure for BTCUSD.

## Structure

```
strategies/
├── HYPOTHESIS_001.md        # London breakout — FAILED (archived)
├── HYPOTHESIS_002.md        # Mean reversion — REFINING (OOS validation next)
├── README.md                # This file
└── backtest/                # Backtesting framework
    ├── __init__.py          # Package exports
    ├── engine.py            # Core backtest engine (event-driven)
    ├── data_loader.py       # CSV loader with date filtering
    ├── fetch_btc_data.py    # Binance API data fetcher
    ├── london_breakout.py   # HYPOTHESIS_001 implementation
    └── mean_reversion.py    # HYPOTHESIS_002 implementation
```

Data lives in `data/BTCUSD_15m.csv` (6 months, 17,276 bars).

## Hypothesis Tracker

| # | Strategy | Status | PF | Win Rate | Verdict |
|:-:|----------|--------|---:|--------:|---------|
| 001 | London Breakout | Archived | 0.48 | 33% | Not viable for crypto |
| 002 | Mean Reversion | Refining | 1.04 | 47% | Marginal edge, validating OOS |

## Workflow

1. **Hypothesis** → Write thesis in `HYPOTHESIS_NNN.md`
2. **Implement** → Code strategy in `backtest/`
3. **Test** → Run backtest on historical data
4. **Evaluate** → Check against validation criteria
5. **Validate** → Out-of-sample test before optimization
6. **Iterate or Archive** → Refine if validated, discard if not

## Running a Backtest

```bash
cd strategies/backtest
python mean_reversion.py ../../data/BTCUSD_15m.csv

# With date filtering (for OOS validation):
python mean_reversion.py ../../data/BTCUSD_15m.csv 2025-12-01 2026-02-05
```

## Getting Data

```bash
cd strategies/backtest
python fetch_btc_data.py   # Fetches 6 months of BTCUSD 15m from Binance
```

## Constraints

- No live trading automation (recommendations only)
- All strategies must have defined stops
- Keep it simple — no heavy ML or complex dependencies
