"""Anthropic (Claude) AI provider implementation for Mentat CLI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import os
import logging

from mentat.providers.interfaces import (
    BaseAIProvider,
    CompletionResponse,
    Message,
    ProviderCapabilities,
    ProviderType,
)

logger = logging.getLogger(__name__)

API_KEY_ENV = "MENTAT_ANTHROPIC_API_KEY"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 256


class AnthropicProvider(BaseAIProvider):
    """Minimal Anthropic provider that wraps the Anthropic SDK or a compatible client.

    This implementation is intentionally defensive about SDK differences so unit tests
    can mock the SDK surface.
    """

    @staticmethod
    def _create_client(api_key: str) -> Optional[Any]:
        """Instantiate the Anthropic SDK client using the simplest available surface."""
        try:
            import anthropic  # type: ignore
        except Exception:  # pragma: no cover - import errors are handled gracefully
            logger.exception("Failed to import anthropic SDK")
            return None

        client: Optional[Any] = None

        if hasattr(anthropic, "Anthropic"):
            try:
                client = anthropic.Anthropic(api_key=api_key)
            except TypeError:
                try:
                    client = anthropic.Anthropic()
                except Exception:
                    client = None
        if client is None and hasattr(anthropic, "Client"):
            try:
                client = anthropic.Client(api_key=api_key)
            except TypeError:
                try:
                    client = anthropic.Client()
                except Exception:
                    client = None

        if client is None:
            logger.warning("Anthropic SDK imported but no supported client constructor succeeded")
        return client

    def _get_available_model_ids(self) -> List[str]:
        """Return model identifiers exposed by the Anthropic client, if any."""
        if not self.client:
            return []
        try:
            resource = getattr(self.client, "models", None)
            if resource is None or not hasattr(resource, "list"):
                return []
            resp = resource.list()
            models: List[str] = []
            try:
                for item in resp:
                    mid = getattr(item, "id", None)
                    if mid is None and isinstance(item, dict):
                        mid = item.get("id")
                    if mid:
                        models.append(str(mid))
            except TypeError:
                if isinstance(resp, dict):
                    data = resp.get("data") or resp.get("models")
                    if isinstance(data, list):
                        for item in data:
                            mid = getattr(item, "id", None) or (item.get("id") if isinstance(item, dict) else None)
                            if mid:
                                models.append(str(mid))
            return models
        except Exception:
            logger.exception("Failed to list Anthropic models")
            return []

    def list_models(self) -> List[str]:
        """Public helper used by tooling (CLI/REPL) to show available models."""
        return self._get_available_model_ids()

    @staticmethod
    def _prepare_messages_payload(messages: List[Message]) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """Split system messages and format the rest for Anthropic's Messages API."""
        system_text: Optional[str] = None
        structured: List[Dict[str, Any]] = []

        for msg in messages:
            role = getattr(msg.role, "value", str(msg.role))
            if role == "system":
                system_text = msg.content if system_text is None else f"{system_text}\n{msg.content}"
                continue
            mapped_role = "user" if role == "user" else "assistant"
            structured.append(
                {
                    "role": mapped_role,
                    "content": [
                        {
                            "type": "text",
                            "text": msg.content,
                        }
                    ],
                }
            )

        return system_text, structured

    @staticmethod
    def _build_completion_prompt(messages: List[Message], system_text: Optional[str]) -> str:
        """Render messages into the Human/Assistant alternating prompt expected by completions."""
        if len(messages) == 1:
            single_role = getattr(messages[0].role, "value", str(messages[0].role))
            if single_role == "user":
                return f"\n\nHuman: {messages[0].content}\n\nAssistant:"

        parts: List[str] = []
        if system_text:
            parts.append(system_text)
        for msg in messages:
            role = getattr(msg.role, "value", str(msg.role))
            if role == "system":
                continue
            label = "Human" if role == "user" else "Assistant"
            parts.append(f"\n\n{label}: {msg.content}")

        prompt = "".join(parts)
        if not prompt.endswith("\n\nAssistant:") and not prompt.rstrip().endswith("Assistant:"):
            prompt += "\n\nAssistant:"
        return prompt

    def _has_messages_api(self) -> bool:
        if not self.client:
            return False
        resource = getattr(self.client, "messages", None)
        return bool(resource and hasattr(resource, "create"))

    def _has_completions_api(self) -> bool:
        if not self.client:
            return False
        resource = getattr(self.client, "completions", None)
        return bool(resource and hasattr(resource, "create"))

    @staticmethod
    def _is_model_error(exc: Exception) -> bool:
        message = str(exc).lower()
        class_name = exc.__class__.__name__.lower()
        keywords = ("model", "unknown", "unrecognized", "not_found", "unsupported")
        if any(k in message for k in keywords):
            return True
        return any(k in class_name for k in ("model", "notfound"))

    def _call_completions_api(
        self,
        chosen_model: str,
        prompt: str,
        max_tokens: int,
        extra_kwargs: Dict[str, Any],
    ) -> Any:
        if not self.client:
            raise RuntimeError("Anthropic client not configured")

        resource = getattr(self.client, "completions", None)
        create_fn = getattr(resource, "create", None) if resource else None
        if create_fn is None:
            raise AttributeError("Anthropic client does not expose completions.create")

        payload = dict(extra_kwargs)
        payload["model"] = chosen_model
        payload.setdefault("prompt", prompt)
        if "max_tokens_to_sample" not in payload and "max_tokens" not in payload:
            payload["max_tokens_to_sample"] = max_tokens

        try:
            return create_fn(**payload)
        except TypeError:
            # Retry with the alternate keyword some SDKs expect.
            payload.pop("max_tokens_to_sample", None)
            payload["max_tokens"] = max_tokens
            return create_fn(**payload)

    def _invoke_with_model(
        self,
        chosen_model: str,
        structured_messages: List[Dict[str, Any]],
        system_text: Optional[str],
        prompt: str,
        max_tokens: int,
        extra_kwargs: Dict[str, Any],
    ) -> Any:
        message_exc: Optional[Exception] = None

        if self._has_messages_api():
            try:
                return self._call_messages_api(
                    chosen_model,
                    structured_messages,
                    system_text,
                    max_tokens,
                    extra_kwargs,
                )
            except Exception as exc:
                if self._is_model_error(exc):
                    raise
                logger.debug("Messages API call failed, falling back to completions: %s", exc)
                message_exc = exc

        if self._has_completions_api():
            return self._call_completions_api(chosen_model, prompt, max_tokens, extra_kwargs)

        if message_exc:
            raise message_exc
        raise RuntimeError("Anthropic client does not expose a supported API surface")

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        config = config or {}
        super().__init__(config)
        api_key = config.get("api_key") or os.getenv(API_KEY_ENV)
        if not api_key:
            # Do not raise here to allow offline unit tests that mock the SDK
            logger.debug("Anthropic API key not provided; provider will be unavailable until set")
            self.client = None
        else:
            self.client = self._create_client(api_key)

        self.model = config.get("model") or DEFAULT_MODEL

    def _discover_and_set_model(self) -> Optional[str]:
        """Attempt to list available models from the SDK and set the first one found.

        Returns the discovered model id or None.
        """
        models = self._get_available_model_ids()
        if models:
            chosen = models[0]
            logger.info("Discovered Anthropic model '%s', switching to it", chosen)
            self.model = chosen
            return chosen
        return None

    def _call_messages_api(
        self,
        chosen_model: str,
        structured_messages: List[Dict[str, Any]],
        system_message: Optional[str],
        max_tokens: int,
        extra_kwargs: Dict[str, Any],
    ) -> Any:
        if not self.client:
            raise RuntimeError("Anthropic client not configured")

        resource = getattr(self.client, "messages", None)
        create_fn = getattr(resource, "create", None) if resource else None
        if create_fn is None:
            raise AttributeError("Anthropic client does not expose messages.create")

        payload = dict(extra_kwargs)
        payload.update(
            {
                "model": chosen_model,
                "messages": structured_messages,
                "max_tokens": max_tokens,
            }
        )
        if system_message:
            payload["system"] = system_message
        return create_fn(**payload)

    def get_type(self) -> ProviderType:
        return ProviderType.ANTHROPIC

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=False,
            supports_function_calling=False,
            supports_vision=False,
            max_context_length=200000,
            supported_formats=[self.model],
        )

    async def complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Generate a completion from Anthropic.

        This method builds a simple prompt from the incoming messages and calls the
        SDK surface if available. It normalizes the response into CompletionResponse.
        """
        if self.client is None:
            raise RuntimeError("Anthropic client not configured (missing API key or SDK)")

        system_msg, structured_messages = self._prepare_messages_payload(messages)
        prompt = self._build_completion_prompt(messages, system_msg)

        chosen_model = model or self.model
        extra_kwargs: Dict[str, Any] = dict(kwargs)
        if temperature is not None:
            extra_kwargs.setdefault("temperature", temperature)

        max_tokens_val = max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS

        resp_obj: Optional[Any] = None
        model_in_use = chosen_model
        last_exc: Optional[Exception] = None

        for attempt in range(2):
            try:
                resp_obj = self._invoke_with_model(
                    model_in_use,
                    structured_messages,
                    system_msg,
                    prompt,
                    max_tokens_val,
                    extra_kwargs,
                )
                break
            except Exception as exc:
                last_exc = exc
                if attempt == 0 and self._is_model_error(exc):
                    discovered = self._discover_and_set_model()
                    if discovered and discovered != model_in_use:
                        model_in_use = discovered
                        continue
                raise

        if resp_obj is None:
            if last_exc:
                raise last_exc
            raise RuntimeError("Anthropic client did not return a response")

        # After successful call (or after retry), extract text from response defensively
        text = getattr(resp_obj, "completion", None) or getattr(resp_obj, "text", None)
        if text is None and hasattr(resp_obj, "content"):
            try:
                content_blocks = getattr(resp_obj, "content")
                texts: List[str] = []
                for block in content_blocks:
                    block_text = getattr(block, "text", None)
                    if block_text is None and isinstance(block, dict):
                        block_text = block.get("text")
                    if block_text:
                        texts.append(block_text)
                if texts:
                    text = "\n".join(texts)
            except Exception:
                text = None
        if text is None:
            # Try dict-like access
            try:
                text = resp_obj["completion"]
            except Exception:
                text = str(resp_obj)

        def _lookup(source: Any, key: str) -> Any:
            if hasattr(source, key):
                return getattr(source, key)
            if isinstance(source, dict):
                return source.get(key)
            if hasattr(source, "__getitem__"):
                try:
                    return source[key]
                except Exception:
                    return None
            return None

        # Extract usage and finish reason if available
        usage = {}
        try:
            usage_obj = getattr(resp_obj, "usage", None)
            if usage_obj is None and hasattr(resp_obj, "__getitem__"):
                usage_obj = resp_obj["usage"]
            if usage_obj:
                prompt_tokens = _lookup(usage_obj, "prompt_tokens") or _lookup(usage_obj, "input_tokens")
                completion_tokens = _lookup(usage_obj, "completion_tokens") or _lookup(usage_obj, "output_tokens")
                total_tokens = _lookup(usage_obj, "total_tokens")
                usage = {
                    "prompt_tokens": int(prompt_tokens or 0),
                    "completion_tokens": int(completion_tokens or 0),
                    "total_tokens": int(total_tokens or (prompt_tokens or 0) + (completion_tokens or 0)),
                }
        except Exception:
            usage = {}

        finish_reason = getattr(resp_obj, "finish_reason", None) or getattr(resp_obj, "stop_reason", None)
        if finish_reason is None:
            try:
                finish_reason = resp_obj["finish_reason"]
            except Exception:
                try:
                    finish_reason = resp_obj["stop_reason"]
                except Exception:
                    finish_reason = None
        if finish_reason is None:
            finish_reason = "stop"

        return CompletionResponse(content=text, model=model_in_use, usage=usage, finish_reason=finish_reason)

    async def test_connection(self) -> bool:
        """Quick availability check. Attempts a no-op if possible, otherwise checks client presence."""
        if self.client is None:
            return False
        # If the SDK provides a simple ping or models.list, try to call it defensively
        try:
            if hasattr(self.client, "models") and hasattr(self.client.models, "list"):
                _ = self.client.models.list()
                return True
            # Otherwise assume configured client means okay
            return True
        except Exception:
            return False
