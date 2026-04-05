#!/usr/bin/env python3
"""
Build unified experiment journal (TSV) from historical screen JSON files.

Inspired by Karpathy's autoresearch pattern: a single, append-only,
machine-readable log of every experiment ever run. Unlike individual
JSON files, this enables instant cross-experiment analytics.

Usage:
    python scripts/build_experiment_journal.py          # Build from all JSON files
    python scripts/build_experiment_journal.py --append  # Only add new entries
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / 'data'
JOURNAL_FILE = DATA_DIR / 'experiment_journal.tsv'

# Columns for the TSV — flat, grep-friendly, analysis-ready
COLUMNS = [
    'timestamp', 'idea_id', 'idea_name', 'archetype', 'timeframe',
    'param_count', 'params_json',
    'gross_pf', 'net_pf', 'win_rate', 'total_trades',
    'sharpe', 'sortino', 'max_dd', 'max_dd_duration_days',
    'expectancy_gross', 'expectancy_net', 'avg_duration_hours',
    'strategy_pnl_gross', 'strategy_pnl_net', 'buy_hold_pnl', 'total_costs',
    'verdict', 'reason',
    'regime_pass', 'data_bars', 'data_period', 'cost_pct',
]


def extract_row(screen: dict) -> dict:
    """Extract a flat row from a screen result dict."""
    params = screen.get('params', {})
    # Count non-path, non-boolean params (complexity proxy)
    param_count = sum(
        1 for k, v in params.items()
        if k not in ('aux_data_dir', 'aux_timeframe_hours')
        and not isinstance(v, bool)
    )

    regime = screen.get('regime_coverage', {})
    regime_pass = regime.get('pass', '') if isinstance(regime, dict) else ''

    return {
        'timestamp': screen.get('timestamp', ''),
        'idea_id': screen.get('idea_id', ''),
        'idea_name': screen.get('idea_name', ''),
        'archetype': screen.get('archetype', ''),
        'timeframe': screen.get('timeframe', ''),
        'param_count': param_count,
        'params_json': json.dumps(params, separators=(',', ':')),
        'gross_pf': screen.get('gross_pf', ''),
        'net_pf': screen.get('net_pf', ''),
        'win_rate': screen.get('win_rate', ''),
        'total_trades': screen.get('total_trades', ''),
        'sharpe': screen.get('sharpe', ''),
        'sortino': screen.get('sortino', ''),
        'max_dd': screen.get('max_dd', ''),
        'max_dd_duration_days': screen.get('max_dd_duration_days', ''),
        'expectancy_gross': screen.get('expectancy_gross', ''),
        'expectancy_net': screen.get('expectancy_net', ''),
        'avg_duration_hours': screen.get('avg_duration_hours', ''),
        'strategy_pnl_gross': screen.get('strategy_pnl_gross', ''),
        'strategy_pnl_net': screen.get('strategy_pnl_net', ''),
        'buy_hold_pnl': screen.get('buy_hold_pnl', ''),
        'total_costs': screen.get('total_costs', ''),
        'verdict': screen.get('verdict', ''),
        'reason': screen.get('reason', ''),
        'regime_pass': regime_pass,
        'data_bars': screen.get('data_bars', ''),
        'data_period': screen.get('data_period', ''),
        'cost_pct': screen.get('cost_pct', ''),
    }


def build_journal(append_only=False):
    """Build experiment journal from all rbi_screen_*.json files."""
    json_files = sorted(DATA_DIR.glob('rbi_screen_*.json'))
    if not json_files:
        print("No screen JSON files found.")
        return

    # Load existing entries if appending
    existing_keys = set()
    if append_only and JOURNAL_FILE.exists():
        with open(JOURNAL_FILE, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                key = f"{row.get('idea_id', '')}|{row.get('timestamp', '')}"
                existing_keys.add(key)

    rows = []
    for jf in json_files:
        try:
            data = json.loads(jf.read_text())
        except json.JSONDecodeError:
            print(f"  Skipping corrupt file: {jf.name}")
            continue

        screens = data.get('screens', [])
        for screen in screens:
            if not screen.get('idea_id'):
                continue
            row = extract_row(screen)
            key = f"{row['idea_id']}|{row['timestamp']}"
            if append_only and key in existing_keys:
                continue
            rows.append(row)

    if not rows:
        print("No new entries to add.")
        return

    # Sort by timestamp
    rows.sort(key=lambda r: r.get('timestamp', ''))

    # Write TSV
    mode = 'a' if append_only and JOURNAL_FILE.exists() else 'w'
    write_header = mode == 'w' or not JOURNAL_FILE.exists()

    with open(JOURNAL_FILE, mode, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter='\t',
                                extrasaction='ignore')
        if write_header:
            writer.writeheader()
        writer.writerows(rows)

    print(f"Experiment journal: {len(rows)} entries written to {JOURNAL_FILE.name}")
    print(f"  Source files: {len(json_files)}")
    print(f"  Unique ideas: {len(set(r['idea_id'] for r in rows))}")
    print(f"  Date range: {rows[0]['timestamp'][:10]} → {rows[-1]['timestamp'][:10]}")

    return rows


def append_screens(screens: list):
    """Append new screen results to the journal. Called from pipeline.py."""
    if not screens:
        return

    rows = [extract_row(s) for s in screens if s.get('idea_id')]
    if not rows:
        return

    write_header = not JOURNAL_FILE.exists()
    with open(JOURNAL_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter='\t',
                                extrasaction='ignore')
        if write_header:
            writer.writeheader()
        writer.writerows(rows)

    print(f"  Journal: appended {len(rows)} entries to {JOURNAL_FILE.name}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Build experiment journal TSV')
    parser.add_argument('--append', action='store_true',
                       help='Only add new entries (skip existing)')
    args = parser.parse_args()

    build_journal(append_only=args.append)
