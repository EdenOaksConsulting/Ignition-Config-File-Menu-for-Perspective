#!/usr/bin/env python3
"""Add Tag → Menu and Menu → Routes Settings tabs."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from menu_samples import ROUTES_OUTPUT_DEFAULT, converter_input_snippet, routes_input_snippet
from perspective_helpers import (
    jython_menu_routes_load_script,
    jython_menu_routes_shutdown_script,
    jython_session_block_save,
    jython_tag_menu_generate_script,
)
from view_thumbnails import ensure_view_thumbnails
from yaml_lite import jython_converter_script, jython_routes_generate_script

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MENU_DIR = (
    PROJECT_ROOT
    / "com.inductiveautomation.perspective"
    / "views"
    / "Config File Menu"
    / "Resources"
    / "Menu"
)
SETTINGS_VIEW = MENU_DIR / "Menu Settings" / "view.json"
HELP_VIEW = MENU_DIR / "Menu Settings Help" / "view.json"
RESOURCE_ACTOR = "content-author"
SHELL_VIEW_PATH = "Config File Menu/Resources/View Dynamic Fallback"

MENU_ROUTES_INPUT_DEFAULT = routes_input_snippet()
MENU_ROUTES_LOAD_SCRIPT = jython_menu_routes_load_script(
    MENU_ROUTES_INPUT_DEFAULT,
    ROUTES_OUTPUT_DEFAULT,
    SHELL_VIEW_PATH,
)
MENU_ROUTES_SHUTDOWN_SCRIPT = jython_menu_routes_shutdown_script(SHELL_VIEW_PATH)
ROUTES_SCRIPT = jython_routes_generate_script(SHELL_VIEW_PATH, root_helper="", save_helper="")
CONVERTER_VIEW = MENU_DIR / "Menu Settings Config Converter" / "view.json"

TAG_MENU_SCRIPT = jython_tag_menu_generate_script()

CONVERTER_INSTRUCTIONS = (
    "Prefer JSON for your menu? Convert your menu YAML here.\n\n"
    "1. Paste menu YAML on the left.\n"
    "2. Click **Convert to JSON**.\n"
    "3. Copy the output into the session property `configFileMenu.contentSource`.\n"
    "4. Set `configFileMenu.contentSourceType` to `json`."
)
CONVERTER_INSTRUCTIONS_BASIS = "170px"

HELP_MARKDOWN = """# Config File Menu Help

Config File Menu builds your Perspective navigation — the docked menu, breadcrumbs, and page titles — from one menu configuration written in YAML or JSON.

## Install

1. Import `config-file-menu-library.zip` and keep the default project name `config-file-menu-library`.
2. Import `config-file-menu-sample.zip` (working example) or `config-file-menu-site.zip` (blank starting point).
3. In a browser session, `/` is the landing page, `/cfm/settings` opens these tools, and `/cfm/diagnostics` shows gateway diagnostics.

## Edit The Menu

1. In the Designer, open **Perspective → Session Properties → custom → `configFileMenu`**.
2. Edit `contentSource` — this one value defines the whole menu (YAML or JSON).
3. Set `contentSourceType` to `yaml` or `json` to match the format you used.
4. In **Page Configuration**, add a page whose URL matches each menu `target`.

Menu item options: `expanded: true` starts a section open. `roles` hides items from users without those roles — it does not secure the page itself, so also configure Perspective security on your views and pages.

## Settings Tabs

- **Settings** — menu behavior for your current session: pinned, dock mode, width, theme, logos, footer links.
- **Help** — this page.
- **Tag → Menu** — build menu YAML or JSON from your existing tags.
- **Menu → Routes** — build Page Configuration JSON from your menu, so every `target` has a page.
- **YAML to JSON** — convert menu YAML to JSON.

## Defaults

The menu starts open, pinned, and in push mode. All settings live in one session object — **Perspective → Session Properties → custom → `configFileMenu`**. To change project-wide defaults, edit its boolean `dockPinned`, `dockContentPush` (`true` = push, `false` = cover), and `dockCloseOnOutsideClick` keys. Changes made on the Settings tab last only for the current session.

## All Settings (`configFileMenu`)

Every setting lives in the one session object **Perspective → Session Properties → custom → `configFileMenu`**. Keys are grouped by prefix. Session defaults apply to each new session; the Settings tab overrides them for the current session only.

**content — the menu itself**

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `contentSource` | string | *(stub menu)* | The menu definition (YAML-lite or JSON); drives dock menu, breadcrumbs, titles |
| `contentSourceType` | string | `yaml` | Format of `contentSource`: `yaml` or `json` |
| `contentDockId` | string | `config-file-menu` | Dock ID the menu uses; must match the `sharedDocks` id in Page Configuration |
| `contentBreadcrumbPrefix` | string | `cfm` | Route prefix treated as the root when building breadcrumbs |

**dock — startup + live open/pin/mode**

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `dockOpen` | boolean | `true` | Menu open state; default is the initial state. Start closed: `false` **and** `dockPinned:false` |
| `dockPinned` | boolean | `true` | Pins the menu open (always push + open; no outside-click dismiss) |
| `dockContentPush` | boolean | `true` | `true` = push (menu pushes content aside); `false` = cover (menu overlays content) |
| `dockCloseOnOutsideClick` | boolean | `true` | When open and unpinned, a click outside closes the menu |

**brand — site name and logos**

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `brandSiteName` | string | `Default Site` | Home label at the start of the breadcrumb trail |
| `brandLogoLarge` | string | *(empty)* | Source for the large logo (shown in the menu header); empty uses the embedded default |
| `brandLogoSmall` | string | *(empty)* | Source for the small logo (shown in the top bar); empty uses the embedded default |
| `brandLogoLink` | string | `/` | URL opened when a logo is clicked |

**layout — typography and width**

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `layoutFont` | string | *(empty)* | CSS font-family for the menu (empty = inherit) |
| `layoutFontSize` | string | `14px` | CSS font-size for menu text |
| `layoutWidthOpen` | string | `220px` | Menu/dock width when open |

**show — visibility toggles**

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `showMenuLogo` | boolean | `true` | Show the large logo in the menu header (`false` hides it) |
| `showTopBarClock` | boolean | `true` | Show the top-bar clock. `false` also stops the recurring clock script (poll rate → 0) |
| `clockRefreshSeconds` | integer | `5` | Clock refresh interval in seconds (min 1); `1` = smooth seconds, larger = fewer gateway calls. Ignored when the clock is hidden |
| `showTopBarSmallLogo` | boolean | `true` | Show the small logo in the top bar |
| `showFooterUser` | boolean | `true` | Show the signed-in user block in the menu footer |
| `showFooterSettings` | boolean | `true` | Show the Settings link in the menu footer |
| `showFooterDiagnostics` | boolean | `true` | Show the Diagnostics link in the menu footer |

**route — shell / fallback navigation**

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `routeFallbackEnabled` | boolean | `true` | Enable shell fallback for menu targets that have no page of their own |
| `routeFallbackPath` | string | `/cfm/target-no-route` | Route used when a target has no dedicated page |

**diagnostics — performance logging**

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `perfLogging` | boolean | `false` | Opt-in timing of the script hot paths to the `CFM.perf` logger. Off = zero overhead. Toggle it here on **General → Performance logging**, or set the `CFM.perf` logger to `TRACE`. See the README Logging & health section |

**Runtime-only (leave at defaults):** `routeLogicalPath` (string) — the logical target requested via fallback, for breadcrumbs/titles; `settingsCurrentTab` (integer) — the active Settings tab index.

## Keep These Pages

When editing Page Configuration, keep the built-in pages: `/`, `/cfm/settings`, `/cfm/diagnostics`, `/cfm/target-no-route`, `/cfm/tools`, and `/cfm/tools/config-converter`.
"""


def resource_json() -> dict:
    return {
        "scope": "G",
        "version": 1,
        "restricted": False,
        "overridable": True,
        "files": ["view.json", "thumbnail.png"],
        "attributes": {
            "lastModification": {
                "actor": RESOURCE_ACTOR,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        },
    }


def session_field_save_script(
    state_key: str,
    field_key: str,
    *,
    value_expr: str = "str(self.props.text or '').strip()",
) -> str:
    return jython_session_block_save(state_key, field_key, value_expr)


def session_binding(state_key: str, field_key: str, default: str) -> dict:
    if "\n" in default or '"' in default or "\\" in default:
        transform = (
            "\tif value is None:\n"
            "\t\treturn ''\n"
            "\treturn str(value)"
        )
    else:
        safe_default = default.replace("\\", "\\\\").replace("'", "\\'")
        transform = f"\treturn str(value if value not in (None, '') else '{safe_default}')"
    return {
        "binding": {
            "config": {"path": f"session.custom.configFileMenu.{state_key}.{field_key}"},
            "transforms": [{"code": transform, "type": "script"}],
            "type": "property",
        }
    }


def persist_text_events(state_key: str, field_key: str) -> dict:
    script = session_field_save_script(state_key, field_key)
    return {
        "component": {
            "onActionPerformed": {"config": {"script": script}, "scope": "G", "type": "script"}
        },
        "dom": {
            "onBlur": {"config": {"script": script}, "scope": "G", "type": "script"},
        },
    }


def persist_dropdown_events(state_key: str, field_key: str) -> dict:
    script = session_field_save_script(
        state_key,
        field_key,
        value_expr="str(self.props.value or '')",
    )
    return {
        "component": {
            "onActionPerformed": {"config": {"script": script}, "scope": "G", "type": "script"}
        }
    }


def bound_text_field(
    name: str,
    state_key: str,
    field_key: str,
    default: str,
    basis: str = "200px",
) -> dict:
    return {
        "meta": {"name": name},
        "position": {"basis": basis, "shrink": 0},
        "propConfig": {"props.text": session_binding(state_key, field_key, default)},
        "props": {"text": default, "style": {"fontFamily": "monospace", "fontSize": "14px"}},
        "events": persist_text_events(state_key, field_key),
        "type": "ia.input.text-field",
    }


def bound_dropdown(
    name: str,
    state_key: str,
    field_key: str,
    options: list[dict],
    default: str,
    basis: str = "180px",
) -> dict:
    return {
        "meta": {"name": name},
        "position": {"basis": basis, "shrink": 0},
        "propConfig": {"props.value": session_binding(state_key, field_key, default)},
        "props": {"options": options, "value": default},
        "events": persist_dropdown_events(state_key, field_key),
        "type": "ia.input.dropdown",
    }


def bound_text_area(
    name: str,
    state_key: str,
    field_key: str,
    default: str,
    *,
    basis: str | None = None,
    grow: int = 1,
    monospace: bool = True,
    height: str | None = None,
) -> dict:
    style: dict = {"fontFamily": "monospace", "fontSize": "14px"} if monospace else {"fontSize": "14px"}
    if height:
        style.update({"width": "100%", "height": height, "maxHeight": height, "overflow": "auto"})
    if "padding" not in style:
        style["padding"] = "8px"
    node = {
        "meta": {"name": name},
        "position": {"grow": grow},
        "propConfig": {"props.text": session_binding(state_key, field_key, default)},
        "props": {"text": default, "style": style, "wrap": "off"},
        "events": persist_text_events(state_key, field_key),
        "type": "ia.input.text-area",
    }
    if basis:
        node["position"]["basis"] = basis
    return node


def text_area(name: str, text: str, grow: int = 1, basis: str | None = None) -> dict:
    node = {
        "meta": {"name": name},
        "position": {"grow": grow},
        "props": {
            "text": text,
            "style": {"fontFamily": "monospace", "fontSize": "14px"},
            "wrap": "off",
        },
        "type": "ia.input.text-area",
    }
    if basis:
        node["position"]["basis"] = basis
    return node


def text_field(name: str, text: str, basis: str = "200px") -> dict:
    return {
        "meta": {"name": name},
        "position": {"basis": basis, "shrink": 0},
        "props": {"text": text, "style": {"fontFamily": "monospace", "fontSize": "14px"}},
        "type": "ia.input.text-field",
    }


def dropdown(
    name: str,
    options: list[dict],
    value: str,
    basis: str = "180px",
) -> dict:
    return {
        "meta": {"name": name},
        "position": {"basis": basis, "shrink": 0},
        "props": {"options": options, "value": value},
        "type": "ia.input.dropdown",
    }


FORM_LABEL_BASIS = "140px"
FORM_ROW_GAP = "12px"
FORM_ROW_CLASS = "cfm-menu__settings-form-row"
FORM_LABEL_CLASS = "cfm-menu__settings-form-label"
PANEL_LABEL_CLASS = "cfm-menu__settings-panel-label"
FORM_FIELD_CLASS = "cfm-menu__settings-form-field"
FORM_ACTION_CLASS = "cfm-menu__settings-form-action"
STATUS_LABEL_CLASS = "cfm-menu__settings-status"
OUTPUT_MODE_DYNAMIC = "dynamic"
OUTPUT_MODE_CREATE_VIEWS = "createViews"
OUTPUT_MODE_DYNAMIC_EXPR = (
	"coalesce({session.custom.configFileMenu.settingsMenuRoutes.outputMode}, 'dynamic')='dynamic'"
)
OUTPUT_MODE_CREATE_VIEWS_EXPR = (
	"coalesce({session.custom.configFileMenu.settingsMenuRoutes.outputMode}, 'dynamic')='createViews'"
)


def label(name: str, text: str, basis: str = FORM_LABEL_BASIS) -> dict:
    return {
        "meta": {"name": name},
        "position": {"basis": basis, "shrink": 0},
        "props": {
            "text": text,
            "style": {
                "classes": FORM_LABEL_CLASS,
                "fontSize": "14px",
                "textAlign": "right",
                "whiteSpace": "nowrap",
            },
        },
        "type": "ia.display.label",
    }


def panel_label(name: str, text: str) -> dict:
    return {
        "meta": {"name": name},
        "position": {"shrink": 0},
        "props": {
            "text": text,
            "style": {
                "classes": PANEL_LABEL_CLASS,
                "fontSize": "14px",
                "fontWeight": "600",
                "textAlign": "left",
            },
        },
        "type": "ia.display.label",
    }


def routes_panel_column(
    column_name: str,
    label_name: str,
    label_text: str,
    field_node: dict,
    *,
    basis: str | None = None,
    grow: int = 1,
    shrink: int = 1,
    display_expr: str | None = None,
) -> dict:
    column = {
        "children": [
            panel_label(label_name, label_text),
            field_node,
        ],
        "meta": {"name": column_name},
        "position": {"grow": grow, "shrink": shrink},
        "props": {
            "direction": "column",
            "style": {
                "boxSizing": "border-box",
                "height": "100%",
                "minHeight": "0",
                "overflow": "hidden",
                "width": "100%",
            },
        },
        "type": "ia.container.flex",
    }
    if basis:
        column["position"]["basis"] = basis
    if display_expr:
        column["propConfig"] = {
            "position.display": {
                "binding": {"config": {"expression": display_expr}, "type": "expr"}
            }
        }
    return column


def form_row_field(field_node: dict) -> dict:
    node = json.loads(json.dumps(field_node))
    position = node.setdefault("position", {})
    position.pop("basis", None)
    position["grow"] = 1
    position["shrink"] = 1
    style = node.setdefault("props", {}).setdefault("style", {})
    style["classes"] = FORM_FIELD_CLASS
    style["width"] = "100%"
    style["minWidth"] = "0"
    style["boxSizing"] = "border-box"
    return node


def form_row_with_display(
    row_name: str,
    label_name: str,
    label_text: str,
    field_node: dict,
    display_expr: str,
) -> dict:
    row = form_row(row_name, label_name, label_text, field_node)
    row["propConfig"] = {
        "position.display": {
            "binding": {"config": {"expression": display_expr}, "type": "expr"}
        }
    }
    return row


def form_row(
    row_name: str,
    label_name: str,
    label_text: str,
    field_node: dict,
) -> dict:
    return {
        "meta": {"name": row_name},
        "position": {"shrink": 0},
        "props": {
            "alignItems": "center",
            "direction": "row",
            "wrap": "nowrap",
            "style": {
                "classes": FORM_ROW_CLASS,
                "boxSizing": "border-box",
                "gap": FORM_ROW_GAP,
                "padding": "4px 16px",
                "width": "100%",
            },
        },
        "type": "ia.container.flex",
        "children": [
            label(label_name, label_text),
            form_row_field(field_node),
        ],
    }


def action_row(button_node: dict, *, name: str = "ActionRow") -> dict:
    button = json.loads(json.dumps(button_node))
    button.setdefault("position", {})["shrink"] = 0
    button["position"].pop("grow", None)
    button.setdefault("props", {}).setdefault("style", {})["classes"] = FORM_ACTION_CLASS
    return {
        "meta": {"name": name},
        "position": {"shrink": 0},
        "props": {
            "alignItems": "center",
            "direction": "row",
            "wrap": "nowrap",
            "style": {
                "classes": FORM_ROW_CLASS,
                "boxSizing": "border-box",
                "gap": FORM_ROW_GAP,
                "padding": "8px 16px 4px",
                "width": "100%",
            },
        },
        "type": "ia.container.flex",
        "children": [
            {
                "meta": {"name": "ActionRowSpacer"},
                "position": {"basis": FORM_LABEL_BASIS, "shrink": 0},
                "props": {
                    "text": "",
                    "style": {"classes": FORM_LABEL_CLASS},
                },
                "type": "ia.display.label",
            },
            button,
        ],
    }


def settings_view_root_style(*, overflow: str = "hidden") -> dict:
    return {
        "boxSizing": "border-box",
        "height": "100%",
        "overflow": overflow,
        "width": "100%",
    }


def button(name: str, text: str, script: str) -> dict:
    return {
        "events": {
            "component": {
                "onActionPerformed": {
                    "config": {"script": script},
                    "scope": "G",
                    "type": "script",
                }
            }
        },
        "meta": {"name": name},
        "position": {"basis": "160px", "shrink": 0},
        "props": {"text": text, "style": {"alignSelf": "flex-start"}},
        "type": "ia.input.button",
    }


def tag_menu_form_rows() -> list[dict]:
    return [
        form_row(
            "TagPathRow",
            "TagPathLabel",
            "Tag path",
            bound_text_field(
                "TagPathInput",
                "settingsTagMenu",
                "tagPath",
                "[default]",
            ),
        ),
        form_row(
            "RoutePrefixRow",
            "RoutePrefixLabel",
            "Route prefix",
            bound_text_field(
                "RoutePrefixInput",
                "settingsTagMenu",
                "routePrefix",
                "/cfm",
            ),
        ),
        form_row(
            "MaxDepthRow",
            "MaxDepthLabel",
            "Max levels",
            bound_text_field("MaxDepthInput", "settingsTagMenu", "maxDepth", "2"),
        ),
        form_row(
            "IncludeRow",
            "IncludeLabel",
            "Include",
            bound_dropdown(
                "IncludeDropdown",
                "settingsTagMenu",
                "includeMode",
                [
                    {"label": "Folders and UDTs", "value": "all"},
                    {"label": "UDT instances only", "value": "udt"},
                    {"label": "Folders only", "value": "folder"},
                ],
                "all",
            ),
        ),
        form_row(
            "FormatRow",
            "FormatLabel",
            "Output",
            bound_dropdown(
                "OutputFormatDropdown",
                "settingsTagMenu",
                "outputFormat",
                [
                    {"label": "YAML", "value": "yaml"},
                    {"label": "JSON", "value": "json"},
                ],
                "yaml",
            ),
        ),
        form_row(
            "LeavesRow",
            "LeavesLabel",
            "UDT leaves",
            bound_dropdown(
                "AppendLeavesDropdown",
                "settingsTagMenu",
                "appendLeaves",
                [
                    {"label": "None", "value": "false"},
                    {"label": "Overview + Details", "value": "true"},
                ],
                "false",
            ),
        ),
        form_row(
            "FolderIconRow",
            "FolderIconLabel",
            "Folder icon",
            bound_text_field(
                "FolderIconInput",
                "settingsTagMenu",
                "folderIcon",
                "material/folder",
            ),
        ),
        form_row(
            "UdtIconRow",
            "UdtIconLabel",
            "UDT icon",
            bound_text_field(
                "UdtIconInput",
                "settingsTagMenu",
                "udtIcon",
                "material/settings",
            ),
        ),
        action_row(button("GenerateTagMenuButton", "Generate menu", TAG_MENU_SCRIPT)),
    ]


def routes_form_rows() -> list[dict]:
    return [
        form_row(
            "MenuTypeRow",
            "MenuTypeLabel",
            "Input type",
            dropdown(
                "MenuTypeDropdown",
                [
                    {"label": "YAML", "value": "yaml"},
                    {"label": "JSON", "value": "json"},
                ],
                "yaml",
            ),
        ),
        form_row(
            "OutputModeRow",
            "OutputModeLabel",
            "Output mode",
            bound_dropdown(
                "OutputModeDropdown",
                "settingsMenuRoutes",
                "outputMode",
                [
                    {"label": "Dynamic Default", "value": OUTPUT_MODE_DYNAMIC},
                    {"label": "Create Views", "value": OUTPUT_MODE_CREATE_VIEWS},
                ],
                OUTPUT_MODE_DYNAMIC,
            ),
        ),
        form_row_with_display(
            "ShellViewRow",
            "ShellViewLabel",
            "Dynamic viewPath",
            bound_text_field(
                "ShellViewInput",
                "settingsMenuRoutes",
                "shellViewPath",
                SHELL_VIEW_PATH,
            ),
            OUTPUT_MODE_DYNAMIC_EXPR,
        ),
        action_row(
            button("GenerateOutputButton", "Generate output", ROUTES_SCRIPT),
            name="RoutesActionRow",
        ),
    ]


def _routes_views_output_area() -> dict:
    node = bound_text_area(
        "ViewsOutput",
        "settingsMenuRoutes",
        "viewsOutput",
        "",
        grow=1,
    )
    node["position"]["shrink"] = 1
    node["props"]["style"].update(
        {
            "boxSizing": "border-box",
            "height": "100%",
            "maxHeight": "none",
            "minHeight": "0",
            "overflow": "auto",
            "width": "100%",
        }
    )
    return node


def routes_text_area(
    name: str,
    text: str,
    *,
    basis: str | None = None,
    grow: int = 1,
    shrink: int = 1,
    full_height: bool = True,
    display_expr: str | None = None,
) -> dict:
    node = text_area(name, text, grow=grow, basis=basis)
    node["position"]["shrink"] = shrink
    if full_height:
        node["props"]["style"].update(
            {
                "boxSizing": "border-box",
                "height": "100%",
                "minHeight": "0",
                "width": "100%",
            }
        )
    if display_expr:
        node["propConfig"] = {
            "position.display": {
                "binding": {"config": {"expression": display_expr}, "type": "expr"}
            }
        }
    return node


def build_tag_menu_view() -> dict:
    return {
        "custom": {},
        "params": {},
        "props": {"defaultSize": {"height": 720, "width": 1100}},
        "root": {
            "children": [
                {
                    "meta": {"name": "Instructions"},
                    "position": {"basis": "210px", "shrink": 0},
                    "props": {
                        "source": (
                            "Build menu items from your existing tags. Use this page in a running "
                            "**Perspective Browser session** — tag browsing does not work in the Designer preview.\n\n"
                            "1. Enter a **tag path**, for example `[default]Site/Area 1`.\n"
                            "2. Click **Generate menu**.\n"
                            "3. Edit the generated menu YAML in the output box or text editor as needed — labels, icons, targets.\n"
                            "4. Copy the output into the session property `configFileMenu.contentSource`.\n"
                            "5. Optional: paste the same YAML into **Menu → Routes** to build the matching Page Configuration pages.\n\n"
                            "**Max levels** sets how many folder levels to include (1 = direct children only)."
                        ),
                        "style": {"padding": "8px 16px"},
                    },
                    "type": "ia.display.markdown",
                },
                *tag_menu_form_rows(),
                {
                    "meta": {"name": "StatusLabel"},
                    "position": {"basis": "28px", "shrink": 0},
                    "props": {
                        "text": "Ready.",
                        "style": {
                            "classes": STATUS_LABEL_CLASS,
                        },
                    },
                    "type": "ia.display.label",
                },
                {
                    "children": [
                        bound_text_area(
                            "TagMenuOutput",
                            "settingsTagMenu",
                            "output",
                            "",
                            grow=1,
                            height="400px",
                        ),
                    ],
                    "meta": {"name": "OutputPanel"},
                    "position": {"grow": 1, "shrink": 1},
                    "props": {
                        "direction": "column",
                        "style": {
                            "boxSizing": "border-box",
                            "minHeight": "0",
                            "overflow": "hidden",
                            "padding": "0 16px 16px",
                            "width": "100%",
                        },
                    },
                    "type": "ia.container.flex",
                },
            ],
            "meta": {"name": "root"},
            "props": {"direction": "column", "style": settings_view_root_style()},
            "type": "ia.container.flex",
        },
    }


def build_routes_view() -> dict:
    return {
        "custom": {},
        "params": {},
        "props": {"defaultSize": {"height": 720, "width": 1100}},
        "root": {
            "children": [
                {
                    "meta": {"name": "Instructions"},
                    "position": {"basis": "210px", "shrink": 0},
                    "props": {
                        "source": (
                            "Every menu `target` needs a matching page in **Page Configuration** — "
                            "this tool builds that page list from your menu.\n\n"
                            "1. Paste your menu YAML or JSON on the left.\n"
                            "2. Choose an **Output mode**:\n"
                            "   - **Dynamic Default** — every page shares one view (**Dynamic viewPath**); the quickest way to start.\n"
                            "   - **Create Views** — every page gets its own `viewPath`, plus a **Views manifest** listing the views to create in the Designer.\n"
                            "3. Click **Generate output**.\n"
                            "4. In your project import zip (site or sample), merge the output into "
                            "`com.inductiveautomation.perspective/page-config/config.json` before importing — "
                            "keep the existing `sharedDocks` and built-in pages such as `/cfm/settings` and `/cfm/diagnostics`."
                        ),
                        "style": {"padding": "8px 16px"},
                    },
                    "type": "ia.display.markdown",
                },
                *routes_form_rows(),
                {
                    "meta": {"name": "RoutesStatusLabel"},
                    "position": {"basis": "28px", "shrink": 0},
                    "props": {
                        "text": "Ready.",
                        "style": {
                            "classes": STATUS_LABEL_CLASS,
                        },
                    },
                    "type": "ia.display.label",
                },
                {
                    "children": [
                        routes_panel_column(
                            "MenuInputColumn",
                            "MenuInputLabel",
                            "Menu input",
                            routes_text_area(
                                "MenuInput",
                                MENU_ROUTES_INPUT_DEFAULT,
                            ),
                            basis="calc(50% - 8px)",
                        ),
                        {
                            "children": [
                                routes_panel_column(
                                    "RoutesOutputColumn",
                                    "RoutesOutputLabel",
                                    "Routes output",
                                    routes_text_area(
                                        "RoutesOutput",
                                        ROUTES_OUTPUT_DEFAULT,
                                    ),
                                ),
                                routes_panel_column(
                                    "ViewsOutputColumn",
                                    "ViewsOutputLabel",
                                    "Views manifest",
                                    _routes_views_output_area(),
                                    display_expr=OUTPUT_MODE_CREATE_VIEWS_EXPR,
                                ),
                            ],
                            "meta": {"name": "OutputColumn"},
                            "position": {"basis": "calc(50% - 8px)", "grow": 1, "shrink": 1},
                            "props": {
                                "direction": "column",
                                "style": {
                                    "boxSizing": "border-box",
                                    "gap": "16px",
                                    "height": "100%",
                                    "minHeight": "0",
                                    "overflow": "hidden",
                                    "width": "100%",
                                },
                            },
                            "type": "ia.container.flex",
                        },
                    ],
                    "meta": {"name": "Panels"},
                    "position": {"grow": 1, "shrink": 1},
                    "props": {
                        "style": {
                            "boxSizing": "border-box",
                            "gap": "16px",
                            "minHeight": "0",
                            "overflow": "hidden",
                            "padding": "0 16px 16px",
                            "width": "100%",
                        },
                    },
                    "type": "ia.container.flex",
                },
            ],
            "events": {
                "component": {
                    "onStartup": {
                        "config": {"script": MENU_ROUTES_LOAD_SCRIPT},
                        "scope": "G",
                        "type": "script",
                    },
                    "onShutdown": {
                        "config": {"script": MENU_ROUTES_SHUTDOWN_SCRIPT},
                        "scope": "G",
                        "type": "script",
                    },
                }
            },
            "meta": {"name": "root"},
            "props": {"direction": "column", "style": settings_view_root_style()},
            "type": "ia.container.flex",
        },
    }


def make_tab(
    name: str,
    label_text: str,
    tab_index: int,
    min_width: str = "120px",
) -> dict:
    return {
        "children": [
            {
                "meta": {"name": "TabLabel"},
                "position": {"grow": 1},
                "props": {
                    "text": label_text,
                    "textStyle": {
                        "fontSize": "14px",
                        "textAlign": "center",
                        "whiteSpace": "nowrap",
                    },
                },
                "type": "ia.display.label",
            }
        ],
        "events": {
            "dom": {
                "onClick": {
                    "config": {"script": f"\tself.view.custom.currentTabIndex = {tab_index}"},
                    "scope": "G",
                    "type": "script",
                }
            }
        },
        "meta": {"name": name},
        "position": {"shrink": 0},
        "propConfig": {
            "props.style.classes": {
                "binding": {
                    "config": {
                        "struct": {
                            "tabIndex": tab_index,
                            "activeIndex": "{view.custom.currentTabIndex}",
                        },
                        "waitOnAll": True,
                    },
                    "transforms": [
                        {
                            "code": (
                                "\treturn exchange.cfm.runtime.settings_tab_class("
                                "value.get('tabIndex'), value.get('activeIndex'))\n"
                            ),
                            "type": "script",
                        }
                    ],
                    "type": "expr-struct",
                }
            },
        },
        "props": {
            "alignItems": "center",
            "justify": "center",
            "style": {
                "classes": "cfm-menu__settings-tab",
                "cursor": "pointer",
                "minWidth": min_width,
                "padding": "0 16px",
            },
        },
        "type": "ia.container.flex",
    }


def patch_menu_routes_generator_defaults(startup: str) -> str:
    menu_input = json.dumps(MENU_ROUTES_INPUT_DEFAULT)
    routes_default = json.dumps(ROUTES_OUTPUT_DEFAULT)
    block = (
        '\tstate.setdefault("settingsMenuRoutes", {\n'
        f'\t\t"menuInput": {menu_input},\n'
        '\t\t"menuType": "yaml",\n'
        '\t\t"outputMode": "dynamic",\n'
        '\t\t"shellViewPath": "Config File Menu/Resources/View Dynamic Fallback",\n'
        f'\t\t"output": {routes_default},\n'
        '\t\t"viewsOutput": ""\n'
        '\t})\n'
    )
    if "settingsMenuRoutes" in startup:
        return re.sub(
            r'\tstate\.setdefault\("settingsMenuRoutes", \{.*?\}\)\n',
            block,
            startup,
            count=1,
            flags=re.DOTALL,
        )
    return startup.replace(
        '\tstate.setdefault("menuWidthOpen", "220px")\n',
        '\tstate.setdefault("menuWidthOpen", "220px")\n'
        '\tstate.setdefault("settingsTagMenu", {\n'
        '\t\t"tagPath": "[default]",\n'
        '\t\t"routePrefix": "/cfm",\n'
        '\t\t"maxDepth": "2",\n'
        '\t\t"includeMode": "all",\n'
        '\t\t"outputFormat": "yaml",\n'
        '\t\t"appendLeaves": "false",\n'
        '\t\t"folderIcon": "material/folder",\n'
        '\t\t"udtIcon": "material/settings",\n'
        '\t\t"output": ""\n'
        '\t})\n'
        + block,
    )


def patch_settings_view() -> None:
    data = json.loads(SETTINGS_VIEW.read_text(encoding="utf-8"))
    tab_bar = data["root"]["children"][0]
    tab_bar["children"] = [
        make_tab("TabSettings", "Settings", 0, "120px"),
        make_tab("TabHelp", "Help", 1, "100px"),
        make_tab("TabTagMenu", "Tag → Menu", 2, "130px"),
        make_tab("TabMenuRoutes", "Menu → Routes", 3, "150px"),
        make_tab("TabConverter", "YAML to JSON", 4, "140px"),
    ]
    tab_bar["props"]["style"] = {
        "classes": "cfm-menu__settings-tabbar",
    }

    tab_content = data["root"]["children"][1]
    tab_content["propConfig"]["props.path"]["binding"]["transforms"][0]["code"] = (
        "\treturn exchange.cfm.runtime.settings_tab_view_path(value)\n"
    )

    data["root"]["events"]["component"]["onStartup"]["config"]["script"] = (
        "\texchange.cfm.runtime.init_settings_shell_state(self)\n"
    )
    data["root"].setdefault("events", {}).setdefault("dom", {})["onClick"] = {
        "config": {"script": "\texchange.cfm.runtime.close_on_outside_click(self)\n"},
        "scope": "G",
        "type": "script",
    }

    SETTINGS_VIEW.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_config_converter_view() -> None:
    data = json.loads(CONVERTER_VIEW.read_text(encoding="utf-8"))
    script = jython_converter_script()
    yaml_default = converter_input_snippet()

    def walk(node: dict) -> None:
        if not isinstance(node, dict):
            return
        meta = node.get("meta") or {}
        if meta.get("name") == "Instructions":
            node.setdefault("props", {})["source"] = CONVERTER_INSTRUCTIONS
            node.setdefault("position", {})["basis"] = CONVERTER_INSTRUCTIONS_BASIS
        elif meta.get("name") == "ConvertButton":
            node.setdefault("events", {}).setdefault("component", {})["onActionPerformed"] = {
                "config": {"script": script},
                "scope": "G",
                "type": "script",
            }
        elif meta.get("name") == "YamlInput":
            node.setdefault("props", {})["text"] = yaml_default
        for child in node.get("children") or []:
            walk(child)

    walk(data.get("root") or {})
    CONVERTER_VIEW.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_help_view() -> None:
    # HELP_MARKDOWN is the single source for Help content and already reflects the
    # current runtime (Settings → General for footer/top-bar toggles). Write it as-is.
    data = json.loads(HELP_VIEW.read_text(encoding="utf-8"))
    data["root"]["children"][0]["props"]["source"] = HELP_MARKDOWN
    HELP_VIEW.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_view_folder(folder_name: str, view_data: dict) -> None:
    folder = MENU_DIR / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "view.json").write_text(json.dumps(view_data, indent=2) + "\n", encoding="utf-8")
    (folder / "resource.json").write_text(
        json.dumps(resource_json(), indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_view_folder("Menu Settings Tag Menu", build_tag_menu_view())
    write_view_folder("Menu Settings Menu Routes", build_routes_view())
    patch_config_converter_view()
    patch_settings_view()
    patch_help_view()
    thumbs = ensure_view_thumbnails(MENU_DIR.parent.parent, force=True)
    print("Wrote Menu Settings Tag Menu and Menu Settings Menu Routes")
    print("Patched Menu Settings tab bar (5 tabs)")
    print(f"View thumbnails created: {thumbs}")


if __name__ == "__main__":
    main()
