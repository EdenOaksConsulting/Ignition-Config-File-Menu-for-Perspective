# Config File Menu

**Author:** EdenOaks Consulting  
**Maintainer:** Matt McPheeters

Config File Menu is a beginner-friendly Perspective navigation library for Ignition. Import the library once, then import either a sample project to learn from or a blank site project to customize. Your menu lives in one place: the session custom property `configFileMenu.contentSource` (**Perspective → Session Properties → custom**), written as YAML-lite or JSON.

## Start Here

Requirements are intentionally small:

- Ignition **8.3.0+** with the Perspective module.
- No database, tag provider, external Python library, or custom module is required.

Use the import zips in this order:

1. Import **`config-file-menu-library.zip`** first. Accept the default project **name** `config-file-menu-library`; child projects inherit by this exact name. The project **title** displays as *Config File Menu Library*.
2. Import **`config-file-menu-sample.zip`** if you want a working example with sample routes.
3. Import **`config-file-menu-site.zip`** if you want a blank production starting point.

## Quick Start: Try The Sample

1. Import `config-file-menu-library.zip` with project name exactly `config-file-menu-library`.
2. Import `config-file-menu-sample.zip`.
3. Open the **Config File Menu Sample** project in Designer.
4. Set **Session Properties → theme** to `light` or `dark`.
5. Launch `/` for the landing page, or `/cfm/dashboard` for the sample dashboard.
6. Open `/cfm/settings` to try the Settings, YAML to JSON, Tag to Menu, and Menu to Routes tools.

## Quick Start: Start A Blank Site

1. Import `config-file-menu-library.zip` with project name exactly `config-file-menu-library`.
2. Extract `config-file-menu-site.zip` to a working folder.
3. Edit `project.json` to rename **Config File Menu — Your Site Name**.
4. Edit `custom.configFileMenu.contentSource` in `com.inductiveautomation.perspective/session-props/props.json`.
5. Set `custom.configFileMenu.contentSourceType` to `yaml` or `json`.
6. Add or merge page routes for every menu `target` in `com.inductiveautomation.perspective/page-config/config.json`.
7. Replace `logo-upload/cfm/*.png` if desired, then run the logo embed helper.
8. Re-zip the folder contents and import the site zip.
9. Set **Session Properties → theme** to `light` or `dark`, then launch your site.

For detailed zip editing, route generation, and logo steps, follow [DEPLOYMENT.md](DEPLOYMENT.md). For a short public overview, see [OVERVIEW.md](OVERVIEW.md).

## Overview

Config File Menu is a **config-driven Perspective navigation system**. Instead of rebuilding menu links, nested sections, icons, and breadcrumbs in Designer every time your application structure changes, you define the menu once in `configFileMenu.contentSource`.

That configuration ships in `session.custom.configFileMenu` and applies to every session. The docked menu, top-bar breadcrumbs, and page titles all read from the same object, so edits stay synchronized.

### Why use it

- **One place to edit the menu** — Update `configFileMenu.contentSource` in Session Properties; the dock, breadcrumbs, and titles stay in sync.
- **Nested navigation without manual wiring** — Unlimited depth via `children`, with icons at every level.
- **YAML or JSON** — Author in YAML-lite for readability, or JSON for structured editing; a built-in converter tab helps during setup.
- **Responsive by design** — Push/cover dock modes, pin, hamburger controls, and optional click-outside close.
- **Host-project friendly** — Advanced Stylesheet overlays CFM CSS on your gateway light/dark (or custom) theme.
- **Role-aware visibility** — Optional `roles` per item (convenience only; enforce access on destination pages).

### Beginner workflow

1. Import the library zip.
2. Import either the sample zip or the site zip.
3. Edit `configFileMenu.contentSource`.
4. Make sure every menu `target` has a matching page route.
5. Save and publish.

## Project Layout

```text
Config File Menu/MenuContent       Main docked menu view
Config File Menu/Resources/...     Supporting views used by the menu
com.inductiveautomation.perspective/stylesheet/stylesheet.css
                                   Advanced Stylesheet (generated from merge CSS)
config/cfm-menu-theme-merge.css    Canonical CSS — edit here; CFM rules + default tokens
config/cfm-logo-source.png         Master logo (build resizes to cfm-logos/)
config/cfm-logos/                  Resized large/small PNGs (embedded in MenuContent at build)
config/cfm-theme-options.json      Optional custom gateway theme names for Settings dropdown
config/menuSiteTemplate.yaml       Empty site menu template for copy/paste
config/menuSampleConfig.yaml       YAML-lite sample for copy/paste only
config/menuSampleConfig.json       JSON sample for copy/paste only
```

The Ignition import zips contain `project.json` and Perspective resources. Documentation, sample config files, and screenshots are packaged separately for Exchange upload.

## Included Perspective Views

- `Config File Menu/MenuContent` is the docked responsive menu.
- `Config File Menu/Resources/Menu/Menu Top Bar` provides open/close controls for responsive behavior.
- `Config File Menu/Resources/Menu/Menu Child` renders a single menu row (icon, label, optional expand arrow).
- `Config File Menu/Resources/Menu/Menu Parent` renders top-level sections with an embedded Menu Child header and nested tree.
- `Config File Menu/Resources/Menu/Menu Section User` renders the signed-in user block.
- `Config File Menu/Resources/Menu/Menu Breadcrumb` supports the top bar breadcrumb.
- `Config File Menu/Resources/View Landing` — default informational landing page for `/`.
- `Config File Menu/Resources/View Dynamic Fallback` — registered sample page view (HMI content placeholder).
- `Config File Menu/Resources/View Route Fallback` — `/cfm/target-no-route` route fallback (route-configuration warning).
- `Config File Menu/Resources/Menu/Menu Settings` is the tabbed settings hub (`/cfm/settings`); also linked from the menu footer when **Settings → General → Menu footer settings** is set to **Show**.
- `Config File Menu/Resources/Diagnostics/Diagnostics Dashboard` is the bundled Diagnostics Dashboard (`/cfm/diagnostics`).
- Datetime clock in the top bar (far right), not in the menu footer.
- `Config File Menu/Resources/Menu/Menu Settings Config Converter` — YAML to JSON tab inside Settings.
- `Config File Menu/Resources/Menu/Menu Settings Tag Menu` — browse a tag path and generate a menu YAML/JSON branch.
- `Config File Menu/Resources/Menu/Menu Settings Menu Routes` — generate `page-config` merge JSON from menu YAML/JSON.

## Compatibility

- Minimum Ignition version: **8.3.0** (Perspective 3.3+).
- Required modules: Perspective.
- Database requirements: none.
- Tag requirements: none.
- External Python libraries: none.

## Import Into Ignition Designer

The normal install is library first, then one child project:

| Step | Import | Use |
|---|---|---|
| 1 | `config-file-menu-library.zip` | Shared library parent. Import once per gateway or CFM version. |
| 2A | `config-file-menu-sample.zip` | Learning, evaluation, and reference routes. |
| 2B | `config-file-menu-site.zip` | Blank production starter. |

Child zips are intentionally thin. They contain `project.json`, `page-config`, `MenuContent`, `View Dynamic Fallback`, and editable logo PNGs; they inherit runtime scripts, menu views, Settings, Diagnostics, and the Advanced Stylesheet from the library parent.

When importing `config-file-menu-library.zip`, keep the project **name** exactly `config-file-menu-library`. The project **title** is *Config File Menu Library*.

For public distribution, upload the project/package files from the repository `dist/` folder, especially `config-file-menu-library.zip`, `config-file-menu-sample.zip`, and `config-file-menu-site.zip`. Do not upload the full workspace root; it may contain unrelated projects, archives, local IDE metadata, or development artifacts that are not part of Config File Menu. For local import testing, import `config-file-menu-library.zip`, then either `config-file-menu-sample.zip` or `config-file-menu-site.zip`.

If Designer import fails or the import dialog shows no resources, try **Gateway → Configure → Projects → Import Project** or rebuild the zips:

```bash
python Config_File_Menu/scripts/build-inheritance-zips.py
```

Artifacts are written to `dist/` at the repository root. Build them with `python Config_File_Menu/scripts/build-inheritance-zips.py`.

### Existing Project Integration Path

Use this advanced path when importing the menu into a host project that already has its own branding. Requires Ignition 8.3+.

1. Import the menu views/resources into the host project. Merge shared docks and page routes into the host `page-config/config.json` instead of replacing the host page configuration.
2. Confirm **Advanced Stylesheet** is enabled under **Styles** (`stylesheet.css` ships with the library import).
3. Set **Session Properties → theme** to **`light`**, **`dark`**, or your custom gateway theme name.
4. Add custom gateway theme names to `config/cfm-theme-options.json` and rebuild, or edit the Settings theme dropdown in Designer.
5. Tune site colors and layout in the **Site overrides** section of `stylesheet.css` (or `config/cfm-menu-theme-merge.css` before rebuild).
6. Configure `Config File Menu/configFileMenu.contentSource` and `configFileMenu.contentSourceType`.
7. Add or merge page routes for every configured menu `target`.
8. Save and publish the host project.

The menu functions without a custom gateway theme. It only looks unstyled if the library Advanced Stylesheet is missing or disabled.

## Header Icons

The top bar shows the hamburger, breadcrumbs, a **datetime clock**, and a **small logo** on the far right (hidden on very narrow viewports). It controls the left menu dock through Perspective's native dock API (the left dock handle defaults to **hide**):

- `material/menu` opens the menu dock when it is hidden.
- `material/menu_open` closes the menu dock when it is visible.

The buttons call `system.perspective.openDock()` and `system.perspective.closeDock()` using `configFileMenu.contentDockId` (default `cfm`). Button visibility follows actual dock state: in **push** mode or when **pinned**, the hamburger icons compare viewport width to primary view width so they stay in sync with the dock handle. In **cover** mode (unpinned), icons follow `session.custom.configFileMenu.dockOpen`. The hamburger and dock handle both work when pinned; pin only blocks click-outside dismiss.

Set `configFileMenu.contentDockId` on `Config File Menu/Resources/Menu/Menu Top Bar` to match the dock ID configured in your host project's `page-config/config.json`.

## Configuration: one session object

All project configuration lives in a single session custom object, **`session.custom.configFileMenu`**, shipped with the library (a `session-props` resource) so it exists on import. Edit it in Designer under **Perspective → Session Properties → custom → `configFileMenu`**. The keys are flat and group-prefixed so related settings sort together:

| Group | Keys |
|---|---|
| `content*` | `contentSource` (the menu YAML/JSON), `contentSourceType` (`yaml`/`json`), `contentDockId`, `contentBreadcrumbPrefix` |
| `dock*` | `dockPinned`, `dockContentPush` (`true` = push, `false` = cover), `dockCloseOnOutsideClick`, `dockOpen` (the initial open/closed state) |
| `brand*` | `brandSiteName`, `brandLogoLarge` (menu header), `brandLogoSmall` (top bar), `brandLogoLink` |
| `layout*` | `layoutFont`, `layoutFontSize`, `layoutWidthOpen` |
| `show*` | `showMenuLogo`, `showTopBarClock`, `clockRefreshSeconds`, `showTopBarSmallLogo`, `showFooterUser`, `showFooterSettings`, `showFooterDiagnostics` |
| `route*` | `routeFallbackEnabled`, `routeFallbackPath`, `routeLogicalPath` |

**Set the menu:** edit `configFileMenu.contentSource` (and `contentSourceType`). **Set startup dock behavior:** edit `dockPinned` / `dockContentPush` / `dockCloseOnOutsideClick` (all default `true`). A child project overrides the inherited `configFileMenu` to set its own menu.

See **[CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)** for every key with its type, default, and purpose.

Session-custom defaults apply to every new session, so these are the values a fresh session starts with. Runtime toggles keep the invariants: cover mode is always unpinned, and a pinned dock is always push + open.

**Start the menu closed:** set `dockOpen: false` **together with** `dockPinned: false` (a pinned dock always opens). The physical dock is closed on menu render via the reliable MenuItems binding, so this works even though a shared dock's `onStartup` does not fire reliably in Perspective 8.3.3.

The **Settings** tab changes the **current session only** and overrides these defaults; a Settings override survives page navigation and MenuContent remounts, and a new session returns to the shipped defaults. Settings is not a persistent project-default editor.

## Dock Layout and Click-Outside Close

The bundled demo configures the left menu dock with `content: "push"` by default so the dock handle and hamburger icons stay in sync. Use the menu header **Mode** control to switch to `cover` overlay behavior.

Clicking outside the menu to close it is not built into Perspective docks opened by script. The sample page shell and Settings close the menu when their root container receives a click:

- `configFileMenu.contentDockId` (default `cfm`)
- `configFileMenu.dockCloseOnOutsideClick` (default `true`)

When integrating into a host project, copy that root `onClick` script onto each page view that should dismiss the menu on background click. Set `closeMenuOnOutsideClick` to `false` on pages where background clicks should not close the menu.

**Note:** With `cover` mode, the dock handle and top-bar buttons can briefly disagree on icon state if the handle is used without updating `session.custom.configFileMenu.dockOpen`. The demo relies on session state for icon sync because cover mode does not change primary view width.

## Pin and Dock Mode Controls

`Config File Menu/MenuContent` includes two header icons (dock mode and pin via `system.perspective.alterDock`):

- **Mode** (`material/view_column` = push, `material/layers` = cover): toggles dock `content` between overlay and push. Switching to **cover** unpins automatically.
- **Pin** (`material/lock_open` / `material/lock`): keeps the menu open in **push** mode (blocks click-outside dismiss). Tooltip shows pin state.

Session state is stored on `session.custom.configFileMenu`:

- `isOpen` — menu open/closed (top-bar icons and click-outside)
- `isPinned` — pin lock
- `dockContent` — `cover` or `push`
- `menuConfig` / `menuConfigType` — menu tree text (synced from `MenuContent` on startup)
- `showTopBarSmallLogo` — session override for top-bar small logo visibility
- `showFooterUser` — show login block in menu footer (Settings → General)
- `showFooterSettings` — show Settings link in menu footer (Settings → General)
- `showFooterDiagnostics` — show Diagnostics link in menu footer (Settings → General)
- `breadcrumbPathPrefix` — route prefix omitted from breadcrumbs (default `cfm`)

Set `configFileMenu.contentDockId` on `MenuContent` to match the left dock ID in `page-config/config.json` (default `cfm`).

Each logo is dedicated to one location:

- **Menu header** — the **large** logo (`brandLogoLarge`). Toggle it with `configFileMenu.showMenuLogo` (default on).
- **Top bar** (top right) — the **small** logo (`brandLogoSmall`). Shown when **Settings → General → Top bar small logo** is set to **Show** (session `showTopBarSmallLogo`, default on) and the viewport is wider than 450px.

Site and sample import zips include editable PNGs at **`logo-upload/cfm/cfm-logo-large.png`** and **`logo-upload/cfm/cfm-logo-small.png`**. Logos display immediately after import via embedded PNG data URIs in `MenuContent/view.json`. After replacing PNG files in an extracted zip, run `python Config_File_Menu/scripts/embed-logos-in-menu-content.py <extracted-folder>` before re-importing.

**Maintainers:** replace `config/cfm-logo-source.png` (or edit `config/cfm-logos/*.png` directly), then run `python Config_File_Menu/scripts/build-hmi-menu-sample.py` to refresh embedded URIs and child zip assets.

Set `configFileMenu.brandLogoLarge`, `configFileMenu.brandLogoSmall`, and `configFileMenu.brandLogoLink` (default `/`) only if using **Tools → Image Management** mounted paths instead (upload the same PNGs to gateway folder `cfm`). Logos are clickable and navigate to `brandLogoLink`.

## Configuration Samples

`config/menuSampleConfig.yaml` and `config/menuSampleConfig.json` are samples only. Ignition does not read them automatically. Copy/paste one sample into `configFileMenu.contentSource`, then set `configFileMenu.contentSourceType` to match.

Every configured `target` should have a matching route in `com.inductiveautomation.perspective/page-config/config.json` for **direct browser URLs** and bookmarks. The library also ships **shell fallback navigation** (enabled by default): when a menu `target` is not registered, menu clicks navigate to `/cfm/target-no-route` with the logical path passed as `requestedPath`. Configure fallback on **Settings → General** (`shellFallbackEnabled`, `shellFallbackRoute`). **Keep the fallback route** (default `/cfm/target-no-route`) in page-config — do not delete it when removing other routes. That route uses **`View Route Fallback`** (warning to create a Page Configuration route). Registered menu URLs should map to **`View Dynamic Fallback`** (or your own view) with the HMI content placeholder. Nested menu leaves (Tree) and top-level links both use fallback.

The sample child project includes reference routes for the full menu tree; the site child ships library routes only; the library alone registers Settings, Diagnostics, tools, and `/cfm/target-no-route`.

YAML-lite example:

```yaml
menu:
  items:
    - label: Home
      icon: material/home
      target: /cfm/dashboard

    - label: Areas
      icon: material/folder
      target: /cfm/areas
      children:
        - label: Area 01
          icon: material/folder
          target: /cfm/areas/area-01
          children:
            - label: Line 01
              icon: material/settings
              target: /cfm/areas/area-01/line-01
```

JSON example:

```json
{
  "items": [
    {
      "label": "Home",
      "icon": "material/home",
      "target": "/cfm/dashboard"
    }
  ]
}
```

Top-level entries under `items` become menu sections. Entries without children behave like direct links. Entries with children expand as nested tree sections. YAML-lite may also wrap the list under `menu.items`.

## Breadcrumb Links

`Config File Menu/Resources/Menu/Menu Top Bar` builds breadcrumbs from the current page path. It reads `session.custom.configFileMenu.contentSource` and resolves each breadcrumb segment against the configured menu hierarchy.

Breadcrumb targets resolve in this order:

- Use the matching menu item's explicit `target` when that target exists in Perspective page configuration.
- Otherwise use the cumulative URL path when it exists in Perspective page configuration.
- Otherwise render the breadcrumb as non-clickable.

For example, `/cfm/areas/area-01/line-01` displays `Areas > Area 01 > Line 01` because the route prefix stored in `session.custom.configFileMenu.breadcrumbPathPrefix` (default `cfm`) is omitted from the breadcrumb trail.

## Settings Page

Open **Settings** from the menu footer (shown by default; toggle with **Settings → General → Menu footer settings**) or directly at `/cfm/settings`. The legacy route `/cfm/tools/config-converter` redirects to the same view.

The Settings page has five tabs:

| Tab | Contents |
|-----|----------|
| **Settings** | Pinned, dock mode, close-on-outside-click, menu width (`session.custom.configFileMenu`) |
| **Help** | Quick start, menu schema summary, dock behavior, host integration notes |
| **Tag → Menu** | Browse a tag provider path; generate a menu YAML/JSON branch for review and merge (live session) |
| **Menu → Routes** | Paste menu YAML/JSON; generate a `page-config` `pages` merge snippet (default view: View Dynamic Fallback) |
| **YAML to JSON** | Paste YAML-lite, convert to JSON, copy into `configFileMenu.contentSource` |

### Tag → Menu workflow

1. Open **Settings → Tag → Menu** in a **live Perspective session** (tag browse may fail in Designer preview).
2. Enter a tag path (e.g. `[default]Plant/Areas`), route prefix (e.g. `/cfm/plant`), and **Max levels** (1 = direct children only).
3. Click **Generate menu**, review the output, and merge the branch into `configFileMenu.contentSource`.
4. Field values and last output persist in `session.custom.configFileMenu.tagMenuGenerator` for the session.
5. Optional `sourceTagPath` keys are authoring metadata; the menu ignores unknown fields at runtime.

### Menu → Routes workflow

1. Paste finalized menu YAML or JSON into **Menu → Routes**.
2. Click **Generate routes** and copy the `pages` object into `page-config/config.json` (or into the extracted zip — see [DEPLOYMENT.md](DEPLOYMENT.md)).
3. Preserve `sharedDocks` and fixed routes (`/cfm/settings`, `/cfm/diagnostics`, etc.).
4. Map `viewPath` to your Perspective views in Designer or in the zip before import.

`configFileMenu.contentSource` defines the menu tree (`items` only). Footer links, footer user login, Diagnostics, and top bar logo visibility are controlled in **Settings → General** (session state).

Menu links and breadcrumbs close the dock when unpinned (same as navigating away from the menu).

## Diagnostics Dashboard

The sample project inherits an adapted [Diagnostics Dashboard](https://inductiveautomation.com/exchange/98/overview) (Ignition Exchange #98) from the library under `Config File Menu/Resources/Diagnostics/`. Open it from the **menu footer** (default on; hide in **Settings → General → Menu footer diagnostics**) at `/cfm/diagnostics`.

| Resource | Path |
|---|---|
| Main dashboard | `Config File Menu/Resources/Diagnostics/Diagnostics Dashboard` |
| Section views | `Config File Menu/Resources/Diagnostics/Diagnostics ...` |
| Card shell | `Config File Menu/Resources/Diagnostics/Diagnostics Card` |
| Styling | `cfm-diag__*` classes in the Advanced Stylesheet |

Views were remapped into the CFM namespace from a Gateway export. Card layout styling uses theme CSS and inline tab-panel styles instead of Perspective style-classes. The dashboard page uses CFM click-outside-close behavior and a narrower default width for use under the menu docks.

To hide Diagnostics, Settings, or the footer user block, open **Settings → General**.

To hide the top bar small logo, open **Settings → General** and set **Top bar small logo** to **Hide** (session override for the current session).

Expand chevrons are fixed on the **left** (tree style). To tighten nested child indent, override these CSS tokens (defaults are `10px` each):

- `--cfm-menu-tree-indent` — left padding on the tree container under each section
- `--cfm-menu-tree-indent-step` — extra left padding per nested tree level

Example (gateway theme `cfm-overrides.css`, or the library Advanced Stylesheet):

```css
:root {
  --cfm-menu-tree-indent: 6px;
  --cfm-menu-tree-indent-step: 6px;
}
```

Optional: `--cfm-menu-tree-shift` nudges the whole tree block; `--cfm-menu-tree-expand-margin` adjusts chevron spacing. See `config/cfm-overrides.template.css`.

See [ATTRIBUTION.md](ATTRIBUTION.md) for Diagnostics Dashboard attribution and license.

## Styling and Theming

Config File Menu uses namespaced style classes such as `cfm-menu`, `cfm-menu--open`, `cfm-menu__link`, and `cfm-menu__topbar`. The bundled Diagnostics dashboard uses `cfm-diag__*` classes for card layout. Perspective maps those view class names to DOM selectors prefixed with `psc-`, so the CSS uses selectors like `.psc-cfm-menu__link` and `.psc-cfm-diag__card`.

These classes do not appear under Designer's **Styles** folder because they are defined in the Advanced Stylesheet, not as native Perspective Style Class JSON resources.

### Advanced Stylesheet (primary path)

The library ships `com.inductiveautomation.perspective/stylesheet/stylesheet.css`. Ignition loads it **after** the active gateway theme and **before** project style-classes, so CFM rules inherit host tokens (`--neutral-*`, `--callToAction--color`, etc.) with minimal overrides.

- Set **Session Properties → theme** to **`light`**, **`dark`**, or a custom gateway theme name.
- Add custom theme names to `config/cfm-theme-options.json` and rebuild, or edit the Settings → General theme dropdown in Designer. Theme names must match gateway registration exactly.
- Tune tokens in the **Site overrides** section at the bottom of `config/cfm-menu-theme-merge.css` (or in `stylesheet.css` after import).

```css
:root {
  --cfm-menu-selected-color: var(--callToAction--color, #005eb8);
  --cfm-menu-width-open: 280px;
  --cfm-settings-tab-active-color: var(--callToAction--color, #005eb8);
}
```

The merge CSS maps menu variables to common Perspective theme tokens such as `--neutral-*`, `--topbar--bgColor`, and `--callToAction--color` so the menu can follow host light, dark, or branded themes with minimal changes. Menu hover, open-section, selected link, and tree child highlights all derive from `--cfm-menu-accent-rgb` and related `--cfm-menu-*` tokens in `config/cfm-menu-theme-merge.css` (overriding gateway theme tree rules such as `light.css` `.ia_treeComponent__node--selected`).

### Where To Edit CSS

- **Canonical rules + default tokens (maintainers):** `config/cfm-menu-theme-merge.css`
- **Site token overrides (integrators):** Site overrides section in merge CSS or `stylesheet.css` after import
- **Generated Advanced Stylesheet (do not edit in repo — sync from canonical):** `com.inductiveautomation.perspective/stylesheet/stylesheet.css` — synced by `python scripts/build-hmi-menu-sample.py`; verified by `python scripts/verify-theme-css.py`

### Styling Approaches

| Approach | Best for | Notes |
|---|---|---|
| Library Advanced Stylesheet + light/dark/custom theme | All projects (recommended) | Ships with library import |
| Native Style Classes | Designer GUI editing | Not used by CFM views |
| No custom CSS | Functional-only import | Menu works, but looks unstyled |

## Supported Fields

Each menu item supports `label`, `icon`, `target`, `children`, `expanded`, `visible`, and `roles`.

`expanded` controls the initial open/closed state of a branch. On **top-level sections** (Areas, Operations, Maintenance), it sets whether the section header shows its child tree on first load. On **nested tree items**, it sets each Perspective Tree node's initial `expanded` flag (default `false` when omitted). A section still auto-opens when the current page path is under that section's `target`, even if `expanded: false`.

Icons can be used at every level. Top-level icons are passed to `Menu Child`; leaf child icons are converted to Perspective Tree icon objects automatically. **Do not rely on custom icons for nested tree branch nodes** (items with `children`) — Perspective can throw `React.cloneElement` errors; branch rows use the Tree default folder icons instead. Use conservative icon paths that exist in your Ignition/Perspective version.

## YAML-Lite Rules

YAML-lite mode uses the small parser in `exchange.cfm.runtime` (`scripts/jython_lib/cfm/config.py` in source). Keep the configuration simple: spaces only, two-space indentation, `key: value` pairs, and `- label: Name` list items. Avoid multiline strings, anchors, aliases, complex YAML types, and inline objects.

## How It Works

`Config File Menu/MenuContent` contains one `MenuItems` FlexRepeater. The repeater binds to `view.configFileMenu.contentSource` and `view.configFileMenu.contentSourceType` only (the authored source), then calls `exchange.cfm.runtime.menu_items_transform`. Binding to the params — not the session mirror — means navigation-time session writes do not re-render the whole menu. For `yaml`, Runtime parses YAML-lite text. For `json`, Runtime accepts either a Perspective object/array value or JSON text and generates instances for `Config File Menu/Resources/Menu/Menu Parent`.

`Menu Parent` works for both direct links with no children and expandable sections with nested child items. `MenuContent` startup copies `configFileMenu.contentSource`/`menuConfigType` into `session.custom.configFileMenu` so other views can read them; `Menu Top Bar` breadcrumbs and the shell-page titles resolve against that session copy (they have no direct access to MenuContent's params). View bindings stay intentionally thin: path resolution, logo fallback, dock toggles, settings state, tag-menu generation, and close-on-outside-click behavior delegate to `exchange.cfm.runtime`.

## Security Note

Menu visibility is not authorization. Role-restricted menu entries are only a convenience for hiding menu items. Always enforce actual access control on the destination Perspective pages, views, or actions.

Production projects should also secure the bundled tool routes:

- `/cfm/settings` includes authoring tools such as Tag to Menu and Menu to Routes. Restrict it to trusted users.
- `/cfm/diagnostics` exposes gateway/session/system diagnostic views. Hide, remove, or restrict it unless the target users should see diagnostics.

## Troubleshooting

If the menu shows `Menu YAML Error`, check indentation, missing labels, invalid `children:` blocks, and unsupported inline YAML objects.

If the menu shows `Menu JSON Error`, confirm `configFileMenu.contentSourceType` is `json` and `configFileMenu.contentSource` is an object with an `items` array, a direct array of menu items, or valid JSON text.

If a link does nothing, confirm the target route exists in Perspective page configuration. Breadcrumbs and page titles resolve against the session copy of the menu config, which `MenuContent` (the shared left dock) populates on startup — so if breadcrumbs are blank, confirm `MenuContent` is mounted as a shared dock on the page.

If the menu renders but looks unstyled, confirm **Advanced Stylesheet** is enabled under **Styles** in Designer and that `stylesheet.css` contains `psc-cfm-menu__settings-tabbar`. Re-import the library zip if the stylesheet resource is missing. In DevTools, search loaded CSS for `psc-cfm-menu__settings-tabbar`.

## Logging & health

The runtime logs **genuine faults** to the gateway under stable **`CFM.*`** logger names — without flooding, since these handlers run on every render/navigation. Logging is **additive**: success paths are unchanged (the fail-open role check still fails open; inline UI errors are unchanged).

**Logger names & levels.** Messages go to `CFM` and `CFM.<area>` (`CFM.menu`, `CFM.breadcrumb`, `CFM.nav`, `CFM.config`, `CFM.settings`, `CFM.health`). Adjust verbosity at runtime in **Gateway → Status → Diagnostics → Logs** (changes persist to `wrapper.log`).

| Area | Level | When |
|------|-------|------|
| `CFM.menu` | ERROR | Menu config failed to parse (menu shows the inline error item) |
| `CFM.menu` | WARN | A role check errored; the item is shown anyway (fail-open) |
| `CFM.breadcrumb` | ERROR | Breadcrumb build failed |
| `CFM.nav` | WARN | A menu target has no registered route and no usable fallback |
| `CFM.config` | DEBUG | `get_state` fell back to empty (diagnostic breadcrumb; off by default) |
| `CFM.settings` | WARN | A Settings generator (Tag→Menu / Menu→Routes / YAML→JSON) failed |
| `CFM.health` | INFO/WARN | Result of the **Validate menu config** action |

**Flood-safety.** High-frequency paths use de-duplication — a repeating fault logs **once** (per distinct message) rather than every render; the dedup cache is bounded. Low-frequency, user-triggered paths (Settings actions) log every time. Log messages are prefixed with **`[CFM ...]`** / **`[CFM health]`** so they're easy to scrape for alerting.

**Validate menu config.** On **Settings → General**, the **Validate menu config** button parses the current menu and reports, in the adjacent output and one `CFM.health` line: total items/targets, **missing routes** (targets with no page and no fallback), **duplicate targets**, and a reminder for items using `roles` (visibility only — secure the destination pages).

### Performance

Opt-in timing for the specific script hot paths, logged to the **`CFM.perf`** logger. It is **off by default and zero-overhead when off** — nothing is timed or formatted unless perf logging is enabled — and **flood-safe when on**.

**Two gates, either turns it on:**

- **`CFM.perf` logger level** — set it to `TRACE` in **Gateway → Status → Diagnostics → Logs**. Timings then log at TRACE.
- **`perfLogging` session property** (boolean, default `false`) — toggle **Performance logging** on **Settings → General**, no gateway access needed. When on, timings log at **INFO** so they're visible at default gateway levels.

**What's measured** (each line is `[CFM perf] <label> <ms>ms <extra>`, unit **milliseconds**):

| Label | What | Honors `perfLogging` property |
|-------|------|-------------------------------|
| `breadcrumb.build` | Breadcrumb build per navigation (re-parses config + `getProjectInfo()`) | yes |
| `nav.navigate` | Navigation incl. `getRegisteredPages()`/`getProjectInfo()`; notes `direct`/`fallback`/`unrouted` | yes |
| `menu.render` | Menu parse + tree render | TRACE only¹ |
| `menu.title` | Page-title resolution (parses the menu) | TRACE only¹ |
| `settings.tagMenu` / `settings.menuRoutes` | The Tag→Menu / Menu→Routes generators (user-triggered) | yes |

¹ The menu-structure and title paths deliberately avoid a session read on every navigation, so they are gated on the `CFM.perf` TRACE logger only — the `perfLogging` property does not force them.

`perf(...)` also accepts a **`threshold_ms`** so a caller can surface only slow cases (a timing below the threshold is not logged); the shipped call sites use no threshold (every occurrence logs when enabled). The `[CFM perf]` marker is stable for alert scraping.

> **Scope.** `CFM.perf` measures only these script hot paths. For **gateway-wide** performance use the platform tools: Perspective session/component metrics, the Designer script & transform **profiler**, and the shipped **Diagnostics Dashboard**.

## License

Copyright © 2026 **EdenOaks Consulting**. Config File Menu original work is maintained by **Matt McPheeters** and licensed under the [MIT License](LICENSE). See [ATTRIBUTION.md](ATTRIBUTION.md) for third-party credits (Diagnostics Dashboard, Artek inspiration).

## Acknowledgments

Config File Menu is an original implementation inspired by [Responsive Navigation Menu Using CSS Style Sheets](https://inductiveautomation.com/exchange/2463) by Artek Integrated Solutions on the Ignition Exchange. It is not a fork of that resource; see [ATTRIBUTION.md](ATTRIBUTION.md) for the rewrite statement and third-party credits.
