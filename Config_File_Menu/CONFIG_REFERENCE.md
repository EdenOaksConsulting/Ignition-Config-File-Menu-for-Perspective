# `configFileMenu` — Settings Reference

All Config File Menu configuration lives in **one** Perspective session custom object:

**Perspective → Session Properties → custom → `configFileMenu`**

It ships with the library (a `session-props` resource, `com.inductiveautomation.perspective/session-props/props.json`) fully populated with the defaults below, so it exists the moment you import. Edit its keys in Designer to change project-wide behavior; a child project overrides the whole object to set its own menu.

Keys are flat and **group-prefixed** so related settings sort together: `content*`, `dock*`, `brand*`, `layout*`, `show*`, `route*` (plus two runtime keys). Session-custom **defaults apply to every new session**, so a key's default is the value a fresh session starts with.

The **Settings** tab (`/cfm/settings`) changes these for the **current session only** and overrides the shipped defaults for that session; a new session returns to the defaults.

---

## content — the menu itself

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `contentSource` | string | *(stub menu)* | **The menu definition** — YAML-lite or JSON. This single value drives the docked menu, the top-bar breadcrumbs, and page titles. A child project sets its menu here. |
| `contentSourceType` | string | `"yaml"` | Format of `contentSource`: `"yaml"` or `"json"`. |
| `contentDockId` | string | `"config-file-menu"` | The Perspective dock ID the menu opens/closes. Must match the left dock `id` in your `page-config/config.json` `sharedDocks`. |
| `contentBreadcrumbPrefix` | string | `"cfm"` | Route prefix used when building breadcrumbs. The leading `/cfm` segment is treated as the root so breadcrumbs read cleanly (e.g. `/cfm/plant/area-1` → *Plant › Area 1*). |

## dock — startup + live open/pin/mode

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `dockOpen` | boolean | `true` | Whether the menu is open. Its **default is the initial open/closed state** of a new session. Also updated live as the menu is toggled. To start closed, set `false` **and** set `dockPinned: false` (see below). |
| `dockPinned` | boolean | `true` | Pins the menu open. A pinned dock is always **push + open** and does **not** dismiss on an outside click. Set `false` to allow closing. |
| `dockContentPush` | boolean | `true` | Dock content mode. `true` = **push** (the open menu pushes page content aside); `false` = **cover** (the menu overlays content). Cover mode is always unpinned. |
| `dockCloseOnOutsideClick` | boolean | `true` | When the menu is open and **unpinned**, a click outside it closes the menu. Ignored while pinned. |

> **Invariants** (enforced by the runtime toggles and at startup): a pinned dock is always push + open; cover mode is always unpinned. To start the menu **closed**, use `dockOpen: false` + `dockPinned: false` (a pinned dock always reopens).

## brand — site name and logos

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `brandSiteName` | string | `"Default Site"` | Site name shown as the **home** label at the start of the breadcrumb trail. |
| `brandLogoLarge` | string | `""` | Optional source (Image Management path or URL) for the **large** logo — the one shown in the **menu header**. Empty uses the embedded default PNG shipped in the view. |
| `brandLogoSmall` | string | `""` | Optional source for the **small** logo — the one shown in the **top bar** (top right). Empty uses the embedded default PNG. |
| `brandLogoLink` | string | `"/"` | URL navigated to when a logo is clicked. |

## layout — menu typography and width

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `layoutFont` | string | `""` | CSS `font-family` for the menu. Empty = inherit the theme font. |
| `layoutFontSize` | string | `"14px"` | CSS `font-size` for the menu text. |
| `layoutWidthOpen` | string | `"220px"` | Width of the menu (and its dock) when open. |

## show — visibility toggles

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `showMenuLogo` | boolean | `true` | Show the **large** logo in the menu header. `false` hides it. (The menu is dedicated to the large logo; the small logo lives in the top bar — see `showTopBarSmallLogo`.) |
| `showTopBarClock` | boolean | `true` | Show the top-bar clock. Setting `false` **stops the recurring clock script** (its poll rate drops to 0), not just hides it — the efficient choice for high-session-count deployments. |
| `clockRefreshSeconds` | integer | `5` | How often the clock refreshes, **in seconds** (the poll interval of its gateway script). Default `5` keeps the per-session tick cost low; set `1` for a smooth ticking-seconds display (at ~5× the gateway calls), or larger (e.g. `60`) for even less load. Clamped to a 1-second minimum; ignored when `showTopBarClock` is `false`. |
| `showTopBarSmallLogo` | boolean | `true` | Show the small logo in the top bar. |
| `showFooterUser` | boolean | `true` | Show the signed-in **user** block in the menu footer. |
| `showFooterSettings` | boolean | `true` | Show the **Settings** link (`/cfm/settings`) in the menu footer. |
| `showFooterDiagnostics` | boolean | `true` | Show the **Diagnostics** link (`/cfm/diagnostics`) in the menu footer. |

## route — shell / fallback navigation

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `routeFallbackEnabled` | boolean | `true` | Enable shell-page fallback for menu `target`s that don't have their own registered page. When on, such targets open the fallback route instead of doing nothing. |
| `routeFallbackPath` | string | `"/cfm/target-no-route"` | The route used when `routeFallbackEnabled` is on and a target has no dedicated page. |

## diagnostics — performance logging

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `perfLogging` | boolean | `false` | **Opt-in performance logging.** When `true`, the runtime times specific script hot paths (breadcrumb build, navigation, menu render/title, the Settings generators) and logs them to the **`CFM.perf`** logger at INFO. **Off by default and zero-overhead when off** — nothing is timed or formatted unless it is enabled (either this property or the `CFM.perf` logger at `TRACE`). Toggle it from the app on **Settings → General → Performance logging**. See the README **Logging & health** section. |

These live in the object because the runtime reads and writes them, but they are session state, not project settings. Leave them at their defaults.

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `routeLogicalPath` | string | `""` | Set at runtime to the logical target requested via the fallback route, so breadcrumbs and page titles resolve correctly on shell pages. |
| `settingsCurrentTab` | integer | `0` | Set at runtime to the index of the active Settings tab. |

---

## Manual test values

Edit each key in **Session Properties → custom → `configFileMenu`** (or on the Settings tab where noted), then reload/observe. Alternates below are safe to flip one at a time.

| Key | Default | Alternate to test | What you should see |
|-----|---------|-------------------|---------------------|
| `contentSource` | *(stub)* | `menu:\n  items:\n    - label: Home\n      icon: material/home\n      target: /cfm/dashboard` | Menu renders the new items; breadcrumbs/titles follow |
| `contentSourceType` | `yaml` | `json` (with a JSON `contentSource`) | Menu still parses from JSON |
| `contentDockId` | `config-file-menu` | *(only change with a matching `sharedDocks` id)* | Mismatched id = menu can't open; keep in sync with page-config |
| `contentBreadcrumbPrefix` | `cfm` | `app` (and route under `/app/...`) | Leading prefix segment dropped from breadcrumbs |
| `dockOpen` | `true` | `false` (with `dockPinned:false`) | Menu **starts closed**; hamburger opens it |
| `dockPinned` | `true` | `false` | Menu can be closed; outside-click/close controls become active |
| `dockContentPush` | `true` | `false` | Open menu **overlays** page content (cover) instead of pushing it |
| `dockCloseOnOutsideClick` | `true` | `false` | With menu open + unpinned, clicking the page does **not** close it |
| `brandSiteName` | `Default Site` | `Acme Plant` | Breadcrumb **home** label changes |
| `brandLogoLarge` | `""` | an Image Management path / URL | Large dock logo swaps from the embedded default |
| `brandLogoSmall` | `""` | an Image Management path / URL | Small logo swaps from the embedded default |
| `brandLogoLink` | `/` | `/cfm/dashboard` | Clicking a logo navigates there |
| `showMenuLogo` | `true` | `false` | Menu-header (large) logo hidden; top-bar small logo unaffected |
| `layoutFont` | `""` | `Georgia, serif` | Menu text font changes |
| `layoutFontSize` | `14px` | `18px` | Menu text larger |
| `layoutWidthOpen` | `220px` | `300px` | Open menu is wider |
| `showTopBarClock` | `true` | `false` | Top-bar clock hidden **and** its script stops (check DevTools WS: idle drops to near-zero) |
| `clockRefreshSeconds` | `5` | `1` / `60` | `1` = smooth ticking seconds (more calls); `60` = once a minute (fewer). Watch DevTools WS |
| `showTopBarSmallLogo` | `true` | `false` | Top-bar small logo hidden |
| `showFooterUser` | `true` | `false` | Footer user block hidden |
| `showFooterSettings` | `true` | `false` | Footer Settings link hidden |
| `showFooterDiagnostics` | `true` | `false` | Footer Diagnostics link hidden |
| `routeFallbackEnabled` | `true` | `false` | A menu `target` with no page does nothing (no fallback) |
| `routeFallbackPath` | `/cfm/target-no-route` | `/cfm/dashboard` (a real page) | Unrouted targets land on that page instead |
| `perfLogging` | `false` | `true` (or Settings → General → Performance logging) | `[CFM perf]` timing lines appear on the `CFM.perf` logger as you navigate; `false` = silent, no timing |

> Tip: the **Settings** tab (`/cfm/settings`) exposes the dock, width, footer, and logo toggles as live controls — quickest for a manual click-through without editing the object by hand. It changes the current session only.

## Where to change what

- **The menu:** `contentSource` (+ `contentSourceType`). Use the **Tag → Menu** and **YAML to JSON** Settings tabs to help author it.
- **Startup dock behavior:** `dockPinned`, `dockContentPush`, `dockCloseOnOutsideClick`, `dockOpen`.
- **Branding:** `brandSiteName`, `brandLogo*`.
- **Per-session experiments:** the **Settings** tab (`/cfm/settings`) — it overrides these for the current session without changing the shipped defaults.

**Health check:** on **Settings → General**, the **Validate menu config** button reports missing routes, duplicate targets, and role reminders for the current menu (also logged to `CFM.health`). Genuine runtime faults are logged under `CFM.*` logger names — see the README **Logging & health** section.

For install and deployment steps, see [DEPLOYMENT.md](DEPLOYMENT.md).
