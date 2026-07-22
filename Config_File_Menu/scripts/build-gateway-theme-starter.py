#!/usr/bin/env python3
"""Build cfm-gateway-theme-starter.zip for Ignition 8.3+ host integration."""

from __future__ import annotations

import shutil
import uuid
import zipfile
from pathlib import Path

from build_paths import DIST_ROOT, PROJECT_ROOT, STAGING_ROOT

STARTER_DIR = PROJECT_ROOT / "config" / "gateway-theme-cfm-light"
MERGE_CSS = PROJECT_ROOT / "config" / "cfm-menu-theme-merge.css"
OUTPUT_ZIP = DIST_ROOT / "cfm-gateway-theme-starter.zip"


def build_gateway_theme_starter() -> Path:
    if not STARTER_DIR.is_dir():
        raise SystemExit(f"Missing gateway theme starter: {STARTER_DIR}")
    if not MERGE_CSS.is_file():
        raise SystemExit(f"Missing merge CSS: {MERGE_CSS}")

    # Stage outside dist/ (STAGING_ROOT is under the system temp dir), matching
    # build-inheritance-zips.py. This used to stage in `dist/staging/` and remove only the
    # inner folder, so every run left an empty `dist/staging/` behind and an interrupted
    # run left its whole tree there — dist/ should hold nothing but the shipping zips.
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)
    staging = STAGING_ROOT / f"gateway-theme-{uuid.uuid4().hex[:8]}"
    shutil.copytree(STARTER_DIR, staging)
    shutil.copy2(MERGE_CSS, staging / "cfm-menu-theme-merge.css")

    OUTPUT_ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(staging.rglob("*")):
            if file_path.is_file():
                arcname = f"gateway-theme-cfm-light/{file_path.relative_to(staging).as_posix()}"
                archive.write(file_path, arcname)

    shutil.rmtree(staging, ignore_errors=True)
    print(f"Wrote {OUTPUT_ZIP}")
    return OUTPUT_ZIP


if __name__ == "__main__":
    build_gateway_theme_starter()
