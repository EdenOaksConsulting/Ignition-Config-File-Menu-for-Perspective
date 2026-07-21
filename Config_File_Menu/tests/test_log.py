"""Tests for cfm.log — de-dup core, log_once/log_always, flood-safety."""

import pytest


class RecordingLogger:
    def __init__(self, trace_enabled=False):
        self.calls = []
        self.trace_enabled = trace_enabled

    def error(self, m):
        self.calls.append(("error", m))

    def warn(self, m):
        self.calls.append(("warn", m))

    def info(self, m):
        self.calls.append(("info", m))

    def debug(self, m):
        self.calls.append(("debug", m))

    def trace(self, m):
        self.calls.append(("trace", m))

    def isTraceEnabled(self):
        return self.trace_enabled


@pytest.fixture
def recorder(cfm, monkeypatch):
    rec = RecordingLogger()
    monkeypatch.setattr(cfm.log, "get_logger", lambda name="": rec)
    cfm.log._LOG_ONCE_CACHE.clear()   # isolate module-level cache between tests
    return rec


# --- pure de-dup core ---

def test_should_emit_dedups_same_key(cfm):
    cache = {}
    assert cfm.log._should_emit(cache, "a|msg", "msg") is True
    assert cfm.log._should_emit(cache, "a|msg", "msg") is False
    assert cfm.log._should_emit(cache, "a|other", "other") is True


def test_should_emit_reemits_on_changed_message(cfm):
    cache = {}
    assert cfm.log._should_emit(cache, "a", "first") is True
    assert cfm.log._should_emit(cache, "a", "second") is True   # value changed for same key
    assert cfm.log._should_emit(cache, "a", "second") is False


def test_should_emit_bounds_cache(cfm):
    cache = {}
    cap = cfm.log._LOG_ONCE_CACHE_CAP
    for i in range(cap):
        cfm.log._should_emit(cache, "k%d" % i, "m%d" % i)
    assert len(cache) == cap
    # Reaching the cap clears the cache before adding the next entry.
    cfm.log._should_emit(cache, "overflow", "m")
    assert len(cache) == 1


# --- log_once / log_always ---

def test_log_once_emits_only_once(cfm, recorder):
    for _ in range(3):
        cfm.log.log_once("menu", "error", "boom")
    assert recorder.calls == [("error", "boom")]


def test_log_once_reemits_when_message_changes(cfm, recorder):
    cfm.log.log_once("menu", "warn", "first")
    cfm.log.log_once("menu", "warn", "second")
    assert recorder.calls == [("warn", "first"), ("warn", "second")]


def test_log_always_emits_every_time(cfm, recorder):
    cfm.log.log_always("settings", "warn", "x")
    cfm.log.log_always("settings", "warn", "x")
    assert recorder.calls == [("warn", "x"), ("warn", "x")]


def test_exc_appended_to_message(cfm, recorder):
    cfm.log.log_always("settings", "warn", "failed", Exception("bad thing"))
    assert recorder.calls == [("warn", "failed: bad thing")]


def test_unknown_level_falls_back_to_info(cfm, recorder):
    cfm.log.log_always("x", "verbose", "hello")
    assert recorder.calls == [("info", "hello")]


def test_logging_never_raises(cfm, monkeypatch):
    class Boom:
        def error(self, m):
            raise RuntimeError("logger down")
        warn = info = debug = error

    monkeypatch.setattr(cfm.log, "get_logger", lambda name="": Boom())
    cfm.log._LOG_ONCE_CACHE.clear()
    # Neither call may propagate the logger failure into a handler.
    cfm.log.log_once("x", "error", "m")
    cfm.log.log_always("x", "error", "m")


def test_get_logger_name_prefix(cfm, monkeypatch):
    names = []
    fake_util = type("U", (), {"getLogger": staticmethod(lambda n: names.append(n))})
    monkeypatch.setattr(cfm.log.system, "util", fake_util)
    cfm.log.get_logger("menu")
    cfm.log.get_logger("")
    assert names == ["CFM.menu", "CFM"]


# --- performance logging ---

def test_now_nanos_non_decreasing_int(cfm):
    a = cfm.log.now_nanos()
    b = cfm.log.now_nanos()
    assert isinstance(a, int) and isinstance(b, int)
    assert b >= a


def test_now_nanos_never_raises(cfm, monkeypatch):
    # Even if time import / java path both fail, it returns an int rather than raising.
    import sys
    monkeypatch.setitem(sys.modules, "time", None)   # force `import time` to fail
    assert cfm.log.now_nanos() == 0


def test_perf_enabled_property_forces_on(cfm, monkeypatch):
    # perf_prop True short-circuits to True regardless of logger level.
    monkeypatch.setattr(cfm.log, "get_logger", lambda name="": RecordingLogger(trace_enabled=False))
    assert cfm.log.perf_enabled(True) is True


def test_perf_enabled_off_when_prop_false_and_trace_off(cfm, monkeypatch):
    monkeypatch.setattr(cfm.log, "get_logger", lambda name="": RecordingLogger(trace_enabled=False))
    assert cfm.log.perf_enabled(False) is False


def test_perf_enabled_on_when_trace_enabled(cfm, monkeypatch):
    monkeypatch.setattr(cfm.log, "get_logger", lambda name="": RecordingLogger(trace_enabled=True))
    assert cfm.log.perf_enabled(False) is True


def test_perf_forced_logs_at_info_with_marker(cfm, monkeypatch):
    rec = RecordingLogger(trace_enabled=False)
    monkeypatch.setattr(cfm.log, "get_logger", lambda name="": rec)
    cfm.log.perf("breadcrumb.build", 2500000, "items=3", force=True)
    assert len(rec.calls) == 1
    level, msg = rec.calls[0]
    assert level == "info"
    assert msg == "[CFM perf] breadcrumb.build 2.5ms items=3"


def test_perf_trace_only_logs_at_trace(cfm, monkeypatch):
    rec = RecordingLogger(trace_enabled=True)
    monkeypatch.setattr(cfm.log, "get_logger", lambda name="": rec)
    cfm.log.perf("menu.render", 1000000, force=False)
    assert rec.calls == [("trace", "[CFM perf] menu.render 1.0ms")]


def test_perf_suppressed_when_off(cfm, monkeypatch):
    rec = RecordingLogger(trace_enabled=False)
    monkeypatch.setattr(cfm.log, "get_logger", lambda name="": rec)
    cfm.log.perf("menu.render", 5000000, force=False)   # neither forced nor trace-enabled
    assert rec.calls == []


def test_perf_respects_threshold(cfm, monkeypatch):
    rec = RecordingLogger(trace_enabled=True)
    monkeypatch.setattr(cfm.log, "get_logger", lambda name="": rec)
    cfm.log.perf("nav.navigate", 500000, threshold_ms=5, force=True)   # 0.5ms < 5ms
    assert rec.calls == []
    cfm.log.perf("nav.navigate", 9000000, threshold_ms=5, force=True)  # 9.0ms >= 5ms
    assert rec.calls == [("info", "[CFM perf] nav.navigate 9.0ms")]


def test_perf_never_raises(cfm, monkeypatch):
    class Boom:
        def isTraceEnabled(self):
            raise RuntimeError("logger down")
        def info(self, m):
            raise RuntimeError("logger down")
        trace = info

    monkeypatch.setattr(cfm.log, "get_logger", lambda name="": Boom())
    # Must swallow the failure rather than propagate into a handler.
    cfm.log.perf("x", 1000000, force=True)
