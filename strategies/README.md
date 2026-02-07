# Quant Strategies

This folder contains trading strategy research and backtesting infrastructure.

## Structure

```
strategies/
├── HYPOTHESIS_001.md      # London breakout (archived — PF 0.48)
├── HYPOTHESIS_002.md      # Mean reversion (archived — PF 0.69 after costs)
├── HYPOTHESIS_003.md      # 4H vol contraction breakout (scoped)
├── backtest/              # Backtesting framework
│   ├── data_loader.py     # Load CSV, resample to 4H/daily
│   ├── engine.py          # Backtest engine + walk-forward + OOS validation
│   ├── fetch_btc_data.py  # Download BTCUSD data
│   ├── london_breakout.py # H001 strategy implementation (archived)
│   └── mean_reversion.py  # H002 strategy implementation (archived)
└── README.md
```

## Workflow

1. **Hypothesis** → Write a clear thesis document (see HYPOTHESIS_003.md for current)
2. **Implement** → Code the strategy in backtest/
3. **Test** → Run backtest on historical data (with transaction costs!)
4. **Validate** → Walk-forward + out-of-sample split
5. **Evaluate** → Check against validation criteria
6. **Iterate or Archive** → Refine if close, discard if not

## Key Constraint

**Gross PF must be > 1.3 for any crypto strategy.** At 0.1% round-trip costs, anything below this threshold is destroyed by transaction friction. This was learned from HYPOTHESIS_002 (PF 1.18 gross → 0.69 net).

## Getting Data

The backtest expects OHLCV data in CSV format:

```csv
datetime,open,high,low,close,volume
2024-01-01 00:00:00,1.1050,1.1055,1.1045,1.1052,1000
```

Current data: `data/BTCUSD_15m.csv` (17,276 bars, Aug 2025 — Feb 2026)

The data loader supports resampling:
- `resample_to_4h(data)` — 15m → 4H bars (for HYPOTHESIS_003)
- `resample_to_daily(data)` — intraday → daily bars

## Running a Backtest

```bash
cd strategies/backtest

# Basic backtest
python mean_reversion.py ../../data/BTCUSD_15m.csv

# Full validation (backtest + OOS + walk-forward)
python mean_reversion.py ../../data/BTCUSD_15m.csv --validate
```

## Constraints

- No live trading automation (recommendations only)
- All strategies must have defined stops (prop-firm compliant)
- Keep it simple - no heavy ML or complex dependencies
- Transaction costs must be modeled (0.1% minimum for crypto)
