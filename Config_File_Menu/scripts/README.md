# Config File Menu — Scripts

| Script | Output / purpose |
|--------|------------------|
| [`build-inheritance-zips.py`](build-inheritance-zips.py) | `../../dist/config-file-menu-library.zip`, `config-file-menu-site.zip`, `config-file-menu-sample.zip` |
| [`build-import-zip.py`](build-import-zip.py) | Delegates to `build-inheritance-zips.py` |
| [`build-hmi-menu-sample.py`](build-hmi-menu-sample.py) | Syncs views, Advanced Stylesheet, page-config, logos |
| [`embed-logos-in-menu-content.py`](embed-logos-in-menu-content.py) | Refresh embedded logo URIs in extracted site/sample zip after PNG replacement (standalone Python 3, no packages) |
| [`audit-css-classes.py`](audit-css-classes.py) | Compare extracted `cfm-*` view/build classes with canonical `.psc-cfm-*` CSS selectors |
| [`verify-theme-css.py`](verify-theme-css.py) | Ensures generated Advanced Stylesheet matches canonical CSS |
| [`apply-menu-sample-config.py`](apply-menu-sample-config.py) | Sync `config/menuSampleConfig.yaml` → JSON + embedded view defaults |

## Build

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
