"""View-param guard: views must not carry params the 2.0.0 refactor moved to the session.

Wraps ``scripts/verify_view_params.py``. See that module for why this exists — a maintainer
script was writing ``MenuContent.params.menuConfig`` back on every run, and the builds that
followed did not clean it up.
"""

import importlib.util
import json
from pathlib import Path


def _load_verifier():
    path = Path(__file__).resolve().parents[1] / "scripts" / "verify_view_params.py"
    spec = importlib.util.spec_from_file_location("verify_view_params", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFIER = _load_verifier()


def test_no_view_declares_a_removed_param():
    ok, message = VERIFIER.check_no_removed_params()
    assert ok, message


def test_menu_content_declares_no_params():
    ok, message = VERIFIER.check_menu_content_has_no_params()
    assert ok, message


def test_guard_catches_a_reintroduced_param(tmp_path):
    """The exact regression seen: a script writing menuConfig back onto a view."""
    view = tmp_path / "view.json"
    view.write_text(json.dumps({"params": {"menuConfig": "menu:\n  items: []\n"}}), encoding="utf-8")
    ok, message = VERIFIER.check_no_removed_params(paths=[view])
    assert not ok
    assert "menuConfig" in message
    assert "contentSource" in message, "message should name the replacement"


def test_guard_catches_params_on_menu_content(tmp_path):
    view = tmp_path / "view.json"
    view.write_text(json.dumps({"params": {"anything": 1}}), encoding="utf-8")
    ok, message = VERIFIER.check_menu_content_has_no_params(path=view)
    assert not ok
    assert "anything" in message


def test_menu_dock_id_is_not_treated_as_removed():
    """`menuDockId` is live plumbing, not removed config.

    The runtime passes it to child view instances after reading the session key
    `contentDockId`. Flagging it would fail on six shipped views.
    """
    assert "menuDockId" not in VERIFIER.REMOVED_VIEW_PARAMS
    ok, _ = VERIFIER.check_no_removed_params()
    assert ok
