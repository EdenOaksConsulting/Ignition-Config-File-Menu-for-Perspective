# Config File Menu — Beginner Deployment Guide

This guide shows the shortest path to install Config File Menu, try the sample, or start a blank site project. Import the library first, then import one child project.

Use the three generated import zips directly: import `config-file-menu-library.zip` first with project name exactly `config-file-menu-library`, then import either `config-file-menu-sample.zip` or `config-file-menu-site.zip`.

For public Exchange submission, upload the project/package files from the repository `dist/` folder, especially `config-file-menu-library.zip`, `config-file-menu-sample.zip`, and `config-file-menu-site.zip`. Do not upload the workspace root.

---

## Package roles

| Zip | Ignition project name | Ignition project title | Use |
|-----|-----------------------|------------------------|-----|
| `config-file-menu-library.zip` | `config-file-menu-library` | Config File Menu Library | Once per gateway / CFM version upgrade |
| `config-file-menu-sample.zip` | `config-file-menu-sample` | Config File Menu Sample | Evaluation, training, reference plant menu |
| `config-file-menu-site.zip` | `config-file-menu-site` | Config File Menu — Your Site Name | Blank production starter |

The library is **inheritable** and ships views, Runtime, Settings tools, Advanced Stylesheet, and fixed routes (`/cfm/settings`, `/cfm/diagnostics`, `/cfm/target-no-route`, etc.).

Child packages (site and sample) are **thin**: they override `project.json`, `page-config`, `MenuContent.params.menuConfig`, and ship editable logo PNGs. Everything else inherits from the library parent.

---

## Path 1: Try The Sample

Use this first if you are new to the project.

1. Import `config-file-menu-library.zip` with project name exactly `config-file-menu-library`.
2. Import `config-file-menu-sample.zip`.
3. Open the **Config File Menu Sample** project in Designer.
4. Set **Session Properties → theme** to `light` or `dark`.
5. Save and publish.
6. Launch `/` for the landing page, or `/cfm/dashboard` for the sample dashboard.
7. Open `/cfm/settings` to review the built-in Settings, YAML to JSON, Tag to Menu, and Menu to Routes tools.

The sample already includes menu config, page routes, shared docks, embedded logos, and reference pages.

## Path 2: Create A Blank Site

Use this for a production starter project.

1. Import `config-file-menu-library.zip` with project name exactly `config-file-menu-library`.
2. Extract `config-file-menu-site.zip` to a working folder.
3. Edit the child zip files listed below.
4. Re-zip the folder contents so `project.json` is at the zip root.
5. Import the edited site zip.
6. Open **Config File Menu — Your Site Name** in Designer.
7. Set **Session Properties → theme** to `light` or `dark`.
8. Save, publish, and launch the site.

### Files To Edit In The Site Zip

Only these files need changes for a typical first site:

| Path in zip | Purpose |
|-------------|---------|
| `project.json` | Replace **Your Site Name** in `title`; optional `description` |
| `com.inductiveautomation.perspective/views/Config File Menu/MenuContent/view.json` | `params.menuConfig`, `params.menuConfigType` (`yaml` or `json`) |
| `com.inductiveautomation.perspective/views/Config File Menu/Resources/Menu/Menu Top Bar/view.json` | Embedded top-bar small logo, refreshed by the logo helper |
| `com.inductiveautomation.perspective/page-config/config.json` | `pages` object — **keep** `sharedDocks` and fixed library routes |
| `logo-upload/cfm/cfm-logo-large.png` | Dock header large logo |
| `logo-upload/cfm/cfm-logo-small.png` | Dock small logo + top-bar logo |

**Do not edit** in the child zip: Runtime, Settings views, Advanced Stylesheet, or `View Dynamic Fallback` (reads menu from session; no duplicate `menuConfig` on view params).

### Minimum Site Menu

Paste this into `MenuContent.view.json` → `params.menuConfig`, then set `params.menuConfigType` to `yaml`:

```yaml
menu:
  items:
    - label: Dashboard
      icon: material/home
      target: /cfm/dashboard
```

Then add a matching `/cfm/dashboard` page route in `page-config/config.json`.

**Minimum Ignition version:** 8.3.0 (Perspective 3.3+). Earlier versions are not supported.

## Next Steps

| File | Use |
|------|-----|
| `config/menuSiteTemplate.yaml` | Empty `items: []` for site deployments |
| `config/menuSampleConfig.yaml` / `.json` | Full reference plant menu (sample package) |

After the basic sample or site import works, use the sections below to generate menus, generate routes, replace logos, or map routes to your own views.

## Production Security

Before publishing a production site, review access to bundled tool and diagnostic routes:

- Restrict `/cfm/settings` to trusted users. It includes Tag to Menu and Menu to Routes authoring tools.
- Hide, remove, or restrict `/cfm/diagnostics` unless users should see gateway/session/system diagnostics.
- Keep page-level authorization on destination pages. Menu `roles` only hide links and do not secure routes.

---

## Advanced: Settings Tools To Generate Menu And Routes

Use these tools when tag browse or route generation is easier in a live session. Import library + site or sample temporarily, open **`/cfm/settings`**, copy tool output back into your extracted zip files, then re-zip and import the final site project.

### Tag → Menu

**Location:** Settings → **Tag → Menu** tab (`/cfm/settings`).

**Requirements:** Live Perspective session (tag browse may fail in Designer preview only).

**Steps:**

1. Enter tag path (e.g. `[default]Plant/Areas`), route prefix (e.g. `/cfm/plant`), and **Max levels**.
2. Click **Generate menu**.
3. Copy the YAML or JSON output.
4. Merge the branch under `menu.items` in `MenuContent/view.json` → `params.menuConfig`.

**Note:** Optional `sourceTagPath` keys are authoring metadata; the runtime menu ignores unknown fields.

### Menu → Routes

**Location:** Settings → **Menu → Routes** tab.

**Steps:**

1. Paste finalized menu YAML or JSON into the menu input panel.
2. Choose **Output mode**:
   - **Dynamic Default** — set **Dynamic viewPath** if all generated routes should use one view (default: `Config File Menu/Resources/View Dynamic Fallback`).
   - **Create Views** — each route gets a unique `viewPath` derived from its target URL; a **Views** output panel provides matching `view.json` templates.
3. Click **Generate output**.
4. Copy the `pages` object from the routes output JSON (and the `views` manifest when using Create Views).
5. Merge into `com.inductiveautomation.perspective/page-config/config.json`:
   - Update or add HMI route entries from the generated `pages`.
   - **Do not remove** `sharedDocks`.
   - **Keep** fixed library routes: `/`, `/cfm/settings`, `/cfm/diagnostics`, `/cfm/target-no-route`, `/cfm/tools`, `/cfm/tools/config-converter`.

**Important:** Ignition **replaces** the parent page-config entirely when importing a child project. The site and sample zips ship a **complete** page-config (pages + sharedDocks). Never import a child with empty pages or missing docks.

**Merge example** — before (site zip, library routes only):

```json
"pages": {
  "/cfm/diagnostics": { "title": "Diagnostics", "viewPath": "..." },
  "/cfm/target-no-route": { "title": "Target No Route", "viewPath": "..." },
  "/cfm/settings": { "title": "Settings", "viewPath": "..." }
}
```

After generating routes for a Dashboard item, merge in the new entry:

```json
"/cfm/dashboard": {
  "title": "Dashboard",
  "viewPath": "Config File Menu/Resources/View Dynamic Fallback"
}
```

Leave existing `/cfm/settings`, `/cfm/diagnostics`, `/cfm/target-no-route`, and `sharedDocks` unchanged.

---

## Logo replacement

Logos display immediately after import via **embedded PNG data URIs** in `MenuContent/view.json` (no Image Management step required).

**Repository (maintainers):** edit `config/cfm-logo-source.png`, run `python Config_File_Menu/scripts/build-hmi-menu-sample.py`, then rebuild import zips. Resized outputs live in `config/cfm-logos/`.

**Site/sample zip (integrators):**

| Asset | File in zip | Build output size | Display area | Recommendations |
|-------|-------------|-------------------|--------------|-----------------|
| Large (dock header) | `logo-upload/cfm/cfm-logo-large.png` | max 72×72 px | 144×56 px, contain | PNG RGBA; transparent background; horizontal logos preferred; source ≥144 px wide |
| Small (dock + top bar) | `logo-upload/cfm/cfm-logo-small.png` | max 40×40 px | 40×40 px, contain | PNG RGBA; square or compact mark; source ≥80 px for sharpness |

**After replacing PNG files**, embedded URIs in `MenuContent/view.json` and `Resources/Menu/Menu Top Bar/view.json` do **not** update automatically. With Python 3 on your PATH (no packages required), run:

```bash
python Config_File_Menu/scripts/embed-logos-in-menu-content.py /path/to/extracted-site-folder
```

Then re-zip and import.

**Designer-only alternative:** if Python is not available, open `MenuContent` and `Menu Top Bar` in Designer, select the logo Image components, and paste a `data:image/png;base64,...` URI into the image source binding's `defaultSource` value. You can generate the base64 data URI with any trusted local or online PNG-to-base64 encoder.

**Optional Designer params** on `MenuContent`:

- `logoVariant` — `large` | `small` | other (hide dock logos)
- `logoLinkTarget` — URL when clicking the dock header logo (default `/`)
- `topbar.showSmallLogo` in `menuConfig` — show small logo in top bar (default `true` in templates)

The standard dock starts open, pinned, and in push mode from Python session initialization in `exchange.cfm.runtime`. To change project-wide startup behavior, edit `ensure_dock_defaults(state)` in `scripts/jython_lib/cfm/dock.py`, then rebuild the import zips. The Settings tab controls current-session dock state only.

**Optional Image Management path** (gateway-level, secondary): upload the same PNG files to folder `cfm` under **Tools → Image Management** (from `logo-upload/cfm/` in an extracted child zip, or from `config/cfm-logos/` in the repository), set `params.logoLargePath` and `params.logoSmallPath` to mounted paths (e.g. `/system/images/cfm/cfm-logo-large.png`). Empty params use embedded URIs.

---

## Applying routes to user-specific views

Generated routes default to **`Config File Menu/Resources/View Dynamic Fallback`** (placeholder content). Point each menu `target` at your own Perspective views using one of these paths.

### Path 1 — Shared shell (zip or Designer)

Use **Dynamic Default** output mode with the default Dynamic viewPath. All menu pages use the View Dynamic Fallback placeholder until you replace content inside your views later.

### Path 1b — Create Views (Designer)

Use **Create Views** output mode. **Generate output** produces per-route `viewPath` values (from target URLs) and a **Views** manifest with `view.json` templates to create under your project.

### Path 2 — Per-route custom views (Designer after import)

1. Open **Page Configuration** on the site or sample project.
2. For each menu `target`, change `viewPath` to your view (e.g. `Plant/Areas/Line01/Overview`).
3. Mixed example in `page-config/config.json`:

```json
"/cfm/dashboard": {
  "title": "Dashboard",
  "viewPath": "Plant/Dashboard"
},
"/cfm/areas/area-01/line-01/overview": {
  "title": "Areas - Area 01 - Line 01 - Overview",
  "viewPath": "Plant/Areas/Line01/Overview"
}
```

4. **`viewParams`:** add per-route params if your views need them. Shell views accept `requestedPath` for fallback navigation via `/cfm/target-no-route`.
5. **Direct URLs / bookmarks:** every menu `target` should exist in page-config. Unregistered targets use shell fallback **`/cfm/target-no-route`** — keep that route.
6. **Authorization:** menu `roles` filter visibility only; configure page-level security separately for production.

### Path 3 — Custom view paths in the zip (no Designer)

After generating output in Settings, hand-edit `viewPath` values in the extracted `page-config/config.json` before re-zipping. Regenerate with a different **Dynamic viewPath** if most routes share one non-default view.

---

## Related documentation

- [README.md](README.md) — feature overview and configuration reference
- [DESIGNER_IMPORT_CHECKLIST.md](DESIGNER_IMPORT_CHECKLIST.md) — post-import validation
- [OVERVIEW.md](OVERVIEW.md) — product summary for Exchange

**Renamed artifact:** `config-file-menu-demo.zip` is now **`config-file-menu-sample.zip`**. Use **`config-file-menu-site.zip`** for new production deployments.
