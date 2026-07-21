# Config File Menu — Scripts

| Script | Output / purpose |
|--------|------------------|
| [`build-inheritance-zips.py`](build-inheritance-zips.py) | `../../dist/config-file-menu-library.zip`, `config-file-menu-site.zip`, `config-file-menu-sample.zip` |
| [`build-import-zip.py`](build-import-zip.py) | Delegates to `build-inheritance-zips.py` |
| [`build-hmi-menu-sample.py`](build-hmi-menu-sample.py) | Syncs views, Advanced Stylesheet, page-config, logos |
| [`build_script_library.py`](build_script_library.py) | Bundles `jython_lib/cfm/*.py` → the deployed `exchange.cfm.runtime` (`code.py`). Run after editing any runtime module |
| [`verify_script_library.py`](verify_script_library.py) | Fails (exit 1) if the committed `code.py` bundle is out of sync with the `cfm` source modules |
| [`verify_public_snapshot.py`](verify_public_snapshot.py) | Fails (exit 1) if a maintainer-only file reached the public tree. Takes an optional ref (default `origin/main`); also backs the pre-push hook |
| [`verify_doc_keys.py`](verify_doc_keys.py) | Fails (exit 1) if a doc references a `configFileMenu` key that no longer exists. Key set = `session-props` plus runtime `setdefault` |
| [`hooks/pre-push`](hooks/pre-push) | Blocks a push that would publish a maintainer-only file. See **Hooks** below |
| [`embed-logos-in-menu-content.py`](embed-logos-in-menu-content.py) | Refresh embedded logo URIs in extracted site/sample zip after PNG replacement (standalone Python 3, no packages) |
| [`audit-css-classes.py`](audit-css-classes.py) | Compare extracted `cfm-*` view/build classes with canonical `.psc-cfm-*` CSS selectors |
| [`verify-theme-css.py`](verify-theme-css.py) | Ensures generated Advanced Stylesheet matches canonical CSS |
| [`apply-menu-sample-config.py`](apply-menu-sample-config.py) | Sync `config/menuSampleConfig.yaml` → JSON + embedded view defaults |

## Hooks

Enable once per clone (hooks are not cloned, so this is needed on every machine):

```bash
git config core.hooksPath Config_File_Menu/scripts/hooks
```

`pre-push` then blocks any push to a **public** remote whose commits still contain a
maintainer-only file. Pushes to a known-private remote (URL containing `Working-Private`)
are skipped; an unrecognized remote is treated as public, so a new fork gets checked rather
than waved through. Bypass with `git push --no-verify`.

The hook only locates a Python interpreter and forwards git's stdin records — the logic
lives in `verify_public_snapshot.py` and is covered by `tests/test_public_snapshot.py`.

> Setting `core.hooksPath` replaces `.git/hooks` entirely. If you later add other hooks,
> put them in this directory too.

## Build

Requires **Pillow** (used to resize the logo PNGs); everything else is standard library:

```bash
pip install -r Config_File_Menu/requirements-dev.txt
```

From repository root:

```bash
python Config_File_Menu/scripts/build-inheritance-zips.py
```

Produces `config-file-menu-library.zip`, `config-file-menu-site.zip`, `config-file-menu-sample.zip`, under **`dist/`** at the repository root. Ephemeral staging uses `dist/staging/` and is removed when the build completes.

## Logo embed helper

After replacing `logo-upload/cfm/*.png` in an extracted child zip, refresh the embedded logo data URIs in `MenuContent/view.json` and `Resources/Menu/Menu Top Bar/view.json`:

```bash
python Config_File_Menu/scripts/embed-logos-in-menu-content.py /path/to/extracted-folder
```

Then re-zip and import.

## Runtime bundle

The deployed runtime is authored as separate modules under `jython_lib/cfm/` and bundled
into one file (`ignition/script-python/exchange/cfm/runtime/code.py`). After editing any
`cfm` module, regenerate the bundle:

```bash
python Config_File_Menu/scripts/build_script_library.py
```

Never hand-edit `code.py`. `verify_script_library.py` (and the pytest drift test) will fail
if it drifts from the source modules.

## Tests

Pure runtime logic (no Perspective dependency) is covered by pytest under
[`../tests`](../tests). From the repository root:

```bash
python -m pytest Config_File_Menu/tests
```

This runs the unit tests (config / settings / menu / tree / breadcrumb, plus the `cfm.log`
de-dup core and the `check_menu_health` logic) as well as the bundle-drift guard and the
settings-key consistency check. See [`../tests/README.md`](../tests/README.md) for the
Jython-vs-CPython split.

> **Note:** the runtime gained a `cfm.log` module (named `CFM.*` loggers with de-duplicated,
> flood-safe logging) and a menu-config health check surfaced via the Settings **Validate
> menu config** action. `cfm.log` is loaded **first** in `BUNDLE_ORDER`. See the README
> **Logging & health** section.
