"""
Parse RESEARCH_BACKLOG.md to extract strategy ideas and their statuses.

Reads the markdown table in the Active Pipeline section and returns
structured data for the pipeline orchestrator.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional


BACKLOG_PATH = Path(__file__).parent.parent / 'RESEARCH_BACKLOG.md'


def parse_backlog(filepath: Optional[str] = None) -> List[Dict]:
    """Parse RESEARCH_BACKLOG.md and extract Active Pipeline entries.

    Returns:
        List of dicts with keys:
            id, idea, source, thesis, status, notes
    """
    path = Path(filepath) if filepath else BACKLOG_PATH
    text = path.read_text()

    # Find the Active Pipeline table
    lines = text.split('\n')
    in_table = False
    header_found = False
    entries = []

    for line in lines:
        stripped = line.strip()

        # Detect start of Active Pipeline table
        if '| # |' in stripped and 'Idea' in stripped:
            in_table = True
            header_found = True
            continue

        # Skip separator line
        if in_table and stripped.startswith('|') and set(stripped.replace('|', '').replace(':', '').strip()) <= {'-'}:
            continue

        # Parse table rows
        if in_table and stripped.startswith('|'):
            cells = [c.strip() for c in stripped.split('|')]
            # Remove empty cells from leading/trailing pipes
            cells = [c for c in cells if c != '']

            if len(cells) >= 5:
                entry = {
                    'id': cells[0].strip(),
                    'idea': cells[1].strip(),
                    'source': cells[2].strip(),
                    'thesis': cells[3].strip(),
                    'status': cells[4].strip(),
                    'notes': cells[5].strip() if len(cells) > 5 else '',
                }
                entries.append(entry)

        # End of table (next section)
        elif in_table and header_found and stripped.startswith('#'):
            break
        elif in_table and stripped == '' and header_found:
            # Empty line might end the table
            continue

    return entries


def get_unscreened(filepath: Optional[str] = None) -> List[Dict]:
    """Get ideas with status 'new' (ready for screening)."""
    return [e for e in parse_backlog(filepath) if e['status'] == 'new']


def get_by_status(status: str, filepath: Optional[str] = None) -> List[Dict]:
    """Get ideas filtered by status."""
    return [e for e in parse_backlog(filepath) if e['status'] == status]


def update_backlog_entry(
    idea_id: str,
    new_status: str,
    new_notes: str,
    filepath: Optional[str] = None,
) -> bool:
    """Update a single entry's status and notes in RESEARCH_BACKLOG.md.

    Args:
        idea_id: The R-number to update (e.g. 'R009')
        new_status: New status value (e.g. 'killed', 'promoted')
        new_notes: New notes text
        filepath: Path to backlog file (default: strategies/RESEARCH_BACKLOG.md)

    Returns:
        True if entry was found and updated, False otherwise.
    """
    path = Path(filepath) if filepath else BACKLOG_PATH
    text = path.read_text()
    lines = text.split('\n')
    updated = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith('|'):
            continue

        cells = [c.strip() for c in stripped.split('|')]
        cells = [c for c in cells if c != '']

        if len(cells) >= 5 and cells[0].strip() == idea_id:
            # Reconstruct the row with updated status and notes
            cells[4] = new_status
            if len(cells) > 5:
                cells[5] = new_notes
            elif new_notes:
                cells.append(new_notes)

            new_line = '| ' + ' | '.join(cells) + ' |'
            lines[i] = new_line
            updated = True
            break

    if updated:
        path.write_text('\n'.join(lines))

    return updated


def add_killed_entry(
    idea_id: str,
    idea_name: str,
    screen_result: str,
    lesson: str,
    filepath: Optional[str] = None,
) -> bool:
    """Add an entry to the Killed Ideas archive table.

    Args:
        idea_id: The K-number (e.g. 'K008')
        idea_name: Strategy name
        screen_result: Brief result string (e.g. 'Gross PF 0.98, 26.8% WR')
        lesson: What was learned
        filepath: Path to backlog file

    Returns:
        True if entry was added successfully.
    """
    path = Path(filepath) if filepath else BACKLOG_PATH
    text = path.read_text()

    # Find the last row in Killed Ideas table
    lines = text.split('\n')
    insert_idx = None
    in_killed = False

    for i, line in enumerate(lines):
        if '## Killed Ideas' in line:
            in_killed = True
            continue
        if in_killed and line.strip().startswith('| K'):
            insert_idx = i  # Track last K-entry
        if in_killed and line.strip().startswith('#'):
            break

    if insert_idx is not None:
        new_row = f"| {idea_id} | {idea_name} | {screen_result} | {lesson} |"
        lines.insert(insert_idx + 1, new_row)
        path.write_text('\n'.join(lines))
        return True

    return False


def get_next_kill_number(filepath: Optional[str] = None) -> str:
    """Get the next K-number for the Killed Ideas archive."""
    path = Path(filepath) if filepath else BACKLOG_PATH
    text = path.read_text()
    k_numbers = [int(m.group(1)) for m in re.finditer(r'K(\d+)', text)]
    next_k = max(k_numbers) + 1 if k_numbers else 1
    return f"K{next_k:03d}"


if __name__ == '__main__':
    print("Parsing RESEARCH_BACKLOG.md...")
    entries = parse_backlog()
    print(f"Found {len(entries)} entries:")
    for e in entries:
        print(f"  [{e['status']:>10}] {e['id']} — {e['idea']}")

    unscreened = get_unscreened()
    print(f"\nUnscreened (new): {len(unscreened)}")
    for e in unscreened:
        print(f"  {e['id']} — {e['idea']}: {e['thesis']}")
