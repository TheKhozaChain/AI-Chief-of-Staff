# Quant Strategies

This folder contains trading strategy research and backtesting infrastructure.

## Structure

```
strategies/
├── HYPOTHESIS_001.md      # London breakout strategy hypothesis
├── HYPOTHESIS_002.md      # (future hypotheses)
├── backtest/              # Backtesting framework
│   ├── data_loader.py     # Load CSV/API data
│   ├── engine.py          # Backtest engine
│   └── london_breakout.py # Strategy implementation
└── data/                  # Historical data (gitignored)
```

## Workflow

1. **Hypothesis** → Write a clear thesis document (see HYPOTHESIS_001.md)
2. **Implement** → Code the strategy in backtest/
3. **Test** → Run backtest on historical data
4. **Evaluate** → Check against validation criteria
5. **Iterate or Archive** → Refine if promising, discard if not

## Getting Data

The backtest expects 15-minute OHLC data in CSV format:

```csv
datetime,open,high,low,close,volume
2024-01-01 00:00:00,1.1050,1.1055,1.1045,1.1052,1000
```

Free data sources:
- **Dukascopy** (dukascopy.com) - Historical tick/bar data
- **Yahoo Finance** - Stocks and indices
- **OANDA API** - If you have an account

Place data files in `strategies/data/` (gitignored for size).

## Running a Backtest

```bash
cd strategies/backtest
python london_breakout.py ../data/EURUSD_15m.csv
```

## Constraints

- No live trading automation (recommendations only)
- All strategies must have defined stops (prop-firm compliant)
- Keep it simple - no heavy ML or complex dependencies
