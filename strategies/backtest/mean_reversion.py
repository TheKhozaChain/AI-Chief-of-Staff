"""
Intraday Mean Reversion Strategy (HYPOTHESIS_002)

Fades extreme price extensions from a short-term moving average on BTCUSD 15m bars.
Includes a time-of-day filter to restrict trading to range-bound sessions.

Status: Archived — marginal edge (PF 1.18), not viable for live trading.
See strategies/HYPOTHESIS_002.md for full analysis and test matrix.

Usage:
    python mean_reversion.py <data_file.csv>

Example:
    python mean_reversion.py ../../data/BTCUSD_15m.csv
"""

from typing import Dict, List, Optional
from data_loader import load_csv
from engine import Backtest
import statistics


# ---------------------------------------------------------------------------
# Strategy parameters (v4 — time-of-day filtered)
# ---------------------------------------------------------------------------
MA_PERIOD = 12              # 12 bars = 3 hours of lookback on 15m
STD_THRESHOLD = 2.0         # Enter when price > 2 std devs from MA
STOP_PCT = 0.4              # Stop loss: 0.4% beyond entry
TAKE_PROFIT_PCT = 0.8       # Take profit: 0.8% from entry
MAX_24H_RANGE_PCT = 5.0     # Skip bar if intraday range exceeds 5%

# Time-of-day filter: only trade during range-bound evening hours (UTC).
# Tested windows: all-hours, 00-07, 16-23, 18-23, 20-23.
# 20-23 UTC produced the best PF (1.18) and win rate (55.4%).
# See HYPOTHESIS_002.md "Time-of-Day Test Matrix" for full results.
ALLOWED_HOURS_UTC = list(range(20, 24))


class MeanReversionStrategy:
    """Fade extreme extensions from a short-term moving average.

    Signal logic:
        1. Compute z-score = (close - MA) / std over the last MA_PERIOD bars.
        2. If z > +STD_THRESHOLD → sell (overbought), if z < -STD_THRESHOLD → buy (oversold).
        3. Stop loss placed STOP_PCT beyond entry; take profit at TAKE_PROFIT_PCT or MA, whichever is closer.

    Filters applied before signal generation:
        - Time-of-day: bar hour must be in ALLOWED_HOURS_UTC.
        - Daily range: skip if intraday high-low range exceeds MAX_24H_RANGE_PCT.
    """

    def __init__(self):
        self.daily_high: Optional[float] = None
        self.daily_low: Optional[float] = None
        self.current_date = None

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        """Evaluate a single bar and return a trade signal or None.

        Args:
            bar: Current OHLCV bar dict with keys: datetime, open, high, low, close, volume.
            prev_bars: Up to 100 preceding bars (same dict format).
            position: Current open position (or None if flat).

        Returns:
            Signal dict with keys 'action', 'stop_loss', 'take_profit', or None.
        """
        if len(prev_bars) < MA_PERIOD:
            return None

        # --- Filter: time-of-day ---
        if bar['datetime'].hour not in ALLOWED_HOURS_UTC:
            return None

        # --- Filter: daily range ---
        bar_date = bar['datetime'].date()
        if bar_date != self.current_date:
            self.current_date = bar_date
            self.daily_high = bar['high']
            self.daily_low = bar['low']
        else:
            self.daily_high = max(self.daily_high, bar['high'])
            self.daily_low = min(self.daily_low, bar['low'])

        daily_range_pct = ((self.daily_high - self.daily_low) / self.daily_low) * 100
        if daily_range_pct > MAX_24H_RANGE_PCT:
            return None

        # --- Compute z-score ---
        recent_closes = [b['close'] for b in prev_bars[-MA_PERIOD:]]
        ma = statistics.mean(recent_closes)
        std = statistics.stdev(recent_closes) if len(recent_closes) > 1 else 0
        if std == 0:
            return None

        z_score = (bar['close'] - ma) / std

        # --- Generate signal ---
        if z_score > STD_THRESHOLD:
            return {
                'action': 'sell',
                'stop_loss': bar['close'] * (1 + STOP_PCT / 100),
                'take_profit': max(ma, bar['close'] * (1 - TAKE_PROFIT_PCT / 100)),
            }
        if z_score < -STD_THRESHOLD:
            return {
                'action': 'buy',
                'stop_loss': bar['close'] * (1 - STOP_PCT / 100),
                'take_profit': min(ma, bar['close'] * (1 + TAKE_PROFIT_PCT / 100)),
            }

        return None


# ---------------------------------------------------------------------------
# Transaction cost assumption
# ---------------------------------------------------------------------------
# Round-trip cost for BTCUSD on major exchanges (Binance taker fee ~0.1% per side).
# 0.1% is conservative — real costs may be higher with slippage.
COST_PCT = 0.1


def run_backtest(data_file: str, cost_pct: float = COST_PCT):
    """Load data and run the mean reversion backtest with transaction costs.

    Args:
        data_file: Path to a CSV with columns: datetime, open, high, low, close, volume.
        cost_pct: Round-trip transaction cost as % of trade value.

    Returns:
        BacktestResult with trade-level details.
    """
    print(f"Loading data from {data_file}...")
    data = load_csv(data_file)
    print(f"Loaded {len(data)} bars\n")

    strategy = MeanReversionStrategy()
    bt = Backtest(data, cost_pct=cost_pct)
    bt.run(strategy)

    print(bt.result.summary())
    return bt.result


def run_full_validation(data_file: str, cost_pct: float = COST_PCT):
    """Run complete validation suite: backtest + out-of-sample + walk-forward.

    This is the proper way to assess whether a strategy is ready for live trading.
    A strategy should pass all three tests before risking real capital.

    Args:
        data_file: Path to OHLCV CSV.
        cost_pct: Round-trip transaction cost %.
    """
    from engine import (
        walk_forward, walk_forward_summary,
        run_in_out_of_sample, in_out_of_sample_summary,
    )

    print(f"Loading data from {data_file}...")
    data = load_csv(data_file)
    print(f"Loaded {len(data)} bars")
    print(f"Transaction cost: {cost_pct}% per trade (round-trip)")

    # --- 1. Full-sample backtest ---
    print("\n" + "=" * 60)
    print("1. FULL-SAMPLE BACKTEST")
    print("=" * 60)
    bt = Backtest(data, cost_pct=cost_pct)
    bt.run(MeanReversionStrategy())
    print(bt.result.summary())

    # --- 2. In-sample vs out-of-sample (70/30 split) ---
    print("=" * 60)
    print("2. IN-SAMPLE vs OUT-OF-SAMPLE (70/30 split)")
    print("=" * 60)
    oos_results = run_in_out_of_sample(
        data, MeanReversionStrategy, train_pct=0.7, cost_pct=cost_pct
    )
    print(in_out_of_sample_summary(oos_results))

    # --- 3. Walk-forward validation (rolling 3000-bar windows) ---
    print("=" * 60)
    print("3. WALK-FORWARD VALIDATION (rolling windows)")
    print("=" * 60)
    wf_results = walk_forward(
        data, MeanReversionStrategy, window_bars=3000, cost_pct=cost_pct
    )
    print(walk_forward_summary(wf_results))

    return bt.result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python mean_reversion.py <data_file.csv>              # basic backtest")
        print("  python mean_reversion.py <data_file.csv> --validate   # full validation")
        print("\nExpected CSV columns: datetime, open, high, low, close, volume")
        sys.exit(1)

    data_file = sys.argv[1]
    if "--validate" in sys.argv:
        run_full_validation(data_file)
    else:
        run_backtest(data_file)
