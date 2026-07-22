# Changelog

All notable changes after the **1.0.0** Exchange candidate are documented here.


## 2.0.2 — 2026-07-21

Internal cleanup. **No behavior change** — the menu, breadcrumbs, titles, dock, and every
setting work exactly as in 2.0.1. Re-import is not required.

### Changed
- **Binding struct members renamed to the session keys they watch.** The MenuItems and
  page-title bindings carried 1.0.0 vocabulary (`paramMenuConfig` / `sessionMenuConfig`
  pairs from the param-vs-session split that 2.0.0 removed). They are now `contentSource`
  and `contentSourceType`. The fallback views declared all four names bound to only two
  distinct expressions, so each menu-source change was evaluated twice; the duplicates are
  collapsed. The names were never read — the transforms resolve the menu from the session
  object — so rendering is identical.
- `build-gateway-theme-starter.py` stages under the system temp dir instead of `dist/`.
  It previously removed only its inner folder, leaving an empty `dist/staging/` after every
  run and a full tree after an interrupted one.

### Fixed
- Removed build patchers stranded by the 2.0.0 refactor. One of them,
  `apply-menu-sample-config.py`, wrote `MenuContent.params.menuConfig` — a param 2.0.0
  deleted — back onto the view on every run, and nothing downstream cleaned it, so the dead
  params would have shipped in a later library zip. The others had no callers or targeted
  anchors that no longer exist.
- `dist/README.md` documented the old staging location.

### Added
- **View-param guard** (`scripts/verify_view_params.py` + a test): no view may declare a
  param the 2.0.0 refactor moved into the session object, and `MenuContent` must declare
  none at all. This closes the surface the doc guard cannot see.


## 2.0.1 — 2026-07-21

Documentation only. **No runtime, view, or stylesheet changes** — the import zips are
functionally identical to 2.0.0, so there is no need to re-import if you are already on it.

### Fixed
- **Docs still described the removed 1.0.0 schema.** 2.0.0 moved every setting into
  `session.custom.configFileMenu`, but 33 references to the old view params and flat state
  keys survived the refactor. `DESIGNER_IMPORT_CHECKLIST.md` told readers to confirm
  `params.menuConfigType`, and `OVERVIEW.md` told them to edit
  `MenuContent.params.menuConfig` — both removed by 2.0.0. Also corrected: the MenuItems
  binding description (it reads the session object, not view params) and a paragraph
  describing a startup copy that the refactor deleted.
- Renamed throughout: `menuConfig` → `contentSource`, `menuConfigType` → `contentSourceType`,
  `menuDockId` → `contentDockId`, `isPinned` → `dockPinned`, `dockContent` → `dockContentPush`,
  `shellFallbackEnabled`/`shellFallbackRoute` → `routeFallbackEnabled`/`routeFallbackPath`,
  `breadcrumbPathPrefix` → `contentBreadcrumbPrefix`.

### Added
- **Doc-drift guard** (`scripts/verify_doc_keys.py` + a test): every `configFileMenu.<key>`
  in a doc is checked against the live key set — `session-props` plus the runtime's
  `setdefault` keys — and the removed names are rejected by name, so a failure reports what
  to write instead.
- **Public-snapshot guard** (`scripts/verify_public_snapshot.py` + a test) and a `pre-push`
  hook that blocks publishing maintainer-only files. Enable with
  `git config core.hooksPath Config_File_Menu/scripts/hooks`.


## 2.0.0 — 2026-07-21

> **Migration note (schema change).** All configuration moved into a single session
> custom object, **`session.custom.configFileMenu`**, shipped as a `session-props`
> resource. The old per-view `MenuContent` params (`menuConfig`, `menuConfigType`, logos,
> `siteName`, `menuDockId`, …), the three top-level `menuControl*` session props, and the
> old flat state keys (`isPinned`, `dockContent`, `menuMode`, `logicalPagePath`,
> `shellFallback*`, `brandLogoVariant`, `tagMenuGenerator`, `menuRoutesGenerator`, …)
> **no longer exist**. When re-importing over an existing project, refresh the
> `configFileMenu` session custom object from the new `session-props` resource so a stale
> object doesn't shadow the new keys. See `CONFIG_REFERENCE.md` for the full key list.

### Changed
- **Centralized all configuration** into one flat, group-prefixed session object
  `session.custom.configFileMenu` (`content*` / `dock*` / `brand*` / `layout*` / `show*` /
  `route*`), shipped with the library so it exists on import. Removed all MenuContent view
  params and the Designer-vs-session reconciliation; the runtime reads/writes the object
  directly. `dockContent` string became the boolean `dockContentPush`; removed the
  redundant `dockMode` mirror of `dockOpen`.
- **Settings generator state keys renamed** to match the `settings*` grouping:
  `tagMenuGenerator` → **`settingsTagMenu`** and `menuRoutesGenerator` →
  **`settingsMenuRoutes`**. These hold the Settings tab form fields and last output only —
  no menu configuration — so the only effect of the rename is that saved generator field
  values from 1.0.0 are not carried over; re-enter them on the tab.
- **Logos dedicated by location:** the menu header shows the **large** logo (toggled by
  `showMenuLogo`); the top bar shows the **small** logo (`showTopBarSmallLogo`). Replaced
  the `brandLogoVariant` (large/small/other) selector.
- **Stylesheet streamlined:** documented and grouped every `:root` token, hoisted repeated
  literals into tokens (`--cfm-menu-row-height`, `--cfm-menu-arrow-box-size`,
  `--cfm-accent-underline`), routed hardcoded radii through `--cfm-radius`, and merged
  duplicate declaration blocks.
- **Clock refresh default** changed from `1`s to **`5`s** to lower the per-session gateway
  tick cost. Set `clockRefreshSeconds: 1` for a smooth ticking-seconds display.
- **Reduced redundant breadcrumb work on navigation.** The parsed menu items (keyed by
  source/type) and the registered page-url list (`getProjectInfo()`, ~2s TTL) are now
  **cached and shared** across breadcrumb build, navigation, and page-title resolution, so
  the burst of breadcrumb binding re-evaluations Perspective fires per navigation reuses one
  parse and one gateway call instead of repeating both. Both caches are bounded; behavior is
  unchanged. Removed the duplicate `logicalPagePath` key from the Top Bar breadcrumb struct
  (it mirrored `routeLogicalPath`, doubling that binding's trigger for no benefit).

### Added
- **Top-bar clock controls:** `showTopBarClock` (setting it `false` sets the `runScript`
  poll rate to 0, halting the recurring gateway call — not just hiding it) and
  `clockRefreshSeconds` (poll interval in seconds).
- **Reliable "start closed":** the physical dock is applied from the MenuItems binding
  (which fires reliably) instead of the shared dock's `onStartup`.
- **`CONFIG_REFERENCE.md`** documenting every `configFileMenu` key (type / default /
  purpose) plus a manual test-value matrix; the same tables are embedded in the in-app
  Settings → Help tab.
- **pytest test suite** (`tests/`) for the pure runtime logic (config/settings/menu/tree/
  breadcrumb), a **bundle-drift guard** (`scripts/verify_script_library.py` + a test) that
  fails if `code.py` is out of sync with the source modules, and a settings-key
  consistency test.
- **Named-logger observability with de-duplication** (`cfm.log`): genuine faults are
  logged under stable `CFM.*` logger names at runtime-adjustable levels, without
  reintroducing floods (high-frequency paths de-duplicate via `log_once`; user-triggered
  paths use `log_always`). Instruments only the genuine-fault sites (menu/breadcrumb
  parse failures, unrouted navigation, fail-open role check, Settings generator failures);
  the high-frequency probe `except:` blocks stay silent. This is **additive** — no
  existing behavior changes (fail-open still fails open; inline UI errors unchanged).
  See the README **Logging & health** section.
- **Menu-config health check:** a pure `check_menu_health` plus a **Validate menu config**
  action on Settings → General that reports missing routes, duplicate targets, and role
  reminders (to the output label and one `CFM.health` line). Results go to the component
  only — no new session key.
- Added tests `tests/test_log.py` (de-dup core + flood-safety) and `tests/test_health.py`.
- **Opt-in performance logging** (`cfm.log.perf`) on the **`CFM.perf`** logger, timing the
  specific script hot paths (breadcrumb build, navigation, menu render/title, the Settings
  generators). **Off by default and zero-overhead when off** — nothing is timed or
  formatted unless enabled — and flood-safe when on. Two gates turn it on: the `CFM.perf`
  logger at `TRACE`, or a new **`perfLogging`** session property (default `false`) toggled
  from **Settings → General**; when the property is on, timings log at INFO so they are
  visible at default gateway levels. Lines carry the stable `[CFM perf]` marker. Additive:
  no behavior change when disabled. See the README **Logging & health → Performance**
  section; `CFM.perf` covers these script paths only (use the platform profiler / metrics /
  Diagnostics Dashboard for gateway-wide performance).

### Fixed
- Removed a dangling `onPropertyChange` handler on MenuContent that called a function
  deleted during the refactor (would throw at runtime).
- Removed customer-domain artifacts from the public library (a `"crac"→"CRAC"` breadcrumb
  replace and an `["hvac","crac","io"]` uppercase list).
- Simplified a tautological logo-display expression and removed dead generator code;
  routed `menu.py` title/icon lookups through `cfm.config.*` (they used bare names that
  only resolved via bundle flattening).
- Corrected the misleading concurrency comment on `set_state_fields` (it is a whole-object
  last-writer-wins read-modify-write, not a per-key isolated write) and documented the
  intentional fail-open on the menu-item `roles` visibility check.
- **Skip no-op `routeLogicalPath` session writes on navigation.** A direct-hit navigation no
  longer rewrites `routeLogicalPath` when it is already empty, the shell fallback only writes
  when the logical target actually changes, and `sync_shell_session` skips an unchanged write.
  Each avoided whole-object session write is one fewer needless re-fire of the breadcrumb
  binding. Navigation behavior is unchanged.
