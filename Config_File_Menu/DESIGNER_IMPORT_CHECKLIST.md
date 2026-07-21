# Designer Import Checklist

Use this checklist after importing the library plus either the sample or site zip into a test gateway. For zip-first customization before import, see [DEPLOYMENT.md](DEPLOYMENT.md).

Use the generated import zips directly: import `config-file-menu-library.zip` first, then import either `config-file-menu-sample.zip` or `config-file-menu-site.zip`.

## Basic Import Checks

1. Import `config-file-menu-library.zip` first.
2. Accept the default project **name** `config-file-menu-library` (do not rename it; child projects inherit by this exact name). The project **title** displays as *Config File Menu Library*.
3. Confirm **inheritable** is enabled on the library project.
4. Import one child project: `config-file-menu-sample.zip` or `config-file-menu-site.zip`.
5. Confirm the child project parent is `config-file-menu-library`.
6. Open the child project, not the library project, for session testing.

For public release review, confirm the Exchange Package tab uses the project/package files from the repository `dist/` folder, especially `config-file-menu-library.zip`, `config-file-menu-sample.zip`, and `config-file-menu-site.zip`. Do not upload the workspace root.

**Page configuration note:** Ignition does not merge parent and child page configs. Child zips ship complete page configuration files with `pages` and `sharedDocks`. If a previous import left an empty page config, delete the child project's `page-config` folder on the gateway and re-import, or re-import the updated zip.

## Sample Launch Checks

Use these checks for **Config File Menu Sample**.

- Set **Session Properties → theme** to `light` or `dark`.
- Launch `/cfm/dashboard`.
- Confirm the left menu dock, top bar, breadcrumbs, datetime, and sample page content appear.
- Open **Session Properties → custom → `configFileMenu`** and confirm `contentSourceType` is `yaml`.
- Confirm `contentSource` contains the sample menu.
- Click several `/cfm/...` sample routes and confirm navigation does not produce route errors.
- Open `/cfm/settings` and confirm the Settings page loads.
- Open `/cfm/diagnostics` and confirm Diagnostics cards load.

## Blank Site Checks

Use these checks for **Config File Menu — Your Site Name**.

- Confirm the project title was renamed if you edited `project.json`.
- Confirm Page Configuration includes the fixed routes `/cfm/settings`, `/cfm/diagnostics`, and `/cfm/target-no-route`.
- Confirm `sharedDocks` is still present.
- Confirm `configFileMenu.contentSource` contains either `items: []` or your customized menu.
- Confirm `contentSourceType` matches the menu text format: `yaml` or `json`.
- Confirm every menu `target` you added has a matching page route.
- Confirm logos display. If you replaced PNGs in an extracted zip, confirm you ran `embed-logos-in-menu-content.py` before re-import.

## Styling Checks

- Confirm **Advanced Stylesheet** is enabled under **Styles** in Designer.
- Set **Session Properties → theme** to `light`, `dark`, or a registered custom gateway theme.
- Confirm the menu has CFM styling, not plain unstyled Perspective containers.
- In browser DevTools, loaded CSS should contain `psc-cfm-menu__settings-tabbar`.
- Resize the session to desktop and mobile widths to confirm responsive behavior.

## Menu And Route Checks

- Confirm only one top-bar toggle icon is visible at a time.
- Confirm the top-bar menu buttons and left dock handle both open and close the menu.
- Toggle the menu header mode icon and confirm the dock switches between cover and push.
- Pin the menu and confirm it stays open in push mode until unpinned.
- Expand and collapse a top-level folder section.
- Navigate to a nested route and confirm breadcrumbs show the expected hierarchy.
- Confirm `/cfm/settings` is restricted to trusted users in production.
- Confirm `/cfm/diagnostics` is hidden, removed, or restricted unless diagnostics are intended for users.
- Confirm page-level authorization is configured separately for production routes; menu `roles` only hide links.

## Optional Advanced Checks

- Copy `config/menuSampleConfig.json` into `contentSource`, set `contentSourceType` to `json`, and confirm the menu still renders.
- On **Tag → Menu**, enter a valid tag path in a live session, click **Generate menu**, and confirm YAML/JSON output appears. Designer preview may not browse tags.
- On **Menu → Routes**, paste sample menu YAML, click **Generate output**, and confirm a `pages` merge JSON snippet is produced.
- Map at least one generated route `viewPath` to a custom Perspective view and confirm navigation loads that view.
- Test users with and without `Operator` or `Administrator` roles to review menu visibility.
- Set `configFileMenu.contentDockId` to match a custom left dock ID when integrating into a host project.
- Tune the Site overrides section in `stylesheet.css` after import, or edit `config/cfm-menu-theme-merge.css` before rebuilding.
