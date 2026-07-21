"""Tests for cfm.menu pure helpers (title/label/icon lookup, link classes)."""

import pytest

MENU = [
    {"label": "Home", "target": "/home", "icon": "material/home"},
    {"label": "Plant", "children": [
        {"label": "Area 1", "target": "/plant/area-1", "icon": "material/factory"},
        {"label": "Nested", "items": [
            {"label": "Deep", "target": "/plant/deep", "icon": "material/layers"},
        ]},
    ]},
]


def test_find_label(cfm):
    assert cfm.menu._find_label(MENU, "/home") == "Home"
    assert cfm.menu._find_label(MENU, "/plant/area-1") == "Area 1"
    assert cfm.menu._find_label(MENU, "/plant/deep") == "Deep"   # deep nesting via items:
    assert cfm.menu._find_label(MENU, "/missing") == ""
    assert cfm.menu._find_label([], "/home") == ""


def test_find_icon(cfm):
    assert cfm.menu._find_icon(MENU, "/home") == "material/home"
    assert cfm.menu._find_icon(MENU, "/plant/area-1") == "material/factory"
    assert cfm.menu._find_icon(MENU, "/plant/deep") == "material/layers"
    assert cfm.menu._find_icon(MENU, "/missing") == ""


def test_fallback_title(cfm):
    t = cfm.menu._fallback_title
    assert t("/plant/area-1") == "Area 1"
    assert t("/io") == "IO"              # the io -> IO special case
    assert t("/plant/io") == "IO"
    assert t("/dashboard") == "Dashboard"
    assert t("") == "HMI Page"
    assert t(None) == "HMI Page"
    assert t("/") == "HMI Page"


@pytest.mark.parametrize("page,target,expected", [
    ("/a", "/a", "cfm-menu__link--selected"),
    ("a", "/a", "cfm-menu__link--selected"),   # both normalized
    ("/a", "/b", ""),
    ("/a", "", ""),                             # empty target never selected
    ("", "/a", ""),
])
def test_menu_link_classes(cfm, page, target, expected):
    assert cfm.menu.menu_link_classes(page, target) == expected
