"""Tests for cfm.settings.check_menu_health (pure menu-config health check)."""


def test_all_ok(cfm):
    items = [
        {"label": "Home", "target": "/home"},
        {"label": "Plant", "children": [{"label": "A1", "target": "/plant/a1"}]},
    ]
    h = cfm.settings.check_menu_health(items, ["/home", "/plant/a1"], False, "")
    assert h["itemCount"] == 3
    assert h["targetsChecked"] == 2
    assert h["missingRoutes"] == []
    assert h["duplicateTargets"] == []
    assert h["roleWarnings"] == []


def test_missing_route(cfm):
    h = cfm.settings.check_menu_health([{"label": "X", "target": "/nope"}], ["/home"], False, "")
    assert h["missingRoutes"] == ["/nope"]


def test_missing_route_covered_by_fallback(cfm):
    items = [{"label": "X", "target": "/nope"}]
    fb = "/cfm/target-no-route"
    # Fallback enabled + registered -> not flagged.
    assert cfm.settings.check_menu_health(items, [fb], True, fb)["missingRoutes"] == []
    # Fallback disabled -> flagged.
    assert cfm.settings.check_menu_health(items, [fb], False, fb)["missingRoutes"] == ["/nope"]
    # Fallback enabled but not itself registered -> flagged.
    assert cfm.settings.check_menu_health(items, [], True, fb)["missingRoutes"] == ["/nope"]


def test_duplicate_targets(cfm):
    items = [{"label": "A", "target": "/dup"}, {"label": "B", "target": "/dup"}]
    h = cfm.settings.check_menu_health(items, ["/dup"], False, "")
    assert h["duplicateTargets"] == ["/dup"]
    assert h["missingRoutes"] == []           # registered, so not missing


def test_role_warnings(cfm):
    items = [{"label": "Secret", "target": "/s", "roles": ["admin"]}]
    h = cfm.settings.check_menu_health(items, ["/s"], False, "")
    assert h["roleWarnings"] == ["Secret"]


def test_empty_and_none(cfm):
    assert cfm.settings.check_menu_health([], [], False, "")["itemCount"] == 0
    assert cfm.settings.check_menu_health(None, None, False, None)["itemCount"] == 0


def test_deep_nesting_and_target_normalization(cfm):
    items = [{"label": "L1", "children": [
        {"label": "L2", "items": [{"label": "L3", "target": "deep"}]},
    ]}]
    h = cfm.settings.check_menu_health(items, [], True, "/cfm/target-no-route")
    assert h["itemCount"] == 3
    assert h["targetsChecked"] == 1
    assert h["missingRoutes"] == ["/deep"]     # "deep" normalized to "/deep"


def test_summary_format(cfm):
    problem = cfm.settings.check_menu_health([{"label": "X", "target": "/nope"}], ["/home"], False, "")
    summary = cfm.settings._format_menu_health_summary(problem)
    assert "missing route" in summary
    assert "/nope" in summary

    ok = cfm.settings.check_menu_health([{"label": "H", "target": "/h"}], ["/h"], False, "")
    assert cfm.settings._format_menu_health_summary(ok).endswith("OK")
