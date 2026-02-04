"""
Intraday Mean Reversion Strategy

Implements HYPOTHESIS_002: Fade extreme extensions from moving average.

Usage:
    python mean_reversion.py data/BTCUSD_15m.csv
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from data_loader import load_csv
from engine import Backtest
import statistics


# Strategy parameters (v3 - profitable)
MA_PERIOD = 12          # 12 bars = 3 hours on 15m
STD_THRESHOLD = 2.0     # Entry when > 2 std devs from MA
STOP_PCT = 0.4          # Stop 0.4% beyond entry
TAKE_PROFIT_PCT = 0.8   # Take profit at 0.8%
MAX_24H_RANGE_PCT = 5.0 # Skip if 24h range > 5%


class MeanReversionStrategy:
    """
    Fades extreme extensions from moving average.
    """
    
    def __init__(self):
        self.daily_high = None
        self.daily_low = None
        self.current_date = None
    
    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        """
        Called on each bar by the backtest engine.
        Returns signal dict or None.
        """
        # Need enough history for MA calculation
        if len(prev_bars) < MA_PERIOD:
            return None
        
        # Track daily range for filter
        bar_date = bar['datetime'].date()
        if bar_date != self.current_date:
            self.current_date = bar_date
            self.daily_high = bar['high']
            self.daily_low = bar['low']
        else:
            self.daily_high = max(self.daily_high, bar['high'])
            self.daily_low = min(self.daily_low, bar['low'])
        
        # Calculate 24h range filter
        if self.daily_high and self.daily_low:
            daily_range_pct = ((self.daily_high - self.daily_low) / self.daily_low) * 100
            if daily_range_pct > MAX_24H_RANGE_PCT:
                return None  # Skip trending days
        
        # Calculate moving average and standard deviation
        recent_closes = [b['close'] for b in prev_bars[-MA_PERIOD:]]
        ma = statistics.mean(recent_closes)
        std = statistics.stdev(recent_closes) if len(recent_closes) > 1 else 0
        
        if std == 0:
            return None
        
        # Calculate z-score (how many std devs from MA)
        z_score = (bar['close'] - ma) / std
        
        # Check for extreme extension
        if z_score > STD_THRESHOLD:
            # Overbought - fade with short
            stop_loss = bar['close'] * (1 + STOP_PCT / 100)
            take_profit = max(ma, bar['close'] * (1 - TAKE_PROFIT_PCT / 100))
            return {
                'action': 'sell',
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
        
        elif z_score < -STD_THRESHOLD:
            # Oversold - fade with long
            stop_loss = bar['close'] * (1 - STOP_PCT / 100)
            take_profit = min(ma, bar['close'] * (1 + TAKE_PROFIT_PCT / 100))
            return {
                'action': 'buy',
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
        
        return None


def run_backtest(data_file: str):
    """Run the backtest on given data file."""
    print(f"Loading data from {data_file}...")
    data = load_csv(data_file)
    print(f"Loaded {len(data)} bars")
    
    print("Running backtest...")
    strategy = MeanReversionStrategy()
    bt = Backtest(data)
    bt.run(strategy)
    
    print(bt.result.summary())
    return bt.result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mean_reversion.py <data_file.csv>")
        print("\nExpected CSV format:")
        print("datetime,open,high,low,close,volume")
        sys.exit(1)
    
    run_backtest(sys.argv[1])
