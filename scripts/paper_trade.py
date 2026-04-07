#!/usr/bin/env python3
"""
Multi-strategy paper trading monitor.

Reads active strategies from data/paper_trade_registry.json,
fetches live BTCUSD data, processes new bars for each strategy,
tracks simulated positions, evaluates graduation criteria,
and sends email alerts on signals and graduation.

Per-strategy state: data/paper_trade_{id}_state.json
Per-strategy log:   data/paper_trade_{id}_log.md
Registry:           data/paper_trade_registry.json

Usage:
    python scripts/paper_trade.py             # Normal run (all active strategies)
    python scripts/paper_trade.py --status    # Print state of all strategies
    python scripts/paper_trade.py --reset H004  # Reset one strategy
    python scripts/paper_trade.py --reset-all   # Reset everything
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

from archetypes import ARCHETYPES
from data_loader import resample

# Load policy thresholds (single source of truth)
try:
    from policy_loader import load_kill_criteria
    _policy = load_kill_criteria()
    _pt = _policy['paper_trading']
    _st = _policy['staleness']
    POLICY_KILL_PF = _pt['kill_pf_below']
    POLICY_KILL_MIN_TRADES = _pt['kill_min_trades']
    POLICY_MAX_DAYS = _pt['max_days']
    POLICY_MIN_TRADES = _pt['min_trades_for_eval']
    POLICY_ZERO_TRADE_KILL_DAYS = _pt['zero_trade_kill_days']
    POLICY_ZERO_TRADE_LIMBO_DAYS = _pt['zero_trade_limbo_days']
    POLICY_STALE_WARNING_DAYS = _st['warning_days_no_trades']
    POLICY_STALE_SILENT_DAYS = _st['warning_days_silent']
except (ImportError, FileNotFoundError):
    POLICY_KILL_PF = 0.8
    POLICY_KILL_MIN_TRADES = 5
    POLICY_MAX_DAYS = 45
    POLICY_MIN_TRADES = 5
    POLICY_ZERO_TRADE_KILL_DAYS = 30
    POLICY_ZERO_TRADE_LIMBO_DAYS = 45
    POLICY_STALE_WARNING_DAYS = 14
    POLICY_STALE_SILENT_DAYS = 30

DATA_DIR = REPO_ROOT / 'data'
REGISTRY_FILE = DATA_DIR / 'paper_trade_registry.json'
COST_PCT = 0.1  # 0.1% round-trip
WARMUP_BARS = 180  # ~30 days of 4H bars for first-run lookback


# ── Data fetching ─────────────────────────────────────────────────

def fetch_recent_1h(days=60):
    """Fetch recent BTCUSD 1H candles with Binance → Bybit → CryptoCompare fallback.

    GitHub Actions runs in the US where Binance (HTTP 451) and Bybit (HTTP 403)
    are geoblocked. Falls back to CryptoCompare which works globally.
    """
    all_data = []

    # Try Binance first
    try:
        all_data = _fetch_binance_1h(days)
    except RuntimeError as e:
        print(f"  Binance failed ({e}). Trying Bybit...")
        try:
            all_data = _fetch_bybit_1h(days)
        except Exception as bybit_err:
            print(f"  Bybit also failed ({bybit_err}). Trying CryptoCompare...")
            try:
                all_data = _fetch_cryptocompare_1h(days)
            except Exception as cc_err:
                print(f"  CryptoCompare also failed: {cc_err}")
                return []

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


def _fetch_binance_1h(days):
    """Fetch from Binance. Raises RuntimeError on geoblock."""
    url = "https://api.binance.com/api/v3/klines"
    all_data = []
    end_time = int(datetime.utcnow().timestamp() * 1000)
    start_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    current = start_time

    max_retries = 3
    consecutive_errors = 0
    wall_start = time.monotonic()
    wall_timeout = 300

    while current < end_time:
        if time.monotonic() - wall_start > wall_timeout:
            print(f"  Hit time limit ({wall_timeout}s). Using {len(all_data)} candles.")
            break
        req_url = f"{url}?symbol=BTCUSDT&interval=1h&startTime={current}&limit=1000"
        try:
            req = urllib.request.Request(req_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                if not data:
                    break
                all_data.extend(data)
                current = data[-1][0] + 1
                consecutive_errors = 0
                time.sleep(0.2)
        except Exception as e:
            error_str = str(e)
            if "451" in error_str or "403" in error_str:
                raise RuntimeError(f"Binance geoblock: {e}")
            consecutive_errors += 1
            print(f"  Binance error ({consecutive_errors}/{max_retries}): {e}")
            if consecutive_errors >= max_retries:
                raise RuntimeError(f"Binance failed after {max_retries} errors: {e}")
            time.sleep(3)
            continue

    return all_data


def _fetch_bybit_1h(days):
    """Fetch BTCUSDT 1H from Bybit. Returns Binance-compatible candle format."""
    all_data = []
    end_time = int(datetime.utcnow().timestamp() * 1000)
    start_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    current = start_time

    max_retries = 5
    consecutive_errors = 0
    wall_start = time.monotonic()
    wall_timeout = 300
    request_count = 0

    print(f"  [Bybit] Fetching {days} days of 1H BTCUSDT...")

    while current < end_time:
        if time.monotonic() - wall_start > wall_timeout:
            print(f"  Hit time limit ({wall_timeout}s). Using {len(all_data)} candles.")
            break
        if request_count >= 200:
            break

        req_url = (
            f"https://api.bybit.com/v5/market/kline"
            f"?category=spot&symbol=BTCUSDT&interval=60"
            f"&start={current}&limit=1000"
        )
        try:
            req = urllib.request.Request(req_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                rows = data.get("result", {}).get("list", [])
                if not rows:
                    break
                # Bybit returns descending order
                rows.sort(key=lambda r: int(r[0]))
                for r in rows:
                    ts_ms = int(r[0])
                    if ts_ms < current:
                        continue
                    # [ts, o, h, l, c, v] — Binance-compatible
                    all_data.append([ts_ms, r[1], r[2], r[3], r[4], r[5]])
                current = int(rows[-1][0]) + 1
                request_count += 1
                consecutive_errors = 0
                if request_count % 10 == 0:
                    print(f"    {len(all_data):,} candles ({request_count} reqs)...")
                if request_count % 50 == 0:
                    time.sleep(1)
        except Exception as e:
            consecutive_errors += 1
            print(f"  Bybit error ({consecutive_errors}/{max_retries}): {e}")
            if consecutive_errors >= max_retries:
                raise RuntimeError(f"Bybit failed after {max_retries} errors: {e}")
            time.sleep(3)
            continue

    # Deduplicate
    seen = set()
    deduped = []
    for candle in all_data:
        ts = candle[0]
        if ts not in seen:
            seen.add(ts)
            deduped.append(candle)
    deduped.sort(key=lambda c: c[0])

    print(f"  [Bybit] Got {len(deduped):,} candles in {request_count} requests")
    return deduped


def _fetch_cryptocompare_1h(days):
    """Fetch BTCUSD 1H from CryptoCompare. Works globally (no geoblock).

    Returns Binance-compatible [ts_ms, open, high, low, close, volume] format.
    """
    all_data = []
    # CryptoCompare returns up to 2000 candles per request
    # For 60 days = 1440 hourly candles, one request is enough
    # For longer periods, paginate backwards
    to_ts = int(datetime.utcnow().timestamp())
    remaining_hours = days * 24
    request_count = 0

    print(f"  [CryptoCompare] Fetching {days} days of 1H BTCUSD...")

    while remaining_hours > 0:
        limit = min(remaining_hours, 2000)
        req_url = (
            f"https://min-api.cryptocompare.com/data/v2/histohour"
            f"?fsym=BTC&tsym=USD&limit={limit}&toTs={to_ts}"
        )
        try:
            req = urllib.request.Request(req_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                candles = data.get("Data", {}).get("Data", [])
                if not candles:
                    break
                for c in candles:
                    ts_ms = c["time"] * 1000
                    all_data.append([
                        ts_ms,
                        str(c["open"]),
                        str(c["high"]),
                        str(c["low"]),
                        str(c["close"]),
                        str(c.get("volumefrom", 0)),
                    ])
                # Move window back
                to_ts = candles[0]["time"] - 1
                remaining_hours -= len(candles)
                request_count += 1
                if request_count % 5 == 0:
                    print(f"    {len(all_data):,} candles ({request_count} reqs)...")
                time.sleep(0.5)
        except Exception as e:
            raise RuntimeError(f"CryptoCompare failed: {e}")

    # Deduplicate and sort
    seen = set()
    deduped = []
    for candle in all_data:
        ts = candle[0]
        if ts not in seen:
            seen.add(ts)
            deduped.append(candle)
    deduped.sort(key=lambda c: c[0])

    print(f"  [CryptoCompare] Got {len(deduped):,} candles in {request_count} requests")
    return deduped


# ── Registry management ──────────────────────────────────────────

def load_registry():
    """Load the paper trade registry."""
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text())
    return {"active": [], "graduated": [], "killed": []}


def save_registry(registry):
    """Save registry to JSON."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2) + '\n')


# ── Per-strategy state management ────────────────────────────────

def state_file_for(strategy_id):
    return DATA_DIR / f'paper_trade_{strategy_id}_state.json'


def log_file_for(strategy_id):
    return DATA_DIR / f'paper_trade_{strategy_id}_log.md'


def load_state(strategy_id, config):
    """Load per-strategy paper trading state."""
    sf = state_file_for(strategy_id)
    if sf.exists():
        raw = json.loads(sf.read_text())
        if raw.get('position') and raw['position'].get('entry_time'):
            raw['position']['entry_time'] = datetime.fromisoformat(raw['position']['entry_time'])
        if raw.get('last_bar_time'):
            raw['last_bar_time'] = datetime.fromisoformat(raw['last_bar_time'])
        for t in raw.get('trades', []):
            t['entry_time'] = datetime.fromisoformat(t['entry_time'])
            t['exit_time'] = datetime.fromisoformat(t['exit_time'])
        return raw
    return {
        'strategy_id': strategy_id,
        'archetype': config['archetype'],
        'params': config['params'],
        'started': config.get('started', datetime.utcnow().strftime('%Y-%m-%d')),
        'position': None,
        'last_bar_time': None,
        'trades': [],
        'total_pnl': 0.0,
        'total_costs': 0.0,
    }


def save_state(strategy_id, state):
    """Save per-strategy state to JSON."""
    def serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Not serializable: {type(obj)}")

    sf = state_file_for(strategy_id)
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps(state, indent=2, default=serialize) + '\n')


# ── Position tracking ─────────────────────────────────────────────

def check_exit(bar, position):
    """Check if position SL/TP hit on this bar (direction-aware)."""
    sl = position['stop_loss']
    tp = position['take_profit']
    direction = position.get('direction', 'long')

    if direction == 'long':
        if bar['low'] <= sl:
            return sl, 'stop_loss'
        if bar['high'] >= tp:
            return tp, 'take_profit'
    else:  # short
        if bar['high'] >= sl:
            return sl, 'stop_loss'
        if bar['low'] <= tp:
            return tp, 'take_profit'

    return None, None


def record_trade(state, bar, exit_price, exit_reason):
    """Close position, record trade, update P&L (direction-aware)."""
    pos = state['position']
    entry = pos['entry_price']
    direction = pos.get('direction', 'long')

    if direction == 'long':
        pnl_gross = exit_price - entry
    else:
        pnl_gross = entry - exit_price

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
        'direction': direction,
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
    """Open a new paper position (direction-aware)."""
    direction = 'short' if signal.get('action') == 'sell' else 'long'
    state['position'] = {
        'entry_time': bar['datetime'],
        'entry_price': bar['close'],
        'stop_loss': signal['stop_loss'],
        'take_profit': signal['take_profit'],
        'direction': direction,
    }
    return state['position']


# ── Logging & alerts ─────────────────────────────────────────────

def append_log(strategy_id, message):
    """Append a timestamped entry to the per-strategy log."""
    lf = log_file_for(strategy_id)
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    entry = f"- **{timestamp}** — {message}\n"

    if not lf.exists():
        lf.write_text(
            f"# Paper Trading Log — {strategy_id}\n\n"
            f"Started: {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
            "---\n\n"
        )

    with open(lf, 'a') as f:
        f.write(entry)


def send_alert(subject, body):
    """Send email alert."""
    try:
        from email_sender import send_email, markdown_to_html
        send_email(
            subject=subject,
            body=markdown_to_html(body),
            html=True,
        )
    except Exception as e:
        print(f"  Alert email failed: {e}")


# ── Graduation evaluation ────────────────────────────────────────

def evaluate_graduation(strategy_id, state, config):
    """Check if strategy meets graduation criteria.

    Returns: ('graduated', reason) | ('killed', reason) | (None, None)
    """
    criteria = config.get('graduation', {})
    min_days = criteria.get('min_days', 30)
    min_trades = criteria.get('min_trades', POLICY_MIN_TRADES)
    min_net_pf = criteria.get('min_net_pf', 1.0)
    max_dd_pct = criteria.get('max_drawdown_pct', 25)
    kill_pf = criteria.get('kill_pf_below', POLICY_KILL_PF)
    kill_min_trades = criteria.get('kill_min_trades', POLICY_KILL_MIN_TRADES)

    started = datetime.fromisoformat(state.get('started', datetime.utcnow().isoformat()[:10]))
    days_active = (datetime.utcnow() - started).days
    trades = state.get('trades', [])
    n_trades = len(trades)

    # Not enough data yet — BUT kill if way past max_days with insufficient trades
    max_days = criteria.get('max_days', POLICY_MAX_DAYS)
    if n_trades < min_trades:
        if days_active >= max_days:
            reason = (f"Killed after {days_active} days with only {n_trades} trades "
                      f"(needed {min_trades}). Insufficient trade production.")
            return 'killed', reason
        return None, None

    # Calculate profit factor
    gross_wins = sum(t['pnl_gross'] for t in trades if t['pnl_gross'] > 0)
    gross_losses = abs(sum(t['pnl_gross'] for t in trades if t['pnl_gross'] < 0))
    net_pf = (gross_wins / gross_losses) if gross_losses > 0 else float('inf')

    # Calculate max drawdown %
    equity_curve = [0.0]
    for t in trades:
        equity_curve.append(equity_curve[-1] + t['pnl_net'])
    peak = equity_curve[0]
    max_dd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = peak - val
        if dd > max_dd:
            max_dd = dd

    # Use entry price of first trade as reference for DD%
    ref_price = trades[0]['entry_price'] if trades else 1
    max_dd_pct_actual = (max_dd / ref_price) * 100

    # Early kill: clearly failing
    if n_trades >= kill_min_trades and net_pf < kill_pf:
        reason = (f"Killed after {n_trades} trades, {days_active} days. "
                  f"Net PF {net_pf:.2f} < {kill_pf} threshold.")
        return 'killed', reason

    # Graduation check
    if net_pf >= min_net_pf and max_dd_pct_actual <= max_dd_pct:
        reason = (f"Graduated after {n_trades} trades, {days_active} days. "
                  f"Net PF {net_pf:.2f}, max DD {max_dd_pct_actual:.1f}%, "
                  f"total P&L ${state['total_pnl']:+,.2f}")
        return 'graduated', reason

    # Failed graduation criteria but not killed yet
    max_days = criteria.get('max_days', POLICY_MAX_DAYS)
    if days_active >= max_days and n_trades >= min_trades:
        # Extended period, still not graduating — kill it
        reason = (f"Killed after {n_trades} trades, {days_active} days. "
                  f"Net PF {net_pf:.2f}, max DD {max_dd_pct_actual:.1f}%. "
                  f"Extended period without meeting graduation criteria.")
        return 'killed', reason

    return None, None


# ── Staleness detection ───────────────────────────────────────────

def check_staleness(strategy_id, state, config):
    """Check if a strategy is stale (no trades for too long).

    Returns: ('stale', reason) | ('zero_trade_kill', reason) | (None, None)
    """
    started = state.get('started')
    if not started:
        return None, None

    started_dt = datetime.fromisoformat(started) if isinstance(started, str) else started
    days_active = (datetime.utcnow() - started_dt).days
    n_trades = len(state.get('trades', []))
    has_position = state.get('position') is not None
    stale_alert_sent = state.get('stale_alert_sent', False)

    # If in a position but well past max_days with 0 completed trades,
    # the strategy is in limbo — waiting indefinitely for one trade to close.
    # Force-kill it. (H004 was stuck 49+ days this way.)
    if has_position and days_active >= POLICY_ZERO_TRADE_LIMBO_DAYS and n_trades == 0:
        reason = (f"{strategy_id}: {days_active} days active, 0 completed trades, "
                  f"stuck in open position since day 1. "
                  f"Auto-killed for exceeding max hold time.")
        return 'zero_trade_kill', reason

    # Skip if in a position — strategy is active (for reasonable durations)
    if has_position:
        return None, None

    # Zero-trade kill: no trades for extended period
    if days_active >= POLICY_ZERO_TRADE_KILL_DAYS and n_trades == 0:
        reason = (f"{strategy_id}: {days_active} days active, 0 trades, no position. "
                  f"Auto-killed for zero trade production.")
        return 'zero_trade_kill', reason

    # Stale warning: no trades for warning period
    if days_active >= POLICY_STALE_WARNING_DAYS and n_trades == 0 and not stale_alert_sent:
        state['stale_alert_sent'] = True
        reason = (f"{strategy_id}: {days_active} days active, 0 trades, no position. "
                  f"Strategy may be mismatched with current market regime.")
        return 'stale', reason

    # Check last_signal_time for strategies that had trades but went silent
    last_signal = state.get('last_signal_time')
    if last_signal and n_trades > 0:
        last_dt = datetime.fromisoformat(last_signal) if isinstance(last_signal, str) else last_signal
        silent_days = (datetime.utcnow() - last_dt).days
        if silent_days >= POLICY_STALE_SILENT_DAYS and not stale_alert_sent:
            state['stale_alert_sent'] = True
            reason = (f"{strategy_id}: Last signal was {silent_days} days ago. "
                      f"Strategy may have stopped generating signals.")
            return 'stale', reason

    return None, None


# ── Main logic ────────────────────────────────────────────────────

def run_strategy(strategy_id, config, bars_1h):
    """Run paper trading for a single strategy."""
    print(f"\n  --- {strategy_id} ({config['archetype']}) ---")

    # Resolve archetype class
    archetype_name = config['archetype']
    archetype_cls = ARCHETYPES.get(archetype_name)
    if not archetype_cls:
        print(f"  ERROR: Unknown archetype '{archetype_name}'")
        return []

    # Load state
    state = load_state(strategy_id, config)
    last_time = state.get('last_bar_time')

    if state['position']:
        pos = state['position']
        direction_label = pos.get('direction', 'long').upper()
        print(f"  Position: {direction_label} @ ${pos['entry_price']:,.2f} "
              f"(SL: ${pos['stop_loss']:,.2f}, TP: ${pos['take_profit']:,.2f})")
    else:
        print(f"  Position: FLAT | Trades: {len(state['trades'])} | P&L: ${state['total_pnl']:+,.2f}")

    # Resample to strategy timeframe
    tf = config.get('timeframe_hours', 4)
    bars = resample(bars_1h, hours=tf) if tf > 1 else bars_1h
    print(f"  {len(bars)} bars at {tf}H timeframe")

    # Find new bars
    if last_time:
        new_bars_start = None
        for i, bar in enumerate(bars):
            if bar['datetime'] > last_time:
                new_bars_start = i
                break
        if new_bars_start is None:
            print(f"  No new bars since last run.")
            state['last_bar_time'] = bars[-1]['datetime']
            save_state(strategy_id, state)
            return []
    else:
        # First run: warm-up with WARMUP_BARS instead of just 1 bar
        new_bars_start = max(0, len(bars) - WARMUP_BARS)
        state['warmup_done'] = True
        print(f"  First run: warm-up processing {len(bars) - new_bars_start} bars")

    # Create strategy instance
    strategy = archetype_cls(**config['params'])

    events = []
    n_new = len(bars) - new_bars_start
    print(f"  Processing {n_new} new bar(s)...")

    for i in range(new_bars_start, len(bars)):
        bar = bars[i]
        prev_bars = bars[max(0, i - 300):i]

        # Check exit first
        if state['position']:
            exit_price, exit_reason = check_exit(bar, state['position'])
            if exit_price is not None:
                trade = record_trade(state, bar, exit_price, exit_reason)
                icon = "TP HIT" if exit_reason == 'take_profit' else "SL HIT"
                msg = (f"[{strategy_id}] {icon}: Exited @ ${exit_price:,.2f} "
                       f"(entry ${trade['entry_price']:,.2f}, "
                       f"P&L ${trade['pnl_net']:+,.2f} / {trade['pnl_pct']:+.2f}%)")
                print(f"    [{bar['datetime']}] {msg}")
                events.append(('exit', strategy_id, trade, msg))

        # Check for entry signal (only when flat)
        if not state['position']:
            signal = strategy(bar, prev_bars, None)
            if signal and signal.get('action') in ('buy', 'sell'):
                pos = open_position(state, bar, signal)
                direction_label = pos.get('direction', 'long').upper()
                state['last_signal_time'] = bar['datetime'].isoformat() if isinstance(bar['datetime'], datetime) else bar['datetime']
                state['stale_alert_sent'] = False
                msg = (f"[{strategy_id}] ENTRY: {direction_label} @ ${bar['close']:,.2f} "
                       f"(SL: ${signal['stop_loss']:,.2f}, "
                       f"TP: ${signal['take_profit']:,.2f})")
                print(f"    [{bar['datetime']}] {msg}")
                events.append(('entry', strategy_id, pos, msg))

    # Update last processed time
    state['last_bar_time'] = bars[-1]['datetime']

    # Current price context
    current_price = bars[-1]['close']
    if state['position']:
        pos = state['position']
        direction = pos.get('direction', 'long')
        if direction == 'long':
            unrealized = current_price - pos['entry_price']
        else:
            unrealized = pos['entry_price'] - current_price
        unrealized_pct = (unrealized / pos['entry_price']) * 100
        print(f"  Unrealized: ${unrealized:+,.2f} ({unrealized_pct:+.2f}%)")

    # Save state
    save_state(strategy_id, state)

    # Check graduation
    grad_result, grad_reason = evaluate_graduation(strategy_id, state, config)
    if grad_result:
        events.append(('graduation', strategy_id, grad_result, grad_reason))

    # Check staleness
    stale_result, stale_reason = check_staleness(strategy_id, state, config)
    if stale_result:
        events.append(('staleness', strategy_id, stale_result, stale_reason))
        # Save state again since check_staleness may have set stale_alert_sent
        save_state(strategy_id, state)

    return events


def run():
    """Main entry point — process all active strategies."""
    print("=" * 60)
    print("PAPER TRADING MONITOR")
    print(f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    registry = load_registry()
    active = registry.get('active', [])

    if not active:
        print("\nNo active strategies in registry.")
        return

    print(f"\nActive strategies: {len(active)}")
    for s in active:
        print(f"  - {s['id']} ({s['archetype']}, {s['timeframe_hours']}H)")

    # Fetch data once (shared across all strategies)
    print(f"\nFetching recent 1H data...")
    bars_1h = fetch_recent_1h(days=60)
    if not bars_1h:
        print("ERROR: No data fetched! Exiting with error.")
        sys.exit(1)

    print(f"  Got {len(bars_1h)} 1H bars")
    print(f"  Range: {bars_1h[0]['datetime']} → {bars_1h[-1]['datetime']}")

    current_price = bars_1h[-1]['close']
    print(f"  Current BTC: ${current_price:,.2f}")

    # Process each strategy
    all_events = []
    graduation_actions = []

    for config in active:
        sid = config['id']
        events = run_strategy(sid, config, bars_1h)
        all_events.extend(events)

        # Collect graduation/kill actions to apply after all strategies run
        for evt in events:
            if evt[0] == 'graduation':
                graduation_actions.append(evt)
            elif evt[0] == 'staleness' and evt[2] == 'zero_trade_kill':
                graduation_actions.append(('graduation', evt[1], 'killed', evt[3]))

    # Apply graduation/kill actions to registry
    for evt in graduation_actions:
        _, sid, result, reason = evt
        config = next((s for s in registry['active'] if s['id'] == sid), None)
        if config:
            registry['active'] = [s for s in registry['active'] if s['id'] != sid]
            entry = {**config, 'ended': datetime.utcnow().strftime('%Y-%m-%d'), 'reason': reason}
            if result == 'graduated':
                registry['graduated'].append(entry)
            else:
                registry['killed'].append(entry)

    save_registry(registry)

    # Send alerts
    for evt in all_events:
        event_type = evt[0]
        sid = evt[1]

        if event_type == 'entry':
            _, _, pos, msg = evt
            append_log(sid, msg)
            dir_label = pos.get('direction', 'long').upper()
            body = (f"### New Paper Trade — {sid}\n\n"
                    f"**{dir_label} BTCUSD** @ ${pos['entry_price']:,.2f}\n\n"
                    f"- Stop Loss: ${pos['stop_loss']:,.2f}\n"
                    f"- Take Profit: ${pos['take_profit']:,.2f}\n"
                    f"- Time: {pos['entry_time']}\n")
            send_alert(f"[{sid} Paper] ENTRY — {dir_label} BTCUSD", body)

        elif event_type == 'exit':
            _, _, trade, msg = evt
            append_log(sid, msg)
            state = load_state(sid, {})
            result_str = "WIN" if trade['pnl_net'] > 0 else "LOSS"
            body = (f"### Trade Closed — {sid} — {result_str}\n\n"
                    f"**Exit** @ ${trade['exit_price']:,.2f} "
                    f"({trade['exit_reason']})\n\n"
                    f"- Entry: ${trade['entry_price']:,.2f}\n"
                    f"- P&L: ${trade['pnl_net']:+,.2f} ({trade['pnl_pct']:+.2f}%)\n"
                    f"- Costs: ${trade['cost']:,.2f}\n")
            send_alert(f"[{sid} Paper] {result_str} — ${trade['pnl_net']:+,.0f}", body)

        elif event_type == 'staleness':
            _, _, stale_type, reason = evt
            if stale_type == 'stale':
                append_log(sid, f"STALE WARNING: {reason}")
                body = (f"### Staleness Warning — {sid}\n\n"
                        f"{reason}\n\n"
                        f"Strategy has been active with no trades. "
                        f"Review market regime compatibility.\n")
                send_alert(f"[{sid} Paper] STALE — no trades detected", body)
            elif stale_type == 'zero_trade_kill':
                append_log(sid, f"ZERO-TRADE KILL: {reason}")
                body = (f"### Strategy Auto-Killed — {sid}\n\n"
                        f"{reason}\n\n"
                        f"Strategy produced zero trades and has been removed.\n")
                send_alert(f"[{sid} Paper] KILLED — zero trades after 30 days", body)

        elif event_type == 'graduation':
            _, _, result, reason = evt
            append_log(sid, f"GRADUATION: {result.upper()} — {reason}")
            if result == 'graduated':
                body = (f"### STRATEGY READY FOR LIVE DEPLOYMENT\n\n"
                        f"**{sid}** has passed paper trading evaluation.\n\n"
                        f"{reason}\n\n"
                        f"**Action required:** Review results and decide on live deployment.\n")
                send_alert(f"READY FOR LIVE — {sid} graduated paper trading", body)
            else:
                body = (f"### Strategy Killed in Paper Trading\n\n"
                        f"**{sid}** has been removed from paper trading.\n\n"
                        f"{reason}\n")
                send_alert(f"[{sid} Paper] KILLED — removed from paper trading", body)

    # Summary
    print(f"\n{'='*60}")
    print(f"Active: {len(registry['active'])}  |  "
          f"Graduated: {len(registry['graduated'])}  |  "
          f"Killed: {len(registry['killed'])}")
    if all_events:
        print(f"Events this run: {len(all_events)}")
    for config in registry['active']:
        sid = config['id']
        sf = state_file_for(sid)
        if sf.exists():
            s = json.loads(sf.read_text())
            pos_str = "IN POSITION" if s.get('position') else "FLAT"
            print(f"  {sid}: {pos_str} | {len(s.get('trades', []))} trades | "
                  f"P&L ${s.get('total_pnl', 0):+,.2f}")
    print(f"{'='*60}")


def print_status():
    """Print current status of all strategies."""
    registry = load_registry()

    print("PAPER TRADING STATUS")
    print("=" * 50)

    for label, strategies in [('Active', registry.get('active', [])),
                               ('Graduated', registry.get('graduated', [])),
                               ('Killed', registry.get('killed', []))]:
        if not strategies:
            continue
        print(f"\n{label}:")
        for config in strategies:
            sid = config['id']
            sf = state_file_for(sid)
            if sf.exists():
                s = json.loads(sf.read_text())
                n_trades = len(s.get('trades', []))
                pnl = s.get('total_pnl', 0)
                pos = s.get('position')
                started = s.get('started', '?')
                days = (datetime.utcnow() - datetime.fromisoformat(started)).days if started != '?' else 0

                print(f"  {sid} ({config['archetype']}, {config.get('timeframe_hours', '?')}H)")
                print(f"    Started: {started} ({days} days ago)")
                print(f"    Trades: {n_trades}  |  P&L: ${pnl:+,.2f}")

                if pos:
                    dir_label = pos.get('direction', 'long').upper()
                    print(f"    Position: {dir_label} @ ${pos['entry_price']:,.2f}")
                    print(f"      SL: ${pos['stop_loss']:,.2f}  |  TP: ${pos['take_profit']:,.2f}")
                else:
                    print(f"    Position: FLAT")

                if s.get('trades'):
                    print(f"    Recent trades:")
                    for t in s['trades'][-3:]:
                        r = "WIN" if t['pnl_net'] > 0 else "LOSS"
                        entry_t = t['entry_time'][:10] if isinstance(t['entry_time'], str) else str(t['entry_time'])[:10]
                        exit_t = t['exit_time'][:10] if isinstance(t['exit_time'], str) else str(t['exit_time'])[:10]
                        print(f"      {entry_t} → {exit_t}: ${t['pnl_net']:+,.2f} ({t['exit_reason']}) [{r}]")

                # Graduation progress
                grad = config.get('graduation', {})
                min_days = grad.get('min_days', 30)
                min_trades = grad.get('min_trades', 5)
                print(f"    Graduation: {days}/{min_days} days, {n_trades}/{min_trades} trades needed")
            else:
                ended = config.get('ended', '?')
                reason = config.get('reason', 'N/A')
                print(f"  {sid}: ended {ended} — {reason}")


def reset_strategy(strategy_id):
    """Reset one strategy's state."""
    sf = state_file_for(strategy_id)
    lf = log_file_for(strategy_id)
    if sf.exists():
        sf.unlink()
    if lf.exists():
        lf.unlink()
    print(f"Reset state for {strategy_id}.")


def reset_all():
    """Reset all paper trading state."""
    registry = load_registry()
    for config in registry.get('active', []):
        reset_strategy(config['id'])
    # Also clean up old single-strategy files
    old_state = DATA_DIR / 'paper_trade_state.json'
    old_log = DATA_DIR / 'paper_trade_log.md'
    if old_state.exists():
        old_state.unlink()
    if old_log.exists():
        old_log.unlink()
    print("All paper trading state reset.")


if __name__ == '__main__':
    if '--status' in sys.argv:
        print_status()
    elif '--reset-all' in sys.argv:
        reset_all()
    elif '--reset' in sys.argv:
        idx = sys.argv.index('--reset')
        if idx + 1 < len(sys.argv):
            reset_strategy(sys.argv[idx + 1])
        else:
            print("Usage: --reset <strategy_id>")
    else:
        run()
