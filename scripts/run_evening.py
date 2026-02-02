#!/usr/bin/env python3
"""
Evening Review Generator for AI Chief of Staff.

Loads context, generates an evening review via LLM, and saves output.
Designed to run via GitHub Actions at 20:00 AEDT.
"""

import os
import sys
import json
from datetime import datetime
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


def get_todays_morning_brief(root: Path) -> str:
    """Try to load today's morning brief for context."""
    data_dir = root / "data"
    today = datetime.now().strftime("%Y-%m-%d")

    # Look for today's morning brief
    for file in data_dir.glob(f"morning_{today}*.md"):
        return load_file(file)

    return ""


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

This is an evening review. Be reflective but not therapist-like. Acknowledge the day without judgment.
"""


def build_user_prompt(root: Path) -> str:
    """Build the user prompt with the evening review template and context."""
    # Load the prompt template
    prompt_template = load_file(root / "PROMPTS" / "evening_review.md")

    # Load memory, todos, and morning brief for context
    memory = load_json(root / "data" / "memory.json")
    todos = load_json(root / "data" / "todo.json")
    morning_brief = get_todays_morning_brief(root)

    # Get current date info
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    day_of_week = now.strftime("%A")

    # Replace placeholders
    prompt = prompt_template.replace("{{DATE}}", date_str)
    prompt = prompt.replace("{{DAY_OF_WEEK}}", day_of_week)

    # Add context if available
    context_parts = []

    if morning_brief:
        context_parts.append(f"## Today's Morning Brief\n{morning_brief}")

    if memory:
        context_parts.append(f"## Recent Memory\n```json\n{json.dumps(memory, indent=2)}\n```")

    if todos and todos.get("tasks"):
        context_parts.append(f"## Current Todos\n```json\n{json.dumps(todos, indent=2)}\n```")

    if context_parts:
        prompt += "\n\n## Additional Context\n" + "\n\n".join(context_parts)

    return prompt


def save_output(root: Path, content: str, brief_type: str = "evening") -> Path:
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
    print("AI CHIEF OF STAFF - EVENING REVIEW")
    print("=" * 60)
    print()

    root = get_repo_root()

    # Build prompts
    print("Loading context...")
    system_prompt = build_system_prompt(root)
    user_prompt = build_user_prompt(root)

    # Generate review
    print("Generating evening review...")
    print()

    try:
        response = generate(prompt=user_prompt, system=system_prompt)
    except Exception as e:
        error_msg = f"# Evening Review - Error\n\nFailed to generate review: {e}\n\nTimestamp: {datetime.now().isoformat()}"
        output_path = save_output(root, error_msg, "evening_error")
        print(f"Error: {e}")
        print(f"Error logged to: {output_path}")
        sys.exit(1)

    # Print to console
    print("-" * 60)
    print(response)
    print("-" * 60)
    print()

    # Save to file
    full_output = f"# Evening Review - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    full_output += f"Generated at: {datetime.now().strftime('%H:%M %Z')}\n\n"
    full_output += "---\n\n"
    full_output += response

    output_path = save_output(root, full_output, "evening")
    print(f"Saved to: {output_path}")

    # Send email if configured
    date_str = datetime.now().strftime("%Y-%m-%d")
    send_email(
        subject=f"Evening Review - {date_str}",
        body=markdown_to_html(response),
        html=True
    )

    print()
    print("Evening review complete.")


if __name__ == "__main__":
    main()
