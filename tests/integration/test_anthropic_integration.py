"""Integration tests for Anthropic provider.

These tests are gated and will be skipped unless both `MENTAT_ANTHROPIC_API_KEY`
and `RUN_CLAUDE_TESTS` environment variables are set. This prevents accidental
charges during normal CI or local runs.
"""

import os

import pytest

from mentat.cli import bootstrap
from mentat.providers.interfaces import Message, MessageRole

skip_reason = "Requires MENTAT_ANTHROPIC_API_KEY and RUN_CLAUDE_TESTS=true"


@pytest.mark.skipif(
    not (os.getenv("MENTAT_ANTHROPIC_API_KEY") and os.getenv("RUN_CLAUDE_TESTS") == "true"),
    reason=skip_reason,
)
def test_anthropic_smoke():
    container = bootstrap()
    provider = container.resolve("provider.anthropic")

    # Simple smoke check: provider should be available and return a short completion
    assert provider is not None

    import asyncio

    messages = [Message(role=MessageRole.USER, content="Say hello")]
    resp = asyncio.run(provider.complete(messages, max_tokens=32))

    assert resp is not None
    assert isinstance(resp.content, str)
    assert len(resp.content) > 0
