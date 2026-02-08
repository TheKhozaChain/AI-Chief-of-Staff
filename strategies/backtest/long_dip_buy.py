"""
Long-Only Dip Buy Quick Screen (R008 + R006 insights)

Combines learnings from 3 killed strategies:
- R006: Long-only BTC bias works (every variant net positive)
- H002: Mean reversion timing has some signal (gross PF 1.18)
- H003: Wider targets absorb transaction costs

Strategy: Buy oversold dips in a confirmed BTC uptrend.
Only longs. Never fight the structural trend.

Usage:
    python long_dip_buy.py ../../data/BTCUSD_1h.csv
"""

import sys
import statistics
from typing import Dict, List, Optional
from data_loader import load_csv, resample_to_4h
from engine import (
    Backtest,
    walk_forward, walk_forward_summary,
    run_in_out_of_sample, in_out_of_sample_summary,
)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
TREND_MA = 80              # 80-bar MA on 4H (~13 days) for trend direction
FAST_MA = 20               # 20-bar MA on 4H (~3.3 days) for mean reversion
Z_THRESHOLD = -1.5         # Enter long when z-score < -1.5 (oversold dip)
STOP_PCT = 3.0             # Stop: 3% below entry
TAKE_PROFIT_PCT = 6.0      # Target: 6% (2:1 R:R)
COST_PCT = 0.1


class LongDipBuyStrategy:
    """Buy oversold dips in a BTC uptrend.

    Logic:
        - Confirm uptrend: price above 80-bar MA on 4H.
        - Wait for dip: z-score (deviation from 20-bar MA) drops below -1.5.
        - Enter long on the dip.
        - Target: 6% recovery. Stop: 3% further decline.
        - Never short. If trend breaks (price below 80 MA), sit flat.

    Rationale:
        BTC's structural uptrend means dips are buying opportunities.
        The z-score filter times the entry to oversold conditions.
        Wider targets (6%) make 0.1% costs negligible (~1.7% of target).
    """

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        if len(prev_bars) < TREND_MA:
            return None

        closes = [b['close'] for b in prev_bars]
        price = bar['close']

        # Trend filter: price must be above long MA (uptrend confirmed)
        trend_ma = statistics.mean(closes[-TREND_MA:])
        if price < trend_ma:
            return None

        # Dip detection: z-score below threshold
        recent = closes[-FAST_MA:]
        if len(recent) < FAST_MA:
            return None
        fast_ma = statistics.mean(recent)
        std = statistics.stdev(recent) if len(recent) > 1 else 0
        if std == 0:
            return None

        z_score = (price - fast_ma) / std

        if z_score < Z_THRESHOLD:
            return {
                'action': 'buy',
                'stop_loss': price * (1 - STOP_PCT / 100),
                'take_profit': price * (1 + TAKE_PROFIT_PCT / 100),
            }

        return None


def run_backtest(data_file: str, cost_pct: float = COST_PCT):
    """Quick screen."""
    print(f"Loading data from {data_file}...")
    raw_data = load_csv(data_file)
    print(f"Loaded {len(raw_data)} bars")

    print("Resampling to 4H...")
    data = resample_to_4h(raw_data)
    print(f"Resampled to {len(data)} 4H bars")
    print(f"Period: {data[0]['datetime']} → {data[-1]['datetime']}")
    print()

    # Gross
    print("=" * 60)
    print("GROSS (0% costs)")
    print("=" * 60)
    bt_gross = Backtest(data, cost_pct=0.0)
    bt_gross.run(LongDipBuyStrategy())
    print(bt_gross.result.summary())

    # Net
    print("=" * 60)
    print(f"NET ({cost_pct}% costs)")
    print("=" * 60)
    bt_net = Backtest(data, cost_pct=cost_pct)
    bt_net.run(LongDipBuyStrategy())
    print(bt_net.result.summary())

    # If promising, run full validation
    gross_pf = bt_gross.result.profit_factor
    if gross_pf >= 1.3:
        print("\n" + "!" * 60)
        print(f"GROSS PF {gross_pf:.2f} >= 1.3 — RUNNING FULL VALIDATION")
        print("!" * 60)

        print("\n" + "=" * 60)
        print("IN-SAMPLE vs OUT-OF-SAMPLE (70/30)")
        print("=" * 60)
        oos = run_in_out_of_sample(data, LongDipBuyStrategy, train_pct=0.7, cost_pct=cost_pct)
        print(in_out_of_sample_summary(oos))

        print("=" * 60)
        print("WALK-FORWARD VALIDATION")
        print("=" * 60)
        wf = walk_forward(data, LongDipBuyStrategy, window_bars=1300, cost_pct=cost_pct)
        print(walk_forward_summary(wf))

    return bt_gross.result, bt_net.result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python long_dip_buy.py <data_file.csv>")
        sys.exit(1)
    run_backtest(sys.argv[1])
