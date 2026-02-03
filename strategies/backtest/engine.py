"""
Simple backtesting engine.

No external dependencies. Easy to understand and modify.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Callable
from enum import Enum


class Direction(Enum):
    LONG = 1
    SHORT = -1


@dataclass
class Trade:
    """Represents a completed trade."""
    entry_time: datetime
    exit_time: datetime
    direction: Direction
    entry_price: float
    exit_price: float
    size: float = 1.0
    
    @property
    def pnl(self) -> float:
        """Profit/loss in price units."""
        if self.direction == Direction.LONG:
            return (self.exit_price - self.entry_price) * self.size
        else:
            return (self.entry_price - self.exit_price) * self.size
    
    @property
    def pnl_pips(self) -> float:
        """P&L in pips (assumes 4-decimal forex)."""
        return self.pnl * 10000


@dataclass
class Position:
    """Represents an open position."""
    entry_time: datetime
    direction: Direction
    entry_price: float
    stop_loss: float
    take_profit: float
    size: float = 1.0


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    trades: List[Trade] = field(default_factory=list)
    
    @property
    def total_trades(self) -> int:
        return len(self.trades)
    
    @property
    def winners(self) -> int:
        return len([t for t in self.trades if t.pnl > 0])
    
    @property
    def losers(self) -> int:
        return len([t for t in self.trades if t.pnl < 0])
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.winners / self.total_trades
    
    @property
    def total_pnl(self) -> float:
        return sum(t.pnl for t in self.trades)
    
    @property
    def total_pnl_pips(self) -> float:
        return sum(t.pnl_pips for t in self.trades)
    
    @property
    def avg_win(self) -> float:
        wins = [t.pnl for t in self.trades if t.pnl > 0]
        return sum(wins) / len(wins) if wins else 0.0
    
    @property
    def avg_loss(self) -> float:
        losses = [t.pnl for t in self.trades if t.pnl < 0]
        return sum(losses) / len(losses) if losses else 0.0
    
    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        return gross_profit / gross_loss
    
    @property
    def max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve."""
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
    
    def summary(self) -> str:
        """Return formatted summary string."""
        return f"""
Backtest Results
================
Total Trades: {self.total_trades}
Winners: {self.winners} ({self.win_rate:.1%})
Losers: {self.losers}

Total P&L: {self.total_pnl:.4f} ({self.total_pnl_pips:.1f} pips)
Avg Win: {self.avg_win:.4f}
Avg Loss: {self.avg_loss:.4f}
Profit Factor: {self.profit_factor:.2f}
Max Drawdown: {self.max_drawdown:.4f}
"""


class Backtest:
    """
    Simple event-driven backtest engine.
    
    Usage:
        bt = Backtest(data)
        bt.run(strategy_func)
        print(bt.result.summary())
    """
    
    def __init__(self, data: List[Dict]):
        self.data = data
        self.position: Optional[Position] = None
        self.result = BacktestResult()
    
    def run(self, strategy: Callable):
        """
        Run backtest with given strategy function.
        
        Strategy function signature:
            def strategy(bar, prev_bars, position) -> Optional[dict]
            
        Returns dict with keys:
            - 'action': 'buy', 'sell', 'close', or None
            - 'stop_loss': price (required for buy/sell)
            - 'take_profit': price (required for buy/sell)
        """
        for i, bar in enumerate(self.data):
            prev_bars = self.data[max(0, i-100):i]  # Last 100 bars
            
            # Check if position hit SL/TP
            if self.position:
                self._check_exit(bar)
            
            # Get strategy signal
            if not self.position:  # Only look for entries if flat
                signal = strategy(bar, prev_bars, self.position)
                if signal:
                    self._process_signal(bar, signal)
        
        # Close any remaining position at end
        if self.position:
            self._close_position(self.data[-1], self.data[-1]['close'])
    
    def _process_signal(self, bar: Dict, signal: Dict):
        """Process strategy signal."""
        action = signal.get('action')
        
        if action == 'buy':
            self.position = Position(
                entry_time=bar['datetime'],
                direction=Direction.LONG,
                entry_price=bar['close'],
                stop_loss=signal['stop_loss'],
                take_profit=signal['take_profit']
            )
        elif action == 'sell':
            self.position = Position(
                entry_time=bar['datetime'],
                direction=Direction.SHORT,
                entry_price=bar['close'],
                stop_loss=signal['stop_loss'],
                take_profit=signal['take_profit']
            )
    
    def _check_exit(self, bar: Dict):
        """Check if position hit stop loss or take profit."""
        if not self.position:
            return
        
        if self.position.direction == Direction.LONG:
            # Check stop loss (low of bar)
            if bar['low'] <= self.position.stop_loss:
                self._close_position(bar, self.position.stop_loss)
            # Check take profit (high of bar)
            elif bar['high'] >= self.position.take_profit:
                self._close_position(bar, self.position.take_profit)
        else:  # SHORT
            # Check stop loss (high of bar)
            if bar['high'] >= self.position.stop_loss:
                self._close_position(bar, self.position.stop_loss)
            # Check take profit (low of bar)
            elif bar['low'] <= self.position.take_profit:
                self._close_position(bar, self.position.take_profit)
    
    def _close_position(self, bar: Dict, exit_price: float):
        """Close position and record trade."""
        if not self.position:
            return
        
        trade = Trade(
            entry_time=self.position.entry_time,
            exit_time=bar['datetime'],
            direction=self.position.direction,
            entry_price=self.position.entry_price,
            exit_price=exit_price,
            size=self.position.size
        )
        self.result.trades.append(trade)
        self.position = None


if __name__ == "__main__":
    print("Backtest engine ready.")
    print("See strategies/backtest/example_strategy.py for usage.")
