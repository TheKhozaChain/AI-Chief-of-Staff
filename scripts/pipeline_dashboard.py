#!/usr/bin/env python3
"""
RBI Pipeline Dashboard — one-glance summary of the full strategy pipeline.

Shows the flow: ideas → screened → promoted → validated → paper trading → live

Usage:
    python3 pipeline_dashboard.py              # Print to stdout
    python3 pipeline_dashboard.py --save       # Save to data/pipeline_dashboard.md
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'strategies' / 'backtest'))

BACKLOG_FILE = REPO_ROOT / 'strategies' / 'RESEARCH_BACKLOG.md'
PROMOTED_QUEUE_FILE = REPO_ROOT / 'data' / 'promoted_queue.json'
PAPER_REGISTRY_FILE = REPO_ROOT / 'data' / 'paper_trade_registry.json'


def parse_backlog_statuses():
    """Parse RESEARCH_BACKLOG.md and count statuses."""
    text = BACKLOG_FILE.read_text()
    statuses = Counter()
    entries = []
    for line in text.split('\n'):
        line = line.strip()
        if not line.startswith('| R'):
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 7:
            continue
        rid = parts[1]
        idea = parts[2]
        status = parts[5]
        statuses[status] += 1
        entries.append({'id': rid, 'idea': idea, 'status': status})
    return statuses, entries


def load_json(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def count_duplicates(entries):
    """Count duplicate archetype+params in promoted entries."""
    promoted_queue = load_json(PROMOTED_QUEUE_FILE)
    seen_params = set()
    unique = 0
    dupes = 0
    for section in ('pending_validation', 'validated', 'failed'):
        for item in promoted_queue.get(section, []):
            archetype = item.get('archetype', '')
            params = item.get('params', {})
            skip_keys = {'aux_data_dir'}
            key = (archetype, tuple(sorted(
                (k, v) for k, v in params.items() if k not in skip_keys
            )))
            if key in seen_params:
                dupes += 1
            else:
                seen_params.add(key)
                unique += 1
    return unique, dupes


def build_dashboard():
    lines = []
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines.append(f"# RBI Pipeline Dashboard — {now}")
    lines.append("")

    # Backlog summary
    statuses, entries = parse_backlog_statuses()
    total = sum(statuses.values())

    lines.append("## Pipeline Flow")
    lines.append("")
    lines.append("```")
    lines.append(f"  Ideas ({total} total)")
    lines.append(f"    |")
    lines.append(f"    +-- new:       {statuses.get('new', 0):3d}  (awaiting screen)")
    lines.append(f"    +-- screening: {statuses.get('screening', 0):3d}  (in progress)")
    lines.append(f"    +-- killed:    {statuses.get('killed', 0):3d}  (failed screen)")
    lines.append(f"    +-- parked:    {statuses.get('parked', 0):3d}  (can't test / regime fail)")
    lines.append(f"    +-- promoted:  {statuses.get('promoted', 0):3d}  (passed screen, awaiting validation)")
    lines.append(f"    +-- validated: {statuses.get('validated', 0):3d}  (passed walk-forward)")
    lines.append(f"    +-- val-failed:{statuses.get('val-failed', 0):3d}  (failed walk-forward)")
    lines.append("```")
    lines.append("")

    # Promoted queue detail
    promoted_queue = load_json(PROMOTED_QUEUE_FILE)
    pending = promoted_queue.get('pending_validation', [])
    validated = promoted_queue.get('validated', [])
    failed = promoted_queue.get('failed', [])

    lines.append("## Validation Queue")
    lines.append("")
    lines.append(f"| Stage | Count |")
    lines.append(f"|-------|-------|")
    lines.append(f"| Pending validation | {len(pending)} |")
    lines.append(f"| Validated (passed) | {len(validated)} |")
    lines.append(f"| Failed validation | {len(failed)} |")
    lines.append("")

    unique, dupes = count_duplicates(entries)
    if dupes > 0:
        lines.append(f"**Duplicate detection:** {dupes} duplicate param sets found in queue.")
        lines.append("")

    # Paper trading
    registry = load_json(PAPER_REGISTRY_FILE)
    active = registry.get('active', [])
    graduated = registry.get('graduated', [])
    killed_pt = registry.get('killed', [])

    lines.append("## Paper Trading")
    lines.append("")
    if active:
        lines.append(f"| Strategy | Archetype | Started | Days |")
        lines.append(f"|----------|-----------|---------|------|")
        for s in active:
            started = s.get('started', '?')
            try:
                days = (datetime.now() - datetime.strptime(started, '%Y-%m-%d')).days
            except (ValueError, TypeError):
                days = '?'
            lines.append(f"| {s['id']} | {s.get('archetype', '?')} | {started} | {days} |")
    else:
        lines.append("No active paper trading strategies.")
    lines.append("")

    if graduated:
        lines.append(f"Graduated to live: {len(graduated)}")
    if killed_pt:
        lines.append(f"Killed during paper trading: {len(killed_pt)}")
    lines.append("")

    # Throughput summary
    lines.append("## Throughput Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total ideas sourced | {total} |")
    lines.append(f"| Screened (killed+promoted+validated+val-failed) | {statuses.get('killed',0) + statuses.get('promoted',0) + statuses.get('validated',0) + statuses.get('val-failed',0)} |")
    lines.append(f"| Promoted (ever) | {statuses.get('promoted',0) + statuses.get('validated',0) + statuses.get('val-failed',0)} |")
    lines.append(f"| Validated (passed) | {statuses.get('validated',0)} |")
    lines.append(f"| Paper trading | {len(active)} active |")
    lines.append(f"| Live | {len(graduated)} |")
    lines.append("")

    # Conversion rates
    screened = statuses.get('killed',0) + statuses.get('promoted',0) + statuses.get('validated',0) + statuses.get('val-failed',0)
    promoted_ever = statuses.get('promoted',0) + statuses.get('validated',0) + statuses.get('val-failed',0)
    validated_count = statuses.get('validated',0)

    if screened > 0:
        lines.append(f"**Screen → Promote rate:** {promoted_ever}/{screened} = {promoted_ever/screened:.0%}")
    if promoted_ever > 0:
        lines.append(f"**Promote → Validate rate:** {validated_count}/{promoted_ever} = {validated_count/promoted_ever:.0%}")
    lines.append("")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='RBI Pipeline Dashboard')
    parser.add_argument('--save', action='store_true', help='Save to data/pipeline_dashboard.md')
    args = parser.parse_args()

    dashboard = build_dashboard()
    print(dashboard)

    if args.save:
        out = REPO_ROOT / 'data' / 'pipeline_dashboard.md'
        out.write_text(dashboard)
        print(f"\nSaved to: {out}")


if __name__ == '__main__':
    main()
