from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class MentatConfig(BaseModel):
    tools_dir: Path = Field(default_factory=lambda: Path("tools"))
    # future: add logging, profiles, etc.
