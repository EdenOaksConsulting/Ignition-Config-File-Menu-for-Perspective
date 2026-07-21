"""Canonical menu sample paths and snippets."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_MENU_YAML_PATH = PROJECT_ROOT / "config" / "menuSampleConfig.yaml"
SAMPLE_MENU_JSON_PATH = PROJECT_ROOT / "config" / "menuSampleConfig.json"


def library_menu_stub(yaml_text: str | None = None) -> str:
    """Empty-items MenuContent param for the inheritable library."""
    return (
        "# Set your menu on the session custom property configFileMenu.contentSource\n"
        "# (Perspective -> Session Properties -> custom -> configFileMenu -> contentSource).\n"
        "menu:\n"
        "  items: []\n"
    )

ROUTES_OUTPUT_DEFAULT = '{\n  "_comment": "Generated routes appear here.",\n  "pages": {}\n}'


def load_sample_menu_yaml() -> str:
    return SAMPLE_MENU_YAML_PATH.read_text(encoding="utf-8")


def routes_input_snippet() -> str:
    """Short YAML prefix from the canonical sample for Settings text areas."""
    lines = load_sample_menu_yaml().splitlines()
    end = 0
    for idx, line in enumerate(lines):
        if line.strip().startswith("- label:") and idx > 0:
            end = idx + 4
            break
    if end <= 0:
        end = min(len(lines), 8)
    return "\n".join(lines[:end]).rstrip() + "\n"


def converter_input_snippet() -> str:
    return routes_input_snippet()
