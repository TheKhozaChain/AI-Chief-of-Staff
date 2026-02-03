"""
Backtesting framework for quant strategy development.

Minimal, no external dependencies beyond Python stdlib.
"""

from .data_loader import load_csv, filter_by_date
from .engine import Backtest, BacktestResult, Trade, Direction

__all__ = [
    'load_csv',
    'filter_by_date', 
    'Backtest',
    'BacktestResult',
    'Trade',
    'Direction'
]
