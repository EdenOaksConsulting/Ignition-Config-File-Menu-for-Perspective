#!/usr/bin/env python3
"""Fail if a view declares a param that 2.0.0 moved into the session object.

2.0.0 deleted the ``MenuContent`` view params and moved every setting into
``session.custom.configFileMenu``. A maintainer script kept writing the old params back:
``apply-menu-sample-config.py`` set ``MenuContent.params.menuConfig`` on every run, and the
builds that ran afterwards did not clean up, so the dead params would have shipped inside
the next library zip. Nothing caught it — the doc guard only reads Markdown.

Two rules:

1. **No view may declare a removed param.** ``REMOVED_VIEW_PARAMS`` lists the ones 2.0.0
   deleted from views.
2. **``MenuContent`` declares no params at all.** Its entire configuration surface moved to
   the session object, so an empty ``params`` is the correct end state and anything
   appearing there is a regression.

**``menuDockId`` is deliberately not listed.** It is a *live* input param on six views —
the runtime passes it to child instances (``cfm/breadcrumb.py``) after reading the session
key ``contentDockId``, and the shared-dock views bind it from
``{session.custom.configFileMenu.contentDockId}``. The session key is the configuration
surface; the param is internal plumbing. Only the config key was renamed.

Usage:
    python Config_File_Menu/scripts/verify_view_params.py
Exit code 0 = clean, 1 = a view carries a removed param.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
VIEWS = PROJECT_ROOT / "com.inductiveautomation.perspective" / "views"
MENU_CONTENT = VIEWS / "Config File Menu" / "MenuContent" / "view.json"

# View params removed by the 2.0.0 session-object refactor, mapped to what replaced them.
REMOVED_VIEW_PARAMS = {
    "menuConfig": "session.custom.configFileMenu.contentSource",
    "menuConfigType": "session.custom.configFileMenu.contentSourceType",
    "siteName": "session.custom.configFileMenu.brandSiteName",
    "logoLargePath": "session.custom.configFileMenu.brandLogoLarge",
    "logoSmallPath": "session.custom.configFileMenu.brandLogoSmall",
    "menuControlIsPinned": "session.custom.configFileMenu.dockPinned",
    "menuControlDockContentPush": "session.custom.configFileMenu.dockContentPush",
    "menuControlCloseOnOutsideClick": "session.custom.configFileMenu.dockCloseOnOutsideClick",
}


def view_files():
    return sorted(VIEWS.rglob("view.json"))


def _params(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    params = data.get("params")
    return params if isinstance(params, dict) else {}


def check_no_removed_params(paths=None):
    """No view may declare a param the refactor moved into the session object."""
    problems = []
    for path in view_files() if paths is None else paths:
        for name in sorted(_params(path)):
            if name in REMOVED_VIEW_PARAMS:
                problems.append(
                    "  %s\n      declares removed param `%s` — use %s"
                    % (_rel(path), name, REMOVED_VIEW_PARAMS[name])
                )
    if problems:
        return False, "Removed view param(s) present:\n" + "\n".join(problems)
    return True, "No removed view params."


def check_menu_content_has_no_params(path=None):
    """MenuContent's configuration surface moved to the session object entirely."""
    path = MENU_CONTENT if path is None else path
    if not path.is_file():
        return False, "Missing %s" % _rel(path)
    params = _params(path)
    if params:
        return False, (
            "%s declares params %s.\n"
            "MenuContent takes no params in 2.0.0 — all configuration lives on "
            "session.custom.configFileMenu. Something wrote them back."
            % (_rel(path), sorted(params))
        )
    return True, "MenuContent declares no params."


def _rel(path):
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def check():
    for fn in (check_no_removed_params, check_menu_content_has_no_params):
        ok, message = fn()
        if not ok:
            return False, message
    return True, "Views carry no removed configuration params."


def main():
    ok, message = check()
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
