# Changelog

All notable changes after the **1.0.0** Exchange candidate are documented here.


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
