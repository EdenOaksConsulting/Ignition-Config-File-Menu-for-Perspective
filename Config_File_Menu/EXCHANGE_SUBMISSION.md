# Exchange Submission Notes

> **Private repo only.** This file is excluded from the public GitHub tree —
> when rebuilding the public `main` squash from `dev`, drop
> `Config_File_Menu/EXCHANGE_SUBMISSION.md` from the tree before committing.

## Overview

Title: Config File Menu for Perspective

Author: EdenOaks Consulting

Maintainer: Matt McPheeters

Tagline: Define your entire Perspective navigation — nested menus, icons, and breadcrumbs — in one YAML or JSON file.

Short description: Config File Menu is a responsive Perspective menu system for Ignition built from a single configuration file. Edit `menuConfig` once to generate nested navigation, icons, breadcrumbs, and optional role-based visibility; the dock, top bar, and page titles stay synchronized at runtime without per-item Designer wiring.

Description: Config File Menu for Perspective turns menu structure into data. Define one YAML or JSON configuration and use it to drive responsive Ignition Perspective navigation. Import `config-file-menu-library.zip` first with project name exactly `config-file-menu-library`, then import the sample child zip to learn or the site child zip to start a blank project. Define your menu as YAML or JSON on `MenuContent.params.menuConfig` — nested sections, Material icons, route targets, expanded state, and optional role filters — and the side dock, breadcrumb bar, and demo page shell all read from the same session-backed config.

The resource includes push/cover dock behavior, pin and hamburger controls, click-outside close, beginner install docs, a tabbed Settings page (preferences, YAML to JSON, Tag to Menu, Menu to Routes, help), host-theme CSS merge for existing branded projects, and a demo HMI route set. An adapted Diagnostics Dashboard (Exchange #98) is bundled for evaluation.

Menu state is kept under a single runtime-created session key (`session.custom.configFileMenu`) — no declared session properties are added, so importing into an existing project will not collide with your session props.

Ideal for integrators who want maintainable, version-controlled navigation without external databases or custom modules. Minimum Ignition 8.3.0; Perspective required. MIT licensed. YAML Ain't Menu Language, but it can drive your Perspective navigation.

Inspired by [Responsive Navigation Menu Using CSS Style Sheets](https://inductiveautomation.com/exchange/2463) by Artek Integrated Solutions. Config File Menu is an original rewrite with config-driven menu content and native Perspective dock control; it does not include Artek source code. Includes an adapted copy of [Diagnostics Dashboard](https://inductiveautomation.com/exchange/98/overview) by Travis Cox. Original work copyright EdenOaks Consulting; maintained by Matt McPheeters; licensed under MIT (see `LICENSE` and `ATTRIBUTION.md`).

## Package

- Resource type: Perspective project/resource.
- Skill level: Beginner to Intermediate.
- Minimum Ignition version: 8.3.0 or newer.
- Required modules: Perspective.
- Other requirements: None.
- Maker Edition compatible: Yes, assuming Perspective is available.



## Suggested Categories

- Visualization
- Navigation / UI
- Scripting / Configuration



## Suggested Tags

- perspective
- menu
- navigation
- yaml
- json
- responsive
- dock
- breadcrumb
- exchange



## Ignition Exchange Submission Files

**This file is maintainer-internal. Never upload EXCHANGE_SUBMISSION.md to the Exchange.**

For the Ignition Exchange **Package Files** upload, use the built artifacts from the repository `dist/` folder. Do not upload the workspace root; it can contain unrelated local projects, archives, IDE metadata, and generated development artifacts.

Upload these project/package files:

- `config-file-menu-library.zip` as the required inheritable library import. Users import this first.
- `config-file-menu-sample.zip` as the evaluation/reference child project. Users import this second if they want the working sample.
- `config-file-menu-site.zip` as the blank production starter child project. Users import this second if they want a clean site starter.

Include these documentation and support files if the Exchange Package tab allows additional files:

- `README.md` as the beginner entry point plus full configuration documentation.
- `DEPLOYMENT.md` as beginner install and zip-first site deployment guide.
- `DESIGNER_IMPORT_CHECKLIST.md` as manual verification guidance.
- `OVERVIEW.md` as a short public introduction for downloaders.
- `CHANGELOG.md` as release history (post-1.0.0; see `docs/archive/CHANGELOG-1.0.0.md` for the initial release).
- `LICENSE` as the MIT license.
- `ATTRIBUTION.md` as inspiration credit and rewrite statement.
- `config/menuSiteTemplate.yaml` as empty site menu copy/paste template.
- `config/menuSampleConfig.yaml` as a YAML-lite copy/paste sample.
- `config/menuSampleConfig.json` as a JSON copy/paste sample.
- `config/cfm-menu-theme-merge.css` as CFM rules + default tokens.
- `scripts/embed-logos-in-menu-content.py` as the standalone logo embed helper; requires only Python 3 (no packages).

For local Gateway or Designer import testing, use the generated project zips directly: import `config-file-menu-library.zip` first with project name exactly `config-file-menu-library`, then `config-file-menu-sample.zip` or `config-file-menu-site.zip`.

Add screenshots through the Exchange listing Images & Screenshots section, showing the expanded menu and demo route.

## Production Security Notes

- `/cfm/settings` contains authoring tools, including Tag to Menu and Menu to Routes. Production projects should restrict this route to trusted users.
- `/cfm/diagnostics` exposes gateway/session/system diagnostic views. Production projects should hide, remove, or restrict this route unless users are intended to see that information.
- Menu `roles` only hide links. Configure actual Perspective page, view, or action authorization separately.

