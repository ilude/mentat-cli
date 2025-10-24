"""Unit tests for the Anthropic provider implementation."""

import sys
import types

from mentat.providers.anthropic_provider import AnthropicProvider
from mentat.providers.interfaces import Message, MessageRole


class DummyResp:
    def __init__(self, text: str = "Hello from Claude"):
        # SDKs differ; provide multiple access patterns
        self.completion = text
        self.text = text
        self.finish_reason = "stop"
        self.usage = {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}


class DummyCompletions:
    @staticmethod
    def create(model, prompt=None, **kwargs):
        return DummyResp("Echo: " + (prompt or ""))


class DummyClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.completions = DummyCompletions()


class DummyModels:
    @staticmethod
    def list():
        return [
            {"id": "claude-3-sonnet"},
            {"id": "claude-3-haiku"},
        ]


class DummyClientWithModels(DummyClient):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.models = DummyModels()


def test_complete_with_mocked_sdk(monkeypatch):
    # Create a fake anthropic module and Client class
    fake = types.ModuleType("anthropic")
    fake.Client = DummyClient
    sys.modules["anthropic"] = fake

    provider = AnthropicProvider(config={"api_key": "fake-key", "model": "claude-test"})

    messages = [Message(role=MessageRole.USER, content="Say hi")]

    import asyncio

    resp = asyncio.run(provider.complete(messages))

    assert resp is not None
    assert "Echo:" in resp.content
    assert resp.model == "claude-test"
    assert isinstance(resp.usage, dict)


def test_test_connection_with_mocked_sdk(monkeypatch):
    fake = types.ModuleType("anthropic")
    fake.Client = DummyClient
    sys.modules["anthropic"] = fake

    provider = AnthropicProvider(config={"api_key": "fake-key"})

    import asyncio

    ok = asyncio.run(provider.test_connection())
    assert ok is True


def test_list_models(monkeypatch):
    fake = types.ModuleType("anthropic")
    fake.Client = DummyClientWithModels
    sys.modules["anthropic"] = fake

    provider = AnthropicProvider(config={"api_key": "fake-key"})

    models = provider.list_models()

    assert models == ["claude-3-sonnet", "claude-3-haiku"]
