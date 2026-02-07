"""
London Session Momentum Breakout Strategy (HYPOTHESIS_001)

Enters on a breakout of the Asian session (00:00-08:00 UTC) high/low during
the London session (08:00-12:00 UTC) on BTCUSD 15m bars.

Status: Archived — negative result (PF 0.48, 33% win rate).
See strategies/HYPOTHESIS_001.md for full analysis.

Usage:
    python london_breakout.py <data_file.csv>
"""

from datetime import time
from typing import Dict, List, Optional
from data_loader import load_csv
from engine import Backtest


# ---------------------------------------------------------------------------
# Strategy parameters
# ---------------------------------------------------------------------------
ASIAN_START = time(0, 0)    # Asian session start (UTC)
ASIAN_END = time(8, 0)      # Asian session end / London open (UTC)
LONDON_END = time(12, 0)    # Stop looking for entries after this (UTC)
MAX_ASIAN_RANGE_PCT = 3.0   # Skip if Asian range > 3% of price
REWARD_RATIO = 1.5          # Take profit = 1.5x the risk (Asian range)


class LondonBreakoutStrategy:
    """Trade breakouts of the Asian session range during London hours.

    Logic:
        1. During 00:00-08:00 UTC, track the session high and low.
        2. During 08:00-12:00 UTC, if price closes above the Asian high → long;
           if below the Asian low → short.
        3. Stop loss at the opposite side of the Asian range; TP at 1.5x risk.
        4. One trade per day maximum.
    """

    def __init__(self):
        self.asian_high: Optional[float] = None
        self.asian_low: Optional[float] = None
        self.current_date = None
        self.traded_today = False

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        """Evaluate a single bar and return a trade signal or None."""
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


COST_PCT = 0.1  # Round-trip transaction cost (%)


def run_backtest(data_file: str, cost_pct: float = COST_PCT):
    """Load data and run the London breakout backtest.

    Args:
        data_file: Path to a CSV with columns: datetime, open, high, low, close, volume.
        cost_pct: Round-trip transaction cost as % of trade value.

    Returns:
        BacktestResult with trade-level details.
    """
    print(f"Loading data from {data_file}...")
    data = load_csv(data_file)
    print(f"Loaded {len(data)} bars")

    strategy = LondonBreakoutStrategy()
    bt = Backtest(data, cost_pct=cost_pct)
    bt.run(strategy)

    print(bt.result.summary())
    return bt.result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python london_breakout.py <data_file.csv>")
        print("\nExpected CSV columns: datetime, open, high, low, close, volume")
        sys.exit(1)

    run_backtest(sys.argv[1])
