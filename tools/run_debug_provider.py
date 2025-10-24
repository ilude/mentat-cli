import importlib
import sys
from pathlib import Path

root = Path(r"c:/Projects/Personal/mentat-cli")
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

cli = importlib.import_module("mentat.cli")

if __name__ == "__main__":
    # call debug_provider
    try:
        import inspect
        import traceback

        print("mentat.cli file:", inspect.getsourcefile(cli))
        print("available attrs:", sorted([a for a in dir(cli) if not a.startswith("_")]))
        # Attempt to call debug_provider if present
        if hasattr(cli, "debug_provider"):
            try:
                cli.debug_provider()
            except Exception:
                traceback.print_exc()
        else:
            print("debug_provider not found on imported module")
    except SystemExit as e:
        print("Exited with", e)
    except Exception as e:
        print("Exception:", e)
