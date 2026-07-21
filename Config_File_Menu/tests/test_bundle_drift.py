"""Bundle-drift guard: the committed code.py must match the cfm source modules.

Wraps ``scripts/verify_script_library.py`` so the check runs as part of pytest. If a
source module is edited without running ``build_script_library.py``, this fails.
"""

import importlib.util
from pathlib import Path


def _load_verifier():
    path = Path(__file__).resolve().parents[1] / "scripts" / "verify_script_library.py"
    spec = importlib.util.spec_from_file_location("verify_script_library", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bundle_in_sync_with_source():
    ok, message = _load_verifier().check()
    assert ok, message
