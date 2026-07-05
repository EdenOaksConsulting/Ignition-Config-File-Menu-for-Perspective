#!/usr/bin/env python3
"""Sync config/menuSampleConfig.yaml into derived JSON and embedded view defaults."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from menu_samples import (
    SAMPLE_MENU_JSON_PATH,
    load_sample_menu_yaml,
    library_menu_stub,
)
from yaml_lite import write_menu_sample_json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MENU_CONTENT = (
    PROJECT_ROOT
    / "com.inductiveautomation.perspective"
    / "views"
    / "Config File Menu"
    / "MenuContent"
    / "view.json"
)


def patch_view_menu_config(view_path: Path, menu_yaml: str) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    data["params"]["menuConfig"] = menu_yaml.strip() + "\n"
    data["params"].setdefault("menuConfigType", "yaml")
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    menu_yaml = load_sample_menu_yaml()
    write_menu_sample_json(menu_yaml, SAMPLE_MENU_JSON_PATH)
    patch_view_menu_config(MENU_CONTENT, library_menu_stub(menu_yaml))
    print(f"Wrote {SAMPLE_MENU_JSON_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Patched {MENU_CONTENT.relative_to(PROJECT_ROOT)} params.menuConfig (library stub)")

    for script_name in ("build-settings-generator-tabs.py", "build-hmi-menu-sample.py"):
        script = PROJECT_ROOT / "scripts" / script_name
        subprocess.run([sys.executable, str(script)], check=True)

    print("Synced menu sample YAML into JSON, MenuContent, and Settings tab defaults.")


if __name__ == "__main__":
    main()
