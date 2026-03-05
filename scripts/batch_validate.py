#!/usr/bin/env python3
"""
Batch walk-forward validation for all promoted strategies.

Reads promoted_queue.json, deduplicates entries, runs walk-forward validation
on all pending strategies, and auto-kills those that fail.

This converts the validation bottleneck from "4 hours per strategy manually"
to "review a summary table."

Usage:
    python3 batch_validate.py                    # Validate all pending
    python3 batch_validate.py --quick-screen     # Quick OOS screen first, then full validate survivors
    python3 batch_validate.py --dry-run          # Show what would be validated without running
"""

import json
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'strategies' / 'backtest'))
sys.path.insert(0, str(REPO_ROOT / 'scripts'))

from engine import Backtest, run_in_out_of_sample
from archetypes import ARCHETYPES
from data_loader import load_csv, resample

DATA_FILE = str(REPO_ROOT / 'data' / 'BTCUSD_1h.csv')
PROMOTED_QUEUE_FILE = REPO_ROOT / 'data' / 'promoted_queue.json'
BACKLOG_FILE = REPO_ROOT / 'strategies' / 'RESEARCH_BACKLOG.md'

# Quick-screen thresholds (fast kill before full validation)
QUICK_OOS_PF_MIN = 1.0       # OOS PF below this = instant kill
QUICK_OOS_DECAY_MAX = 50.0   # OOS PF decay > 50% = instant kill

# Full validation thresholds
FULL_OOS_PF_MIN = 1.2
FULL_OOS_DECAY_MAX = 30.0
COST_PCT = 0.1


def load_promoted_queue():
    if not PROMOTED_QUEUE_FILE.exists():
        return {'pending_validation': [], 'validated': [], 'failed': []}
    return json.loads(PROMOTED_QUEUE_FILE.read_text())


def save_promoted_queue(queue):
    PROMOTED_QUEUE_FILE.write_text(json.dumps(queue, indent=2) + '\n')


def dedup_pending(pending):
    """Remove duplicate archetype+params entries, keeping earliest promoted."""
    seen = {}
    unique = []
    duplicates = []

    for entry in pending:
        archetype = entry.get('archetype', '')
        params = entry.get('params', {})
        # Create a hashable key from archetype + sorted params
        skip_keys = {'aux_data_dir'}
        param_key = tuple(sorted(
            (k, v) for k, v in params.items() if k not in skip_keys
        ))
        key = (archetype, param_key)

        if key in seen:
            duplicates.append((entry, seen[key]))
        else:
            seen[key] = entry.get('research_id', entry.get('hypothesis_id', '?'))
            unique.append(entry)

    return unique, duplicates


def quick_oos_screen(data, entry):
    """Run a quick 70/30 in-sample/out-of-sample split.

    Returns (oos_pf, pf_decay_pct, pass_bool).
    """
    archetype_key = entry.get('archetype')
    if archetype_key not in ARCHETYPES:
        return 0, -100, False

    params = dict(entry.get('params', {}))
    strategy_class = ARCHETYPES[archetype_key]
    factory = lambda: strategy_class(**params)

    ios = run_in_out_of_sample(data, factory, train_pct=0.7, cost_pct=COST_PCT)
    oos_pf = ios['out_of_sample'].profit_factor
    is_pf = ios['in_sample'].profit_factor

    if is_pf > 0:
        decay = (oos_pf - is_pf) / is_pf * 100
    else:
        decay = -100

    passed = oos_pf >= QUICK_OOS_PF_MIN and decay > -QUICK_OOS_DECAY_MAX
    return oos_pf, decay, passed


def run_batch(quick_screen=False, dry_run=False):
    print("=" * 60)
    print(f"BATCH VALIDATION — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    queue = load_promoted_queue()
    pending = list(queue.get('pending_validation', []))

    if not pending:
        print("\nNo strategies pending validation.")
        print("Check promoted_queue.json — pending_validation is empty.")
        return

    print(f"\nPending validation: {len(pending)} strategies")

    # Step 1: Dedup
    unique, duplicates = dedup_pending(pending)
    if duplicates:
        print(f"\nDuplicates found: {len(duplicates)}")
        for dup, orig_id in duplicates:
            print(f"  {dup.get('research_id', '?')} ({dup.get('name', '?')}) "
                  f"— duplicate of {orig_id}")
        if not dry_run:
            # Move duplicates to failed
            for dup, orig_id in duplicates:
                dup['validation_error'] = f'Duplicate of {orig_id} (same archetype+params)'
                dup['validated_date'] = datetime.now().strftime('%Y-%m-%d')
                queue['failed'].append(dup)

    print(f"\nUnique strategies to validate: {len(unique)}")
    for entry in unique:
        print(f"  {entry.get('hypothesis_id', '?')} ({entry.get('research_id', '?')}) "
              f"— {entry.get('name', '?')} — PF {entry.get('screen_pf', '?')}")

    if dry_run:
        print("\n[DRY RUN] No changes made.")
        return

    # Load data
    print("\nLoading data...")
    data_1h = load_csv(DATA_FILE)
    print(f"  {len(data_1h):,} bars")

    # Step 2: Quick OOS screen (if requested)
    survivors = unique
    if quick_screen:
        print(f"\n{'='*60}")
        print("QUICK OOS SCREEN (70/30 split)")
        print(f"Kill threshold: OOS PF < {QUICK_OOS_PF_MIN} or decay > {QUICK_OOS_DECAY_MAX}%")
        print(f"{'='*60}")

        survivors = []
        for entry in unique:
            hyp_id = entry.get('hypothesis_id', '?')
            rid = entry.get('research_id', '?')
            tf = int(entry.get('timeframe_hours', 4))
            data = resample(data_1h, hours=tf) if tf > 1 else data_1h

            try:
                oos_pf, decay, passed = quick_oos_screen(data, entry)
                status = "PASS" if passed else "KILL"
                print(f"  [{status}] {hyp_id} ({rid}): OOS PF {oos_pf:.2f}, decay {decay:+.1f}%")

                if passed:
                    survivors.append(entry)
                else:
                    entry['validation_error'] = (
                        f'Quick screen failed: OOS PF {oos_pf:.2f}, decay {decay:+.1f}%'
                    )
                    entry['validated_date'] = datetime.now().strftime('%Y-%m-%d')
                    entry['validation_overall'] = False
                    queue['failed'].append(entry)
            except Exception as e:
                print(f"  [ERROR] {hyp_id} ({rid}): {e}")
                entry['validation_error'] = str(e)
                queue['failed'].append(entry)

        print(f"\nSurvivors: {len(survivors)}/{len(unique)}")

    # Step 3: Full validation for survivors
    if survivors:
        print(f"\n{'='*60}")
        print(f"FULL WALK-FORWARD VALIDATION — {len(survivors)} strategies")
        print(f"{'='*60}")

        # Use the existing validate_from_queue mechanism
        # Write survivors back as pending, then call validate_from_queue
        queue['pending_validation'] = survivors
        save_promoted_queue(queue)

        from validate_promoted import validate_from_queue
        results = validate_from_queue()

        print(f"\n{'='*60}")
        print("BATCH VALIDATION COMPLETE")
        print(f"{'='*60}")

        if results:
            validated = [r for r in results if r['overall']]
            failed = [r for r in results if not r['overall']]
            print(f"  Validated: {len(validated)}")
            print(f"  Failed: {len(failed)}")
            for r in validated:
                print(f"    [PASS] {r['hypothesis']}: PF {r['baseline_pf']:.2f}, "
                      f"OOS PF {r['oos_pf']:.2f}")
            for r in failed:
                print(f"    [FAIL] {r['hypothesis']}: PF {r['baseline_pf']:.2f}, "
                      f"OOS PF {r['oos_pf']:.2f}")
    else:
        queue['pending_validation'] = []
        save_promoted_queue(queue)
        print("\nNo strategies survived to full validation.")

    # Build summary report
    report = build_batch_report(queue)
    report_path = REPO_ROOT / 'data' / f"batch_validation_{datetime.now().strftime('%Y%m%d')}.md"
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")


def build_batch_report(queue):
    lines = [
        f"# Batch Validation Report — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"## Validated ({len(queue.get('validated', []))})",
        "",
        "| ID | Research | Name | Archetype | Screen PF | Tests Passed |",
        "|----|---------:|------|-----------|-----------|-------------|",
    ]
    for v in queue.get('validated', []):
        lines.append(
            f"| {v.get('hypothesis_id', '?')} | {v.get('research_id', '?')} | "
            f"{v.get('name', '?')} | {v.get('archetype', '?')} | "
            f"{v.get('screen_pf', '?')} | {v.get('validation_passed_tests', '?')}/4 |"
        )

    lines.extend([
        "",
        f"## Failed ({len(queue.get('failed', []))})",
        "",
        "| ID | Research | Name | Reason |",
        "|----|---------|------|--------|",
    ])
    for f in queue.get('failed', []):
        reason = f.get('validation_error', f"Tests: {f.get('validation_passed_tests', '?')}/4")
        lines.append(
            f"| {f.get('hypothesis_id', '?')} | {f.get('research_id', '?')} | "
            f"{f.get('name', '?')} | {reason} |"
        )

    lines.append("")
    return "\n".join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch walk-forward validation')
    parser.add_argument('--quick-screen', action='store_true',
                       help='Run quick OOS screen first, then full validate survivors')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be validated without running')
    args = parser.parse_args()

    run_batch(quick_screen=args.quick_screen, dry_run=args.dry_run)
