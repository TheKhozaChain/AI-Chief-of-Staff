#!/usr/bin/env python3
"""
Paper trading monitor for H004 (Volatility-Adjusted Trend Following).

Fetches recent BTCUSD data, runs the strategy on new 4H bars,
tracks simulated positions, and sends email alerts on trade signals.

State persists in data/paper_trade_state.json between runs.
Designed to run every 4 hours via GitHub Actions.

Usage:
    python scripts/paper_trade.py             # Normal run
    python scripts/paper_trade.py --status    # Print current state
    python scripts/paper_trade.py --reset     # Reset state (start fresh)
"""

import json
import sys
import os
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# Setup paths
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'strategies' / 'backtest'))
sys.path.insert(0, str(REPO_ROOT / 'scripts'))

from archetypes import VolAdjustedTrend
from data_loader import resample

STATE_FILE = REPO_ROOT / 'data' / 'paper_trade_state.json'
LOG_FILE = REPO_ROOT / 'data' / 'paper_trade_log.md'
COST_PCT = 0.1  # 0.1% round-trip

# H004 validated params
STRATEGY_PARAMS = {
    'ma_period': 30,
    'atr_period': 20,
    'stop_atr_mult': 3.0,
    'target_atr_mult': 6.0,
    'trend_filter_period': 80,
    'long_only': True,
}


# ── Data fetching ─────────────────────────────────────────────────

def fetch_recent_1h(days=60):
    """Fetch recent BTCUSD 1H candles from Binance."""
    url = "https://api.binance.com/api/v3/klines"
    all_data = []
    end_time = int(datetime.utcnow().timestamp() * 1000)
    start_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    current = start_time

    while current < end_time:
        req_url = f"{url}?symbol=BTCUSDT&interval=1h&startTime={current}&limit=1000"
        try:
            req = urllib.request.Request(req_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                if not data:
                    break
                all_data.extend(data)
                current = data[-1][0] + 1
                time.sleep(0.2)
        except Exception as e:
            print(f"  Fetch error: {e}, retrying...")
            time.sleep(3)
            continue

    # Convert to bar dicts
    bars = []
    for c in all_data:
        bars.append({
            'datetime': datetime.utcfromtimestamp(c[0] / 1000),
            'open': float(c[1]),
            'high': float(c[2]),
            'low': float(c[3]),
            'close': float(c[4]),
            'volume': float(c[5]),
        })
    bars.sort(key=lambda x: x['datetime'])
    return bars


# ── State management ──────────────────────────────────────────────

def load_state():
    """Load paper trading state from JSON."""
    if STATE_FILE.exists():
        raw = json.loads(STATE_FILE.read_text())
        # Parse datetime strings back to datetime objects where needed
        if raw.get('position') and raw['position'].get('entry_time'):
            raw['position']['entry_time'] = datetime.fromisoformat(raw['position']['entry_time'])
        if raw.get('last_bar_time'):
            raw['last_bar_time'] = datetime.fromisoformat(raw['last_bar_time'])
        for t in raw.get('trades', []):
            t['entry_time'] = datetime.fromisoformat(t['entry_time'])
            t['exit_time'] = datetime.fromisoformat(t['exit_time'])
        return raw
    return {
        'strategy': 'H004_VolAdjustedTrend',
        'params': STRATEGY_PARAMS,
        'started': datetime.utcnow().isoformat(),
        'position': None,
        'last_bar_time': None,
        'trades': [],
        'total_pnl': 0.0,
        'total_costs': 0.0,
    }


def save_state(state):
    """Save state to JSON with datetime serialization."""
    def serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Not serializable: {type(obj)}")

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=serialize) + '\n')


# ── Position tracking ─────────────────────────────────────────────

def check_exit(bar, position):
    """Check if position SL/TP hit on this bar. Returns exit_price or None."""
    sl = position['stop_loss']
    tp = position['take_profit']

    # Long position: SL if low <= stop, TP if high >= target
    if bar['low'] <= sl:
        return sl, 'stop_loss'
    if bar['high'] >= tp:
        return tp, 'take_profit'
    return None, None


def record_trade(state, bar, exit_price, exit_reason):
    """Close position, record trade, update P&L."""
    pos = state['position']
    entry = pos['entry_price']
    pnl_gross = (exit_price - entry)
    cost = entry * (COST_PCT / 100)
    pnl_net = pnl_gross - cost
    pnl_pct = (pnl_net / entry) * 100

    trade = {
        'entry_time': pos['entry_time'],
        'entry_price': entry,
        'exit_time': bar['datetime'],
        'exit_price': exit_price,
        'stop_loss': pos['stop_loss'],
        'take_profit': pos['take_profit'],
        'exit_reason': exit_reason,
        'pnl_gross': round(pnl_gross, 2),
        'pnl_net': round(pnl_net, 2),
        'pnl_pct': round(pnl_pct, 4),
        'cost': round(cost, 2),
    }

    state['trades'].append(trade)
    state['total_pnl'] += pnl_net
    state['total_costs'] += cost
    state['position'] = None

    return trade


def open_position(state, bar, signal):
    """Open a new paper position."""
    state['position'] = {
        'entry_time': bar['datetime'],
        'entry_price': bar['close'],
        'stop_loss': signal['stop_loss'],
        'take_profit': signal['take_profit'],
    }
    return state['position']


# ── Logging ───────────────────────────────────────────────────────

def append_log(message):
    """Append a timestamped entry to the paper trade log."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    entry = f"- **{timestamp}** — {message}\n"

    if not LOG_FILE.exists():
        LOG_FILE.write_text(
            "# Paper Trading Log — H004 (Vol-Adjusted Trend)\n\n"
            f"Started: {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
            "---\n\n"
        )

    with open(LOG_FILE, 'a') as f:
        f.write(entry)


def send_alert(subject, body):
    """Send email alert for trade signals."""
    try:
        from email_sender import send_email, markdown_to_html
        send_email(
            subject=f"[H004 Paper] {subject}",
            body=markdown_to_html(body),
            html=True,
        )
    except Exception as e:
        print(f"  Alert email failed: {e}")


# ── Main logic ────────────────────────────────────────────────────

def run():
    """Main paper trading loop."""
    print("=" * 60)
    print("H004 PAPER TRADING MONITOR")
    print(f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # Load state
    state = load_state()
    last_time = state.get('last_bar_time')
    print(f"\nLast processed: {last_time or 'never (first run)'}")

    if state['position']:
        pos = state['position']
        print(f"Open position: LONG @ ${pos['entry_price']:,.2f}")
        print(f"  SL: ${pos['stop_loss']:,.2f}  |  TP: ${pos['take_profit']:,.2f}")
    else:
        print("No open position")

    print(f"Completed trades: {len(state['trades'])}")
    print(f"Running P&L: ${state['total_pnl']:,.2f}")

    # Fetch recent data
    print(f"\nFetching recent 1H data...")
    bars_1h = fetch_recent_1h(days=60)
    if not bars_1h:
        print("ERROR: No data fetched!")
        return state

    print(f"  Got {len(bars_1h)} 1H bars")
    print(f"  Range: {bars_1h[0]['datetime']} → {bars_1h[-1]['datetime']}")

    # Resample to 4H
    bars_4h = resample(bars_1h, hours=4)
    print(f"  Resampled to {len(bars_4h)} 4H bars")

    # Find new bars to process
    if last_time:
        new_bars_start = None
        for i, bar in enumerate(bars_4h):
            if bar['datetime'] > last_time:
                new_bars_start = i
                break
        if new_bars_start is None:
            print("\nNo new bars since last run.")
            # Still update state with latest bar time
            state['last_bar_time'] = bars_4h[-1]['datetime']
            save_state(state)
            return state
        # We need prev_bars for the strategy, so slice carefully
    else:
        # First run: only process the very last bar
        new_bars_start = len(bars_4h) - 1

    # Create strategy instance
    strategy = VolAdjustedTrend(**STRATEGY_PARAMS)

    events = []
    print(f"\nProcessing {len(bars_4h) - new_bars_start} new bar(s)...")

    for i in range(new_bars_start, len(bars_4h)):
        bar = bars_4h[i]
        prev_bars = bars_4h[max(0, i - 300):i]

        # Check exit first
        if state['position']:
            exit_price, exit_reason = check_exit(bar, state['position'])
            if exit_price is not None:
                trade = record_trade(state, bar, exit_price, exit_reason)
                icon = "TP HIT" if exit_reason == 'take_profit' else "SL HIT"
                msg = (f"{icon}: Exited @ ${exit_price:,.2f} "
                       f"(entry ${trade['entry_price']:,.2f}, "
                       f"P&L ${trade['pnl_net']:+,.2f} / {trade['pnl_pct']:+.2f}%)")
                print(f"  [{bar['datetime']}] {msg}")
                events.append(('exit', trade, msg))

        # Check for entry signal (only when flat)
        if not state['position']:
            signal = strategy(bar, prev_bars, None)
            if signal and signal.get('action') == 'buy':
                pos = open_position(state, bar, signal)
                msg = (f"ENTRY: Long @ ${bar['close']:,.2f} "
                       f"(SL: ${signal['stop_loss']:,.2f}, "
                       f"TP: ${signal['take_profit']:,.2f})")
                print(f"  [{bar['datetime']}] {msg}")
                events.append(('entry', pos, msg))

    # Update last processed time
    state['last_bar_time'] = bars_4h[-1]['datetime']

    # Current price context
    current_price = bars_4h[-1]['close']
    print(f"\nCurrent BTC price: ${current_price:,.2f}")

    if state['position']:
        pos = state['position']
        unrealized = current_price - pos['entry_price']
        unrealized_pct = (unrealized / pos['entry_price']) * 100
        dist_to_sl = ((current_price - pos['stop_loss']) / current_price) * 100
        dist_to_tp = ((pos['take_profit'] - current_price) / current_price) * 100
        print(f"Unrealized P&L: ${unrealized:+,.2f} ({unrealized_pct:+.2f}%)")
        print(f"Distance to SL: {dist_to_sl:.2f}%  |  Distance to TP: {dist_to_tp:.2f}%")

    # Save state
    save_state(state)
    print(f"\nState saved to {STATE_FILE}")

    # Send alerts and log events
    for event_type, data, msg in events:
        append_log(msg)

        if event_type == 'entry':
            body = (f"### New Paper Trade\n\n"
                    f"**LONG BTCUSD** @ ${data['entry_price']:,.2f}\n\n"
                    f"- Stop Loss: ${data['stop_loss']:,.2f}\n"
                    f"- Take Profit: ${data['take_profit']:,.2f}\n"
                    f"- Time: {data['entry_time']}\n")
            send_alert("ENTRY — Long BTCUSD", body)

        elif event_type == 'exit':
            result = "WIN" if data['pnl_net'] > 0 else "LOSS"
            body = (f"### Trade Closed — {result}\n\n"
                    f"**Exit** @ ${data['exit_price']:,.2f} "
                    f"({data['exit_reason']})\n\n"
                    f"- Entry: ${data['entry_price']:,.2f}\n"
                    f"- P&L: ${data['pnl_net']:+,.2f} ({data['pnl_pct']:+.2f}%)\n"
                    f"- Costs: ${data['cost']:,.2f}\n"
                    f"- Running total: ${state['total_pnl']:+,.2f} "
                    f"({len(state['trades'])} trades)\n")
            send_alert(f"{result} — ${data['pnl_net']:+,.0f}", body)

    # Summary
    print(f"\n{'='*60}")
    print(f"Status: {'IN POSITION' if state['position'] else 'FLAT'}")
    print(f"Trades: {len(state['trades'])}  |  P&L: ${state['total_pnl']:+,.2f}")
    if events:
        print(f"Events this run: {len(events)}")
    print(f"{'='*60}")

    return state


def print_status():
    """Print current paper trading state."""
    state = load_state()
    print("H004 Paper Trading Status")
    print("=" * 40)
    print(f"Started: {state.get('started', '?')}")
    print(f"Trades: {len(state.get('trades', []))}")
    print(f"Total P&L: ${state.get('total_pnl', 0):+,.2f}")
    print(f"Total Costs: ${state.get('total_costs', 0):,.2f}")

    if state.get('position'):
        pos = state['position']
        print(f"\nOpen: LONG @ ${pos['entry_price']:,.2f}")
        print(f"  SL: ${pos['stop_loss']:,.2f}")
        print(f"  TP: ${pos['take_profit']:,.2f}")
        print(f"  Since: {pos['entry_time']}")
    else:
        print("\nNo open position")

    if state.get('trades'):
        print(f"\nRecent trades:")
        for t in state['trades'][-5:]:
            result = "WIN" if t['pnl_net'] > 0 else "LOSS"
            print(f"  {t['entry_time'][:10]} → {t['exit_time'][:10]}: "
                  f"${t['pnl_net']:+,.2f} ({t['exit_reason']}) [{result}]")


def reset_state():
    """Reset paper trading state."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    print("Paper trading state reset.")


if __name__ == '__main__':
    if '--status' in sys.argv:
        print_status()
    elif '--reset' in sys.argv:
        reset_state()
    else:
        run()
