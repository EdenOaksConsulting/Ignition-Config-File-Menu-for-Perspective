"""Shared paths for Config File Menu build scripts."""

from __future__ import annotations

import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
DIST_ROOT = REPO_ROOT / "dist"
STAGING_ROOT = Path(tempfile.gettempdir()) / "cfm-dist-staging"

LIBRARY_ZIP = DIST_ROOT / "config-file-menu-library.zip"
SITE_ZIP = DIST_ROOT / "config-file-menu-site.zip"
SAMPLE_ZIP = DIST_ROOT / "config-file-menu-sample.zip"
