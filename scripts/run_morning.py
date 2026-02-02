#!/usr/bin/env python3
"""
Morning Brief Generator for AI Chief of Staff.

Loads context, generates a morning briefing via LLM, and saves output.
Designed to run via GitHub Actions at 08:00 AEDT.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from llm import generate


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

    # TODO: Optional integrations (uncomment and configure as needed)
    #
    # Email delivery:
    # send_email(subject="Morning Brief", body=response)
    #
    # GitHub Issue:
    # create_github_issue(title=f"Morning Brief - {date}", body=response)
    #
    # Slack/Discord webhook:
    # post_to_webhook(url=os.environ["WEBHOOK_URL"], content=response)

    print()
    print("Morning brief complete.")


if __name__ == "__main__":
    main()
