#!/usr/bin/env python3
"""Fail if the committed runtime bundle is out of sync with the cfm source modules.

The deployed runtime (``ignition/script-python/exchange/cfm/runtime/code.py``) is
generated from ``scripts/jython_lib/cfm/*.py`` by ``build_script_library.py``. This
check regenerates the bundle in memory and compares it (line-endings normalized) to
the committed file, so a source edit that was not followed by a rebuild is caught.

Usage:
    python Config_File_Menu/scripts/verify_script_library.py
Exit code 0 = in sync, 1 = drift (message tells you to run the bundler).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REBUILD_HINT = "python Config_File_Menu/scripts/build_script_library.py"


def _load_bundler():
    spec = importlib.util.spec_from_file_location(
        "build_script_library", str(SCRIPTS_DIR / "build_script_library.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check():
    """Return (ok: bool, message: str)."""
    bundler = _load_bundler()
    expected = bundler.build_runtime_source().replace("\r\n", "\n")
    code_py = bundler.DEST_ROOT / "code.py"
    if not code_py.is_file():
        return False, "Missing bundle %s. Run: %s" % (code_py, REBUILD_HINT)
    actual = code_py.read_text(encoding="utf-8").replace("\r\n", "\n")
    if actual == expected:
        return True, "Bundle code.py is in sync with the cfm source modules."
    return False, (
        "Bundle code.py is OUT OF SYNC with the cfm source modules.\n"
        "A source module changed without regenerating the bundle. Run:\n    " + REBUILD_HINT
    )


def main():
    ok, message = check()
    print(message)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
