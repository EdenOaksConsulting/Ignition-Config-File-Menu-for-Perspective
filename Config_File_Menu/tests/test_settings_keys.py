"""Consistency between the Settings-owned key list, what init seeds, and props.json.

Three sources must agree on the ``configFileMenu`` keys the Settings shell manages:
  1. ``SETTINGS_SHELL_OWNED_KEYS`` in settings.py (what gets written back),
  2. the keys ``init_settings_shell_state`` actually seeds (directly + via the
     ensure_* helpers in menu.py),
  3. the defaults shipped in session-props/props.json.

Drift between them causes a key to silently not persist or not ship a default.
"""

import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "scripts" / "jython_lib" / "cfm"
PROPS = (
    Path(__file__).resolve().parents[1]
    / "com.inductiveautomation.perspective"
    / "session-props"
    / "props.json"
)

# configFileMenu keys the Settings shell owns and seeds but that are NOT shipped as
# defaults in props.json: they are nested generator "scratch" objects, created lazily
# on first use of the Tag->Menu / Menu->Routes tools rather than shipped up front.
LAZY_NOT_SHIPPED = {"settingsTagMenu", "settingsMenuRoutes"}


def _shipped_keys():
    data = json.loads(PROPS.read_text(encoding="utf-8"))
    return set(data["custom"]["configFileMenu"].keys())


def _func_body(source, name):
    match = re.search(r"\ndef " + re.escape(name) + r"\(", source)
    assert match, "function %s not found" % name
    rest = source[match.start() + 1:]
    nxt = re.search(r"\ndef ", rest)
    return rest[: nxt.start()] if nxt else rest


def _seed_keys_in(body):
    keys = set(re.findall(r'setdefault\("([^"]+)"', body))
    keys |= set(re.findall(r'state\["([^"]+)"\]\s*=', body))
    return keys


def _seeded_keys():
    settings_src = (SRC / "settings.py").read_text(encoding="utf-8")
    menu_src = (SRC / "menu.py").read_text(encoding="utf-8")
    keys = _seed_keys_in(_func_body(settings_src, "init_settings_shell_state"))
    # init delegates the show* toggles to these helpers:
    keys |= _seed_keys_in(_func_body(menu_src, "ensure_show_topbar_small_logo_state"))
    keys |= _seed_keys_in(_func_body(menu_src, "ensure_footer_visibility_state"))
    return keys


def test_owned_keys_ship_as_defaults(cfm):
    shipped = _shipped_keys()
    owned = set(cfm.settings.SETTINGS_SHELL_OWNED_KEYS)
    missing = (owned - LAZY_NOT_SHIPPED) - shipped
    assert not missing, "Settings-owned keys missing a default in props.json: %s" % sorted(missing)


def test_seeded_matches_owned(cfm):
    owned = set(cfm.settings.SETTINGS_SHELL_OWNED_KEYS)
    seeded = _seeded_keys()
    # Every owned key must actually be seeded, or it never gets a default written.
    assert owned <= seeded, "Owned but never seeded by init: %s" % sorted(owned - seeded)
    # Every seeded key must be declared owned, or the owned-keys write silently drops it.
    assert seeded <= owned, "Seeded but not in SETTINGS_SHELL_OWNED_KEYS: %s" % sorted(seeded - owned)


def test_lazy_scratch_keys_are_not_shipped(cfm):
    # Guard the documented exception: the scratch objects must stay out of props.json.
    shipped = _shipped_keys()
    assert LAZY_NOT_SHIPPED.isdisjoint(shipped), (
        "Scratch keys unexpectedly shipped as defaults: %s"
        % sorted(LAZY_NOT_SHIPPED & shipped)
    )
