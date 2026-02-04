"""
London Session Momentum Breakout Strategy

Implements HYPOTHESIS_001: Breakout of Asian session range at London open.

Usage:
    python london_breakout.py data/BTCUSD_15m.csv
"""

from datetime import datetime, time
from typing import Dict, List, Optional
from data_loader import load_csv
from engine import Backtest


# Strategy parameters
ASIAN_START = time(0, 0)   # 00:00 GMT
ASIAN_END = time(8, 0)     # 08:00 GMT
LONDON_END = time(12, 0)   # 12:00 GMT - stop looking for entries
MAX_ASIAN_RANGE_PCT = 3.0  # Skip if range > 3% of price
REWARD_RATIO = 1.5         # TP = 1.5x risk


class LondonBreakoutStrategy:
    """
    Tracks Asian session range and generates breakout signals.
    """
    
    def __init__(self):
        self.asian_high = None
        self.asian_low = None
        self.current_date = None
        self.traded_today = False
    
    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        """
        Called on each bar by the backtest engine.
        Returns signal dict or None.
        """
        bar_time = bar['datetime'].time()
        bar_date = bar['datetime'].date()
        
        # Reset on new day
        if bar_date != self.current_date:
            self.current_date = bar_date
            self.asian_high = None
            self.asian_low = None
            self.traded_today = False
        
        # During Asian session: track high/low
        if ASIAN_START <= bar_time < ASIAN_END:
            if self.asian_high is None:
                self.asian_high = bar['high']
                self.asian_low = bar['low']
            else:
                self.asian_high = max(self.asian_high, bar['high'])
                self.asian_low = min(self.asian_low, bar['low'])
            return None
        
        # No range defined yet
        if self.asian_high is None or self.asian_low is None:
            return None
        
        # Already traded today
        if self.traded_today:
            return None
        
        # Outside London entry window
        if bar_time >= LONDON_END:
            return None
        
        # Calculate range as percentage of price
        asian_range = self.asian_high - self.asian_low
        mid_price = (self.asian_high + self.asian_low) / 2
        asian_range_pct = (asian_range / mid_price) * 100
        
        # Skip if range too wide
        if asian_range_pct > MAX_ASIAN_RANGE_PCT:
            return None
        
        # Check for breakout (close above/below range)
        if bar['close'] > self.asian_high:
            # Long breakout
            self.traded_today = True
            stop_loss = self.asian_low
            take_profit = bar['close'] + (asian_range * REWARD_RATIO)
            return {
                'action': 'buy',
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
        
        elif bar['close'] < self.asian_low:
            # Short breakout
            self.traded_today = True
            stop_loss = self.asian_high
            take_profit = bar['close'] - (asian_range * REWARD_RATIO)
            return {
                'action': 'sell',
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
    strategy = LondonBreakoutStrategy()
    bt = Backtest(data)
    bt.run(strategy)
    
    print(bt.result.summary())
    return bt.result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python london_breakout.py <data_file.csv>")
        print("\nExpected CSV format:")
        print("datetime,open,high,low,close,volume")
        print("2024-01-01 00:00:00,42000.50,42100.00,41900.00,42050.00,1000")
        print("\nTo get BTCUSD data, you can use:")
        print("- Binance API (free historical)")
        print("- CoinGecko API")
        print("- Yahoo Finance (BTC-USD)")
        sys.exit(1)
    
    run_backtest(sys.argv[1])
