"""Pytest scaffolding for the Config File Menu runtime.

The deployed runtime is authored as separate modules under
``scripts/jython_lib/cfm`` and bundled into one flat file
(``ignition/script-python/exchange/cfm/runtime/code.py``) that runs under
**Jython 2.7** inside Ignition. These tests exercise the *pure* logic in those
source modules under **CPython 3 + pytest**.

To import the Jython-2.7 source under CPython we provide the two globals the
platform injects — ``system`` (stubbed) and the cross-module ``cfm`` namespace —
plus ``basestring``. Only the ``system`` calls used by the tested pure functions
(``system.util.jsonDecode``/``jsonEncode``) are meaningful; the rest are inert so
that importing a module and touching an untested function does not explode.
"""

import builtins
import importlib.util
import json as _json
import sys
import types
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TESTS_DIR.parent                       # Config_File_Menu
SRC_DIR = PROJECT_DIR / "scripts" / "jython_lib" / "cfm"

# Dependency-safe load order (mirrors build_script_library.BUNDLE_ORDER).
BUNDLE_ORDER = ("log", "config", "ui", "nav", "dock", "menu", "tree", "breadcrumb", "settings")

# Jython 2.7 modules use `basestring`; provide it under CPython 3.
if not hasattr(builtins, "basestring"):
    builtins.basestring = str  # type: ignore[attr-defined]


def _make_system_stub():
    """A minimal stand-in for Ignition's global ``system`` object."""
    system = types.ModuleType("system")

    util = types.ModuleType("system.util")
    util.jsonDecode = lambda text: _json.loads(text)

    def _json_encode(obj, indent=None):
        return _json.dumps(obj, indent=indent) if indent else _json.dumps(obj)

    util.jsonEncode = _json_encode

    def _get_logger(_name):
        noop = lambda *a, **k: None
        # isTraceEnabled defaults to False so the real perf helpers treat perf logging as
        # off unless a test overrides the logger (perf is opt-in / TRACE-gated).
        return types.SimpleNamespace(
            info=noop, warn=noop, debug=noop, error=noop, trace=noop,
            isTraceEnabled=lambda: False,
        )

    util.getLogger = _get_logger
    system.util = util

    def _unavailable(*_a, **_k):
        raise RuntimeError("Ignition `system` call is not available under pytest")

    system.perspective = types.SimpleNamespace(
        navigate=_unavailable,
        openDock=_unavailable,
        closeDock=_unavailable,
        alterDock=_unavailable,
        sendMessage=_unavailable,
        getProjectInfo=lambda *a, **k: {"pageConfigs": []},
    )
    system.tag = types.SimpleNamespace(browse=_unavailable, getConfiguration=_unavailable)
    system.security = types.SimpleNamespace(hasRole=_unavailable)
    system.device = types.SimpleNamespace(listDevices=_unavailable)
    system.dataset = types.SimpleNamespace(toPyDataSet=lambda d: d)
    return system


def _load_cfm():
    """Load the real source modules and wire up the cross-module ``cfm`` namespace."""
    system = _make_system_stub()
    sys.modules.setdefault("system", system)

    cfm = types.ModuleType("cfm")
    for name in BUNDLE_ORDER:
        path = SRC_DIR / (name + ".py")
        if not path.is_file():
            raise RuntimeError("Missing runtime source module: %s" % path)
        spec = importlib.util.spec_from_file_location("cfm_" + name, str(path))
        module = importlib.util.module_from_spec(spec)
        # Inject the platform globals before exec so any module-level use resolves.
        module.__dict__["system"] = system
        module.__dict__["cfm"] = cfm
        module.__dict__["basestring"] = str
        spec.loader.exec_module(module)
        setattr(cfm, name, module)

    sys.modules["cfm"] = cfm
    return cfm


# Loaded once at collection time; the source modules are stateless.
_CFM = _load_cfm()


@pytest.fixture(scope="session")
def cfm():
    """The ``cfm`` namespace with ``.config``, ``.menu``, ``.tree``, etc."""
    return _CFM
