# Config File Menu — Overview

**Generate your entire Perspective navigation from one configuration file — YAML or JSON drives nested menus, icons, breadcrumbs, and page titles that stay in sync on every publish.**

**Author:** EdenOaks Consulting  
**Maintainer:** Matt McPheeters  
**License:** [MIT](LICENSE)

---

## What it does

Config File Menu turns your Perspective navigation into **data you can generate and maintain outside Designer**. Define labels, icons, routes, nested sections, and optional role visibility once in `configFileMenu.contentSource`; the docked side menu, top-bar breadcrumbs, and sample page titles are built from that same definition at runtime.

**Advantages of configuration-file menu generation:**

- **Single source of truth** — One parameter drives the dock, breadcrumbs, and titles; no per-link embeds to keep aligned.
- **Fast iteration** — Add sites, reorder sections, or change icons by editing text, then publish.
- **Version-control friendly** — Store menu structure in git alongside your project, or generate it from templates and scripts.
- **Portable authoring** — Start from sample YAML/JSON, convert between formats in Settings, or produce config from external tooling.
- **No runtime dependencies** — No database, custom modules, or Python libraries required.

## Why use it

- **One place to edit the menu** — Update `configFileMenu.contentSource` in Session Properties; the dock, breadcrumbs, and titles stay in sync.
- **Nested navigation without manual wiring** — Unlimited depth via `children`, with icons at every level.
- **YAML or JSON** — Author in YAML-lite for readability, or JSON for structured editing; a built-in converter tab helps during setup.
- **Responsive by design** — Push/cover dock modes, pin, hamburger controls, and optional click-outside close.
- **Host-project friendly** — Advanced Stylesheet overlays CFM CSS on gateway light/dark or custom themes.
- **Role-aware visibility** — Optional `roles` per item (convenience only; enforce access on destination pages).

## Quick start

1. Import **`config-file-menu-library.zip`** first with project name exactly `config-file-menu-library`.
2. Choose one child zip:
   - **`config-file-menu-sample.zip`** to learn with a working reference project.
   - **`config-file-menu-site.zip`** to start a blank production site.
3. Set Session Properties **theme** to **`light`** or **`dark`**.
4. For the sample, launch **`/cfm/dashboard`**.
5. For a blank site, edit **Session Properties → custom → `configFileMenu` → `contentSource`**, add routes for each menu `target`, then publish.

Use the generated import zips directly: import `config-file-menu-library.zip` first with project name exactly `config-file-menu-library`, then import either `config-file-menu-sample.zip` or `config-file-menu-site.zip`. See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step site customization.

## Menu configuration example

```yaml
menu:
  items:
    - label: Dashboard
      icon: material/home
      target: /cfm/dashboard

    - label: Areas
      icon: material/account_tree
      target: /cfm/areas
      children:
        - label: Area 01
          icon: material/location_city
          target: /cfm/areas/area-01
          children:
            - label: Line 01
              icon: material/precision_manufacturing
              target: /cfm/areas/area-01/line-01
```

Set `contentSourceType` to `yaml` or `json`. Every `target` needs a matching route in `page-config/config.json`.

Samples: [`config/menuSiteTemplate.yaml`](config/menuSiteTemplate.yaml) · [`config/menuSampleConfig.yaml`](config/menuSampleConfig.yaml) · [`config/menuSampleConfig.json`](config/menuSampleConfig.json)

## What's included

| Component | Purpose |
|---|---|
| **MenuContent** | Docked responsive menu driven by `configFileMenu.contentSource` |
| **Top Bar** | Hamburger, breadcrumbs, datetime clock |
| **Settings hub** | Preferences, YAML→JSON, Tag→Menu, Menu→Routes, help (`/cfm/settings`) |
| **View Dynamic Fallback** | Shared sample page view for generated routes |
| **Diagnostics Dashboard** | Adapted Exchange #98 page (`/cfm/diagnostics`) |
| **Advanced Stylesheet** | `config/cfm-menu-theme-merge.css` (canonical); `stylesheet/stylesheet.css` generated at build |

## Requirements

| | |
|---|---|
| **Ignition** | 8.3.0+ (Perspective 3.3+) |
| **Modules** | Perspective |
| **Database / tags** | None |

## Integration paths

**Evaluate the sample** — Import library + sample, set theme to light/dark, explore reference routes and Diagnostics.

**Deploy a site** — Import library + site zip; customize menu, routes, and logos in the zip before import ([DEPLOYMENT.md](DEPLOYMENT.md)).

**Add to an existing project** — Import views, merge shared docks and page routes, confirm Advanced Stylesheet is enabled, set Session Properties **theme**, configure `configFileMenu.contentSource`.

## Further reading

| Document | Contents |
|---|---|
| [DEPLOYMENT.md](DEPLOYMENT.md) | Zip-first site deployment, logos, Settings tools, route→view mapping |
| [README.md](README.md) | Full installation, configuration, theming, and troubleshooting |
| [DESIGNER_IMPORT_CHECKLIST.md](DESIGNER_IMPORT_CHECKLIST.md) | Pre-publish verification |
| [ATTRIBUTION.md](ATTRIBUTION.md) | Third-party credits and licenses |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

## License & attribution

Config File Menu is original work by **EdenOaks Consulting**, maintained by **Matt McPheeters**, and licensed under **MIT**.

Inspired by [Artek Responsive Navigation](https://inductiveautomation.com/exchange/2463) (concept only; no Artek source included). Includes an adapted [Diagnostics Dashboard](https://inductiveautomation.com/exchange/98/overview) by Travis Cox.
