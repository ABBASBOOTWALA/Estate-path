import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


MODEL = "claude-sonnet-4-6"


def ask_claude(system_prompt: str, user_message: str) -> str:
    """Single-turn Claude call returning text response."""
    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def ask_claude_with_history(system_prompt: str, history: list) -> str:
    """Multi-turn Claude call with conversation history."""
    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=history,
    )
    return response.content[0].text


def stream_claude(system_prompt: str, user_message: str):
    """Stream Claude response, yielding text chunks."""
    with _get_client().messages.stream(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text in stream.text_stream:
            yield text
