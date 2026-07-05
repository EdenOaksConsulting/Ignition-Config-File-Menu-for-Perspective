#!/usr/bin/env python3
"""Build Config File Menu library + site + sample import zips."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    script = PROJECT_ROOT / "scripts" / "build-inheritance-zips.py"
    subprocess.run([sys.executable, str(script)], check=True)


if __name__ == "__main__":
    main()
