"""
Event-driven backtesting engine with live-readiness assessment.

Processes OHLCV bars sequentially, checks stops/targets on each bar,
and records completed trades. Includes transaction cost modeling,
risk-adjusted metrics, walk-forward validation, and buy-and-hold benchmark.

No external dependencies — stdlib only.

Usage:
    bt = Backtest(data, cost_pct=0.1)
    bt.run(strategy_callable)
    print(bt.result.summary())

    # Walk-forward validation
    results = walk_forward(data, MyStrategy, window_bars=2000, cost_pct=0.1)
    print(walk_forward_summary(results))
"""

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from enum import Enum


class Direction(Enum):
    LONG = 1
    SHORT = -1


# ---------------------------------------------------------------------------
# Trade
# ---------------------------------------------------------------------------

@dataclass
class Trade:
    """A completed trade with entry/exit details and transaction costs."""
    entry_time: datetime
    exit_time: datetime
    direction: Direction
    entry_price: float
    exit_price: float
    size: float = 1.0
    costs: float = 0.0  # Round-trip transaction costs (spread + commission)

    @property
    def pnl_gross(self) -> float:
        """Profit/loss before transaction costs (in price units)."""
        if self.direction == Direction.LONG:
            return (self.exit_price - self.entry_price) * self.size
        return (self.entry_price - self.exit_price) * self.size

    @property
    def pnl(self) -> float:
        """Profit/loss after transaction costs (in price units)."""
        return self.pnl_gross - self.costs

    @property
    def pnl_pct(self) -> float:
        """Net P&L as percentage of entry price."""
        return (self.pnl / self.entry_price) * 100

    @property
    def duration(self) -> timedelta:
        """How long the trade was open."""
        return self.exit_time - self.entry_time


# ---------------------------------------------------------------------------
# Position (open, not yet closed)
# ---------------------------------------------------------------------------

@dataclass
class Position:
    """An open position awaiting exit."""
    entry_time: datetime
    direction: Direction
    entry_price: float
    stop_loss: float
    take_profit: float
    size: float = 1.0


# ---------------------------------------------------------------------------
# BacktestResult — all metrics computed from the trade list
# ---------------------------------------------------------------------------

@dataclass
class BacktestResult:
    """Comprehensive results from a backtest run.

    Includes basic stats (win rate, PF), risk-adjusted metrics (Sharpe, Sortino),
    duration analysis, drawdown duration, and buy-and-hold benchmark comparison.
    """
    trades: List[Trade] = field(default_factory=list)
    buy_hold_pnl: float = 0.0        # Set by Backtest engine
    buy_hold_pnl_pct: float = 0.0    # Set by Backtest engine
    cost_pct: float = 0.0            # Transaction cost used

    # --- Basic stats ---

    @property
    def total_trades(self) -> int:
        return len(self.trades)

    @property
    def winners(self) -> int:
        return len([t for t in self.trades if t.pnl > 0])

    @property
    def losers(self) -> int:
        return len([t for t in self.trades if t.pnl <= 0])

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.winners / self.total_trades

    @property
    def total_pnl(self) -> float:
        return sum(t.pnl for t in self.trades)

    @property
    def total_pnl_gross(self) -> float:
        return sum(t.pnl_gross for t in self.trades)

    @property
    def total_costs(self) -> float:
        return sum(t.costs for t in self.trades)

    @property
    def total_pnl_pct(self) -> float:
        return sum(t.pnl_pct for t in self.trades)

    @property
    def avg_win(self) -> float:
        wins = [t.pnl for t in self.trades if t.pnl > 0]
        return sum(wins) / len(wins) if wins else 0.0

    @property
    def avg_loss(self) -> float:
        losses = [t.pnl for t in self.trades if t.pnl <= 0]
        return sum(losses) / len(losses) if losses else 0.0

    @property
    def expectancy(self) -> float:
        """Average net P&L per trade."""
        if self.total_trades == 0:
            return 0.0
        return self.total_pnl / self.total_trades

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.trades if t.pnl <= 0))
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

    # --- Risk-adjusted metrics ---

    @property
    def sharpe_ratio(self) -> float:
        """Annualized Sharpe ratio from per-trade percentage returns.

        Uses the actual trading period to estimate trades-per-year,
        then annualizes: Sharpe = (mean_return / std_return) * sqrt(trades_per_year).
        """
        if len(self.trades) < 2:
            return 0.0
        returns = [t.pnl_pct for t in self.trades]
        mean_r = statistics.mean(returns)
        std_r = statistics.stdev(returns)
        if std_r == 0:
            return 0.0
        trades_per_year = self._trades_per_year()
        if trades_per_year == 0:
            return 0.0
        return (mean_r / std_r) * math.sqrt(trades_per_year)

    @property
    def sortino_ratio(self) -> float:
        """Annualized Sortino ratio (penalizes downside volatility only).

        Capped to [-99, 99] for display sanity when downside std is near zero.
        """
        if len(self.trades) < 2:
            return 0.0
        returns = [t.pnl_pct for t in self.trades]
        mean_r = statistics.mean(returns)
        downside = [r for r in returns if r < 0]
        if len(downside) < 2:
            return min(99.0, max(-99.0, 99.0 if mean_r > 0 else 0.0))
        downside_std = statistics.stdev(downside)
        if downside_std == 0:
            return min(99.0, max(-99.0, 99.0 if mean_r > 0 else 0.0))
        trades_per_year = self._trades_per_year()
        if trades_per_year == 0:
            return 0.0
        raw = (mean_r / downside_std) * math.sqrt(trades_per_year)
        return min(99.0, max(-99.0, raw))

    # --- Duration analysis ---

    @property
    def avg_trade_duration(self) -> timedelta:
        """Average time a trade is held open."""
        if not self.trades:
            return timedelta(0)
        total = sum((t.duration for t in self.trades), timedelta(0))
        return total / len(self.trades)

    @property
    def avg_trade_duration_hours(self) -> float:
        """Average trade duration in hours (for display)."""
        return self.avg_trade_duration.total_seconds() / 3600

    # --- Drawdown analysis ---

    @property
    def max_drawdown(self) -> float:
        """Maximum drawdown in price units from the equity curve."""
        if not self.trades:
            return 0.0
        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for trade in self.trades:
            equity += trade.pnl
            peak = max(peak, equity)
            dd = peak - equity
            max_dd = max(max_dd, dd)
        return max_dd

    @property
    def max_drawdown_duration_days(self) -> float:
        """Longest time (in days) from equity peak to recovery or end of test."""
        if not self.trades:
            return 0.0
        equity = 0.0
        peak = 0.0
        peak_time = self.trades[0].entry_time
        max_dd_dur = timedelta(0)
        for trade in self.trades:
            equity += trade.pnl
            if equity >= peak:
                peak = equity
                peak_time = trade.exit_time
            else:
                dd_dur = trade.exit_time - peak_time
                if dd_dur > max_dd_dur:
                    max_dd_dur = dd_dur
        return max_dd_dur.total_seconds() / 86400

    # --- Helpers ---

    def _trades_per_year(self) -> float:
        """Estimate annualized trade frequency from actual data."""
        if len(self.trades) < 2:
            return 0.0
        total_days = (self.trades[-1].exit_time - self.trades[0].entry_time).days
        if total_days == 0:
            return 0.0
        return len(self.trades) / total_days * 365

    # --- Verdict ---

    def live_readiness_check(self) -> Dict[str, dict]:
        """Evaluate strategy against live-trading criteria.

        Returns a dict of {criterion: {value, target, passed}}.
        """
        checks = {
            "profit_factor": {
                "value": round(self.profit_factor, 2),
                "target": ">= 1.3",
                "passed": self.profit_factor >= 1.3,
            },
            "win_rate": {
                "value": f"{self.win_rate:.1%}",
                "target": ">= 50%",
                "passed": self.win_rate >= 0.50,
            },
            "sharpe_ratio": {
                "value": round(self.sharpe_ratio, 2),
                "target": ">= 1.0",
                "passed": self.sharpe_ratio >= 1.0,
            },
            "total_trades": {
                "value": self.total_trades,
                "target": ">= 100",
                "passed": self.total_trades >= 100,
            },
            "expectancy_positive": {
                "value": round(self.expectancy, 2),
                "target": "> 0",
                "passed": self.expectancy > 0,
            },
            "beats_buy_hold": {
                "value": f"${self.total_pnl:,.0f} vs ${self.buy_hold_pnl:,.0f}",
                "target": "strategy > buy & hold",
                "passed": self.total_pnl > self.buy_hold_pnl,
            },
            "max_drawdown_duration": {
                "value": f"{self.max_drawdown_duration_days:.0f} days",
                "target": "< 30 days",
                "passed": self.max_drawdown_duration_days < 30,
            },
        }
        return checks

    # --- Display ---

    def summary(self) -> str:
        """Formatted summary with all metrics."""
        dur = self.avg_trade_duration
        dur_str = f"{dur.total_seconds() / 3600:.1f}h"

        lines = f"""
Backtest Results
================
Total Trades: {self.total_trades}
Winners: {self.winners} ({self.win_rate:.1%})
Losers: {self.losers}

P&L (gross):  ${self.total_pnl_gross:,.2f}
Costs:        ${self.total_costs:,.2f}  (cost_pct={self.cost_pct}%)
P&L (net):    ${self.total_pnl:,.2f} ({self.total_pnl_pct:.2f}%)
Avg Win:      ${self.avg_win:,.2f}
Avg Loss:     ${self.avg_loss:,.2f}
Expectancy:   ${self.expectancy:,.2f} / trade

Profit Factor:  {self.profit_factor:.2f}
Sharpe Ratio:   {self.sharpe_ratio:.2f}
Sortino Ratio:  {self.sortino_ratio:.2f}

Max Drawdown:          ${self.max_drawdown:,.2f}
Max Drawdown Duration: {self.max_drawdown_duration_days:.0f} days
Avg Trade Duration:    {dur_str}

Buy & Hold:    ${self.buy_hold_pnl:,.2f} ({self.buy_hold_pnl_pct:.2f}%)
"""
        # Live readiness
        checks = self.live_readiness_check()
        passed = sum(1 for c in checks.values() if c["passed"])
        total = len(checks)
        lines += f"\nLive Readiness: {passed}/{total} criteria met\n"
        for name, c in checks.items():
            icon = "PASS" if c["passed"] else "FAIL"
            lines += f"  [{icon}] {name}: {c['value']} (target: {c['target']})\n"

        return lines


# ---------------------------------------------------------------------------
# Backtest engine
# ---------------------------------------------------------------------------

class Backtest:
    """Event-driven backtest engine with transaction cost support.

    Args:
        data: List of OHLCV bar dicts (datetime, open, high, low, close, volume).
        cost_pct: Round-trip transaction cost as a percentage of trade value.
                  E.g., 0.1 means 0.1% total cost per trade (spread + commission).
                  Typical values: 0.05-0.1% for crypto majors, 0.02-0.05% for FX.

    Usage:
        bt = Backtest(data, cost_pct=0.1)
        bt.run(strategy_callable)
        print(bt.result.summary())
    """

    def __init__(self, data: List[Dict], cost_pct: float = 0.0):
        self.data = data
        self.cost_pct = cost_pct
        self.position: Optional[Position] = None
        self.result = BacktestResult(cost_pct=cost_pct)

    def run(self, strategy: Callable):
        """Run backtest with the given strategy callable.

        The strategy is called on each bar where there is no open position:
            signal = strategy(bar, prev_bars, position) -> Optional[dict]

        Signal dict keys:
            - 'action': 'buy' or 'sell'
            - 'stop_loss': price level
            - 'take_profit': price level
        """
        for i, bar in enumerate(self.data):
            prev_bars = self.data[max(0, i - 100):i]

            # Check if position hit SL/TP
            if self.position:
                self._check_exit(bar)

            # Get strategy signal (only when flat)
            if not self.position:
                signal = strategy(bar, prev_bars, self.position)
                if signal:
                    self._process_signal(bar, signal)

        # Close any remaining position at end of data
        if self.position:
            self._close_position(self.data[-1], self.data[-1]['close'])

        # Compute buy-and-hold benchmark
        if len(self.data) >= 2:
            start_price = self.data[0]['close']
            end_price = self.data[-1]['close']
            self.result.buy_hold_pnl = end_price - start_price
            self.result.buy_hold_pnl_pct = ((end_price - start_price) / start_price) * 100

    def _process_signal(self, bar: Dict, signal: Dict):
        """Open a new position from a strategy signal."""
        action = signal.get('action')
        if action == 'buy':
            self.position = Position(
                entry_time=bar['datetime'],
                direction=Direction.LONG,
                entry_price=bar['close'],
                stop_loss=signal['stop_loss'],
                take_profit=signal['take_profit'],
            )
        elif action == 'sell':
            self.position = Position(
                entry_time=bar['datetime'],
                direction=Direction.SHORT,
                entry_price=bar['close'],
                stop_loss=signal['stop_loss'],
                take_profit=signal['take_profit'],
            )

    def _check_exit(self, bar: Dict):
        """Check if the open position hit its stop loss or take profit."""
        if not self.position:
            return
        if self.position.direction == Direction.LONG:
            if bar['low'] <= self.position.stop_loss:
                self._close_position(bar, self.position.stop_loss)
            elif bar['high'] >= self.position.take_profit:
                self._close_position(bar, self.position.take_profit)
        else:  # SHORT
            if bar['high'] >= self.position.stop_loss:
                self._close_position(bar, self.position.stop_loss)
            elif bar['low'] <= self.position.take_profit:
                self._close_position(bar, self.position.take_profit)

    def _close_position(self, bar: Dict, exit_price: float):
        """Close position, apply transaction costs, and record the trade."""
        if not self.position:
            return
        # Transaction cost = cost_pct% of entry price (round-trip)
        costs = self.position.entry_price * (self.cost_pct / 100) * self.position.size
        trade = Trade(
            entry_time=self.position.entry_time,
            exit_time=bar['datetime'],
            direction=self.position.direction,
            entry_price=self.position.entry_price,
            exit_price=exit_price,
            size=self.position.size,
            costs=costs,
        )
        self.result.trades.append(trade)
        self.position = None


# ---------------------------------------------------------------------------
# Walk-forward (rolling window) validation
# ---------------------------------------------------------------------------

def walk_forward(
    data: List[Dict],
    strategy_factory: Callable,
    window_bars: int = 2000,
    cost_pct: float = 0.0,
) -> List[Dict]:
    """Run a strategy across rolling non-overlapping windows.

    For rule-based strategies (fixed parameters), this tests whether the edge
    is stable across different time periods rather than concentrated in one regime.

    Args:
        data: Full OHLCV dataset.
        strategy_factory: Callable that returns a fresh strategy instance.
        window_bars: Number of bars per test window.
        cost_pct: Transaction cost percentage per trade.

    Returns:
        List of dicts with keys: period_start, period_end, result (BacktestResult).
    """
    results = []
    i = 0
    while i + window_bars <= len(data):
        window = data[i : i + window_bars]
        strategy = strategy_factory()
        bt = Backtest(window, cost_pct=cost_pct)
        bt.run(strategy)
        results.append({
            'period_start': window[0]['datetime'],
            'period_end': window[-1]['datetime'],
            'result': bt.result,
        })
        i += window_bars
    return results


def walk_forward_summary(results: List[Dict]) -> str:
    """Format walk-forward results into a readable table.

    Args:
        results: Output from walk_forward().

    Returns:
        Formatted string with per-window and aggregate metrics.
    """
    if not results:
        return "No walk-forward results."

    lines = [
        "\nWalk-Forward Validation",
        "=" * 60,
        f"{'Period':<28} {'Trades':>6} {'WR':>6} {'PF':>6} {'Sharpe':>7} {'Net P&L':>12}",
        "-" * 60,
    ]

    all_trades = []
    for r in results:
        res = r['result']
        start = r['period_start'].strftime('%Y-%m-%d')
        end = r['period_end'].strftime('%Y-%m-%d')
        lines.append(
            f"{start} → {end}  "
            f"{res.total_trades:>6} "
            f"{res.win_rate:>5.1%} "
            f"{res.profit_factor:>6.2f} "
            f"{res.sharpe_ratio:>7.2f} "
            f"${res.total_pnl:>10,.2f}"
        )
        all_trades.extend(res.trades)

    # Aggregate stats
    profitable_windows = sum(1 for r in results if r['result'].total_pnl > 0)
    total_windows = len(results)
    total_net = sum(r['result'].total_pnl for r in results)

    lines.append("-" * 60)
    lines.append(f"Windows: {total_windows}  |  Profitable: {profitable_windows}/{total_windows}  |  Total Net: ${total_net:,.2f}")

    # Consistency check
    if total_windows >= 3:
        pf_values = [r['result'].profit_factor for r in results if r['result'].total_trades > 0]
        if len(pf_values) >= 2:
            pf_std = statistics.stdev(pf_values)
            pf_mean = statistics.mean(pf_values)
            lines.append(f"PF consistency: mean={pf_mean:.2f}, std={pf_std:.2f}")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Out-of-sample split runner
# ---------------------------------------------------------------------------

def run_in_out_of_sample(
    data: List[Dict],
    strategy_factory: Callable,
    train_pct: float = 0.7,
    cost_pct: float = 0.0,
) -> Dict:
    """Split data into in-sample and out-of-sample, run both.

    Args:
        data: Full OHLCV dataset.
        strategy_factory: Callable returning a fresh strategy instance.
        train_pct: Fraction of data for in-sample (default 70%).
        cost_pct: Transaction cost percentage.

    Returns:
        Dict with keys: in_sample (BacktestResult), out_of_sample (BacktestResult).
    """
    split_idx = int(len(data) * train_pct)
    in_sample_data = data[:split_idx]
    out_of_sample_data = data[split_idx:]

    bt_is = Backtest(in_sample_data, cost_pct=cost_pct)
    bt_is.run(strategy_factory())

    bt_oos = Backtest(out_of_sample_data, cost_pct=cost_pct)
    bt_oos.run(strategy_factory())

    return {
        'in_sample': bt_is.result,
        'out_of_sample': bt_oos.result,
        'in_sample_bars': len(in_sample_data),
        'out_of_sample_bars': len(out_of_sample_data),
    }


def in_out_of_sample_summary(results: Dict) -> str:
    """Format in-sample vs out-of-sample comparison."""
    is_res = results['in_sample']
    oos_res = results['out_of_sample']

    lines = [
        "\nIn-Sample vs Out-of-Sample",
        "=" * 55,
        f"{'Metric':<25} {'In-Sample':>13} {'Out-of-Sample':>13}",
        "-" * 55,
        f"{'Bars':<25} {results['in_sample_bars']:>13,} {results['out_of_sample_bars']:>13,}",
        f"{'Total Trades':<25} {is_res.total_trades:>13} {oos_res.total_trades:>13}",
        f"{'Win Rate':<25} {is_res.win_rate:>12.1%} {oos_res.win_rate:>12.1%}",
        f"{'Profit Factor':<25} {is_res.profit_factor:>13.2f} {oos_res.profit_factor:>13.2f}",
        f"{'Sharpe Ratio':<25} {is_res.sharpe_ratio:>13.2f} {oos_res.sharpe_ratio:>13.2f}",
        f"{'Net P&L':<25} ${is_res.total_pnl:>11,.2f} ${oos_res.total_pnl:>11,.2f}",
        f"{'Max Drawdown':<25} ${is_res.max_drawdown:>11,.2f} ${oos_res.max_drawdown:>11,.2f}",
        f"{'Avg Duration':<25} {is_res.avg_trade_duration_hours:>12.1f}h {oos_res.avg_trade_duration_hours:>12.1f}h",
        "-" * 55,
    ]

    # Degradation check
    if is_res.profit_factor > 0 and oos_res.profit_factor > 0:
        pf_decay = (oos_res.profit_factor - is_res.profit_factor) / is_res.profit_factor * 100
        lines.append(f"PF change in-sample → out-of-sample: {pf_decay:+.1f}%")
        if pf_decay < -30:
            lines.append("WARNING: >30% PF degradation suggests overfitting")
        elif oos_res.profit_factor >= 1.2:
            lines.append("Out-of-sample PF >= 1.2 — edge appears robust")

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print("Backtest engine ready.")
    print("See mean_reversion.py or london_breakout.py for usage examples.")
