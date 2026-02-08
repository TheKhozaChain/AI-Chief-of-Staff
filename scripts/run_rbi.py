#!/usr/bin/env python3
"""
RBI Pipeline Runner — automated Research-Backtest-Implement cycle.

1. Refreshes BTCUSD data (optional, via --refresh-data)
2. Screens all 'new' ideas from RESEARCH_BACKLOG.md
3. Generates new research ideas via LLM (optional, via --source-ideas)
4. Saves results and updates backlog

Designed to run via GitHub Actions (weekly) or locally.

Usage:
    python run_rbi.py                           # Screen new ideas only
    python run_rbi.py --refresh-data            # Refresh data first
    python run_rbi.py --source-ideas            # Also generate new ideas
    python run_rbi.py --refresh-data --source-ideas  # Full pipeline
    python run_rbi.py --ids R009,R011           # Screen specific ideas
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Set up paths
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'scripts'))
sys.path.insert(0, str(REPO_ROOT / 'strategies' / 'backtest'))

DATA_DIR = REPO_ROOT / 'data'
DATA_FILE = str(DATA_DIR / 'BTCUSD_1h.csv')
BACKLOG_FILE = str(REPO_ROOT / 'strategies' / 'RESEARCH_BACKLOG.md')


def refresh_data():
    """Refresh BTCUSD data from Binance."""
    print("\n=== DATA REFRESH ===")
    from fetch_btc_data import fetch_and_save
    fetch_and_save('1h', 1095)
    fetch_and_save('15m', 1095)
    print("Data refresh complete.\n")


def run_screens(idea_ids=None):
    """Run the RBI screening pipeline."""
    print("\n=== RBI SCREENING ===")
    from pipeline import run_pipeline, save_results

    results = run_pipeline(
        data_file=DATA_FILE,
        idea_ids=idea_ids,
        update_backlog=True,
    )

    # Save results JSON
    if results['screened']:
        save_results(results)

    return results


def source_ideas(pipeline_results=None):
    """Use LLM to generate new research ideas based on killed strategies."""
    print("\n=== IDEA SOURCING (LLM) ===")

    try:
        from llm import generate
    except ImportError:
        print("LLM module not available. Skipping idea sourcing.")
        return []

    # Build context from backlog
    from backlog_parser import parse_backlog, get_next_kill_number
    entries = parse_backlog(BACKLOG_FILE)

    killed = [e for e in entries if e['status'] == 'killed']
    promoted = [e for e in entries if e['status'] == 'promoted']
    parked = [e for e in entries if e['status'] == 'parked']
    existing_ids = [e['id'] for e in entries]
    next_r_num = max(int(e['id'][1:]) for e in entries) + 1 if entries else 1

    # Build LLM prompt
    system = """You are a quantitative trading researcher specializing in cryptocurrency markets.
Your job is to propose NEW trading strategy ideas for BTCUSD backtesting.

Rules:
- Ideas must be testable with OHLCV price data (we have 3 years of 15m and 1h BTCUSD data)
- Each idea needs a clear edge thesis (WHY it should work)
- Focus on trend-following, momentum, and breakout strategies (mean reversion has failed for crypto)
- Design around wide targets (4%+) to absorb transaction costs (0.1% round-trip)
- BTC has a structural uptrend (+200% over 3 years) — long-only or long-biased is preferred
- Do NOT propose ideas that require external data (funding rates, order book, sentiment, etc.)
- Generate exactly 3 new ideas"""

    killed_str = "\n".join(f"- {e['id']} {e['idea']}: {e['notes']}" for e in killed)
    promoted_str = "\n".join(f"- {e['id']} {e['idea']}: {e['notes']}" for e in promoted) if promoted else "None yet"
    parked_str = "\n".join(f"- {e['id']} {e['idea']}: {e['notes']}" for e in parked) if parked else "None"

    recent_context = ""
    if pipeline_results and pipeline_results.get('screened'):
        recent_context = "\n\nMost recent screening results:\n"
        for r in pipeline_results['screened']:
            recent_context += f"- {r.get('idea_id', '?')} {r.get('idea_name', '?')}: PF {r.get('gross_pf', '?')}, verdict: {r.get('verdict', '?')}\n"

    prompt = f"""Based on our research history, propose 3 NEW trading strategy ideas for BTCUSD.

## What's been killed (didn't work):
{killed_str}

## What's been promoted (shows promise):
{promoted_str}

## What's parked (can't test yet):
{parked_str}
{recent_context}

## Key learnings:
- Mean reversion doesn't work in crypto (too much momentum)
- Trend following works best, especially with wider stops and targets
- Volatility-adjusted strategies show promise (PF 1.46 with ATR-based stops)
- Donchian breakout works (PF 1.31)
- Daily timeframe shows strong results but low trade count
- Squeeze breakouts predict magnitude but not direction

## Available strategy archetypes:
- ma_crossover: Fast/slow MA crossover with configurable periods
- donchian_breakout: N-bar high/low breakout
- vol_adjusted_trend: MA trend with ATR-scaled stops/targets
- daily_trend: Longer-hold trend following on daily bars
- bollinger_breakout: BB squeeze breakout

For each idea, output EXACTLY this format (one per idea):
---
R{next_r_num:03d}: [Name]
Source: [where this insight comes from]
Thesis: [one sentence edge thesis]
Archetype: [which archetype to use, or 'custom' if none fit]
Suggested params: [key parameters to test]
---"""

    print(f"Generating ideas starting from R{next_r_num:03d}...")

    try:
        response = generate(prompt=prompt, system=system)
        print(f"LLM response received ({len(response)} chars)")
    except Exception as e:
        print(f"LLM call failed: {e}")
        return []

    # Parse LLM response into structured ideas
    ideas = _parse_llm_ideas(response, next_r_num)

    if ideas:
        _append_ideas_to_backlog(ideas, BACKLOG_FILE)
        print(f"Added {len(ideas)} new ideas to backlog: {', '.join(i['id'] for i in ideas)}")
    else:
        print("No parseable ideas in LLM response.")
        print(f"Raw response:\n{response[:500]}")

    return ideas


def _parse_llm_ideas(response: str, start_num: int) -> list:
    """Parse LLM response into structured idea dicts."""
    ideas = []
    # Split by --- or R0XX patterns
    blocks = re.split(r'---+', response)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Try to extract R-number and name
        name_match = re.search(r'R\d{3}:\s*(.+)', block)
        if not name_match:
            continue

        name = name_match.group(1).strip()
        idea_id = f"R{start_num + len(ideas):03d}"

        # Extract fields
        source = _extract_field(block, 'Source')
        thesis = _extract_field(block, 'Thesis')
        archetype = _extract_field(block, 'Archetype')
        params = _extract_field(block, 'Suggested params')

        if name and thesis:
            ideas.append({
                'id': idea_id,
                'idea': name,
                'source': source or 'AI-generated',
                'thesis': thesis,
                'archetype': archetype or 'custom',
                'params': params or '',
                'status': 'new',
            })

    return ideas[:3]  # Cap at 3


def _extract_field(text: str, field_name: str) -> str:
    """Extract a field value from a text block."""
    pattern = rf'{field_name}:\s*(.+)'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ''


def _append_ideas_to_backlog(ideas: list, filepath: str):
    """Append new ideas to the Active Pipeline table in RESEARCH_BACKLOG.md."""
    path = Path(filepath)
    text = path.read_text()
    lines = text.split('\n')

    # Find the last row in the Active Pipeline table
    insert_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('| R') or line.strip().startswith('| R0'):
            insert_idx = i

    if insert_idx is None:
        print("Could not find Active Pipeline table to insert ideas.")
        return

    # Insert new rows after the last R-entry
    for j, idea in enumerate(ideas):
        notes = f"Archetype: {idea['archetype']}. {idea['params']}"
        row = (f"| {idea['id']} | {idea['idea']} | {idea['source']} | "
               f"{idea['thesis']} | {idea['status']} | {notes} |")
        lines.insert(insert_idx + 1 + j, row)

    path.write_text('\n'.join(lines))


def build_report(pipeline_results, new_ideas) -> str:
    """Build a formatted report for the morning brief."""
    lines = [
        f"# RBI Pipeline Report — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        pipeline_results.get('summary', 'No screening results.'),
        "",
    ]

    if new_ideas:
        lines.append("## New Research Ideas (LLM-sourced)")
        for idea in new_ideas:
            lines.append(f"- **{idea['id']}** — {idea['idea']}: {idea['thesis']}")
        lines.append("")

    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='RBI Pipeline Runner')
    parser.add_argument('--refresh-data', action='store_true',
                       help='Refresh BTCUSD data from Binance before screening')
    parser.add_argument('--source-ideas', action='store_true',
                       help='Use LLM to generate new research ideas')
    parser.add_argument('--ids', default='',
                       help='Comma-separated idea IDs to screen')
    args = parser.parse_args()

    print("=" * 60)
    print(f"RBI PIPELINE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Step 1: Data refresh (optional)
    if args.refresh_data:
        refresh_data()

    # Step 2: Run screens
    idea_ids = [x.strip() for x in args.ids.split(',') if x.strip()] if args.ids else None
    pipeline_results = run_screens(idea_ids)

    # Step 3: Source new ideas (optional)
    new_ideas = []
    if args.source_ideas:
        new_ideas = source_ideas(pipeline_results)

    # Step 4: Build and save report
    report = build_report(pipeline_results, new_ideas)
    report_path = DATA_DIR / f"rbi_report_{datetime.now().strftime('%Y%m%d')}.md"
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")

    # Summary
    print(f"\n{'=' * 60}")
    print("PIPELINE COMPLETE")
    print(f"Screened: {len(pipeline_results.get('screened', []))}")
    print(f"Promoted: {len(pipeline_results.get('promoted', []))}")
    print(f"Killed: {len(pipeline_results.get('killed', []))}")
    if new_ideas:
        print(f"New ideas sourced: {len(new_ideas)}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
