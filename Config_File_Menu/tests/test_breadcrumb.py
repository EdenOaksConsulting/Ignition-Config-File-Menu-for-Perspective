"""Tests for cfm.breadcrumb pure helpers (path->target/label lookup, home)."""


MENU = [
    {"label": "Plant", "target": "/plant", "children": [
        {"label": "Area 1", "target": "/plant/area-1"},
    ]},
    {"label": "Home", "target": "/home"},
]


def _target_lookup(cfm):
    lookup = {}
    cfm.breadcrumb._add_lookup(MENU, [], lookup)
    return lookup


def _label_lookup(cfm):
    lookup = {}
    cfm.breadcrumb._add_label_lookup(MENU, [], lookup)
    return lookup


def test_add_lookup_keys_by_slug_trail(cfm):
    lookup = _target_lookup(cfm)
    assert lookup[("plant",)] == "/plant"
    assert lookup[("plant", "area-1")] == "/plant/area-1"
    assert lookup[("home",)] == "/home"


def test_menu_target_for_suffix_match(cfm):
    lookup = _target_lookup(cfm)
    assert cfm.breadcrumb._menu_target_for(["plant", "area-1"], lookup) == "/plant/area-1"
    # A leading unmatched segment still resolves by suffix.
    assert cfm.breadcrumb._menu_target_for(["x", "plant", "area-1"], lookup) == "/plant/area-1"
    assert cfm.breadcrumb._menu_target_for(["nope"], lookup) == ""


def test_add_label_lookup_and_label_for(cfm):
    lookup = _label_lookup(cfm)
    assert lookup[("plant", "area-1")] == "Area 1"
    assert cfm.breadcrumb._menu_label_for(["plant", "area-1"], lookup) == "Area 1"
    assert cfm.breadcrumb._menu_label_for(["missing"], lookup) == ""


def test_home_target_root_in_pages(cfm):
    assert cfm.breadcrumb._home_target_for(MENU, "cfm", ["/", "/home"]) == "/"


def test_home_target_prefers_home_label(cfm):
    # No "/" page: falls back to the item labelled "home" whose target is registered.
    assert cfm.breadcrumb._home_target_for(MENU, "cfm", ["/home", "/plant"]) == "/home"


def test_home_target_first_registered_target(cfm):
    # No "/" and no "home" label: first item whose target is a registered page.
    menu = [{"label": "Dash", "target": "/plant"}]
    assert cfm.breadcrumb._home_target_for(menu, "cfm", ["/plant"]) == "/plant"


def test_home_target_prefix_dashboard_fallback(cfm):
    assert cfm.breadcrumb._home_target_for([], "cfm", ["/cfm/dashboard"]) == "/cfm/dashboard"


def test_home_target_none(cfm):
    assert cfm.breadcrumb._home_target_for([], "cfm", ["/unrelated"]) == ""


def test_home_target_shell_fallback_returns_root(cfm):
    # With shell fallback on, any target resolves; root wins.
    assert cfm.breadcrumb._home_target_for(MENU, "cfm", [], shell_fallback=True) == "/"
