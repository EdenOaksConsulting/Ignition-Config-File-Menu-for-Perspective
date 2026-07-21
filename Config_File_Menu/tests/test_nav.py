"""Tests for cfm.nav navigation — no-op routeLogicalPath writes are skipped.

A whole-object session write to configFileMenu re-fires the breadcrumb binding, so a
navigation must not write routeLogicalPath when it would not change.
"""


class _Custom:
    def __init__(self, state):
        self.configFileMenu = dict(state)


class _Session:
    def __init__(self, state):
        self.custom = _Custom(state)


class _Component:
    def __init__(self, session):
        self.session = session


def _spy_writes(cfm, monkeypatch):
    writes = []
    real = cfm.config.set_state_fields
    monkeypatch.setattr(cfm.config, "set_state_fields", lambda s, f: writes.append(dict(f)) or real(s, f))
    return writes


def _stub_pages(cfm, monkeypatch, urls):
    cfm.config._PAGE_URLS_CACHE["urls"] = None
    cfm.config._PAGE_URLS_CACHE["at"] = 0
    monkeypatch.setattr(cfm.config.system.perspective, "getProjectInfo",
                        lambda *a, **k: {"pageConfigs": [{"url": u} for u in urls]})
    monkeypatch.setattr(cfm.config.system.perspective, "navigate", lambda **k: None, raising=False)


def test_direct_hit_skips_noop_route_write(cfm, monkeypatch):
    # routeLogicalPath already "" -> a direct hit must not re-write it.
    _stub_pages(cfm, monkeypatch, ["/home"])
    writes = _spy_writes(cfm, monkeypatch)
    sess = _Session({"routeLogicalPath": "", "dockPinned": True})
    cfm.nav.navigate_with_fallback(_Component(sess), "/home", close_dock=False)
    assert all("routeLogicalPath" not in w for w in writes)


def test_direct_hit_clears_stale_route(cfm, monkeypatch):
    # routeLogicalPath set from a prior fallback -> direct hit clears it (write happens).
    _stub_pages(cfm, monkeypatch, ["/home"])
    writes = _spy_writes(cfm, monkeypatch)
    sess = _Session({"routeLogicalPath": "/old", "dockPinned": True})
    cfm.nav.navigate_with_fallback(_Component(sess), "/home", close_dock=False)
    assert any(w.get("routeLogicalPath") == "" for w in writes)


def test_fallback_skips_write_when_unchanged(cfm, monkeypatch):
    # logical already equals the requested target -> no write.
    _stub_pages(cfm, monkeypatch, ["/cfm/target-no-route"])
    writes = _spy_writes(cfm, monkeypatch)
    sess = _Session({
        "routeLogicalPath": "/plant/a1", "dockPinned": True,
        "routeFallbackEnabled": True, "routeFallbackPath": "/cfm/target-no-route",
    })
    cfm.nav.navigate_with_fallback(_Component(sess), "/plant/a1", close_dock=False)
    assert all("routeLogicalPath" not in w for w in writes)


def test_fallback_writes_when_changed(cfm, monkeypatch):
    # logical differs from the target -> write the new logical path.
    _stub_pages(cfm, monkeypatch, ["/cfm/target-no-route"])
    writes = _spy_writes(cfm, monkeypatch)
    sess = _Session({
        "routeLogicalPath": "", "dockPinned": True,
        "routeFallbackEnabled": True, "routeFallbackPath": "/cfm/target-no-route",
    })
    cfm.nav.navigate_with_fallback(_Component(sess), "/plant/a1", close_dock=False)
    assert any(w.get("routeLogicalPath") == "/plant/a1" for w in writes)
