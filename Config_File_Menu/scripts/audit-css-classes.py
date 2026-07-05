#!/usr/bin/env python3
"""Report drift between CFM view classes and canonical CSS selectors."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from build_paths import PROJECT_ROOT

VIEWS_ROOT = PROJECT_ROOT / "com.inductiveautomation.perspective" / "views" / "Config File Menu"
CANONICAL_CSS = PROJECT_ROOT / "config" / "cfm-menu-theme-merge.css"
SCRIPT_ROOT = PROJECT_ROOT / "scripts"

CLASS_RE = re.compile(r"\bcfm-[A-Za-z0-9_-]+")
CSS_SELECTOR_RE = re.compile(r"\.psc-(cfm-[A-Za-z0-9_-]+)")


def is_style_class(value: str) -> bool:
    return (
        value == "cfm-menu"
        or value.startswith("cfm-menu--")
        or value.startswith("cfm-menu__")
        or value.startswith("cfm-page__")
        or value.startswith("cfm-diag__")
    )


def clean_classes(values: set[str]) -> set[str]:
    return {
        value
        for value in values
        if is_style_class(value) and not value.endswith("--") and not value.endswith("__")
    }


def collect_json_classes(path: Path) -> set[str]:
    def walk(value: object, found: set[str]) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child, found)
        elif isinstance(value, list):
            for child in value:
                walk(child, found)
        elif isinstance(value, str):
            found.update(CLASS_RE.findall(value))

    data = json.loads(path.read_text(encoding="utf-8"))
    classes: set[str] = set()
    walk(data, classes)
    return clean_classes(classes)


def collect_script_classes(path: Path) -> set[str]:
    classes: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if "cfm-" in line:
            classes.update(CLASS_RE.findall(line))
    return clean_classes(classes)


def collect_used_classes() -> set[str]:
    used: set[str] = set()
    for view_json in VIEWS_ROOT.rglob("view.json"):
        used.update(collect_json_classes(view_json))
    for script in SCRIPT_ROOT.rglob("*.py"):
        used.update(collect_script_classes(script))
    return used


def collect_css_classes() -> set[str]:
    return set(CSS_SELECTOR_RE.findall(CANONICAL_CSS.read_text(encoding="utf-8")))


def print_section(title: str, values: set[str]) -> None:
    print(title)
    if not values:
        print("  none")
        return
    for value in sorted(values):
        print(f"  {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit non-zero when unused CSS or classes without CSS are found.",
    )
    args = parser.parse_args()

    used = collect_used_classes()
    css = collect_css_classes()
    unused_css = css - used
    missing_css = used - css

    print(f"View/build classes: {len(used)}")
    print(f"Canonical CSS classes: {len(css)}")
    print_section("\nCSS selectors with no extracted class usage:", unused_css)
    print_section("\nExtracted classes with no canonical CSS selector:", missing_css)

    return 1 if args.fail_on_drift and (unused_css or missing_css) else 0


if __name__ == "__main__":
    raise SystemExit(main())
