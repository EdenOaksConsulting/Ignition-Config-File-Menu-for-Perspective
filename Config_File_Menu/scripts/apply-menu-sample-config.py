#!/usr/bin/env python3
"""Sync config/menuSampleConfig.yaml into derived JSON and embedded view defaults."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from menu_samples import SAMPLE_MENU_JSON_PATH, load_sample_menu_yaml
from yaml_lite import write_menu_sample_json

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# A `patch_view_menu_config` step used to run here, writing the library stub into
# `MenuContent.params.menuConfig` / `.menuConfigType`. Those params were removed in 2.0.0 —
# the menu now lives in `session.custom.configFileMenu.contentSource`, written into the
# session-props resource by build-hmi-menu-sample.py. The step was not just obsolete but
# harmful: it reintroduced the dead params into the shipped view, and the builds invoked
# below did not clean them, so they would have shipped in the next library zip.


def main() -> None:
    menu_yaml = load_sample_menu_yaml()
    write_menu_sample_json(menu_yaml, SAMPLE_MENU_JSON_PATH)
    print(f"Wrote {SAMPLE_MENU_JSON_PATH.relative_to(PROJECT_ROOT)}")

    for script_name in ("build-settings-generator-tabs.py", "build-hmi-menu-sample.py"):
        script = PROJECT_ROOT / "scripts" / script_name
        subprocess.run([sys.executable, str(script)], check=True)

    print("Synced menu sample YAML into JSON, MenuContent, and Settings tab defaults.")


if __name__ == "__main__":
    main()
