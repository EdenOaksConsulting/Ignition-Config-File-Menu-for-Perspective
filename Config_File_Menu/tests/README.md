# Tests

Unit tests for the Config File Menu runtime's **pure** logic.

## Running

From the repository root:

```bash
python -m pytest Config_File_Menu/tests
```

Only `pytest` is required (dev-only — it is **not** a runtime dependency of the deployed
project). Install it with:

```bash
python -m pip install -r Config_File_Menu/requirements-dev.txt
```

## Jython vs CPython

The deployed runtime runs under **Jython 2.7** inside Ignition, authored as separate
modules in [`../scripts/jython_lib/cfm`](../scripts/jython_lib/cfm) and bundled into one
file (`ignition/script-python/exchange/cfm/runtime/code.py`) by `build_script_library.py`.

These tests run those **source modules** under **CPython 3 + pytest**. `conftest.py`
bridges the two environments by injecting the globals Ignition normally provides:

- a stub `system` object (only `system.util.jsonDecode`/`jsonEncode` are meaningful; the
  rest are inert so importing modules and touching untested functions doesn't blow up),
- the cross-module `cfm` namespace (so `cfm.config.*` etc. resolve across source modules),
- `basestring` (Jython 2.7 built-in, aliased to `str`).

Tests receive the loaded namespace via the `cfm` fixture, e.g. `cfm.config.is_true("yes")`.

Only side-effect-free functions are tested here — anything that calls Ignition
`system.perspective.*` / `system.tag.*` / reads live `session`/`component`/`page` objects
is out of scope (it needs a running gateway).

## What's covered

| File | Under test |
|------|------------|
| `test_config.py` | `is_true`, `scalar`, `clean_lines`, `parse_yaml_lite`, `normalize_path`, `slug`, `get_children`, `load_menu_items`, `dict_block`, `resolve_effective_page_path_from_value` |
| `test_settings.py` | `_walk_menu`, `target_to_view_path`, `_slug_to_title`, `_tag_slugify`, `_yaml_quote`, `_emit_yaml`, `_load_menu` |
| `test_menu.py` | `_find_label`, `_find_icon`, `_fallback_title`, `menu_link_classes` |
| `test_tree.py` | `page_belongs_to_section`, `section_classes`, `section_header_classes` |
| `test_breadcrumb.py` | `_add_lookup`, `_menu_target_for`, `_add_label_lookup`, `_menu_label_for`, `_home_target_for` |
| `test_bundle_drift.py` | Guards that the committed `code.py` bundle matches the source modules (wraps `scripts/verify_script_library.py`) |
| `test_settings_keys.py` | The Settings-owned key list, what `init_settings_shell_state` seeds, and `session-props/props.json` defaults agree |
