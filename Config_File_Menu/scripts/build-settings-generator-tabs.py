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

HELP_MARKDOWN = """# Config File Menu Help

Config File Menu turns one YAML-lite or JSON configuration into a responsive Ignition Perspective navigation system.

## Import Order

1. Import `config-file-menu-library.zip`.
2. Import `config-file-menu-sample.zip` to explore a reference project, or `config-file-menu-site.zip` to start a blank site.
3. Open `/` for the landing page, `/cfm/settings` for authoring tools, and `/cfm/diagnostics` for evaluation diagnostics.

## Configure The Menu

- Edit `Config File Menu/MenuContent.params.menuConfig`.
- Set `params.menuConfigType` to `yaml` or `json`.
- Each menu item `target` should have a matching Page Configuration route.
- Use `expanded: true` on sections that should start open.
- Use `roles` to hide menu items by user role; still configure page-level security separately.

## Settings Page Tabs

- **Settings** — pinned state, dock mode, outside-click behavior, menu width, top bar logo, and footer links for the current session.
- **Help** — this documentation.
- **Tag → Menu** — browse a tag path and generate a menu branch in a live session.
- **Menu → Routes** — generate `page-config` merge JSON from menu YAML or JSON.
- **YAML to JSON** — convert YAML-lite menu text to JSON.

## Startup Defaults

The standard dock starts open, pinned, and in push mode. Project-wide startup defaults are defined in the `exchange.cfm.runtime` project library script (`ensure_dock_defaults`). The Settings tab changes current-session state only.

## Routes

Keep the fixed routes `/`, `/cfm/settings`, `/cfm/diagnostics`, `/cfm/target-no-route`, `/cfm/tools`, and `/cfm/tools/config-converter` when merging generated page configuration.
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
            "onKeyUp": {"config": {"script": script}, "scope": "G", "type": "script"},
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
	"coalesce({session.custom.configFileMenu.menuRoutesGenerator.outputMode}, 'dynamic')='dynamic'"
)
OUTPUT_MODE_CREATE_VIEWS_EXPR = (
	"coalesce({session.custom.configFileMenu.menuRoutesGenerator.outputMode}, 'dynamic')='createViews'"
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
                "tagMenuGenerator",
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
                "tagMenuGenerator",
                "routePrefix",
                "/cfm",
            ),
        ),
        form_row(
            "MaxDepthRow",
            "MaxDepthLabel",
            "Max levels",
            bound_text_field("MaxDepthInput", "tagMenuGenerator", "maxDepth", "2"),
        ),
        form_row(
            "IncludeRow",
            "IncludeLabel",
            "Include",
            bound_dropdown(
                "IncludeDropdown",
                "tagMenuGenerator",
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
                "tagMenuGenerator",
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
                "tagMenuGenerator",
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
                "tagMenuGenerator",
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
                "tagMenuGenerator",
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
                "menuRoutesGenerator",
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
                "menuRoutesGenerator",
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
        "menuRoutesGenerator",
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
                    "position": {"basis": "120px", "shrink": 0},
                    "props": {
                        "source": (
                            "Browse a **tag provider path** and generate a menu YAML or JSON branch for copy/paste into "
                            "`MenuContent.params.menuConfig`. Run in a **live session** (not Designer preview). "
                            "**Max levels** limits nesting below the browse path (1 = direct children only). "
                            "Field values persist in `session.custom.configFileMenu.tagMenuGenerator` while the session is open."
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
                            "tagMenuGenerator",
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
                    "position": {"basis": "100px", "shrink": 0},
                    "props": {
                        "source": (
                            "Paste **menu YAML or JSON**, then click **Generate output**.\n\n"
                            "**Dynamic Default** — every route uses the **Dynamic viewPath** (default: View Dynamic Fallback). "
                            "Copy the `pages` object into `page-config/config.json`.\n\n"
                            "**Create Views** — each route gets a unique `viewPath` derived from its target URL, "
                            "and a matching `views` manifest for copy/paste view creation. "
                            "Preserve `sharedDocks` and fixed routes (`/cfm/settings`, `/cfm/diagnostics`)."
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
        '\tstate.setdefault("menuRoutesGenerator", {\n'
        f'\t\t"menuInput": {menu_input},\n'
        '\t\t"menuType": "yaml",\n'
        '\t\t"outputMode": "dynamic",\n'
        '\t\t"shellViewPath": "Config File Menu/Resources/View Dynamic Fallback",\n'
        f'\t\t"output": {routes_default},\n'
        '\t\t"viewsOutput": ""\n'
        '\t})\n'
    )
    if "menuRoutesGenerator" in startup:
        return re.sub(
            r'\tstate\.setdefault\("menuRoutesGenerator", \{.*?\}\)\n',
            block,
            startup,
            count=1,
            flags=re.DOTALL,
        )
    return startup.replace(
        '\tstate.setdefault("menuWidthOpen", "220px")\n',
        '\tstate.setdefault("menuWidthOpen", "220px")\n'
        '\tstate.setdefault("tagMenuGenerator", {\n'
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
        if meta.get("name") == "ConvertButton":
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
    data = json.loads(HELP_VIEW.read_text(encoding="utf-8"))
    source = HELP_MARKDOWN
    source = source.replace(
        "Import `config-file-menu.zip` into your Perspective project.",
        "Import `config-file-menu-library.zip` first, then `config-file-menu-site.zip` or `config-file-menu-sample.zip` as the child project.",
    )
    if "Advanced Stylesheet" not in source:
        source = source.replace(
            "4. For host projects, merge `config/cfm-menu-theme-merge.css` into your active theme.",
            "4. Set Session Properties **theme** to **light**, **dark**, or your custom gateway theme. CFM styling comes from the library Advanced Stylesheet (`stylesheet.css`).",
        )
    source = source.replace(
        "- **footer.showSettings** — show Settings link in the menu footer (default on in the demo sample).\n"
        "- **Settings → General → Menu footer user** — show login block in the menu footer.\n"
        "- **Settings → General → Menu footer diagnostics** — show Diagnostics link in the menu footer.\n",
        "- **Settings → General → Menu footer user** — show login block in the menu footer.\n"
        "- **Settings → General → Menu footer settings** — show Settings link in the menu footer.\n"
        "- **Settings → General → Menu footer diagnostics** — show Diagnostics link in the menu footer.\n",
    )
    source = source.replace(
        "- **footer.showUser** — show login block in the menu footer.\n"
        "- **footer.showSettings** — show Settings link in the menu footer (default on in the demo sample).\n"
        "- **footer.showDiagnostics** — show Diagnostics link in the menu footer (default on in the demo sample).\n",
        "- **Settings → General → Menu footer user** — show login block in the menu footer.\n"
        "- **Settings → General → Menu footer settings** — show Settings link in the menu footer.\n"
        "- **Settings → General → Menu footer diagnostics** — show Diagnostics link in the menu footer.\n",
    )
    if "footer.showDiagnostics" not in source:
        source = source.replace(
            "- **footer.showSettings** — show Settings link in the menu footer (default on in the demo sample).\n"
            "- Clock and theme moved to the **top bar** and **Settings** page.\n"
            "- **Diagnostics** is a bundled main menu item at `/cfm/diagnostics`.\n",
            "- **footer.showSettings** — show Settings link in the menu footer (default on in the demo sample).\n"
            "- **footer.showDiagnostics** — show Diagnostics link in the menu footer (default on in the demo sample).\n"
            "- Clock and theme are in the **top bar** and **Settings** page (not footer config flags).\n",
        )
    source = source.replace(
        "### Settings page tabs\n"
        "- **Settings** — pinned, dock mode, outside-click, menu width, top bar logo, footer user/diagnostics.\n"
        "- **YAML to JSON** — convert menu YAML-lite to JSON.\n"
        "- **Tag → Menu** — browse a tag path and generate a menu branch (live session).\n"
        "- **Menu → Routes** — generate `page-config` merge JSON from menu YAML/JSON.\n"
        "- **Help** — this documentation.\n",
        "### Settings page tabs\n"
        "- **Settings** — pinned, dock mode, outside-click, menu width, top bar logo, footer user/diagnostics.\n"
        "- **Help** — this documentation.\n"
        "- **Tag → Menu** — browse a tag path and generate a menu branch (live session).\n"
        "- **Menu → Routes** — generate `page-config` merge JSON from menu YAML/JSON.\n"
        "- **YAML to JSON** — convert menu YAML-lite to JSON.\n",
    )
    if "Tag → Menu" not in source:
        source = source.replace(
            "### Settings page tabs\n"
            "- **Settings** — pinned, dock mode, outside-click, menu width, top bar logo, footer user/diagnostics.\n"
            "- **YAML to JSON** — authoring utility for menu config.\n"
            "- **Help** — this documentation.\n",
            "### Settings page tabs\n"
            "- **Settings** — pinned, dock mode, outside-click, menu width, top bar logo, footer user/diagnostics.\n"
            "- **Help** — this documentation.\n"
            "- **Tag → Menu** — browse a tag path and generate a menu branch (live session).\n"
            "- **Menu → Routes** — generate `page-config` merge JSON from menu YAML/JSON.\n"
            "- **YAML to JSON** — convert menu YAML-lite to JSON.\n",
        )
    data["root"]["children"][0]["props"]["source"] = source
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
    thumbs = ensure_view_thumbnails(MENU_DIR.parent.parent)
    print("Wrote Menu Settings Tag Menu and Menu Settings Menu Routes")
    print("Patched Menu Settings tab bar (5 tabs)")
    print(f"View thumbnails created: {thumbs}")


if __name__ == "__main__":
    main()
