from __future__ import annotations

import sys
from pathlib import Path

# Ensure `src` is on sys.path for test imports when running in isolated envs
root = Path(__file__).resolve().parents[1]
src_dir = root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
