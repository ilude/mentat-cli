"""Tests for provider model listing functionality.

This test module includes live API tests that are gated by the presence of API keys.
Tests will be skipped if the required API keys are not set in the environment.

API Keys Required:
- ANTHROPIC_API_KEY: Required to run tests for Anthropic provider model listing
- OPENAI_API_KEY: Required to run tests for OpenAI provider model listing

To run all tests including model listing tests:
    export ANTHROPIC_API_KEY=<your-key>
    export OPENAI_API_KEY=<your-key>
    pytest tests/unit/test_providers/test_model_listing.py -v

To see which tests are being skipped:
    pytest tests/unit/test_providers/test_model_listing.py -v -rs

The tests verify that:
1. Each provider can list models via API when configured
2. Models are correctly typed and non-empty
3. Provider-specific models are present (Claude for Anthropic, GPT for OpenAI)
4. Different providers list different sets of models
"""

from __future__ import annotations

import os

import pytest

from mentat.cli import bootstrap


@pytest.fixture
def container():
    """Create and return a bootstrapped container."""
    return bootstrap()


@pytest.fixture
def anthropic_provider(container):
    """Get the Anthropic provider."""
    return container.resolve("provider.anthropic")


@pytest.fixture
def openai_provider(container):
    """Get the OpenAI provider."""
    return container.resolve("provider.openai")


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping live API tests",
)
class TestAnthropicModelListing:
    """Tests for Anthropic provider model listing (requires API key)."""

    def test_anthropic_lists_models(self, anthropic_provider):
        """Test that Anthropic provider can list models."""
        models = anthropic_provider.list_models()
        assert models is not None
        assert isinstance(models, list)
        assert len(models) > 0
        # Verify models are strings
        assert all(isinstance(m, str) for m in models)
        # Verify Claude models are present
        assert any("claude" in m.lower() for m in models)

    def test_anthropic_models_contain_claude(self, anthropic_provider):
        """Test that Anthropic models contain Claude in the name."""
        models = anthropic_provider.list_models()
        assert any("claude" in model.lower() for model in models)


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set; skipping live API tests",
)
class TestOpenAIModelListing:
    """Tests for OpenAI provider model listing (requires API key)."""

    def test_openai_lists_models(self, openai_provider):
        """Test that OpenAI provider can list models."""
        models = openai_provider.list_models()
        assert models is not None
        assert isinstance(models, list)
        assert len(models) > 0
        # Verify models are strings
        assert all(isinstance(m, str) for m in models)
        # Verify GPT models are present
        assert any("gpt" in m.lower() for m in models)

    def test_openai_models_contain_gpt(self, openai_provider):
        """Test that OpenAI models contain GPT variants."""
        models = openai_provider.list_models()
        gpt_models = [m for m in models if "gpt" in m.lower()]
        assert len(gpt_models) > 0


@pytest.mark.skipif(
    not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("OPENAI_API_KEY")),
    reason="Both ANTHROPIC_API_KEY and OPENAI_API_KEY required for comparison tests",
)
class TestProviderModelSeparation:
    """Tests comparing model listings across providers (requires both API keys)."""

    def test_providers_list_different_models(self, anthropic_provider, openai_provider):
        """Test that Anthropic and OpenAI providers list different models."""
        anth_models = set(anthropic_provider.list_models())
        openai_models = set(openai_provider.list_models())

        # The model sets should not be identical
        assert anth_models != openai_models

        # Verify provider-specific models
        anth_first = list(anth_models)[0]
        openai_first = list(openai_models)[0]

        assert anth_first != openai_first
