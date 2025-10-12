from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Optional

from .models import MentatConfig


def load_config(config_path: Optional[Path] = None) -> MentatConfig:
    """Load Mentat configuration from TOML if present; else defaults.

    Looks for `config/mentat.toml` by default relative to CWD.
    """
    if config_path is None:
        config_path = Path("config") / "mentat.toml"

    if config_path.exists():
        with config_path.open("rb") as f:
            data = tomllib.load(f)
        cfg = MentatConfig(**data)
        # normalize to absolute Path
        cfg.tools_dir = Path(cfg.tools_dir)
        return cfg

    return MentatConfig()
