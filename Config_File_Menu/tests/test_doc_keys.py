"""Doc-drift guard: the docs must not reference configuration keys that no longer exist.

Wraps ``scripts/verify_doc_keys.py``. See that module for why this exists — v2.0.0 shipped
an import checklist telling readers to inspect ``params.menuConfigType``, a param the same
release removed.
"""

import importlib.util
from pathlib import Path


def _load_verifier():
    path = Path(__file__).resolve().parents[1] / "scripts" / "verify_doc_keys.py"
    spec = importlib.util.spec_from_file_location("verify_doc_keys", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFIER = _load_verifier()


def test_docs_reference_only_live_keys():
    ok, message = VERIFIER.check()
    assert ok, message


def test_key_set_includes_both_declared_and_runtime_keys():
    """The valid set is session-props plus runtime setdefault, not session-props alone.

    Checking props.json by itself reported live keys such as `settingsTagMenu` — created on
    first run rather than declared — as unknown.
    """
    keys = VERIFIER.current_keys()
    assert "contentSource" in keys, "declared session-props key missing"
    assert "settingsTagMenu" in keys, "runtime setdefault key missing"


def test_guard_detects_a_removed_key(tmp_path):
    """A doc reintroducing an old name is caught."""
    doc = tmp_path / "regression.md"
    doc.write_text("Edit `MenuContent.params.menuConfig` to set the menu.\n", encoding="utf-8")
    findings = VERIFIER.scan(paths=[doc], keys=VERIFIER.current_keys())
    assert findings, "removed key was not detected"
    assert any("menuConfig" in f[3] for f in findings)


def test_guard_detects_an_unknown_config_key(tmp_path):
    """A doc inventing a configFileMenu key is caught."""
    doc = tmp_path / "regression.md"
    doc.write_text("Set `configFileMenu.notARealKey` to true.\n", encoding="utf-8")
    findings = VERIFIER.scan(paths=[doc], keys=VERIFIER.current_keys())
    assert any("notARealKey" in f[3] for f in findings)


def test_guard_accepts_a_live_key(tmp_path):
    doc = tmp_path / "clean.md"
    doc.write_text("Set `configFileMenu.contentSourceType` to `yaml`.\n", encoding="utf-8")
    assert VERIFIER.scan(paths=[doc], keys=VERIFIER.current_keys()) == []
