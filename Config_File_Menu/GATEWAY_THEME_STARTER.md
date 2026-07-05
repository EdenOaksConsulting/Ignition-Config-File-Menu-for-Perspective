# Gateway Theme Starter

`cfm-gateway-theme-starter.zip` is an advanced, optional artifact for Ignition 8.3+ gateways that need Config File Menu styling installed as a gateway theme instead of using the project Advanced Stylesheet.

Most users should not use it. The normal install path is:

1. Import `config-file-menu-library.zip`.
2. Import `config-file-menu-sample.zip` or `config-file-menu-site.zip`.
3. Use the Advanced Stylesheet that ships with the library.

## When To Use It

Use the gateway theme starter only when a gateway owner wants CFM CSS available as part of a custom Perspective theme across multiple projects, or when a site has an existing theme deployment process that manages CSS outside project resources.

Do not use both the library Advanced Stylesheet and this gateway theme starter for the same CFM CSS rules. Loading both can make style behavior harder to diagnose.

## Build

From the repository root:

```bash
python Config_File_Menu/scripts/build-gateway-theme-starter.py
```

The script writes:

```text
dist/cfm-gateway-theme-starter.zip
```

The zip contains a `gateway-theme-cfm-light/` folder with:

- `index.css`, which imports Ignition's `light` theme, `cfm-menu-theme-merge.css`, and `cfm-overrides.css`.
- `cfm-menu-theme-merge.css`, copied from `Config_File_Menu/config/cfm-menu-theme-merge.css`.
- `cfm-overrides.css`, for site-specific token overrides.
- Ignition theme resource metadata.

## Manual Install

1. Extract `cfm-gateway-theme-starter.zip`.
2. Rename the extracted `gateway-theme-cfm-light` folder for the site, for example `plant-menu-light`.
3. Copy the renamed folder to the gateway theme resources directory:

```text
%IgnitionInstall%/data/config/resources/core/com.inductiveautomation.perspective/themes/
```

4. Edit `cfm-overrides.css` in that folder for site-specific tokens such as menu width, tree indent, or colors.
5. In the Gateway, run **Platform -> Overview -> Scan File System**.
6. In Designer, open the target project and set **Session Properties -> theme** to the renamed custom theme.
7. Save, publish, and hard-refresh Perspective sessions.

## Verify

Open a CFM route such as `/cfm/settings`, then use browser DevTools to confirm `psc-cfm-*` rules are loaded from the custom theme. The Settings tabs, menu hover state, selected menu item, breadcrumb, and folder rows should match the library Advanced Stylesheet appearance.

## Exchange Submission Note

Do not include `cfm-gateway-theme-starter.zip` in the normal Ignition Exchange submission package files. It is an advanced maintainer artifact, not part of the standard import path.
