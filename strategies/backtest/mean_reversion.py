"""
Intraday Mean Reversion Strategy (HYPOTHESIS_002)

Fades extreme price extensions from a short-term moving average on
BTCUSD 15-minute bars. Enters when price moves > N standard deviations
from the MA, exits at take-profit (reversion toward mean) or stop-loss.

Filters out high-range days (>5% daily range) to avoid trending markets.

Results (Aug 2025 – Feb 2026, full sample):
    1,410 trades | 47% win rate | PF 1.04 | +13.6%

Usage:
    python mean_reversion.py data/BTCUSD_15m.csv
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from data_loader import load_csv, filter_by_date
from engine import Backtest
import statistics


# --- Strategy parameters ---
MA_PERIOD = 12            # Lookback for moving average (12 bars = 3 hours on 15m)
STD_THRESHOLD = 2.0       # Z-score threshold for entry (number of std devs from MA)
STOP_PCT = 0.4            # Stop loss: 0.4% beyond entry price
TAKE_PROFIT_PCT = 0.8     # Take profit: 0.8% from entry (or MA, whichever is closer)
MAX_24H_RANGE_PCT = 5.0   # Skip bar if intraday range exceeds this (trending filter)


class MeanReversionStrategy:
    """Fade extreme extensions from a short-term moving average.

    On each bar, computes a z-score of the current close relative to
    a 12-period SMA. When the z-score exceeds +/- 2.0, generates a
    counter-trend signal with fixed stop-loss and take-profit levels.

    A daily range filter skips signals on days where price has already
    moved more than MAX_24H_RANGE_PCT, avoiding trending/news days.
    """

    def __init__(self):
        self.daily_high: Optional[float] = None
        self.daily_low: Optional[float] = None
        self.current_date = None

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        """Evaluate a single bar and return a trade signal or None.

        Args:
            bar: Current OHLCV bar as dict with keys:
                 datetime, open, high, low, close, volume.
            prev_bars: List of preceding bars (up to 100).
            position: Current open position (None if flat).

        Returns:
            Signal dict with 'action', 'stop_loss', 'take_profit',
            or None if no trade.
        """
        if len(prev_bars) < MA_PERIOD:
            return None

        # Reset daily range tracker on new day
        bar_date = bar['datetime'].date()
        if bar_date != self.current_date:
            self.current_date = bar_date
            self.daily_high = bar['high']
            self.daily_low = bar['low']
        else:
            self.daily_high = max(self.daily_high, bar['high'])
            self.daily_low = min(self.daily_low, bar['low'])

        # Skip if daily range is too wide (trending/news day)
        if self.daily_high and self.daily_low:
            daily_range_pct = ((self.daily_high - self.daily_low) / self.daily_low) * 100
            if daily_range_pct > MAX_24H_RANGE_PCT:
                return None

        # Compute moving average and standard deviation
        recent_closes = [b['close'] for b in prev_bars[-MA_PERIOD:]]
        ma = statistics.mean(recent_closes)
        std = statistics.stdev(recent_closes) if len(recent_closes) > 1 else 0

        if std == 0:
            return None

        z_score = (bar['close'] - ma) / std

        if z_score > STD_THRESHOLD:
            # Overbought — fade with short
            stop_loss = bar['close'] * (1 + STOP_PCT / 100)
            take_profit = max(ma, bar['close'] * (1 - TAKE_PROFIT_PCT / 100))
            return {
                'action': 'sell',
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }

        elif z_score < -STD_THRESHOLD:
            # Oversold — fade with long
            stop_loss = bar['close'] * (1 - STOP_PCT / 100)
            take_profit = min(ma, bar['close'] * (1 + TAKE_PROFIT_PCT / 100))
            return {
                'action': 'buy',
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }

        return None


def run_backtest(data_file: str, start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None):
    """Run the mean reversion backtest on given data file.

    Args:
        data_file: Path to CSV with OHLCV data.
        start_date: Optional start of date window (inclusive).
        end_date: Optional end of date window (inclusive).

    Returns:
        BacktestResult with trade-level detail.
    """
    data = load_csv(data_file)

    if start_date or end_date:
        data = filter_by_date(data, start=start_date, end=end_date)

    print(f"Bars: {len(data)} | "
          f"Range: {data[0]['datetime'].date()} to {data[-1]['datetime'].date()}")

    strategy = MeanReversionStrategy()
    bt = Backtest(data)
    bt.run(strategy)

    print(bt.result.summary())
    return bt.result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python mean_reversion.py <data_file.csv> [start_date] [end_date]")
        print("\n  data_file    CSV with columns: datetime,open,high,low,close,volume")
        print("  start_date   Optional, format: YYYY-MM-DD")
        print("  end_date     Optional, format: YYYY-MM-DD")
        sys.exit(1)

    start = datetime.strptime(sys.argv[2], "%Y-%m-%d") if len(sys.argv) > 2 else None
    end = datetime.strptime(sys.argv[3], "%Y-%m-%d") if len(sys.argv) > 3 else None

    run_backtest(sys.argv[1], start_date=start, end_date=end)
