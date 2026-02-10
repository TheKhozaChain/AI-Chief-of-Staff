"""
RBI Pipeline Orchestrator — automated research-to-screening flow.

Reads the research backlog, maps unscreened ideas to strategy archetypes,
runs automated screens (with param sweeps), updates the backlog with results,
and generates a summary report.

Usage:
    python pipeline.py                           # Screen all 'new' ideas
    python pipeline.py --ids R009,R011           # Screen specific ideas
    python pipeline.py --data ../../data/BTCUSD_1h.csv  # Custom data path
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backlog_parser import (
    parse_backlog, get_unscreened, update_backlog_entry,
    add_killed_entry, get_next_kill_number,
)
from screen_runner import run_screen, run_param_sweep
from archetypes import ARCHETYPES


# Default data file path (relative to this file)
DEFAULT_DATA = str(Path(__file__).parent.parent.parent / 'data' / 'BTCUSD_1h.csv')

# Mapping of research ideas to archetype configs.
# Each entry defines which archetype to use and what parameter grid to sweep.
# Ideas not in this mapping will be parked with a note.
IDEA_ARCHETYPE_MAP = {
    'R003': {
        'archetype': 'bollinger_breakout',
        'timeframe_hours': 4,
        'param_grid': {
            'bb_period': [20],
            'bb_std': [1.5, 2.0],
            'squeeze_lookback': [50],
            'squeeze_percentile': [20],
            'min_squeeze_bars': [3],
            'stop_pct': [1.5, 2.5],
            'target_pct': [4.0, 6.0],
        },
        'note': 'Volume profile approximated via BB squeeze (no volume profile data).',
    },
    'R007': {
        'archetype': 'vol_adjusted_trend',
        'timeframe_hours': 4,
        'param_grid': {
            'ma_period': [20, 30],
            'atr_period': [14, 20],
            'stop_atr_mult': [1.5, 2.0, 3.0],
            'target_atr_mult': [4.0, 6.0, 8.0],
            'trend_filter_period': [60, 80],
            'long_only': [True],
        },
    },
    'R009': {
        'archetype': 'donchian_breakout',
        'timeframe_hours': 4,
        'param_grid': {
            'channel_period': [10, 20, 30, 50],
            'stop_pct': [2.0, 3.0, 4.0],
            'target_pct': [6.0, 9.0, 12.0],
            'long_only': [True],
        },
    },
    'R011': {
        'archetype': 'daily_trend',
        'timeframe_hours': 24,
        'param_grid': {
            'fast_period': [5, 10, 20],
            'slow_period': [20, 40, 60],
            'stop_pct': [5.0, 6.0, 8.0],
            'target_pct': [15.0, 18.0, 24.0],
            'long_only': [True],
        },
    },
    'R010': {
        'archetype': 'multi_asset_momentum',
        'timeframe_hours': 4,
        'param_grid': {
            'roc_period': [10, 20, 30],
            'min_roc': [1.0, 2.0, 3.0],
            'stop_pct': [2.0, 3.0, 4.0],
            'target_pct': [6.0, 8.0, 12.0],
            'aux_data_dir': [str(Path(__file__).parent.parent.parent / 'data')],
            'aux_timeframe_hours': [4],
            'long_only': [True],
        },
    },
}


def run_pipeline(
    data_file: str = DEFAULT_DATA,
    idea_ids: Optional[List[str]] = None,
    update_backlog: bool = True,
) -> Dict:
    """Run the full RBI screening pipeline.

    Args:
        data_file: Path to OHLCV CSV data file
        idea_ids: Specific idea IDs to screen (None = all 'new' ideas)
        update_backlog: Whether to update RESEARCH_BACKLOG.md with results

    Returns:
        Dict with keys:
            screened: list of screen results
            promoted: list of promoted idea IDs
            killed: list of killed idea IDs
            parked: list of parked idea IDs
            summary: formatted report string
    """
    print(f"RBI Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'=' * 60}")

    # Get ideas to screen
    if idea_ids:
        all_entries = parse_backlog()
        entries = [e for e in all_entries if e['id'] in idea_ids]
    else:
        entries = get_unscreened()

    if not entries:
        print("No ideas to screen.")
        return {
            'screened': [], 'promoted': [], 'killed': [],
            'parked': [], 'summary': 'No ideas to screen.',
        }

    print(f"Screening {len(entries)} ideas:")
    for e in entries:
        print(f"  {e['id']} — {e['idea']}")
    print()

    results = []
    promoted = []
    killed = []
    parked = []

    for entry in entries:
        idea_id = entry['id']
        idea_name = entry['idea']
        print(f"\n--- Screening {idea_id}: {idea_name} ---")

        config = IDEA_ARCHETYPE_MAP.get(idea_id)

        if not config:
            print(f"  No archetype mapping for {idea_id}. Parking.")
            parked.append(idea_id)
            if update_backlog:
                update_backlog_entry(
                    idea_id, 'parked',
                    'No archetype mapping. Needs manual strategy implementation.',
                )
            results.append({
                'idea_id': idea_id,
                'idea_name': idea_name,
                'verdict': 'park',
                'reason': 'No archetype mapping available.',
            })
            continue

        # Run param sweep
        archetype = config['archetype']
        timeframe = config.get('timeframe_hours', 4)
        param_grid = config['param_grid']

        print(f"  Archetype: {archetype}")
        print(f"  Timeframe: {timeframe}H")
        combos = 1
        for v in param_grid.values():
            combos *= len(v)
        print(f"  Param combinations: {combos}")

        sweep_results = run_param_sweep(
            archetype=archetype,
            param_grid=param_grid,
            data_file=data_file,
            timeframe_hours=timeframe,
            idea_id=idea_id,
            idea_name=idea_name,
        )

        if not sweep_results:
            parked.append(idea_id)
            results.append({
                'idea_id': idea_id,
                'idea_name': idea_name,
                'verdict': 'park',
                'reason': 'Sweep returned no results.',
            })
            continue

        best = sweep_results[0]
        results.append(best)

        # Report
        gross_pf = best.get('gross_pf', 0)
        trades = best.get('total_trades', 0)
        wr = best.get('win_rate', 0)
        print(f"  Best: PF {gross_pf} | {trades} trades | {wr:.1%} WR")
        print(f"  Params: {best.get('params', {})}")
        print(f"  Verdict: {best['verdict'].upper()}")

        # Update backlog
        if best['verdict'] == 'promote':
            promoted.append(idea_id)
            notes = (f"**PROMOTED**: PF {gross_pf} gross, {trades} trades, "
                     f"{wr:.1%} WR. Best params: {best.get('params', {})}.")
            if config.get('note'):
                notes += f" {config['note']}"
            if update_backlog:
                update_backlog_entry(idea_id, 'promoted', notes)

        elif best['verdict'] == 'kill':
            killed.append(idea_id)
            notes = (f"PF {gross_pf} gross, {trades} trades, "
                     f"{wr:.1%} WR. Best of {combos} param combos.")
            if config.get('note'):
                notes += f" {config['note']}"
            if update_backlog:
                update_backlog_entry(idea_id, 'killed', notes)
                # Add to killed archive
                k_num = get_next_kill_number()
                screen_str = f"Gross PF {gross_pf}, {wr:.1%} WR"
                lesson = best.get('reason', 'Below threshold.')
                add_killed_entry(k_num, f"{idea_name} (BTC {best.get('timeframe', '4H')})",
                                screen_str, lesson)

        else:
            parked.append(idea_id)
            if update_backlog:
                update_backlog_entry(idea_id, 'parked', best.get('reason', ''))

    # Generate summary report
    summary = _build_summary(results, promoted, killed, parked)

    print(f"\n{'=' * 60}")
    print(summary)

    return {
        'screened': results,
        'promoted': promoted,
        'killed': killed,
        'parked': parked,
        'summary': summary,
    }


def _build_summary(results, promoted, killed, parked) -> str:
    """Build a formatted pipeline summary."""
    lines = [
        f"\nRBI Pipeline Summary — {datetime.now().strftime('%Y-%m-%d')}",
        "=" * 60,
        f"Screened: {len(results)} ideas",
        f"Promoted: {len(promoted)} ({', '.join(promoted) if promoted else 'none'})",
        f"Killed: {len(killed)} ({', '.join(killed) if killed else 'none'})",
        f"Parked: {len(parked)} ({', '.join(parked) if parked else 'none'})",
        "",
    ]

    if promoted:
        lines.append("PROMOTED IDEAS (ready for full hypothesis):")
        for r in results:
            if r.get('verdict') == 'promote':
                lines.append(f"  {r['idea_id']} — {r['idea_name']}")
                lines.append(f"    PF: {r.get('gross_pf', '?')} gross | "
                            f"Trades: {r.get('total_trades', '?')} | "
                            f"Sharpe: {r.get('sharpe', '?')}")
                lines.append(f"    Params: {r.get('params', {})}")
                lines.append("")

    if killed:
        lines.append("KILLED IDEAS:")
        for r in results:
            if r.get('verdict') == 'kill':
                lines.append(f"  {r['idea_id']} — {r['idea_name']}: "
                            f"PF {r.get('gross_pf', '?')}")
        lines.append("")

    return "\n".join(lines)


def save_results(results: Dict, output_dir: Optional[str] = None):
    """Save pipeline results to JSON for record-keeping."""
    out_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent / 'data'
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"rbi_screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path = out_dir / filename

    # Make results JSON-serializable
    serializable = {
        'timestamp': datetime.now().isoformat(),
        'promoted': results['promoted'],
        'killed': results['killed'],
        'parked': results['parked'],
        'summary': results['summary'],
        'screens': [],
    }
    for r in results['screened']:
        screen = {k: v for k, v in r.items() if k != 'summary'}
        serializable['screens'].append(screen)

    with open(out_path, 'w') as f:
        json.dump(serializable, f, indent=2, default=str)

    print(f"Results saved to {out_path}")
    return str(out_path)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='RBI Pipeline Orchestrator')
    parser.add_argument('--data', default=DEFAULT_DATA, help='Path to OHLCV CSV')
    parser.add_argument('--ids', default='', help='Comma-separated idea IDs to screen')
    parser.add_argument('--no-update', action='store_true', help='Skip updating RESEARCH_BACKLOG.md')
    parser.add_argument('--save', action='store_true', help='Save results to JSON')
    args = parser.parse_args()

    idea_ids = [x.strip() for x in args.ids.split(',') if x.strip()] if args.ids else None

    results = run_pipeline(
        data_file=args.data,
        idea_ids=idea_ids,
        update_backlog=not args.no_update,
    )

    if args.save:
        save_results(results)
