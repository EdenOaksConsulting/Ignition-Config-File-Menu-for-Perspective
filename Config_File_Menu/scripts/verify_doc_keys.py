#!/usr/bin/env python3
"""Fail if the docs reference configuration keys that no longer exist.

The 2.0.0 refactor moved every setting into ``session.custom.configFileMenu`` and deleted
the old ``MenuContent`` view params and flat state keys. The docs were not swept at the
same time, so v2.0.0 shipped with an install checklist telling readers to inspect
``params.menuConfigType`` — a param the same release removes. This check makes that class
of drift fail loudly instead of reaching downloaders.

Two rules:

1. **Every ``configFileMenu.<key>`` mentioned in a doc must exist** in the shipped
   ``session-props`` resource, which is the authoritative key list.
2. **No doc may mention a removed name.** ``REMOVED_NAMES`` maps each to its replacement,
   so the failure tells you what to write instead.

``CHANGELOG.md`` and ``EXCHANGE_SUBMISSION.md`` are exempt: documenting the old names is
exactly their job (migration notes and the listing's upgrade warning).

Usage:
    python Config_File_Menu/scripts/verify_doc_keys.py
Exit code 0 = clean, 1 = a doc references something that no longer exists.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent

SESSION_PROPS = (
    PROJECT_ROOT / "com.inductiveautomation.perspective" / "session-props" / "props.json"
)
RUNTIME_BUNDLE = (
    PROJECT_ROOT / "ignition" / "script-python" / "exchange" / "cfm" / "runtime" / "code.py"
)

# Some keys are declared in session-props; others are created on first run by
# `state.setdefault(...)` in the runtime. Both are real, so the valid set is their union —
# checking props.json alone reports live keys like `settingsTagMenu` as unknown.
SETDEFAULT = re.compile(r'state\.setdefault\("([A-Za-z_][A-Za-z0-9_]*)"')

# Docs that legitimately name the old keys.
EXEMPT = {"CHANGELOG.md", "EXCHANGE_SUBMISSION.md"}

# Removed name -> what to write instead (None where the concept is simply gone).
REMOVED_NAMES = {
    "menuConfig": "contentSource",
    "menuConfigType": "contentSourceType",
    "menuDockId": "contentDockId",
    "siteName": "brandSiteName",
    "menuWidthOpen": "layoutWidthOpen",
    "isPinned": "dockPinned",
    "dockContent": "dockContentPush",
    "dockMode": "dockOpen",
    "menuMode": "dockOpen",
    "logicalPagePath": "routeLogicalPath",
    "shellFallbackEnabled": "routeFallbackEnabled",
    "shellFallbackRoute": "routeFallbackPath",
    "tagMenuGenerator": "settingsTagMenu",
    "menuRoutesGenerator": "settingsMenuRoutes",
    "brandLogoVariant": None,     # replaced by showMenuLogo / showTopBarSmallLogo
    "menuControl": None,          # the three menuControl* session props are gone
    "MenuContent.params": None,   # view params were removed wholesale
}

KEY_REFERENCE = re.compile(r"configFileMenu\.(\w+)")


def current_keys():
    """Declared session-props keys plus the ones the runtime creates via setdefault."""
    data = json.loads(SESSION_PROPS.read_text(encoding="utf-8"))
    keys = set(data["custom"]["configFileMenu"].keys())
    keys.update(SETDEFAULT.findall(RUNTIME_BUNDLE.read_text(encoding="utf-8")))
    return keys


def doc_files():
    """Every Markdown doc in the project, minus the exempt ones."""
    found = [REPO_ROOT / "README.md"]
    found.extend(sorted(PROJECT_ROOT.rglob("*.md")))
    return [
        p for p in found
        if p.is_file() and p.name not in EXEMPT and "docs/archive" not in p.as_posix()
    ]


def _removed_name_pattern(name):
    # `MenuContent.params` contains a dot; match it literally. Bare names get word
    # boundaries so `menuConfig` does not fire on `menuConfigType` (both are listed
    # separately, and the longer one should report its own replacement).
    #
    # The lookbehind deliberately allows a preceding dot: `params.menuConfig` is exactly
    # the drift being hunted, and excluding dots hid five hits in the import checklist.
    if "." in name:
        return re.compile(re.escape(name))
    return re.compile(r"(?<!\w)" + re.escape(name) + r"(?![\w])")


def _display_path(path):
    """Repo-relative where possible; the plain path otherwise (callers may pass any file)."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def scan(paths=None, keys=None):
    """Return a list of (relative_path, line_no, line, problem) findings."""
    keys = current_keys() if keys is None else keys
    paths = doc_files() if paths is None else paths
    patterns = [(n, r, _removed_name_pattern(n)) for n, r in REMOVED_NAMES.items()]

    findings = []
    for path in paths:
        rel = _display_path(path)
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in KEY_REFERENCE.finditer(line):
                key = match.group(1)
                if key not in keys:
                    findings.append((rel, number, line.strip(), "unknown key `%s`" % key))
            for name, replacement, pattern in patterns:
                if pattern.search(line):
                    hint = (
                        "use `%s`" % replacement if replacement
                        else "removed with no direct replacement"
                    )
                    findings.append(
                        (rel, number, line.strip(), "removed `%s` — %s" % (name, hint))
                    )
    return findings


def check():
    findings = scan()
    if not findings:
        return True, "No stale configuration keys in the docs."
    lines = ["%d stale key reference(s) in the docs:" % len(findings), ""]
    for rel, number, line, problem in findings:
        excerpt = line if len(line) <= 96 else line[:93] + "..."
        lines.append("  %s:%d  %s" % (rel, number, problem))
        lines.append("      %s" % excerpt)
    lines.append("")
    lines.append("The shipped session-props resource is the source of truth: %s"
                 % SESSION_PROPS.relative_to(REPO_ROOT).as_posix())
    return False, "\n".join(lines)


def main():
    ok, message = check()
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
