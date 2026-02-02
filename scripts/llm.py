"""
Minimal LLM wrapper for AI Chief of Staff.

Supports Anthropic (Claude) and OpenAI (GPT) via environment variables.
Intentionally simple and readable.
"""

import os
from typing import Optional


def get_provider() -> str:
    """Get the LLM provider from environment. Defaults to anthropic."""
    return os.environ.get("LLM_PROVIDER", "anthropic").lower()


def get_api_key(provider: str) -> str:
    """Get the API key for the specified provider."""
    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return key
    elif provider == "openai":
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return key
    else:
        raise ValueError(f"Unknown provider: {provider}")


def call_anthropic(prompt: str, system: str, api_key: str) -> str:
    """Call Anthropic Claude API."""
    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic package not installed. Run: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)

    # Use Claude Haiku for cost efficiency (or Sonnet for better quality)
    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")

    message = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def call_openai(prompt: str, system: str, api_key: str) -> str:
    """Call OpenAI GPT API."""
    try:
        import openai
    except ImportError:
        raise ImportError("openai package not installed. Run: pip install openai")

    client = openai.OpenAI(api_key=api_key)

    # Use GPT-4o-mini for cost efficiency
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    response = client.chat.completions.create(
        model=model,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


def generate(prompt: str, system: Optional[str] = None) -> str:
    """
    Generate a response from the configured LLM.

    Args:
        prompt: The user prompt to send
        system: Optional system prompt (context about the task)

    Returns:
        The LLM's response text

    Raises:
        ValueError: If API key is missing or provider is unknown
        ImportError: If required SDK is not installed
    """
    provider = get_provider()
    api_key = get_api_key(provider)

    system = system or "You are a helpful assistant."

    if provider == "anthropic":
        return call_anthropic(prompt, system, api_key)
    elif provider == "openai":
        return call_openai(prompt, system, api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")


# Simple test when run directly
if __name__ == "__main__":
    print("Testing LLM wrapper...")
    print(f"Provider: {get_provider()}")

    try:
        response = generate(
            prompt="Say 'Hello, Chief of Staff system is working!' in exactly those words.",
            system="You are a test assistant. Follow instructions exactly."
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
