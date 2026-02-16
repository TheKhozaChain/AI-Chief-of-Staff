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
    'R012': {
        'archetype': 'adaptive_momentum_burst',
        'timeframe_hours': 4,
        'param_grid': {
            'bb_period': [20],
            'bb_std': [1.5, 2.0],
            'squeeze_lookback': [50],
            'squeeze_pct': [20],
            'min_squeeze_bars': [3],
            'ma_period': [30, 50],
            'ma_slope_bars': [5],
            'stop_pct': [2.0, 3.0],
            'target_pct': [6.0, 8.0, 12.0],
        },
    },
    'R013': {
        'archetype': 'acceleration_breakout',
        'timeframe_hours': 4,
        'param_grid': {
            'channel_period': [10, 20, 30],
            'roc_short': [3, 5],
            'roc_long': [15, 20],
            'stop_pct': [2.0, 3.0, 4.0],
            'target_pct': [6.0, 9.0, 12.0],
        },
    },
    'R014': {
        'archetype': 'mtf_breakout',
        'timeframe_hours': 4,
        'param_grid': {
            'channel_period': [10, 15, 20],
            'trend_ma_period': [90, 120, 150],
            'stop_pct': [2.0, 3.0, 4.0],
            'target_pct': [6.0, 9.0, 12.0],
        },
    },
    'R015': {
        'archetype': 'volume_breakout',
        'timeframe_hours': 4,
        'param_grid': {
            'channel_period': [15, 20, 30],
            'vol_period': [15, 20],
            'vol_mult': [1.2, 1.5, 2.0],
            'stop_pct': [2.0, 3.0],
            'target_pct': [6.0, 9.0, 12.0],
        },
    },
    'R016': {
        'archetype': 'dual_momentum_consensus',
        'timeframe_hours': 4,
        'param_grid': {
            'channel_period': [15, 20, 30],
            'roc_fast': [3, 5],
            'roc_med': [10, 15],
            'roc_slow': [20, 30],
            'stop_pct': [2.0, 3.0],
            'target_pct': [6.0, 9.0, 12.0],
        },
    },
    'R017': {
        'archetype': 'trend_strength_breakout',
        'timeframe_hours': 4,
        'param_grid': {
            'channel_period': [15, 20, 30],
            'adx_period': [14, 20],
            'adx_threshold': [20, 25, 30],
            'stop_pct': [2.0, 3.0],
            'target_pct': [6.0, 9.0, 12.0],
        },
    },
    'R018': {
        'archetype': 'trend_pullback',
        'timeframe_hours': 4,
        'param_grid': {
            'ma_period': [30, 50, 80],
            'ma_slope_bars': [5],
            'pullback_pct': [1.0, 2.0, 3.0],
            'roc_period': [3, 5],
            'min_roc': [0.3, 0.5, 1.0],
            'stop_pct': [2.0, 3.0],
            'target_pct': [6.0, 9.0, 12.0],
        },
    },
    'R019': {
        'archetype': 'atr_regime_adaptive',
        'timeframe_hours': 4,
        'param_grid': {
            'ma_period': [20, 30],
            'atr_period': [14, 20],
            'atr_history': [90, 120],
            'base_stop_pct': [2.0, 3.0],
            'base_target_pct': [8.0, 12.0],
            'trend_filter_period': [60, 80],
        },
    },
    'R020': {
        'archetype': 'consecutive_momentum',
        'timeframe_hours': 4,
        'param_grid': {
            'channel_period': [15, 20, 30],
            'consec_bars': [2, 3, 4],
            'stop_pct': [2.0, 3.0],
            'target_pct': [6.0, 9.0, 12.0],
        },
    },
    'R021': {
        'archetype': 'range_compression_expansion',
        'timeframe_hours': 4,
        'param_grid': {
            'atr_period': [20],
            'atr_lookback': [60],
            'compression_percentile': [10, 20],
            'breakout_atr_mult': [1.0, 1.5],
            'confirmation_bars': [2],
            'stop_pct': [2.0, 3.0],
            'target_pct': [6.0, 9.0],
            'long_only': [True],
        },
    },
    'R022': {
        'archetype': 'momentum_exhaustion_reversal',
        'timeframe_hours': 4,
        'param_grid': {
            'ma_period': [50, 80],
            'rsi_period': [14],
            'rsi_threshold': [25, 30],
            'bounce_min_pct': [0.5, 1.0],
            'stop_pct': [2.0, 3.0],
            'target_pct': [6.0, 9.0],
            'long_only': [True],
        },
    },
    'R023': {
        'archetype': 'gap_and_go',
        'timeframe_hours': 4,
        'param_grid': {
            'ma_period': [50],
            'gap_min_pct': [0.5, 1.0],
            'lookback_period': [20],
            'roc_period': [10],
            'min_roc': [1.0, 2.0],
            'entry_delay_bars': [1],
            'stop_pct': [2.0, 3.0],
            'target_pct': [6.0, 9.0],
            'long_only': [True],
        },
    },
}

REPO_ROOT = Path(__file__).parent.parent.parent
PROMOTED_QUEUE_FILE = REPO_ROOT / 'data' / 'promoted_queue.json'

# Default param grids per strategy (used by auto-mapping)
DEFAULT_PARAM_GRIDS = {
    'ma_crossover': {'fast_period': [10, 20], 'slow_period': [40, 80], 'stop_pct': [3.0, 4.0], 'target_pct': [9.0, 12.0], 'long_only': [True]},
    'donchian_breakout': {'channel_period': [10, 20, 30], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 9.0], 'long_only': [True]},
    'vol_adjusted_trend': {'ma_period': [20, 30], 'atr_period': [14, 20], 'stop_atr_mult': [2.0, 3.0], 'target_atr_mult': [4.0, 6.0], 'trend_filter_period': [60, 80], 'long_only': [True]},
    'daily_trend': {'fast_period': [5, 10], 'slow_period': [20, 40], 'stop_pct': [5.0, 6.0], 'target_pct': [15.0, 24.0], 'long_only': [True]},
    'bollinger_breakout': {'bb_period': [20], 'bb_std': [1.5, 2.0], 'stop_pct': [2.0, 3.0], 'target_pct': [4.0, 6.0]},
    'adaptive_momentum_burst': {'bb_period': [20], 'bb_std': [2.0], 'squeeze_lookback': [50], 'squeeze_pct': [20], 'min_squeeze_bars': [3], 'ma_period': [30, 50], 'ma_slope_bars': [5], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 8.0]},
    'acceleration_breakout': {'channel_period': [10, 20], 'roc_short': [5], 'roc_long': [20], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 9.0]},
    'mtf_breakout': {'channel_period': [10, 20], 'trend_ma_period': [90, 120], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 9.0]},
    'volume_breakout': {'channel_period': [15, 20], 'vol_period': [20], 'vol_mult': [1.5, 2.0], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 12.0]},
    'dual_momentum_consensus': {'channel_period': [15, 20], 'roc_fast': [5], 'roc_med': [15], 'roc_slow': [30], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 12.0]},
    'trend_strength_breakout': {'channel_period': [15, 20], 'adx_period': [14], 'adx_threshold': [25], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 12.0]},
    'trend_pullback': {'ma_period': [30, 50], 'ma_slope_bars': [5], 'pullback_pct': [2.0], 'roc_period': [3], 'min_roc': [0.5], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 12.0]},
    'atr_regime_adaptive': {'ma_period': [20, 30], 'atr_period': [14], 'atr_history': [120], 'base_stop_pct': [2.0, 3.0], 'base_target_pct': [8.0, 12.0], 'trend_filter_period': [60, 80]},
    'consecutive_momentum': {'channel_period': [15, 20], 'consec_bars': [3], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 12.0]},
    'range_compression_expansion': {'atr_period': [14, 20], 'atr_lookback': [60], 'compression_percentile': [10, 15], 'breakout_atr_mult': [1.5], 'confirmation_bars': [2], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 9.0], 'long_only': [True]},
    'momentum_exhaustion_reversal': {'ma_period': [50], 'rsi_period': [14], 'rsi_threshold': [30], 'bounce_min_pct': [0.5], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 9.0], 'long_only': [True]},
    'gap_and_go': {'ma_period': [50], 'gap_min_pct': [1.0], 'lookback_period': [20], 'roc_period': [10], 'min_roc': [2.0], 'entry_delay_bars': [1], 'stop_pct': [2.0, 3.0], 'target_pct': [6.0, 9.0], 'long_only': [True]},
}


def _auto_map_from_backlog(entry: Dict) -> Optional[Dict]:
    """Try to infer strategy config from a backlog entry's notes field.

    When LLM-sourced ideas include 'Archetype: <name>' in their notes,
    this auto-maps them to a screening config with default param grids.
    """
    import re
    notes = entry.get('notes', '')
    match = re.search(r'[Aa]rchetype:\s*(\w+)', notes)
    if not match:
        return None

    archetype = match.group(1).strip()
    if archetype not in ARCHETYPES:
        return None

    param_grid = DEFAULT_PARAM_GRIDS.get(archetype)
    if not param_grid:
        return None

    timeframe = 24 if archetype == 'daily_trend' else 4
    print(f"  Auto-mapped {entry['id']} to {archetype} (from backlog notes)")
    return {
        'archetype': archetype,
        'timeframe_hours': timeframe,
        'param_grid': param_grid,
    }


def _default_promoted_queue() -> Dict:
    return {
        'pending_validation': [],
        'validated': [],
        'failed': [],
    }


def _load_promoted_queue() -> Dict:
    if not PROMOTED_QUEUE_FILE.exists():
        return _default_promoted_queue()
    try:
        queue = json.loads(PROMOTED_QUEUE_FILE.read_text())
        if not isinstance(queue, dict):
            return _default_promoted_queue()
        queue.setdefault('pending_validation', [])
        queue.setdefault('validated', [])
        queue.setdefault('failed', [])
        return queue
    except json.JSONDecodeError:
        return _default_promoted_queue()


def _save_promoted_queue(queue: Dict):
    PROMOTED_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROMOTED_QUEUE_FILE.write_text(json.dumps(queue, indent=2) + '\n')


def _next_hypothesis_id(queue: Optional[Dict] = None) -> str:
    highest = 0
    for p in REPO_ROOT.glob('strategies/HYPOTHESIS_*.md'):
        stem = p.stem  # HYPOTHESIS_004
        try:
            n = int(stem.split('_')[-1])
            highest = max(highest, n)
        except (ValueError, IndexError):
            continue

    if queue:
        for section in ('pending_validation', 'validated', 'failed'):
            for item in queue.get(section, []):
                hyp_id = item.get('hypothesis_id', '')
                if isinstance(hyp_id, str) and hyp_id.startswith('H'):
                    try:
                        highest = max(highest, int(hyp_id[1:]))
                    except ValueError:
                        continue

    return f"H{highest + 1:03d}"


def _queue_has_research_id(queue: Dict, research_id: str) -> bool:
    for section in ('pending_validation', 'validated', 'failed'):
        for item in queue.get(section, []):
            if item.get('research_id') == research_id:
                return True
    return False


def _queue_promoted_strategy(idea_id: str, idea_name: str, best: Dict, config: Dict):
    queue = _load_promoted_queue()
    if _queue_has_research_id(queue, idea_id):
        print(f"  Queue: {idea_id} already tracked, skipping.")
        return

    queue['pending_validation'].append({
        'hypothesis_id': _next_hypothesis_id(queue),
        'research_id': idea_id,
        'name': idea_name,
        'archetype': config['archetype'],
        'timeframe_hours': config.get('timeframe_hours', 4),
        'params': best.get('params', {}),
        'promoted_date': datetime.now().strftime('%Y-%m-%d'),
        'screen_pf': best.get('gross_pf', best.get('profit_factor', 0)),
        'screen_trades': best.get('total_trades', 0),
    })
    _save_promoted_queue(queue)
    print(f"  Queue: added {idea_id} for validation.")


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

        # Auto-map: if no hardcoded config, try to infer from backlog notes
        if not config:
            config = _auto_map_from_backlog(entry)

        if not config:
            print(f"  No strategy mapping for {idea_id}. Parking.")
            parked.append(idea_id)
            if update_backlog:
                update_backlog_entry(
                    idea_id, 'parked',
                    'No strategy mapping found. Add to IDEA_ARCHETYPE_MAP or include "Archetype: <name>" in notes.',
                )
            results.append({
                'idea_id': idea_id,
                'idea_name': idea_name,
                'verdict': 'park',
                'reason': 'No strategy mapping available.',
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
            _queue_promoted_strategy(
                idea_id=idea_id,
                idea_name=idea_name,
                best=best,
                config=config,
            )

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
