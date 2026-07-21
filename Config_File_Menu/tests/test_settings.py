"""Tests for cfm.settings pure helpers (menu/route generators, YAML emit)."""


def test_tag_slugify(cfm):
    s = cfm.settings._tag_slugify
    assert s("Area 1") == "area-1"
    assert s("Plant/Room A") == "plant-room-a"
    assert s("HVAC_Unit") == "hvac-unit"
    assert s("   ") == "item"          # empty after strip -> fallback
    assert s("!!!") == "item"          # nothing alphanumeric -> fallback
    assert s(None) == "item"


def test_slug_to_title(cfm):
    s = cfm.settings._slug_to_title
    assert s("area-1") == "Area 1"
    assert s("plant_room") == "Plant Room"
    assert s("io") == "Io"             # plain title-case (see _fallback_title for IO special case)
    assert s("") == "Page"
    assert s(None) == "Page"


def test_target_to_view_path(cfm):
    t = cfm.settings.target_to_view_path
    assert t("/cfm/plant/area-1") == "Plant/Area 1"
    assert t("cfm/plant/area-1") == "Plant/Area 1"      # leading slash added
    assert t("/cfm") == "Page"                          # only the prefix -> Page
    assert t("/other/page") == "Other/Page"             # prefix not matched, kept
    # custom prefix
    assert t("/app/dash", path_prefix="app") == "Dash"


def test_yaml_quote(cfm):
    q = cfm.settings._yaml_quote
    assert q("") == '""'
    assert q("plain") == "plain"
    assert q("has space") == "has space"
    assert q("a:b") == '"a:b"'          # colon is special
    assert q("area-1") == '"area-1"'    # dash is special
    assert q(None) == '""'


def test_emit_yaml_simple_item_roundtrips(cfm):
    items = [{"label": "Home", "target": "/home"}]
    text = cfm.settings._emit_yaml(items)
    assert "- label: Home" in text
    # The emitted YAML parses back to the same label/target via the lite parser.
    parsed = cfm.config.parse_yaml_lite("items:\n" + "\n".join("  " + ln for ln in text.splitlines()))
    reparsed = parsed.get("items") if isinstance(parsed, dict) else parsed
    assert reparsed[0]["label"] == "Home"


def test_emit_yaml_empty_list(cfm):
    assert cfm.settings._emit_yaml([]) == "[]"


def test_walk_menu_builds_routes_with_trail(cfm):
    items = [
        {"label": "Home", "target": "/home"},
        {"label": "Plant", "children": [
            {"label": "Area 1", "target": "/plant/area-1"},
        ]},
    ]
    routes = cfm.settings._walk_menu(items, [])
    assert ("/home", "Home") in routes
    assert ("/plant/area-1", "Plant - Area 1") in routes
    # Plant itself has no target, so it produces no route of its own
    assert not any(title == "Plant" for _, title in routes)


def test_walk_menu_prepends_slash_and_skips_non_dicts(cfm):
    items = [{"label": "Bare", "target": "bare"}, "not-a-dict", {"no": "label"}]
    routes = cfm.settings._walk_menu(items, [])
    assert ("/bare", "Bare") in routes
    # The label-less dict has no target -> no route; the string is skipped.
    assert len(routes) == 1


def test_walk_menu_empty(cfm):
    assert cfm.settings._walk_menu([], []) == []
    assert cfm.settings._walk_menu(None, None) == []


def test_load_menu_yaml_and_json(cfm):
    yaml_items = cfm.settings._load_menu("menu:\n  items:\n    - label: A\n", "yaml")
    assert yaml_items[0]["label"] == "A"
    json_items = cfm.settings._load_menu('{"items": [{"label": "B"}]}', "json")
    assert json_items[0]["label"] == "B"


def test_load_menu_bare_and_empty(cfm):
    assert cfm.settings._load_menu("", "yaml") == []
    # A list at the root is returned as-is.
    assert cfm.settings._load_menu('[{"label": "C"}]', "json") == [{"label": "C"}]
