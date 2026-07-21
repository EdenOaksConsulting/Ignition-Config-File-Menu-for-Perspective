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


# --- parsed menu-items cache ---

def test_load_menu_items_cache_hit_returns_same_object(cfm):
    cfm.config._MENU_ITEMS_CACHE.clear()
    text = "menu:\n  items:\n    - label: Cached\n      target: /cached\n"
    a = cfm.config.load_menu_items(text, "yaml")
    b = cfm.config.load_menu_items(text, "yaml")
    assert a is b                              # second call served from cache, not re-parsed
    assert a[0]["label"] == "Cached"


def test_load_menu_items_cache_invalidates_on_source_or_type_change(cfm):
    cfm.config._MENU_ITEMS_CACHE.clear()
    a = cfm.config.load_menu_items("menu:\n  items:\n    - label: One\n", "yaml")
    b = cfm.config.load_menu_items("menu:\n  items:\n    - label: Two\n", "yaml")
    assert a[0]["label"] == "One" and b[0]["label"] == "Two"
    assert a is not b                          # changed source -> distinct cache key
    # same text but different type is also a distinct key
    j = '{"menu": {"items": [{"label": "One"}]}}'
    assert cfm.config.load_menu_items(j, "json")[0]["label"] == "One"


def test_load_menu_items_cache_matches_uncached(cfm):
    cfm.config._MENU_ITEMS_CACHE.clear()
    text = "menu:\n  items:\n    - label: Home\n      target: /home\n"
    assert cfm.config.load_menu_items(text, "yaml") == cfm.config._load_menu_items_uncached(text, "yaml")


def test_load_menu_items_cache_is_bounded(cfm):
    cfm.config._MENU_ITEMS_CACHE.clear()
    cap = cfm.config._MENU_ITEMS_CACHE_CAP
    for i in range(cap):
        cfm.config.load_menu_items("menu:\n  items:\n    - label: L%d\n" % i, "yaml")
    assert len(cfm.config._MENU_ITEMS_CACHE) == cap
    # reaching the cap clears the cache wholesale before inserting the next entry
    cfm.config.load_menu_items("menu:\n  items:\n    - label: Overflow\n", "yaml")
    assert len(cfm.config._MENU_ITEMS_CACHE) == 1


def test_load_menu_items_non_string_bypasses_cache(cfm):
    cfm.config._MENU_ITEMS_CACHE.clear()
    doc = {"menu": {"items": [{"label": "Doc"}]}}
    items = cfm.config.load_menu_items(doc, "json")
    assert items[0]["label"] == "Doc"
    assert len(cfm.config._MENU_ITEMS_CACHE) == 0     # unhashable source is never cached


# --- registered page-url cache (TTL) ---

def _reset_pages_cache(cfm):
    cfm.config._PAGE_URLS_CACHE["urls"] = None
    cfm.config._PAGE_URLS_CACHE["at"] = 0


def test_pages_cache_shares_one_call_within_ttl(cfm, monkeypatch):
    _reset_pages_cache(cfm)
    calls = {"n": 0}

    def fake_info(*a, **k):
        calls["n"] += 1
        return {"pageConfigs": [{"url": "/"}, {"url": "/cfm/settings"}]}

    monkeypatch.setattr(cfm.config.system.perspective, "getProjectInfo", fake_info)
    clock = {"t": 1000000000}
    monkeypatch.setattr(cfm.log, "now_nanos", lambda: clock["t"])
    first = cfm.config.get_project_page_urls_cached()
    clock["t"] += 500000000                    # +0.5s, inside the ~2s TTL
    second = cfm.config.get_project_page_urls_cached()
    assert first == ["/", "/cfm/settings"]
    assert second == first
    assert calls["n"] == 1                      # second served from cache


def test_pages_cache_refreshes_after_ttl(cfm, monkeypatch):
    _reset_pages_cache(cfm)
    calls = {"n": 0}

    def fake_info(*a, **k):
        calls["n"] += 1
        return {"pageConfigs": [{"url": "/"}]}

    monkeypatch.setattr(cfm.config.system.perspective, "getProjectInfo", fake_info)
    clock = {"t": 1000000000}
    monkeypatch.setattr(cfm.log, "now_nanos", lambda: clock["t"])
    cfm.config.get_project_page_urls_cached()
    clock["t"] += 3000000000                    # +3s, past the TTL
    cfm.config.get_project_page_urls_cached()
    assert calls["n"] == 2


def test_pages_cache_serves_last_good_on_error(cfm, monkeypatch):
    _reset_pages_cache(cfm)
    clock = {"t": 1000000000}
    monkeypatch.setattr(cfm.log, "now_nanos", lambda: clock["t"])
    monkeypatch.setattr(cfm.config.system.perspective, "getProjectInfo",
                        lambda *a, **k: {"pageConfigs": [{"url": "/a"}]})
    assert cfm.config.get_project_page_urls_cached() == ["/a"]
    clock["t"] += 3000000000                     # force a refresh attempt

    def boom(*a, **k):
        raise RuntimeError("gateway down")

    monkeypatch.setattr(cfm.config.system.perspective, "getProjectInfo", boom)
    assert cfm.config.get_project_page_urls_cached() == ["/a"]   # last good served, no raise


# --- no-op routeLogicalPath guard ---

def test_should_write_route_logical(cfm):
    w = cfm.config.should_write_route_logical
    assert w("", "") is False
    assert w(None, "") is False
    assert w(None, None) is False
    assert w("/x", "") is True
    assert w("", "/x") is True
    assert w("/x", "/x") is False
    assert w("/x", "/y") is True
