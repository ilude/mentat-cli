from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class AnthropicConfig(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None


class ProvidersConfig(BaseModel):
    anthropic: Optional[AnthropicConfig] = None


class MentatConfig(BaseModel):
    tools_dir: Path = Field(default_factory=lambda: Path("tools"))
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    # future: add logging, profiles, etc.
