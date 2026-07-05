#!/usr/bin/env python3
"""Verify Advanced Stylesheet CSS matches the canonical merge snippet."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from build_paths import PROJECT_ROOT

CANONICAL = PROJECT_ROOT / "config" / "cfm-menu-theme-merge.css"
STYLESHEET = (
    PROJECT_ROOT
    / "com.inductiveautomation.perspective"
    / "stylesheet"
    / "stylesheet.css"
)

GENERATED_HEADER = re.compile(
    r"^/\* Config File Menu — Advanced Stylesheet.*?\*/\s*",
    re.DOTALL,
)


def stylesheet_body(text: str) -> str:
    return GENERATED_HEADER.sub("", text, count=1).strip()


def verify() -> None:
    if not CANONICAL.is_file():
        raise SystemExit(f"Missing canonical CSS: {CANONICAL}")
    if not STYLESHEET.is_file():
        raise SystemExit(
            f"Missing Advanced Stylesheet CSS: {STYLESHEET}\n"
            "Run: python scripts/build-hmi-menu-sample.py"
        )
    canonical = CANONICAL.read_text(encoding="utf-8").strip()
    generated = stylesheet_body(STYLESHEET.read_text(encoding="utf-8"))
    if canonical != generated:
        raise SystemExit(
            "Advanced Stylesheet out of sync with config/cfm-menu-theme-merge.css.\n"
            "Run: python scripts/build-hmi-menu-sample.py"
        )
    print(f"Verified Advanced Stylesheet matches canonical ({CANONICAL.name})")


if __name__ == "__main__":
    verify()
    sys.exit(0)
