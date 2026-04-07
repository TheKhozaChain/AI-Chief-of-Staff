"""
Automated RBI screen runner.

Takes a strategy archetype + params, runs it through the backtest engine,
and returns a structured verdict (kill / promote / park).

Usage:
    from screen_runner import run_screen

    result = run_screen(
        archetype='donchian_breakout',
        params={'channel_period': 20, 'stop_pct': 3.0, 'target_pct': 9.0},
        data_file='../../data/BTCUSD_1h.csv',
        timeframe_hours=4,
        idea_id='R009',
        idea_name='Donchian Channel Breakout',
    )
    print(result['summary'])

    # Or run directly:
    python screen_runner.py --archetype donchian_breakout --data ../../data/BTCUSD_1h.csv
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent dir to path for imports when run as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_csv, resample
from engine import Backtest
from archetypes import ARCHETYPES
from regime import run_regime_coverage_check

# Load thresholds from policies/ (single source of truth)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
try:
    from policy_loader import load_kill_criteria, load_promotion_criteria
    _kill = load_kill_criteria()
    COST_PCT = load_promotion_criteria()['screening']['cost_pct']
    PF_THRESHOLD = _kill['screening']['min_gross_pf']
    MIN_TRADES = _kill['screening']['min_trades']
except (ImportError, FileNotFoundError):
    COST_PCT = 0.1
    PF_THRESHOLD = 1.5
    MIN_TRADES = 20


def run_screen(
    archetype: str,
    params: Dict,
    data_file: str,
    timeframe_hours: int = 4,
    cost_pct: float = COST_PCT,
    idea_id: str = '',
    idea_name: str = '',
) -> Dict:
    """Run a single strategy screen and return structured results.

    Args:
        archetype: Name from ARCHETYPES registry (e.g. 'donchian_breakout')
        params: Dict of parameters to pass to archetype constructor
        data_file: Path to OHLCV CSV file
        timeframe_hours: Resample to this timeframe (hours)
        cost_pct: Transaction cost percentage
        idea_id: Research backlog ID (e.g. 'R009')
        idea_name: Human-readable name

    Returns:
        Dict with keys:
            idea_id, idea_name, archetype, params, timeframe,
            gross_pf, net_pf, win_rate, total_trades, expectancy,
            sharpe, sortino, max_dd, avg_duration_hours,
            buy_hold_pnl, strategy_pnl,
            verdict ('kill' | 'promote' | 'park'),
            reason, summary (formatted string), timestamp
    """
    # Validate archetype
    if archetype not in ARCHETYPES:
        return {
            'idea_id': idea_id,
            'idea_name': idea_name,
            'verdict': 'park',
            'reason': f'Unknown archetype: {archetype}. Available: {list(ARCHETYPES.keys())}',
            'timestamp': datetime.now().isoformat(),
        }

    # Load and resample data
    raw_data = load_csv(data_file)
    data = resample(raw_data, hours=timeframe_hours) if timeframe_hours > 1 else raw_data

    # Create strategy instance
    strategy_class = ARCHETYPES[archetype]
    strategy = strategy_class(**params)

    # Run gross backtest
    bt_gross = Backtest(data, cost_pct=0.0)
    bt_gross.run(strategy)
    gross = bt_gross.result

    # Run net backtest
    strategy_net = strategy_class(**params)
    bt_net = Backtest(data, cost_pct=cost_pct)
    bt_net.run(strategy_net)
    net = bt_net.result

    # Determine verdict
    gross_pf = gross.profit_factor
    regime_coverage = None
    if gross.total_trades < MIN_TRADES:
        verdict = 'park'
        reason = f'Insufficient trades ({gross.total_trades}). Need {MIN_TRADES}+ for meaningful screen.'
    elif gross_pf >= PF_THRESHOLD:
        # Base criteria pass — run regime coverage check before promoting
        regime_coverage = run_regime_coverage_check(
            data,
            strategy_factory=lambda: strategy_class(**params),
            cost_pct=cost_pct,
        )
        if regime_coverage['pass']:
            verdict = 'promote'
            reason = f'Gross PF {gross_pf:.2f} >= {PF_THRESHOLD} threshold. Regime coverage OK. Promote to full hypothesis.'
        else:
            verdict = 'park'
            reason = (f'Gross PF {gross_pf:.2f} passes threshold but regime coverage failed: '
                      f'{regime_coverage["reason"]}')
    elif gross_pf >= 1.0:
        verdict = 'kill'
        reason = f'Gross PF {gross_pf:.2f} — positive expectancy but below {PF_THRESHOLD} threshold.'
    else:
        verdict = 'kill'
        reason = f'Gross PF {gross_pf:.2f} — negative expectancy.'

    # Simplicity scoring (autoresearch criterion: prefer fewer params at same PF)
    param_count = sum(
        1 for k, v in params.items()
        if k not in ('aux_data_dir', 'aux_timeframe_hours')
        and not isinstance(v, bool)
    )

    # Build result
    result = {
        'idea_id': idea_id,
        'idea_name': idea_name,
        'archetype': archetype,
        'params': params,
        'param_count': param_count,
        'timeframe': f'{timeframe_hours}H' if timeframe_hours < 24 else 'D',
        'data_bars': len(data),
        'data_period': f"{data[0]['datetime'].strftime('%Y-%m-%d')} → {data[-1]['datetime'].strftime('%Y-%m-%d')}",
        'gross_pf': round(gross_pf, 2),
        'net_pf': round(net.profit_factor, 2),
        'win_rate': round(gross.win_rate, 3),
        'total_trades': gross.total_trades,
        'expectancy_gross': round(gross.expectancy, 2),
        'expectancy_net': round(net.expectancy, 2),
        'sharpe': round(net.sharpe_ratio, 2),
        'sortino': round(net.sortino_ratio, 2),
        'max_dd': round(net.max_drawdown, 2),
        'max_dd_duration_days': round(net.max_drawdown_duration_days, 0),
        'avg_duration_hours': round(gross.avg_trade_duration_hours, 1),
        'buy_hold_pnl': round(gross.buy_hold_pnl, 2),
        'strategy_pnl_gross': round(gross.total_pnl, 2),
        'strategy_pnl_net': round(net.total_pnl, 2),
        'total_costs': round(net.total_costs, 2),
        'cost_pct': cost_pct,
        'verdict': verdict,
        'reason': reason,
        'regime_coverage': regime_coverage,
        'timestamp': datetime.now().isoformat(),
    }

    # Build formatted summary
    result['summary'] = _format_summary(result)
    return result


def run_param_sweep(
    archetype: str,
    param_grid: Dict[str, list],
    data_file: str,
    timeframe_hours: int = 4,
    cost_pct: float = COST_PCT,
    idea_id: str = '',
    idea_name: str = '',
) -> List[Dict]:
    """Run a parameter sweep and return sorted results.

    Args:
        archetype: Name from ARCHETYPES registry
        param_grid: Dict mapping param name to list of values to try.
                    E.g. {'channel_period': [10, 20, 30], 'stop_pct': [2, 3, 4]}
        data_file: Path to OHLCV CSV
        timeframe_hours: Resample timeframe
        cost_pct: Transaction cost
        idea_id: Research backlog ID
        idea_name: Human-readable name

    Returns:
        List of screen results sorted by gross PF descending.
    """
    import itertools

    keys = list(param_grid.keys())
    values = list(param_grid.values())
    results = []

    for combo in itertools.product(*values):
        params = dict(zip(keys, combo))
        result = run_screen(
            archetype=archetype,
            params=params,
            data_file=data_file,
            timeframe_hours=timeframe_hours,
            cost_pct=cost_pct,
            idea_id=idea_id,
            idea_name=idea_name,
        )
        results.append(result)

    # Sort by gross PF desc, then by simplicity (fewer params = better) as tiebreaker
    results.sort(key=lambda r: (-r.get('gross_pf', 0), r.get('param_count', 99)))
    return results


def _format_summary(r: Dict) -> str:
    """Format a screen result into a readable summary."""
    verdict_icon = {'kill': 'KILLED', 'promote': 'PROMOTED', 'park': 'PARKED'}
    v = verdict_icon.get(r['verdict'], r['verdict'].upper())

    summary = f"""
Screen Result: {r['idea_id']} — {r['idea_name']}
{'=' * 60}
Archetype:  {r['archetype']}
Params:     {r['params']}
Timeframe:  {r['timeframe']}
Data:       {r['data_bars']} bars ({r['data_period']})
Cost:       {r['cost_pct']}% per trade

Gross PF:   {r['gross_pf']}
Net PF:     {r['net_pf']}
Win Rate:   {r['win_rate']:.1%}
Trades:     {r['total_trades']}
Expectancy: ${r['expectancy_gross']} gross / ${r['expectancy_net']} net
Sharpe:     {r['sharpe']}
Sortino:    {r['sortino']}
Max DD:     ${r['max_dd']:,.0f} ({r['max_dd_duration_days']:.0f} days)
Avg Hold:   {r['avg_duration_hours']}h

Strategy P&L:  ${r['strategy_pnl_gross']:,.0f} gross / ${r['strategy_pnl_net']:,.0f} net
Buy & Hold:    ${r['buy_hold_pnl']:,.0f}
Total Costs:   ${r['total_costs']:,.0f}

VERDICT: [{v}] {r['reason']}
"""
    # Add regime breakdown if present
    rc = r.get('regime_coverage')
    if rc and isinstance(rc, dict) and rc.get('regimes'):
        regime_lines = ["\nRegime Coverage:"]
        for regime_name, info in rc['regimes'].items():
            if info.get('skipped'):
                regime_lines.append(f"  {regime_name:>8}: SKIPPED ({info.get('reason', 'too few bars')})")
            else:
                status = "OK" if info.get('passed', True) else "FAIL"
                regime_lines.append(
                    f"  {regime_name:>8}: [{status}] {info['bars']} bars, "
                    f"{info['trades']} trades, PF {info['pf']}"
                )
        summary += "\n".join(regime_lines) + "\n"

    return summary


def screen_multiple(screens: List[Dict], data_file: str) -> List[Dict]:
    """Run multiple screens and return all results.

    Args:
        screens: List of dicts with keys:
            archetype, params, timeframe_hours, idea_id, idea_name
        data_file: Path to OHLCV CSV

    Returns:
        List of screen results.
    """
    results = []
    for s in screens:
        result = run_screen(
            archetype=s['archetype'],
            params=s['params'],
            data_file=data_file,
            timeframe_hours=s.get('timeframe_hours', 4),
            idea_id=s.get('idea_id', ''),
            idea_name=s.get('idea_name', ''),
        )
        results.append(result)
        # Print progress
        print(f"  [{result['verdict'].upper()}] {result['idea_id']} {result['idea_name']}: "
              f"PF {result.get('gross_pf', '?')}")
    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='RBI Automated Screen Runner')
    parser.add_argument('--archetype', required=True, choices=list(ARCHETYPES.keys()))
    parser.add_argument('--data', required=True, help='Path to OHLCV CSV file')
    parser.add_argument('--timeframe', type=int, default=4, help='Timeframe in hours')
    parser.add_argument('--id', default='', help='Research idea ID (e.g. R009)')
    parser.add_argument('--name', default='', help='Research idea name')
    parser.add_argument('--params', default='{}', help='JSON string of strategy params')
    parser.add_argument('--sweep', default='', help='JSON param grid for sweep')
    args = parser.parse_args()

    params = json.loads(args.params)

    if args.sweep:
        grid = json.loads(args.sweep)
        results = run_param_sweep(
            archetype=args.archetype,
            param_grid=grid,
            data_file=args.data,
            timeframe_hours=args.timeframe,
            idea_id=args.id,
            idea_name=args.name,
        )
        print(f"\nParameter Sweep: {len(results)} combinations tested")
        print(f"{'=' * 60}")
        for i, r in enumerate(results[:5]):
            print(f"  #{i+1}: PF {r.get('gross_pf', '?')} | {r.get('params', {})}")
        if results:
            print(f"\nBest result:")
            print(results[0]['summary'])
    else:
        result = run_screen(
            archetype=args.archetype,
            params=params,
            data_file=args.data,
            timeframe_hours=args.timeframe,
            idea_id=args.id,
            idea_name=args.name,
        )
        print(result['summary'])
