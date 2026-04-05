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


def refresh_data(include_15m=False):
    """Refresh BTCUSD data. Only 1h by default (sufficient for screening)."""
    print("\n=== DATA REFRESH ===")
    from fetch_btc_data import fetch_and_save
    fetch_and_save('1h', 1095)
    if include_15m:
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
    # Rotate archetype focus to diversify sourcing and reduce duplicates
    archetype_groups = [
        ['trend_pullback', 'momentum_exhaustion_reversal', 'atr_regime_adaptive'],
        ['range_compression_expansion', 'acceleration_breakout', 'volume_breakout'],
        ['donchian_breakout', 'trend_strength_breakout', 'consecutive_momentum'],
        ['adaptive_momentum_burst', 'dual_momentum_consensus', 'mtf_breakout'],
        ['mean_reversion_short', 'breakdown_momentum', 'ma_crossover'],
    ]
    day_of_year = datetime.now().timetuple().tm_yday
    focus_group = archetype_groups[day_of_year % len(archetype_groups)]
    focus_str = ', '.join(focus_group)

    system = f"""You are a quantitative trading researcher specializing in cryptocurrency markets.
Your job is to propose NEW trading strategy ideas for BTCUSD backtesting.

Rules:
- Ideas must be testable with OHLCV price data (we have 3 years of 15m and 1h BTCUSD data)
- Each idea needs a clear edge thesis (WHY it should work)
- Focus on trend-following, momentum, and breakout strategies (mean reversion has failed for crypto)
- Design around wide targets (4%+) to absorb transaction costs (0.1% round-trip)
- BTC has a structural uptrend (+200% over 3 years) — long-only or long-biased is preferred
- Do NOT propose ideas that require external data (funding rates, order book, sentiment, etc.)
- Generate exactly 1 new idea
- IMPORTANT: The idea MUST use one of today's focus archetypes. Do NOT duplicate existing strategies.
- Today's focus archetypes (prefer these): {focus_str}
- IMPORTANT: Vary parameters significantly from existing promoted strategies. Do NOT just rename an existing strategy."""

    killed_str = "\n".join(f"- {e['id']} {e['idea']}: {e['notes']}" for e in killed)
    promoted_str = "\n".join(f"- {e['id']} {e['idea']}: {e['notes']}" for e in promoted) if promoted else "None yet"
    parked_str = "\n".join(f"- {e['id']} {e['idea']}: {e['notes']}" for e in parked) if parked else "None"

    recent_context = ""
    if pipeline_results and pipeline_results.get('screened'):
        recent_context = "\n\nMost recent screening results:\n"
        for r in pipeline_results['screened']:
            recent_context += f"- {r.get('idea_id', '?')} {r.get('idea_name', '?')}: PF {r.get('gross_pf', '?')}, verdict: {r.get('verdict', '?')}\n"

    # Load meta-analysis insights (autoresearch pattern: feed experiment history into sourcing)
    insights_context = ""
    insights_file = REPO_ROOT / 'data' / 'experiment_insights.json'
    if insights_file.exists():
        try:
            insights = json.loads(insights_file.read_text())
            recs = insights.get('recommendations', [])
            if recs:
                insights_context = "\n\n## Meta-analysis insights (from experiment history):\n"
                for rec in recs:
                    insights_context += f"- {rec}\n"
            # Add top archetypes info
            board = insights.get('archetype_leaderboard', [])
            top_archs = [a for a in board[:5] if a.get('promo_rate', 0) > 0]
            if top_archs:
                insights_context += "\nArchetype performance ranking:\n"
                for a in top_archs:
                    insights_context += (f"- {a['archetype']}: {a['promo_rate']:.0%} promo rate, "
                                        f"avg PF {a['avg_pf']}, max PF {a['max_pf']} "
                                        f"({a['total_screens']} screens)\n")
        except (json.JSONDecodeError, KeyError):
            pass

    prompt = f"""Based on our research history, propose 1 NEW trading strategy idea for BTCUSD.

## What's been killed (didn't work):
{killed_str}

## What's been promoted (shows promise):
{promoted_str}

## What's parked (can't test yet):
{parked_str}
{recent_context}
{insights_context}

## Key learnings:
- Mean reversion doesn't work in crypto (too much momentum)
- Trend following works best, especially with wider stops and targets
- Volatility-adjusted strategies show promise (PF 1.46 with ATR-based stops)
- Donchian breakout works (PF 1.31)
- Daily timeframe shows strong results but low trade count
- Squeeze breakouts predict magnitude but not direction

## Available strategy archetypes (use ONLY these, never 'custom'):
- ma_crossover: Fast/slow MA crossover with configurable periods
- donchian_breakout: N-bar high/low breakout
- vol_adjusted_trend: MA trend with ATR-scaled stops/targets
- daily_trend: Longer-hold trend following on daily bars
- bollinger_breakout: BB squeeze breakout
- adaptive_momentum_burst: Squeeze breakout with trend MA confirmation
- acceleration_breakout: Donchian breakout + ROC acceleration filter
- mtf_breakout: Donchian breakout + slow MA trend filter
- volume_breakout: Donchian breakout + volume spike confirmation
- dual_momentum_consensus: Donchian breakout + 3-period ROC consensus
- trend_strength_breakout: Donchian breakout + ADX trend strength filter
- trend_pullback: Buy pullback to rising MA with momentum bounce
- atr_regime_adaptive: Trend following with ATR-percentile stop scaling
- consecutive_momentum: Donchian breakout + N consecutive positive bars
- range_compression_expansion: ATR compression detection + breakout
- momentum_exhaustion_reversal: RSI oversold bounce within uptrend
- gap_and_go: Gap continuation in trending market

IMPORTANT: You MUST pick one of the archetypes above. Do NOT use 'custom'.
Design ideas that FIT an existing archetype with appropriate parameters.

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
        # Dedup: check if archetype already has promoted/validated strategies
        ideas = _dedup_sourced_ideas(ideas, entries)
        if ideas:
            _append_ideas_to_backlog(ideas, BACKLOG_FILE)
            print(f"Added {len(ideas)} new ideas to backlog: {', '.join(i['id'] for i in ideas)}")
        else:
            print("All sourced ideas were duplicates of existing strategies. None added.")
    else:
        print("No parseable ideas in LLM response.")
        print(f"Raw response:\n{response[:500]}")

    return ideas


def _dedup_sourced_ideas(ideas: list, existing_entries: list) -> list:
    """Filter out ideas whose archetype already has 3+ promoted/validated entries.

    Prevents the pipeline from generating more ideas for saturated archetypes.
    """
    archetype_counts = {}
    for entry in existing_entries:
        if entry['status'] in ('promoted', 'validated'):
            # Extract archetype from notes
            notes = entry.get('notes', '')
            match = re.search(r'[Aa]rchetype:\s*(\w+)', notes)
            if match:
                arch = match.group(1)
                archetype_counts[arch] = archetype_counts.get(arch, 0) + 1

    filtered = []
    for idea in ideas:
        arch = idea.get('archetype', 'custom')
        count = archetype_counts.get(arch, 0)
        if count >= 3:
            print(f"  Skipping {idea['id']} ({idea['idea']}): archetype '{arch}' "
                  f"already has {count} promoted/validated entries.")
        else:
            filtered.append(idea)

    return filtered


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


def sync_memory(pipeline_results, new_ideas):
    """Update data/memory.json with pipeline results.

    Keeps memory.json in sync so morning/evening briefs have accurate context.
    """
    memory_path = DATA_DIR / 'memory.json'

    try:
        memory = json.loads(memory_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        print("Warning: Could not read memory.json, skipping sync.")
        return

    now = datetime.now()
    today = now.strftime('%Y-%m-%d')

    promoted = pipeline_results.get('promoted', [])
    killed = pipeline_results.get('killed', [])
    parked = pipeline_results.get('parked', [])
    screened = pipeline_results.get('screened', [])

    # Nothing happened — skip update
    if not screened and not new_ideas:
        return

    # --- Update version and timestamp ---
    memory['version'] = memory.get('version', 0) + 1
    memory['last_updated'] = now.astimezone().isoformat()

    # --- Update active_context ---
    total_promoted = len(memory.get('strategies', {}).get('promoted_awaiting_validation', []))
    parts = []
    if screened:
        parts.append(f"{len(screened)}_screened")
    if promoted:
        parts.append(f"{len(promoted)}_promoted")
    if killed:
        parts.append(f"{len(killed)}_killed")
    if new_ideas:
        parts.append(f"{len(new_ideas)}_new_ideas_sourced")

    ctx = memory.setdefault('active_context', {})
    ctx['status'] = f"pipeline_ran_{today}_{'_'.join(parts)}"
    if promoted:
        ctx['next_action'] = 'walk_forward_validate_newly_promoted_strategies'

    # --- Add session_log entry ---
    log = memory.setdefault('session_log', [])

    summary_parts = []
    if screened:
        summary_parts.append(f"Pipeline screened {len(screened)} ideas.")
    if promoted:
        promo_details = []
        for r in screened:
            if r.get('verdict') == 'promote':
                promo_details.append(f"{r['idea_id']} (PF {r.get('gross_pf', '?')})")
        summary_parts.append(f"Promoted: {', '.join(promo_details)}.")
    if killed:
        kill_details = []
        for r in screened:
            if r.get('verdict') == 'kill':
                kill_details.append(f"{r['idea_id']} (PF {r.get('gross_pf', '?')})")
        summary_parts.append(f"Killed: {', '.join(kill_details)}.")
    if new_ideas:
        ids = [i['id'] for i in new_ideas]
        summary_parts.append(f"New ideas sourced: {', '.join(ids)}.")

    entry = {
        'date': today,
        'summary': ' '.join(summary_parts),
        'decisions': [],
        'artifacts': [],
        'source': 'automated_rbi_pipeline',
    }
    if promoted:
        entry['decisions'].extend(f"{pid}_promoted" for pid in promoted)
    if killed:
        entry['decisions'].extend(f"{kid}_killed" for kid in killed)

    # Replace today's pipeline entry if one exists, otherwise prepend
    replaced = False
    for i, existing in enumerate(log):
        if existing.get('date') == today and existing.get('source') == 'automated_rbi_pipeline':
            log[i] = entry
            replaced = True
            break
    if not replaced:
        log.insert(0, entry)

    # Keep log trimmed to 10 entries
    memory['session_log'] = log[:10]

    # --- Update strategies ---
    strats = memory.setdefault('strategies', {})
    promoted_list = strats.setdefault('promoted_awaiting_validation', [])
    killed_list = strats.setdefault('killed', [])
    research_queue = strats.setdefault('research_queue', [])

    # Add newly promoted strategies
    existing_promoted_ids = {s.get('research_id') for s in promoted_list}
    for r in screened:
        if r.get('verdict') == 'promote' and r.get('idea_id') not in existing_promoted_ids:
            promoted_list.append({
                'research_id': r['idea_id'],
                'name': r.get('idea_name', ''),
                'gross_pf': r.get('gross_pf', 0),
                'trades': r.get('total_trades', 0),
                'win_rate': f"{r.get('win_rate', 0):.1%}" if isinstance(r.get('win_rate'), float) else str(r.get('win_rate', '')),
                'params': r.get('params', {}),
                'next_step': 'walk_forward_validation',
            })

    # Add newly killed strategies
    for r in screened:
        if r.get('verdict') == 'kill':
            kill_str = f"{r['idea_id']} ({r.get('idea_name', '')}, PF {r.get('gross_pf', '?')})"
            if kill_str not in killed_list:
                killed_list.append(kill_str)

    # Remove promoted/killed from research queue
    resolved_ids = set(promoted + killed)
    research_queue[:] = [r for r in research_queue if r.get('id') not in resolved_ids]

    # Add new ideas to research queue
    existing_queue_ids = {r.get('id') for r in research_queue}
    for idea in new_ideas:
        if idea['id'] not in existing_queue_ids:
            research_queue.append({
                'id': idea['id'],
                'name': idea.get('idea', ''),
                'status': 'new',
                'note': f"Auto-sourced. Archetype: {idea.get('archetype', 'custom')}.",
            })

    # --- Write back ---
    memory_path.write_text(json.dumps(memory, indent=2, default=str) + '\n')
    print(f"memory.json synced (v{memory['version']}): {', '.join(parts) if parts else 'no changes'}")


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
    parser.add_argument('--skip-screens', action='store_true',
                       help='Skip screening step (useful for source-only runs)')
    parser.add_argument('--ids', default='',
                       help='Comma-separated idea IDs to screen')
    args = parser.parse_args()

    print("=" * 60)
    print(f"RBI PIPELINE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Step 1: Data refresh (optional)
    if args.refresh_data:
        refresh_data()

    # Step 2: Run screens (unless --skip-screens)
    pipeline_results = {'screened': [], 'promoted': [], 'killed': [], 'parked': [],
                        'summary': 'Screening skipped.'}
    if not args.skip_screens:
        idea_ids = [x.strip() for x in args.ids.split(',') if x.strip()] if args.ids else None
        pipeline_results = run_screens(idea_ids)

    # Step 3: Source new ideas (optional)
    new_ideas = []
    if args.source_ideas:
        new_ideas = source_ideas(pipeline_results)

    # Step 4: Sync memory.json with results
    sync_memory(pipeline_results, new_ideas)

    # Step 5: Build and save report
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
