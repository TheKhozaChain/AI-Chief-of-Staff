#!/usr/bin/env python3
"""
Morning Brief Generator for AI Chief of Staff.

Loads context, generates a morning briefing via LLM, and saves output.
Designed to run via GitHub Actions at 08:00 AEDT.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from llm import generate
from email_sender import send_email, markdown_to_html


def get_repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent


def load_file(path: Path) -> str:
    """Load a file's contents, return empty string if not found."""
    try:
        return path.read_text()
    except FileNotFoundError:
        print(f"Warning: {path} not found")
        return ""


def load_json(path: Path) -> dict:
    """Load a JSON file, return empty dict if not found or invalid."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def build_system_prompt(root: Path) -> str:
    """Build the system prompt from context files."""
    user = load_file(root / "USER.md")
    mission = load_file(root / "MISSION.md")
    principles = load_file(root / "OPERATING_PRINCIPLES.md")

    return f"""You are an AI Chief of Staff for Sipho Khoza.

## User Profile
{user}

## Mission
{mission}

## Operating Principles
{principles}

Follow these documents precisely. Generate outputs that match the user's communication preferences: concise, practical, structured, with clear next steps.
"""


def build_user_prompt(root: Path) -> str:
    """Build the user prompt with the morning brief template and context."""
    # Load the prompt template
    prompt_template = load_file(root / "PROMPTS" / "morning_brief.md")

    # Load memory and todos for context
    memory = load_json(root / "data" / "memory.json")
    todos = load_json(root / "data" / "todo.json")

    # Get current date info
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    day_of_week = now.strftime("%A")

    # Replace placeholders
    prompt = prompt_template.replace("{{DATE}}", date_str)
    prompt = prompt.replace("{{DAY_OF_WEEK}}", day_of_week)

    # Add context if available
    context_parts = []

    # CRITICAL: Load KANBAN for current state of work
    # This prevents stale briefs that recommend already-completed items
    kanban_text = load_file(root / "KANBAN.md")
    if kanban_text:
        context_parts.append(f"## Current Work Board (KANBAN.md)\n"
                             f"IMPORTANT: Use this to determine what's already done "
                             f"and what's actually queued. Do NOT recommend items that "
                             f"appear in the Done section.\n\n{kanban_text}")

    # Load research backlog for RBI status
    backlog_text = load_file(root / "strategies" / "RESEARCH_BACKLOG.md")
    if backlog_text:
        context_parts.append(f"## Research Backlog\n{backlog_text[:3000]}")

    # Load yesterday's evening review if it exists
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    evening_files = sorted(root.glob(f"data/evening_{yesterday}*"))
    if evening_files:
        evening_text = load_file(evening_files[-1])
        if evening_text:
            context_parts.append(f"## Yesterday's Evening Review\n{evening_text[:2000]}")

    # Load most recent execution report
    exec_files = sorted(root.glob("data/execution_*"))
    if exec_files:
        exec_text = load_file(exec_files[-1])
        if exec_text:
            context_parts.append(f"## Most Recent Execution Report\n{exec_text[:1500]}")

    if memory:
        context_parts.append(f"## Recent Memory\n```json\n{json.dumps(memory, indent=2)}\n```")

    if todos and todos.get("tasks"):
        context_parts.append(f"## Current Todos\n```json\n{json.dumps(todos, indent=2)}\n```")

    if context_parts:
        prompt += "\n\n## Additional Context\n" + "\n\n".join(context_parts)

    return prompt


def save_output(root: Path, content: str, brief_type: str = "morning") -> Path:
    """Save the generated output to a timestamped file."""
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"{brief_type}_{timestamp}.md"
    output_path = data_dir / filename

    output_path.write_text(content)
    return output_path


def main():
    """Main entry point."""
    print("=" * 60)
    print("AI CHIEF OF STAFF - MORNING BRIEF")
    print("=" * 60)
    print()

    root = get_repo_root()

    # Build prompts
    print("Loading context...")
    system_prompt = build_system_prompt(root)
    user_prompt = build_user_prompt(root)

    # Generate briefing
    print("Generating morning brief...")
    print()

    try:
        response = generate(prompt=user_prompt, system=system_prompt)
    except Exception as e:
        error_msg = f"# Morning Brief - Error\n\nFailed to generate brief: {e}\n\nTimestamp: {datetime.now().isoformat()}"
        output_path = save_output(root, error_msg, "morning_error")
        print(f"Error: {e}")
        print(f"Error logged to: {output_path}")
        sys.exit(1)

    # Print to console
    print("-" * 60)
    print(response)
    print("-" * 60)
    print()

    # Save to file
    full_output = f"# Morning Brief - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    full_output += f"Generated at: {datetime.now().strftime('%H:%M %Z')}\n\n"
    full_output += "---\n\n"
    full_output += response

    output_path = save_output(root, full_output, "morning")
    print(f"Saved to: {output_path}")

    # Send email if configured
    date_str = datetime.now().strftime("%Y-%m-%d")
    send_email(
        subject=f"Morning Brief - {date_str}",
        body=markdown_to_html(response),
        html=True
    )

    print()
    print("Morning brief complete.")


if __name__ == "__main__":
    main()
