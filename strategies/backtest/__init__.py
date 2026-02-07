"""
Backtesting framework for quant strategy development.

Minimal, no external dependencies beyond Python stdlib.
Includes transaction costs, risk-adjusted metrics, out-of-sample testing,
and walk-forward validation.
"""

from .data_loader import load_csv, filter_by_date
from .engine import (
    Backtest, BacktestResult, Trade, Direction,
    walk_forward, walk_forward_summary,
    run_in_out_of_sample, in_out_of_sample_summary,
)

__all__ = [
    'load_csv',
    'filter_by_date',
    'Backtest',
    'BacktestResult',
    'Trade',
    'Direction',
    'walk_forward',
    'walk_forward_summary',
    'run_in_out_of_sample',
    'in_out_of_sample_summary',
]
