"""Tests for cfm.config pure helpers."""

import types


def test_is_true_truthy(cfm):
    for v in (True, "true", "TRUE", "1", "yes", "Yes", "on", "ON"):
        assert cfm.config.is_true(v) is True, v


def test_is_true_falsy(cfm):
    for v in (False, "false", "no", "off", "", "0", None, "maybe", "2"):
        assert cfm.config.is_true(v) is False, v


def test_scalar_keywords_and_quotes(cfm):
    s = cfm.config.scalar
    assert s("true") is True
    assert s("YES") is True
    assert s("off") is False
    assert s("null") is None
    assert s("None") is None
    assert s('"hello"') == "hello"
    assert s("'world'") == "world"
    assert s("42") == "42"          # non-keyword scalars stay strings
    assert s("  spaced  ") == "spaced"
    assert s("") == ""
    assert s(None) == ""


def test_clean_lines_strips_comments_and_blanks(cfm):
    text = "menu:\n  # a comment\n\n  items: []\n"
    lines = cfm.config.clean_lines(text)
    assert lines == [(0, "menu:"), (2, "items: []")]


def test_parse_yaml_lite_empty_uses_default_root(cfm):
    assert cfm.config.parse_yaml_lite("") == {"menu": {"items": []}}
    assert cfm.config.parse_yaml_lite("   \n # only comment\n") == {"menu": {"items": []}}


def test_parse_yaml_lite_custom_empty_root(cfm):
    assert cfm.config.parse_yaml_lite("", empty_root={"items": []}) == {"items": []}


def test_parse_yaml_lite_nested_children(cfm):
    text = (
        "menu:\n"
        "  items:\n"
        "    - label: Home\n"
        "      target: /home\n"
        "    - label: Plant\n"
        "      children:\n"
        "        - label: Area 1\n"
        "          target: /plant/area-1\n"
    )
    parsed = cfm.config.parse_yaml_lite(text)
    items = parsed["menu"]["items"]
    assert [i["label"] for i in items] == ["Home", "Plant"]
    assert items[0]["target"] == "/home"
    plant_children = items[1]["children"]
    assert plant_children[0]["label"] == "Area 1"
    assert plant_children[0]["target"] == "/plant/area-1"


def test_parse_yaml_lite_ignores_comment_lines(cfm):
    text = "# leading comment\nmenu:\n  items:\n    - label: Only\n"
    items = cfm.config.parse_yaml_lite(text)["menu"]["items"]
    assert [i["label"] for i in items] == ["Only"]


def test_normalize_path(cfm):
    n = cfm.config.normalize_path
    assert n("") == ""
    assert n(None) == ""
    assert n("a") == "/a"
    assert n("/a/b") == "/a/b"
    assert n("//a//b//") == "/a/b"     # collapse double slashes + trailing strip
    assert n("/a/b/") == "/a/b"
    assert n("/") == "/"
    assert n("///") == "/"


def test_slug(cfm):
    assert cfm.config.slug("Area 1") == "area-1"
    assert cfm.config.slug("  Plant Room  ") == "plant-room"
    assert cfm.config.slug(None) == ""
    assert cfm.config.slug("") == ""


def test_get_children_accepts_children_or_items(cfm):
    assert cfm.config.get_children({"children": [1, 2]}) == [1, 2]
    assert cfm.config.get_children({"items": [3]}) == [3]
    assert cfm.config.get_children({}) == []
    # children preferred over items when both present
    assert cfm.config.get_children({"children": ["c"], "items": ["i"]}) == ["c"]


def test_dict_block(cfm):
    state = {"blk": {"a": 1}}
    out = cfm.config.dict_block(state, "blk")
    assert out == {"a": 1}
    out["a"] = 2                       # returned dict is a copy
    assert state["blk"]["a"] == 1
    assert cfm.config.dict_block({}, "missing") == {}
    assert cfm.config.dict_block({"blk": None}, "blk") == {}
    assert cfm.config.dict_block({"blk": "not a dict"}, "blk") == {}


def test_load_menu_items_yaml(cfm):
    text = "menu:\n  items:\n    - label: Home\n      target: /home\n"
    items = cfm.config.load_menu_items(text, "yaml")
    assert items[0]["label"] == "Home"


def test_load_menu_items_json(cfm):
    text = '{"menu": {"items": [{"label": "H", "target": "/h"}]}}'
    items = cfm.config.load_menu_items(text, "json")
    assert items == [{"label": "H", "target": "/h"}]


def test_load_menu_items_bare_list_and_empty(cfm):
    # A bare items list (no menu: wrapper)
    assert cfm.config.load_menu_items("items:\n  - label: A\n", "yaml")[0]["label"] == "A"
    # Empty input -> empty item list (default empty_root has no items under menu)
    assert cfm.config.load_menu_items("", "yaml") == []


def test_load_menu_items_malformed_json_raises_or_empty(cfm):
    # Malformed JSON: jsonDecode (stub uses json.loads) raises; load_menu_items does not
    # swallow it, so the caller's transform is responsible. Assert it raises cleanly.
    import pytest
    with pytest.raises(Exception):
        cfm.config.load_menu_items("{not json", "json")


def test_resolve_effective_page_path_priority(cfm):
    r = cfm.config.resolve_effective_page_path_from_value
    # requestedPath wins
    assert r({"requestedPath": "/a", "routeLogicalPath": "/b", "path": "/c"}) == "/a"
    # then routeLogicalPath
    assert r({"routeLogicalPath": "/b", "path": "/c"}) == "/b"
    # then path
    assert r({"path": "/c"}) == "/c"
    # normalization applies
    assert r({"path": "c//d/"}) == "/c/d"


def test_resolve_effective_page_path_page_fallback(cfm):
    page = types.SimpleNamespace(props=types.SimpleNamespace(path="/from/page"))
    assert cfm.config.resolve_effective_page_path_from_value({}, page) == "/from/page"
    # no value and no usable page -> empty
    assert cfm.config.resolve_effective_page_path_from_value({}, None) == ""
