#!/usr/bin/env python3
"""Build generic HMI menu sample: config, routes, page shell, and logo assets."""

from __future__ import annotations

import base64
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required: pip install Pillow") from exc

from menu_samples import (
    library_menu_stub,
    SAMPLE_MENU_JSON_PATH,
    load_sample_menu_yaml,
)
from perspective_helpers import (
    EFFECTIVE_PAGE_PATH_EXPR,
    PATH_LABEL_EXPR,
    jython_footer_visibility_script,
    jython_topbar_small_logo_visible_script,
    jython_navigate_menu_target,
    jython_menu_link_body_click_script,
    jython_section_arrow_click_script,
    jython_section_header_body_click_script,
    jython_section_toggle_message_script,
    jython_section_tree_page_sync_script,
    jython_section_tree_startup_script,
    jython_tree_item_clicked_script,
)
from view_thumbnails import ensure_view_thumbnails
from yaml_lite import (
    jython_title_icon_resolve_script,
    jython_title_resolve_script,
    parse_yaml_lite_items,
    walk_menu_items,
    write_menu_sample_json,
)
from jython_thin import (
    RUNTIME_MODULE,
    thin_breadcrumb_instances,
    thin_menu_items_transform,
    thin_close_outside_click,
    thin_dock_mode_toggle,
    thin_dock_pin_toggle,
    thin_menu_content_startup,
    thin_menu_content_property_change,
    thin_menu_toggle_click,
    thin_settings_dock_content_change,
    thin_settings_general_startup,
    thin_settings_menu_width_change,
    thin_settings_pinned_change,
    thin_shell_startup,
    thin_topbar_toggle_classes,
    thin_topbar_toggle_icon,
    thin_topbar_startup,
)
from build_script_library import install_script_library

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_JSON = PROJECT_ROOT / "project.json"
PERSPECTIVE = PROJECT_ROOT / "com.inductiveautomation.perspective"
VIEWS = PERSPECTIVE / "views" / "Config File Menu"
PAGE_CONFIG = PERSPECTIVE / "page-config" / "config.json"
SHELL_VIEW = VIEWS / "Resources" / "View Dynamic Fallback"
ROUTE_FALLBACK_VIEW = VIEWS / "Resources" / "View Route Fallback"
LANDING_VIEW = VIEWS / "Resources" / "View Landing"
SHELL_VIEW_PATH = "Config File Menu/Resources/View Dynamic Fallback"
ROUTE_FALLBACK_VIEW_PATH = "Config File Menu/Resources/View Route Fallback"
LANDING_VIEW_PATH = "Config File Menu/Resources/View Landing"
SHELL_FALLBACK_ROUTE = "/cfm/target-no-route"
SHELL_FALLBACK_PAGE_TITLE = "Target No Route"

SHELL_HMI_PLACEHOLDER_TEXT = "Replace this placeholder with your HMI screen content."
SHELL_ROUTE_PLACEHOLDER_TEXT = (
    "Create a Page Configuration route for the menu path shown above.\n\n"
    "In Designer, open Page Configuration and add a pages entry for that URL "
    "(or use Settings → Menu → Routes to generate a merge snippet). Set viewPath to your "
    "HMI screen or to View Dynamic Fallback. This "
    + SHELL_FALLBACK_ROUTE
    + " route uses View Route Fallback only."
)
LANDING_MARKDOWN = """# Config File Menu for Perspective

This project turns one YAML-lite or JSON menu configuration into a responsive Ignition Perspective navigation system.

## Start Here

- Open `/cfm/settings` for Settings, Help, Tag to Menu, Menu to Routes, and YAML to JSON tools.
- Edit `Config File Menu/MenuContent.params.menuConfig` to define the menu tree.
- Add Page Configuration routes for each menu `target`.
- Use `/cfm/diagnostics` to review the bundled diagnostics dashboard during evaluation.

## Dock Defaults

The standard layout starts open, pinned, and in push mode. Project-wide startup defaults live in the `exchange.cfm.runtime` project library script (`ensure_dock_defaults`).

## Next Step

For a blank production site, import `config-file-menu-library.zip` first, then `config-file-menu-site.zip`. For a reference project with sample routes, import `config-file-menu-sample.zip` after the library.
"""
LOGOS_DIR = PROJECT_ROOT / "config" / "cfm-logos"
LOGO_LARGE = LOGOS_DIR / "cfm-logo-large.png"
LOGO_SMALL = LOGOS_DIR / "cfm-logo-small.png"
# After upload via Tools > Image Management (gateway-level, not project zip):
LOGO_LARGE_PATH = "/system/images/cfm/cfm-logo-large.png"
LOGO_SMALL_PATH = "/system/images/cfm/cfm-logo-small.png"
LOGO_LARGE_DATA_URI = ""
LOGO_SMALL_DATA_URI = ""
RESOURCE_ACTOR = "content-author"
LIBRARY_PROJECT_NAME = "config-file-menu-library"
LIBRARY_PROJECT_TITLE = "Config File Menu Library"
SITE_PROJECT_NAME = "Config File Menu — Your Site Name"
SAMPLE_PROJECT_NAME = "Config File Menu Sample"

def sample_menu_yaml() -> str:
    return load_sample_menu_yaml()


MENU_PAGE_STRUCT = {
    "path": "{page.props.path}",
    "requestedPath": "{view.params.requestedPath}",
    "logicalPagePath": "{session.custom.configFileMenu.logicalPagePath}",
    "sessionMenuConfig": "{session.custom.configFileMenu.menuConfig}",
    "sessionMenuConfigType": "{session.custom.configFileMenu.menuConfigType}",
    "paramMenuConfig": "{view.params.menuConfig}",
    "paramMenuConfigType": "{view.params.menuConfigType}",
}

TITLE_RESOLVE_SCRIPT = jython_title_resolve_script()
TITLE_ICON_RESOLVE_SCRIPT = jython_title_icon_resolve_script()

HMI_SHELL_STARTUP_SCRIPT = thin_shell_startup()
CLICK_OUTSIDE_SCRIPT = thin_close_outside_click()

LOGO_NAV_SCRIPT = jython_navigate_menu_target(include_dock_close=False, use_logo_target=True)
MENU_LINK_NAV_SCRIPT = jython_navigate_menu_target(include_dock_close=True, use_logo_target=False)
LOGO_VARIANT_EXPR = (
    "if(len(coalesce(toString({session.custom.configFileMenu.logoVariant}),''))>0,"
    "lower({session.custom.configFileMenu.logoVariant}),"
    "lower({view.params.logoVariant}))"
)
TOPBAR_CLOCK_EXPR = f'runScript("{RUNTIME_MODULE}.format_topbar_clock", 1000)'


def png_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def logo_source_expr(session_key: str, param_key: str, data_uri: str) -> str:
    escaped = data_uri.replace("\\", "\\\\").replace("'", "\\'")
    return (
        f"if(len(coalesce(toString({{{session_key}}}),''))>0,"
        f"toString({{{session_key}}}),"
        f"if(len(coalesce(toString({{view.params.{param_key}}}),''))>0,"
        f"toString({{view.params.{param_key}}}),"
        f"'{escaped}'))"
    )


def perspective_string_literal(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def logo_source_binding(variant: str, data_uri: str) -> dict:
    key = "logoSmallPath" if variant == "small" else "logoLargePath"
    return {
        "binding": {
            "config": {
                "struct": {
                    "variant": perspective_string_literal(variant),
                    "sessionSource": f"{{session.custom.configFileMenu.{key}}}",
                    "paramSource": f"{{view.params.{key}}}",
                    "defaultSource": perspective_string_literal(data_uri),
                },
                "waitOnAll": True,
            },
            "transforms": [
                {
                    "code": "\treturn exchange.cfm.runtime.resolve_logo_source(value, self.session, self.view)\n",
                    "type": "script",
                }
            ],
            "type": "expr-struct",
        }
    }


def print_logo_resource_paths() -> None:
    print("Logo PNG files (canonical repo path):")
    print(f"  config/cfm-logo-source.png  (master; resized by build)")
    print(f"  config/cfm-logos/cfm-logo-large.png")
    print(f"  config/cfm-logos/cfm-logo-small.png")
    print("Child import zips package these as logo-upload/cfm/*.png with embedded data URIs.")
    print("Optional: upload the same PNGs to Tools > Image Management folder 'cfm', then set:")
    print(f"  logoLargePath = {LOGO_LARGE_PATH}")
    print(f"  logoSmallPath = {LOGO_SMALL_PATH}")


def view_resource_json() -> dict:
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


def page_config_resource_json() -> dict:
    return {
        "scope": "G",
        "version": 1,
        "restricted": False,
        "overridable": True,
        "files": ["config.json"],
        "attributes": {
            "lastModification": {
                "actor": RESOURCE_ACTOR,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        },
    }


def build_shell_title_row() -> dict:
    return {
        "meta": {"name": "TitleRow"},
        "type": "ia.container.flex",
        "position": {"basis": "48px", "shrink": 0},
        "props": {
            "alignItems": "center",
            "direction": "row",
            "style": {"gap": "12px", "minHeight": "48px"},
        },
        "children": [
            {
                "meta": {"name": "TitleIcon"},
                "type": "ia.display.icon",
                "position": {"basis": "36px", "shrink": 0},
                "propConfig": {
                    "props.path": {
                        "binding": {
                            "config": {"struct": MENU_PAGE_STRUCT, "waitOnAll": False},
                            "transforms": [{"code": TITLE_ICON_RESOLVE_SCRIPT, "type": "script"}],
                            "type": "expr-struct",
                        }
                    }
                },
                "props": {"path": "material/description", "style": {"height": "36px", "width": "36px"}},
            },
            {
                "meta": {"name": "TitleLabel"},
                "type": "ia.display.label",
                "position": {"grow": 1},
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "config": {"struct": MENU_PAGE_STRUCT, "waitOnAll": False},
                            "transforms": [{"code": TITLE_RESOLVE_SCRIPT, "type": "script"}],
                            "type": "expr-struct",
                        }
                    }
                },
                "props": {
                    "textStyle": {"fontSize": "1.75em", "fontWeight": "600"},
                    "style": {"classes": "cfm-page__title"},
                },
            },
        ],
    }


def build_shell_path_label() -> dict:
    return {
        "meta": {"name": "PathLabel"},
        "type": "ia.display.label",
        "position": {"basis": "32px", "shrink": 0},
        "propConfig": {
            "props.text": {
                "binding": {
                    "config": {"struct": MENU_PAGE_STRUCT, "waitOnAll": True},
                    "transforms": [
                        {
                            "code": "\treturn exchange.cfm.runtime.resolve_effective_page_path_from_value(value, self.page)\n",
                            "type": "script",
                        }
                    ],
                    "type": "expr-struct",
                }
            }
        },
        "props": {
            "textStyle": {"fontSize": "1em"},
            "style": {"classes": "cfm-page__path"},
        },
    }


def build_shell_placeholder_section(*, placeholder_kind: str) -> dict:
    if placeholder_kind == "route":
        return {
            "meta": {"name": "RouteNotice"},
            "type": "ia.container.flex",
            "position": {"grow": 1},
            "props": {
                "direction": "column",
                "style": {"classes": "cfm-page__notice"},
            },
            "children": [
                {
                    "meta": {"name": "RouteWarningRow"},
                    "type": "ia.container.flex",
                    "position": {"shrink": 0},
                    "props": {
                        "alignItems": "center",
                        "direction": "row",
                        "style": {"gap": "10px", "classes": "cfm-page__notice-row"},
                    },
                    "children": [
                        {
                            "meta": {"name": "RouteWarningIcon"},
                            "type": "ia.display.icon",
                            "position": {"basis": "28px", "shrink": 0},
                            "props": {
                                "path": "material/warning",
                                "style": {"height": "28px", "width": "28px"},
                            },
                        },
                        {
                            "meta": {"name": "RouteWarningTitle"},
                            "type": "ia.display.label",
                            "position": {"grow": 1},
                            "props": {
                                "text": "Route fallback — create a Page Configuration route",
                                "textStyle": {"fontSize": "1.15em", "fontWeight": "600"},
                                "style": {"classes": "cfm-page__notice-title"},
                            },
                        },
                    ],
                },
                {
                    "meta": {"name": "Placeholder"},
                    "type": "ia.display.label",
                    "position": {"grow": 1},
                    "props": {
                        "alignVertical": "top",
                        "text": SHELL_ROUTE_PLACEHOLDER_TEXT,
                        "textStyle": {"fontSize": "1.05em"},
                        "style": {"classes": "cfm-page__notice-body"},
                    },
                },
            ],
        }
    return {
        "meta": {"name": "Placeholder"},
        "type": "ia.display.label",
        "position": {"grow": 1},
        "props": {
            "alignVertical": "top",
            "text": SHELL_HMI_PLACEHOLDER_TEXT,
            "textStyle": {"fontSize": "1.1em"},
            "style": {"classes": "cfm-page__muted"},
        },
    }


def build_shell_view(*, include_sample_menu_config: bool = False, placeholder_kind: str = "hmi") -> dict:
    params: dict = {
        "menuDockId": "config-file-menu",
        "closeMenuOnOutsideClick": True,
        "requestedPath": "",
    }
    prop_config: dict = {
        "params.menuDockId": {"paramDirection": "input", "persistent": True},
        "params.closeMenuOnOutsideClick": {"paramDirection": "input", "persistent": True},
        "params.requestedPath": {"paramDirection": "input", "persistent": True},
    }
    if include_sample_menu_config:
        params["menuConfig"] = sample_menu_yaml().strip() + "\n"
        params["menuConfigType"] = "yaml"
        prop_config["params.menuConfig"] = {"paramDirection": "input", "persistent": True}
        prop_config["params.menuConfigType"] = {"paramDirection": "input", "persistent": True}

    return {
        "custom": {},
        "params": params,
        "propConfig": prop_config,
        "props": {"defaultSize": {"height": 900, "width": 1200}},
        "root": {
            "meta": {"name": "root"},
            "type": "ia.container.flex",
            "props": {"style": {"height": "100%", "classes": "cfm-page__root"}},
            "events": {
                "component": {
                    "onStartup": {
                        "config": {"script": HMI_SHELL_STARTUP_SCRIPT},
                        "scope": "G",
                        "type": "script",
                    }
                },
                "dom": {
                    "onClick": {
                        "config": {"script": CLICK_OUTSIDE_SCRIPT},
                        "scope": "G",
                        "type": "script",
                    }
                },
            },
            "children": [
                {
                    "meta": {"name": "PageWrapper"},
                    "type": "ia.container.flex",
                    "position": {"grow": 1},
                    "props": {
                        "direction": "column",
                        "style": {
                            "margin": "0 auto",
                            "maxWidth": "1680px",
                            "padding": "24px",
                            "width": "100%",
                        },
                    },
                    "children": [
                        {
                            "meta": {"name": "PageCard"},
                            "type": "ia.container.flex",
                            "position": {"grow": 1},
                            "props": {
                                "direction": "column",
                                "style": {"classes": "cfm-page__card"},
                            },
                            "children": [
                                build_shell_title_row(),
                                build_shell_path_label(),
                                build_shell_placeholder_section(placeholder_kind=placeholder_kind),
                            ],
                        }
                    ],
                }
            ],
        },
    }


def build_landing_view() -> dict:
    return {
        "custom": {},
        "params": {
            "menuDockId": "config-file-menu",
            "closeMenuOnOutsideClick": True,
        },
        "propConfig": {
            "params.menuDockId": {"paramDirection": "input", "persistent": True},
            "params.closeMenuOnOutsideClick": {"paramDirection": "input", "persistent": True},
        },
        "props": {"defaultSize": {"height": 900, "width": 1200}},
        "root": {
            "meta": {"name": "root"},
            "type": "ia.container.flex",
            "props": {"style": {"height": "100%", "classes": "cfm-page__root"}},
            "events": {
                "component": {
                    "onStartup": {
                        "config": {"script": HMI_SHELL_STARTUP_SCRIPT},
                        "scope": "G",
                        "type": "script",
                    }
                },
                "dom": {
                    "onClick": {
                        "config": {"script": CLICK_OUTSIDE_SCRIPT},
                        "scope": "G",
                        "type": "script",
                    }
                },
            },
            "children": [
                {
                    "meta": {"name": "PageWrapper"},
                    "type": "ia.container.flex",
                    "position": {"grow": 1},
                    "props": {
                        "direction": "column",
                        "style": {
                            "margin": "0 auto",
                            "maxWidth": "1280px",
                            "padding": "24px",
                            "width": "100%",
                        },
                    },
                    "children": [
                        {
                            "meta": {"name": "LandingCard"},
                            "type": "ia.container.flex",
                            "position": {"grow": 1},
                            "props": {
                                "direction": "column",
                                "style": {"classes": "cfm-page__card"},
                            },
                            "children": [
                                {
                                    "meta": {"name": "LandingMarkdown"},
                                    "type": "ia.display.markdown",
                                    "position": {"grow": 1},
                                    "props": {
                                        "source": LANDING_MARKDOWN,
                                        "style": {
                                            "padding": "24px",
                                            "fontSize": "15px",
                                            "lineHeight": "1.5",
                                        },
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    }


def shell_page(title: str, *, route_placeholder: bool = False) -> dict:
    return {
        "title": title,
        "viewPath": ROUTE_FALLBACK_VIEW_PATH if route_placeholder else SHELL_VIEW_PATH,
    }


def build_shared_docks() -> dict:
    return {
        "cornerPriority": "top-bottom",
        "left": [
            {
                "anchor": "fixed",
                "autoBreakpoint": 768,
                "content": "push",
                "handle": "hide",
                "iconUrl": "",
                "id": "config-file-menu",
                "modal": False,
                "resizable": False,
                "show": "visible",
                "size": 220,
                "viewParams": {},
                "viewPath": "Config File Menu/MenuContent",
            }
        ],
        "top": [
            {
                "anchor": "fixed",
                "autoBreakpoint": 480,
                "content": "push",
                "handle": "hide",
                "iconUrl": "",
                "id": "config-file-menu-top-bar",
                "modal": False,
                "resizable": False,
                "show": "visible",
                "size": 58,
                "viewParams": {},
                "viewPath": "Config File Menu/Resources/Menu/Menu Top Bar",
            }
        ],
    }


def build_library_pages() -> dict:
    """Routes for library-bundled Settings and Diagnostics views (no sample HMI tree)."""
    return dict(
        sorted(
            {
                "/": {
                    "title": "Config File Menu",
                    "viewPath": LANDING_VIEW_PATH,
                },
                SHELL_FALLBACK_ROUTE: shell_page(SHELL_FALLBACK_PAGE_TITLE, route_placeholder=True),
                "/cfm/settings": {
                    "title": "Settings",
                    "viewPath": "Config File Menu/Resources/Menu/Menu Settings",
                },
                "/cfm/tools": shell_page("Config File Menu Tools"),
                "/cfm/tools/config-converter": {
                    "title": "Menu Config Converter",
                    "viewPath": "Config File Menu/Resources/Menu/Menu Settings",
                    "viewParams": {"currentTabIndex": 4},
                },
                "/cfm/diagnostics": {
                    "title": "Diagnostics",
                    "viewPath": "Config File Menu/Resources/Diagnostics/Diagnostics Dashboard",
                },
            }.items()
        )
    )


def build_sample_pages(routes: list[tuple[str, str, str]]) -> dict:
    pages = dict(build_library_pages())
    pages["/cfm"] = shell_page("Config File Menu")

    seen: set[str] = set(pages)
    for target, label, title in routes:
        if target in seen:
            continue
        seen.add(target)
        if target == "/cfm/diagnostics":
            continue
        pages[target] = shell_page(title)

    return dict(sorted(pages.items()))


def build_library_page_config() -> dict:
    return {
        "pages": build_library_pages(),
        "sharedDocks": build_shared_docks(),
    }


def build_sample_page_config(routes: list[tuple[str, str, str]]) -> dict:
    # Child page-config replaces the parent entirely in Ignition — include docks + pages.
    return build_page_config(routes)


def build_page_config(routes: list[tuple[str, str, str]]) -> dict:
    return {
        "pages": build_sample_pages(routes),
        "sharedDocks": build_shared_docks(),
    }


def library_project_json() -> dict:
    return {
        "title": LIBRARY_PROJECT_TITLE,
        "description": (
            "Inheritable Perspective menu library: dock shell, views, Advanced Stylesheet, "
            "and Settings tools. Copyright EdenOaks Consulting / Matt McPheeters."
        ),
        "enabled": True,
        "inheritable": True,
        "parent": "",
    }


def site_project_json() -> dict:
    return {
        "title": SITE_PROJECT_NAME,
        "description": (
            "Site deployment child of Config File Menu Library. Customize menuConfig, page routes, "
            "and logos in the import zip before importing. Copyright EdenOaks Consulting / Matt McPheeters."
        ),
        "enabled": True,
        "inheritable": False,
        "parent": LIBRARY_PROJECT_NAME,
    }


def sample_project_json() -> dict:
    return {
        "title": SAMPLE_PROJECT_NAME,
        "description": (
            "Sample child of Config File Menu Library with reference /cfm routes and menuConfig. "
            "Copyright EdenOaks Consulting / Matt McPheeters."
        ),
        "enabled": True,
        "inheritable": False,
        "parent": LIBRARY_PROJECT_NAME,
    }


def write_project_json(manifest: dict) -> None:
    PROJECT_JSON.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def resize_logo(source: Path, dest: Path, size: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as img:
        img = img.convert("RGBA")
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        img.save(dest, format="PNG", optimize=True)


def create_placeholder_logo(dest: Path, size: int = 128, label: str = "CFM") -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (size, size), (0, 86, 145, 255))
    draw = ImageDraw.Draw(img)
    inset = max(size // 8, 4)
    draw.rounded_rectangle(
        (inset, inset, size - inset, size - inset),
        radius=max(size // 10, 4),
        fill=(255, 255, 255, 255),
    )
    try:
        font = ImageFont.truetype("arial.ttf", max(size // 4, 12))
    except OSError:
        font = ImageFont.load_default()
    text_bbox = draw.textbbox((0, 0), label, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    draw.text(
        ((size - text_w) / 2, (size - text_h) / 2 - text_bbox[1]),
        label,
        fill=(0, 86, 145, 255),
        font=font,
    )
    img.save(dest, format="PNG", optimize=True)


def write_image_resources(source_logo: Path) -> None:
    global LOGO_LARGE_DATA_URI, LOGO_SMALL_DATA_URI

    LOGOS_DIR.mkdir(parents=True, exist_ok=True)
    resize_logo(source_logo, LOGO_LARGE, 72)
    resize_logo(source_logo, LOGO_SMALL, 40)

    LOGO_LARGE_DATA_URI = png_data_uri(LOGO_LARGE)
    LOGO_SMALL_DATA_URI = png_data_uri(LOGO_SMALL)

    legacy_images = PERSPECTIVE / "images" / "cfm"
    if legacy_images.is_dir():
        try:
            shutil.rmtree(legacy_images)
        except OSError:
            pass

    if source_logo.resolve() != (PROJECT_ROOT / "config" / "cfm-logo-source.png").resolve():
        shutil.copy2(source_logo, PROJECT_ROOT / "config" / "cfm-logo-source.png")


def make_footer_link(
    *,
    name: str,
    label: str,
    icon: str,
    target: str,
    footer_key: str,
    default_visible: bool = True,
) -> dict:
    return {
        "meta": {"name": name},
        "position": {"shrink": 0},
        "propConfig": {
            "position.display": {
                "binding": {
                    "config": {
                        "struct": {
                            "sessionMenuConfig": "{session.custom.configFileMenu.menuConfig}",
                            "sessionMenuConfigType": "{session.custom.configFileMenu.menuConfigType}",
                            "paramMenuConfig": "{view.params.menuConfig}",
                            "paramMenuConfigType": "{view.params.menuConfigType}",
                        },
                        "waitOnAll": True,
                    },
                    "transforms": [
                        {
                            "code": jython_footer_visibility_script(
                                footer_key, default=default_visible
                            ),
                            "type": "script",
                        }
                    ],
                    "type": "expr-struct",
                }
            }
        },
        "props": {
            "path": "Config File Menu/Resources/Menu/Menu Child",
            "style": {"classes": "cfm-menu__direct-link-embed"},
            "params": {
                "icon": icon,
                "isLink": True,
                "label": label,
                "menuDockId": "config-file-menu",
                "showArrow": False,
                "target": target,
            },
        },
        "type": "ia.display.view",
    }


def patch_menu_footer(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    footer_order = ("MenuFooterDiagnostics", "MenuFooterSettings", "MenuSectionUser")

    def reorder_footer_children(children: list) -> list:
        by_name = {child.get("meta", {}).get("name"): child for child in children}
        ordered = [by_name[name] for name in footer_order if name in by_name]
        for child in children:
            name = child.get("meta", {}).get("name")
            if name not in footer_order:
                ordered.append(child)
        return ordered

    def walk(node: dict) -> None:
        if node.get("meta", {}).get("name") == "MenuFooter":
            children = node.setdefault("children", [])
            for child in children:
                name = child.get("meta", {}).get("name", "")
                if name == "MenuFooterSettings":
                    child["propConfig"]["position.display"]["binding"]["transforms"][0][
                        "code"
                    ] = jython_footer_visibility_script("showSettings", default=True)
                elif name == "MenuFooterDiagnostics":
                    child["propConfig"]["position.display"]["binding"]["transforms"][0][
                        "code"
                    ] = jython_footer_visibility_script("showDiagnostics", default=True)
                elif name == "MenuSectionUser":
                    child["propConfig"]["position.display"]["binding"]["transforms"][0][
                        "code"
                    ] = jython_footer_visibility_script("showUser", default=True)
                if child.get("type") == "ia.display.view" and "Menu Child" in str(
                    child.get("props", {}).get("path", "")
                ):
                    child.setdefault("props", {}).setdefault("style", {})[
                        "classes"
                    ] = "cfm-menu__direct-link-embed"
            if not any(
                child.get("meta", {}).get("name") == "MenuFooterDiagnostics"
                for child in children
            ):
                children.insert(
                    0,
                    make_footer_link(
                        name="MenuFooterDiagnostics",
                        label="Diagnostics",
                        icon="material/medical_services",
                        target="/cfm/diagnostics",
                        footer_key="showDiagnostics",
                        default_visible=True,
                    ),
                )
            node["children"] = reorder_footer_children(children)
            return
        for child in node.get("children") or []:
            walk(child)

    walk(data.get("root") or {})
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_menu_settings_general(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    root = data["root"]
    root["children"] = [
        child
        for child in root.get("children") or []
        if child.get("meta", {}).get("name") not in ("MenuFontRow", "MenuFontSizeRow")
    ]
    root["events"]["component"]["onStartup"]["config"]["script"] = thin_settings_general_startup()
    patch_menu_settings_general_row_layout(root)
    children = root["children"]
    theme_row = next(
        (child for child in children if child.get("meta", {}).get("name") == "ThemeRow"),
        None,
    )
    if theme_row is None:
        insert_idx = next(
            (
                idx + 1
                for idx, child in enumerate(children)
                if child.get("meta", {}).get("name") == "MenuWidthRow"
            ),
            len(children),
        )
        children.insert(insert_idx, make_theme_row())
    else:
        for child in theme_row.get("children") or []:
            if child.get("meta", {}).get("name") == "ThemeDropdown":
                child.setdefault("props", {})["options"] = load_theme_dropdown_options()
                break
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_view_menu_config(view_path: Path, menu_yaml: str) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    data["params"]["menuConfig"] = menu_yaml.strip() + "\n"
    if "menuConfigType" not in data.get("params", {}):
        data["params"]["menuConfigType"] = "yaml"
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_logo_sources(
    view_path: Path,
    *,
    logo_large: Path | None = None,
    logo_small: Path | None = None,
) -> None:
    large_path = logo_large or LOGO_LARGE
    small_path = logo_small or LOGO_SMALL
    if not large_path.is_file() or not small_path.is_file():
        raise SystemExit(
            f"Logo PNGs missing ({large_path}, {small_path}); run write_image_resources first."
        )

    large_uri = png_data_uri(large_path)
    small_uri = png_data_uri(small_path)
    large_default = large_uri
    small_default = small_uri

    data = json.loads(view_path.read_text(encoding="utf-8"))

    def walk(node: dict) -> None:
        if not isinstance(node, dict):
            return
        meta = node.get("meta") or {}
        name = meta.get("name", "")
        if name == "MenuLargeBreakpoint":
            props = node.setdefault("props", {})
            props["fit"] = {"height": 56, "mode": "contain", "width": 144}
            props.pop("source", None)
            node.setdefault("propConfig", {})["props.source"] = {
                **logo_source_binding("large", large_default)
            }
        elif name == "MenuSmallBreakpoint":
            props = node.setdefault("props", {})
            props["fit"] = {"height": 40, "mode": "contain", "width": 40}
            props.pop("source", None)
            node.setdefault("propConfig", {})["props.source"] = {
                **logo_source_binding("small", small_default)
            }
        elif name == "TopLogo":
            node.setdefault("propConfig", {})["props.style.cursor"] = {
                "binding": {
                    "config": {"expression": "'pointer'"},
                    "type": "expr",
                }
            }
            events = node.setdefault("events", {}).setdefault("dom", {})
            events["onClick"] = {
                "config": {"script": LOGO_NAV_SCRIPT},
                "scope": "G",
                "type": "script",
            }
        for child in node.get("children") or []:
            walk(child)

    walk(data.get("root") or {})
    params = data.setdefault("params", {})
    params["logoLargePath"] = ""
    params["logoSmallPath"] = ""
    params["logoLinkTarget"] = "/"
    prop_config = data.setdefault("propConfig", {})
    prop_config["params.logoLargePath"] = {"paramDirection": "input", "persistent": True}
    prop_config["params.logoSmallPath"] = {"paramDirection": "input", "persistent": True}
    prop_config["params.logoLinkTarget"] = {"paramDirection": "input", "persistent": True}
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_header_layout(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))

    def walk(node: dict) -> None:
        if not isinstance(node, dict):
            return
        meta = node.get("meta") or {}
        name = meta.get("name", "")
        if name == "HeaderArea":
            props = node.setdefault("props", {})
            props["alignItems"] = "center"
            props["direction"] = "row"
            props["justify"] = "space-between"
            style = props.setdefault("style", {})
            style.pop("height", None)
            style.pop("minHeight", None)
        elif name == "TopLogo":
            position = node.setdefault("position", {})
            position["grow"] = 1
            position["shrink"] = 1
            position.pop("basis", None)
            props = node.setdefault("props", {})
            props["alignItems"] = "center"
            props["justify"] = "center"
            style = props.setdefault("style", {})
            style["minWidth"] = "0"
            style["width"] = "100%"
        elif name == "MenuLargeBreakpoint":
            style = node.setdefault("props", {}).setdefault("style", {})
            style["alignSelf"] = "center"
        elif name == "MenuSmallBreakpoint":
            node.setdefault("propConfig", {})["position.display"] = {
                "binding": {
                    "config": {"expression": "false"},
                    "type": "expr",
                }
            }
        elif name == "DockControls":
            position = node.setdefault("position", {})
            position.pop("basis", None)
            position.pop("grow", None)
            position["shrink"] = 0
            props = node.setdefault("props", {})
            props["alignItems"] = "flex-end"
            props["direction"] = "column"
            props["justify"] = "center"
            style = props.setdefault("style", {})
            style["gap"] = "4px"
            style["paddingRight"] = "8px"
            style.pop("paddingBottom", None)
            style.pop("width", None)
            style.pop("height", None)
            style.pop("minHeight", None)
        for child in node.get("children") or []:
            walk(child)

    walk(data.get("root") or {})
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build_top_bar_small_logo_node(small_default: str, small_expr: str) -> dict:
    return {
        "meta": {"name": "TopBarSmallLogo"},
        "position": {"shrink": 0},
        "props": {
            "fit": {"height": 32, "mode": "contain", "width": 32},
            "style": {
                "classes": "cfm-menu__topbar-logo cfm-menu__logo",
                "cursor": "pointer",
            },
        },
        "type": "ia.display.image",
        "propConfig": {
            "position.display": {
                "binding": {
                    "config": {
                        "struct": {
                            "sessionMenuConfig": "{session.custom.configFileMenu.menuConfig}",
                            "sessionMenuConfigType": "{session.custom.configFileMenu.menuConfigType}",
                            "paramMenuConfig": "{view.params.menuConfig}",
                            "paramMenuConfigType": "{view.params.menuConfigType}",
                            "viewportWidth": "{page.props.dimensions.viewport.width}",
                        },
                        "waitOnAll": True,
                    },
                    "transforms": [
                        {
                            "code": jython_topbar_small_logo_visible_script(),
                            "type": "script",
                        }
                    ],
                    "type": "expr-struct",
                }
            },
            "props.source": {
                **logo_source_binding("small", small_default)
            },
        },
        "events": {
            "dom": {
                "onClick": {
                    "config": {"script": LOGO_NAV_SCRIPT},
                    "scope": "G",
                    "type": "script",
                }
            }
        },
    }


def patch_top_bar_clock(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))

    def walk(node: dict) -> bool:
        if node.get("meta", {}).get("name") == "TopBarClock":
            prop_config = node.setdefault("propConfig", {})
            prop_config["props.text"] = {
                "binding": {
                    "config": {"expression": TOPBAR_CLOCK_EXPR},
                    "type": "expr",
                }
            }
            return True
        for child in node.get("children") or []:
            if walk(child):
                return True
        return False

    if not walk(data.get("root") or {}):
        raise KeyError(f"TopBarClock not found in {view_path}")
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_top_bar_small_logo(view_path: Path) -> None:
    if not LOGO_LARGE.is_file() or not LOGO_SMALL.is_file():
        raise SystemExit(f"Logo PNGs missing under {LOGOS_DIR}; run write_image_resources first.")

    small_expr = ""
    small_default = LOGO_SMALL_DATA_URI or png_data_uri(LOGO_SMALL)

    data = json.loads(view_path.read_text(encoding="utf-8"))
    children = data["root"]["children"]
    small_logo = None
    for child in children:
        if child.get("meta", {}).get("name") == "TopBarSmallLogo":
            small_logo = child
            break

    if small_logo is None:
        clock_idx = next(
            i
            for i, child in enumerate(children)
            if child.get("meta", {}).get("name") == "TopBarClock"
        )
        children.insert(clock_idx + 1, build_top_bar_small_logo_node(small_default, small_expr))
    else:
        small_logo["props"]["fit"] = {"height": 32, "mode": "contain", "width": 32}
        small_logo["props"].pop("source", None)
        style = small_logo.setdefault("props", {}).setdefault("style", {})
        style["classes"] = "cfm-menu__topbar-logo cfm-menu__logo"
        style["cursor"] = "pointer"
        small_logo["propConfig"]["position.display"] = {
            "binding": {
                "config": {
                    "struct": {
                        "sessionMenuConfig": "{session.custom.configFileMenu.menuConfig}",
                        "sessionMenuConfigType": "{session.custom.configFileMenu.menuConfigType}",
                        "paramMenuConfig": "{view.params.menuConfig}",
                        "paramMenuConfigType": "{view.params.menuConfigType}",
                        "viewportWidth": "{page.props.dimensions.viewport.width}",
                    },
                    "waitOnAll": True,
                },
                "transforms": [
                    {
                        "code": jython_topbar_small_logo_visible_script(),
                        "type": "script",
                    }
                ],
                "type": "expr-struct",
            }
        }
        small_logo["propConfig"]["props.source"] = {
            **logo_source_binding("small", small_default)
        }
        small_logo["events"] = {
            "dom": {
                "onClick": {
                    "config": {"script": LOGO_NAV_SCRIPT},
                    "scope": "G",
                    "type": "script",
                }
            }
        }

    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_menu_repeater_transform(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    script = thin_menu_items_transform()

    def walk(node: dict) -> None:
        if not isinstance(node, dict):
            return
        if node.get("meta", {}).get("name") == "MenuItems":
            node["propConfig"]["props.instances"]["binding"]["transforms"][0]["code"] = script
            return
        for child in node.get("children") or []:
            walk(child)

    walk(data.get("root") or {})
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def set_onclick_script(view_path: Path, script: str) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))

    def walk(node: dict) -> bool:
        events = node.get("events") or {}
        dom = events.get("dom") or {}
        on_click = dom.get("onClick")
        if on_click and on_click.get("type") == "script":
            on_click["config"]["script"] = script
            return True
        for child in node.get("children") or []:
            if walk(child):
                return True
        return False

    if not walk(data.get("root") or {}):
        raise KeyError(f"onClick script not found in {view_path}")
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_effective_page_path_binding(view_path: Path, prop_key: str) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    binding = data["propConfig"][prop_key]["binding"]
    if prop_key == "custom.page":
        transform_code = (
            "\tpage_path = exchange.cfm.runtime.resolve_effective_page_path_from_value(value, self.page)\n"
            "\treturn exchange.cfm.runtime.sync_section_tree_page(self, page_path)\n"
        )
    elif prop_key == "custom.key" and view_path.parent.name == "Menu Child":
        transform_code = (
            "\tpage_path = exchange.cfm.runtime.resolve_effective_page_path_from_value(value, self.page)\n"
            "\treturn exchange.cfm.runtime.menu_link_classes(page_path, self.view.params.target)\n"
        )
    else:
        transform_code = "\treturn exchange.cfm.runtime.resolve_effective_page_path_from_value(value, self.page)\n"
    binding["type"] = "expr-struct"
    binding["config"] = {
        "struct": {
            "path": "{page.props.path}",
            "requestedPath": "{view.params.requestedPath}",
            "logicalPagePath": "{session.custom.configFileMenu.logicalPagePath}",
        },
        "waitOnAll": True,
    }
    binding["transforms"] = [
        {
            "code": transform_code,
            "type": "script",
        }
    ]
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_top_bar_library_scripts(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    root = data["root"]
    root["events"]["component"]["onStartup"]["config"]["script"] = thin_topbar_startup()
    toggle_trigger_struct = {
        "deviceType": "{session.props.device.type}",
        "dockContent": "{session.custom.configFileMenu.dockContent}",
        "isPinned": "{session.custom.configFileMenu.isPinned}",
        "isOpen": "{session.custom.configFileMenu.isOpen}",
        "viewportWidth": "{page.props.dimensions.viewport.width}",
        "primaryViewWidth": "{page.props.dimensions.primaryView.width}",
    }

    def walk(node: dict) -> None:
        meta = node.get("meta", {})
        name = meta.get("name", "")
        if name == "MenuToggleButton":
            node["events"]["dom"]["onClick"]["config"]["script"] = thin_menu_toggle_click()
            prop_config = node.setdefault("propConfig", {})
            prop_config["props.path"] = {
                "binding": {
                    "config": {"struct": toggle_trigger_struct, "waitOnAll": True},
                    "transforms": [{"code": thin_topbar_toggle_icon(), "type": "script"}],
                    "type": "expr-struct",
                }
            }
            prop_config["props.style.classes"] = {
                "binding": {
                    "config": {"struct": toggle_trigger_struct, "waitOnAll": True},
                    "transforms": [{"code": thin_topbar_toggle_classes(), "type": "script"}],
                    "type": "expr-struct",
                }
            }
        elif name == "FlexRepeater":
            binding = node["propConfig"]["props.instances"]["binding"]
            struct = binding["config"]["struct"]
            struct["path"] = "{page.props.path}"
            struct["requestedPath"] = "{view.params.requestedPath}"
            struct["logicalPagePath"] = "{session.custom.configFileMenu.logicalPagePath}"
            struct["shellFallbackEnabled"] = "{session.custom.configFileMenu.shellFallbackEnabled}"
            binding["transforms"][0]["code"] = thin_breadcrumb_instances()
        for child in node.get("children") or []:
            walk(child)

    walk(root)
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_menu_content_arrow_side(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    data["root"]["propConfig"]["props.style.classes"] = {
        "binding": {
            "config": {
                "struct": {
                    "deviceType": "{session.props.device.type}",
                    "isOpen": "{session.custom.configFileMenu.isOpen}",
                    "menuMode": "{session.custom.configFileMenu.menuMode}",
                },
                "waitOnAll": True,
            },
            "transforms": [
                {
                    "code": "\treturn exchange.cfm.runtime.menu_panel_classes(self.session)\n",
                    "type": "script",
                }
            ],
            "type": "expr-struct",
        }
    }
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _set_style_classes_expression(node: dict, expression: str) -> bool:
    prop_config = node.get("propConfig") or {}
    binding = (prop_config.get("props.style.classes") or {}).get("binding") or {}
    if binding.get("type") != "expr":
        return False
    binding.setdefault("config", {})["expression"] = expression
    return True


def patch_menu_views_lock_arrow_left() -> None:
    menu_parent = VIEWS / "Resources" / "Menu" / "Menu Parent" / "view.json"
    menu_child = VIEWS / "Resources" / "Menu" / "Menu Child" / "view.json"

    parent_data = json.loads(menu_parent.read_text(encoding="utf-8"))
    parent_data["propConfig"]["custom.key"]["binding"]["transforms"][0]["code"] = SECTION_KEY_TRANSFORM
    _set_style_classes_expression(parent_data.get("root") or {}, SECTION_TREE_CLASSES_EXPR)
    for child in (parent_data.get("root") or {}).get("children") or []:
        if child.get("meta", {}).get("name") == "SectionHeader":
            child.setdefault("propConfig", {})["props.style.classes"] = SECTION_HEADER_CLASSES_BINDING
        if child.get("meta", {}).get("name") == "Tree":
            _set_style_classes_expression(child, TREE_CLASSES_EXPR)
    menu_parent.write_text(json.dumps(parent_data, indent=2) + "\n", encoding="utf-8")

    child_data = json.loads(menu_child.read_text(encoding="utf-8"))
    _set_style_classes_expression(child_data.get("root") or {}, MENU_CHILD_CLASSES_EXPR)
    menu_child.write_text(json.dumps(child_data, indent=2) + "\n", encoding="utf-8")


def patch_menu_content_startup(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    component = data["root"].setdefault("events", {}).setdefault("component", {})
    component["onStartup"]["config"]["script"] = thin_menu_content_startup()
    component["onPropertyChange"] = {
        "config": {"script": thin_menu_content_property_change()},
        "scope": "G",
        "type": "script",
    }
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_settings_general_startup(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    data["root"]["events"]["component"]["onStartup"]["config"]["script"] = thin_settings_general_startup()
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_top_bar_fallback(view_path: Path) -> None:
    patch_top_bar_library_scripts(view_path)


SHELL_FALLBACK_DEFAULTS = (
    "\tstate.setdefault('shellFallbackEnabled', True)\n"
    f"\tstate.setdefault('shellFallbackRoute', '{SHELL_FALLBACK_ROUTE}')\n"
    "\tstate.setdefault('logicalPagePath', '')\n"
    "\tstate.setdefault('showTopBarSmallLogo', True)\n"
)


def patch_startup_shell_fallback_defaults(script: str) -> str:
    script = script.replace("shellFallbackRoute', '/cfm/page'", f"shellFallbackRoute', '{SHELL_FALLBACK_ROUTE}'")
    script = script.replace('shellFallbackRoute", "/cfm/page"', f'shellFallbackRoute", "{SHELL_FALLBACK_ROUTE}"')
    if "shellFallbackEnabled" in script:
        return script
    marker = "\tself.session.custom.configFileMenu = state"
    if marker in script:
        return script.replace(marker, SHELL_FALLBACK_DEFAULTS + marker)
    return script


def make_settings_row(
    *,
    name: str,
    label_text: str,
    input_name: str,
    session_key: str,
    input_type: str = "text-field",
    dropdown_options: list[dict] | None = None,
    save_script: str | None = None,
) -> dict:
    input_node: dict = {
        "meta": {"name": input_name},
        "position": {"basis": "320px", "grow": 1},
        "props": {"text": ""} if input_type == "text-field" else {"value": ""},
        "type": f"ia.input.{input_type}",
    }
    if input_type == "dropdown" and dropdown_options:
        if session_key in (
            "shellFallbackEnabled",
            "showTopBarSmallLogo",
            "showFooterUser",
            "showFooterSettings",
            "showFooterDiagnostics",
        ):
            value_transform = (
                "\tif value in (True, False):\n"
                "\t\treturn value\n"
                "\tif value in (None, ''):\n"
                "\t\treturn True\n"
                "\treturn str(value).lower() in ('true', '1', 'yes', 'on')"
            )
        else:
            value_transform = (
                "\tif value in (True, False):\n"
                "\t\treturn value\n"
                "\treturn str(value).lower() in ('true', '1', 'yes', 'on')"
            )
        input_node["props"] = {
            "options": dropdown_options,
            "value": dropdown_options[0]["value"],
        }
        input_node["propConfig"] = {
            "props.value": {
                "binding": {
                    "config": {"path": f"session.custom.configFileMenu.{session_key}"},
                    "transforms": [{"code": value_transform, "type": "script"}],
                    "type": "property",
                }
            }
        }
    else:
        text_transform = (
            f"\treturn str(value or '{SHELL_FALLBACK_ROUTE}')"
            if session_key == "shellFallbackRoute"
            else "\treturn str(value if value not in (None, '') else '')"
        )
        input_node["propConfig"] = {
            "props.text": {
                "binding": {
                    "config": {"path": f"session.custom.configFileMenu.{session_key}"},
                    "transforms": [{"code": text_transform, "type": "script"}],
                    "type": "property",
                }
            }
        }
        if session_key == "shellFallbackRoute":
            input_node["props"]["text"] = SHELL_FALLBACK_ROUTE
    if save_script:
        input_node["events"] = {
            "component": {
                "onActionPerformed": {
                    "config": {"script": save_script},
                    "scope": "G",
                    "type": "script",
                }
            }
        }
        if input_type == "text-field":
            dom_events = {
                "onBlur": {
                    "config": {"script": save_script},
                    "scope": "G",
                    "type": "script",
                }
            }
            input_node["events"]["dom"] = dom_events
    return {
        "children": [
            {
                "meta": {"name": f"{name}Label"},
                "position": {"basis": "240px", "shrink": 0},
                "props": {"text": label_text},
                "type": "ia.display.label",
            },
            input_node,
        ],
        "meta": {"name": name},
        "position": {"shrink": 0},
        "props": {
            "alignItems": "center",
            "wrap": "nowrap",
            "style": {"gap": "12px", "padding": "8px 16px"},
        },
        "type": "ia.container.flex",
    }


THEME_SAVE_SCRIPT = (
    "\ttry:\n"
    "\t\tself.session.props.theme = str(self.props.value or 'light')\n"
    "\texcept:\n"
    "\t\tpass\n"
)

DEFAULT_THEME_OPTIONS: list[dict[str, str]] = [
    {"label": "Light", "value": "light"},
    {"label": "Dark", "value": "dark"},
    {"label": "Light (Cool)", "value": "light-cool"},
    {"label": "Light (Warm)", "value": "light-warm"},
    {"label": "Dark (Cool)", "value": "dark-cool"},
    {"label": "Dark (Warm)", "value": "dark-warm"},
]


def load_theme_dropdown_options() -> list[dict[str, str]]:
    options = list(DEFAULT_THEME_OPTIONS)
    options_path = PROJECT_ROOT / "config" / "cfm-theme-options.json"
    if not options_path.is_file():
        return options
    data = json.loads(options_path.read_text(encoding="utf-8"))
    for entry in data.get("customThemes") or []:
        label = str(entry.get("label") or "").strip()
        value = str(entry.get("value") or "").strip()
        if label and value:
            options.append({"label": label, "value": value})
    return options


def make_theme_row() -> dict:
    return {
        "children": [
            {
                "meta": {"name": "ThemeLabel"},
                "position": {"basis": "240px", "shrink": 0},
                "props": {"text": "Session theme"},
                "type": "ia.display.label",
            },
            {
                "meta": {"name": "ThemeDropdown"},
                "position": {"basis": "320px", "grow": 1},
                "propConfig": {
                    "props.value": {
                        "binding": {
                            "config": {"path": "session.props.theme"},
                            "transforms": [
                                {"code": "\treturn str(value or 'light')", "type": "script"}
                            ],
                            "type": "property",
                        }
                    }
                },
                "props": {
                    "options": load_theme_dropdown_options(),
                    "value": "light",
                },
                "events": {
                    "component": {
                        "onActionPerformed": {
                            "config": {"script": THEME_SAVE_SCRIPT},
                            "scope": "G",
                            "type": "script",
                        }
                    }
                },
                "type": "ia.input.dropdown",
            },
        ],
        "meta": {"name": "ThemeRow"},
        "position": {"shrink": 0},
        "props": {
            "alignItems": "center",
            "wrap": "nowrap",
            "style": {"gap": "12px", "padding": "8px 16px"},
        },
        "type": "ia.container.flex",
    }


def patch_menu_settings_general_row_layout(root: dict) -> None:
    for child in root.get("children") or []:
        if child.get("type") != "ia.container.flex":
            continue
        props = child.setdefault("props", {})
        props["wrap"] = "nowrap"
        props.setdefault("alignItems", "center")


FALLBACK_ENABLED_SAVE = (
    "\tval = self.props.value\n"
    "\tif val in (True, False):\n"
    "\t\texchange.cfm.runtime.set_state_field(self.session, 'shellFallbackEnabled', val)\n"
    "\telse:\n"
    "\t\texchange.cfm.runtime.set_state_field(self.session, 'shellFallbackEnabled', exchange.cfm.runtime.is_true(val))\n"
)

FALLBACK_ROUTE_SAVE = (
    f"\troute = str(self.props.text or '{SHELL_FALLBACK_ROUTE}').strip()\n"
    "\tif not route.startswith('/'):\n"
    "\t\troute = '/' + route\n"
    "\texchange.cfm.runtime.set_state_field(self.session, 'shellFallbackRoute', route)\n"
)

TOPBAR_SMALL_LOGO_SAVE = (
    "\tval = self.props.value\n"
    "\tif val in (True, False):\n"
    "\t\texchange.cfm.runtime.set_state_field(self.session, 'showTopBarSmallLogo', val)\n"
    "\telse:\n"
    "\t\texchange.cfm.runtime.set_state_field(self.session, 'showTopBarSmallLogo', exchange.cfm.runtime.is_true(val))\n"
)

FOOTER_USER_SAVE = (
    "\tval = self.props.value\n"
    "\tif val in (True, False):\n"
    "\t\texchange.cfm.runtime.set_state_field(self.session, 'showFooterUser', val)\n"
    "\telse:\n"
    "\t\texchange.cfm.runtime.set_state_field(self.session, 'showFooterUser', exchange.cfm.runtime.is_true(val))\n"
)

FOOTER_DIAGNOSTICS_SAVE = (
    "\tval = self.props.value\n"
    "\tif val in (True, False):\n"
    "\t\texchange.cfm.runtime.set_state_field(self.session, 'showFooterDiagnostics', val)\n"
    "\telse:\n"
    "\t\texchange.cfm.runtime.set_state_field(self.session, 'showFooterDiagnostics', exchange.cfm.runtime.is_true(val))\n"
)

FOOTER_SETTINGS_SAVE = (
    "\tval = self.props.value\n"
    "\tif val in (True, False):\n"
    "\t\texchange.cfm.runtime.set_state_field(self.session, 'showFooterSettings', val)\n"
    "\telse:\n"
    "\t\texchange.cfm.runtime.set_state_field(self.session, 'showFooterSettings', exchange.cfm.runtime.is_true(val))\n"
)

MENU_CONTENT_PANEL_CLASSES_EXPR = (
    "concat("
    "if({session.props.device.type}='designer',"
    "'cfm-menu cfm-menu--open cfm-menu__panel',"
    "if(coalesce({session.custom.configFileMenu.isOpen}, false)=true || "
    "lower(coalesce(toString({session.custom.configFileMenu.menuMode}), 'closed'))='open',"
    "'cfm-menu cfm-menu--open cfm-menu__panel',"
    "'cfm-menu cfm-menu--closed cfm-menu__panel')),"
    " ' cfm-menu__arrow-left')"
)


def remove_expand_arrow_side_settings_row(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    root = data["root"]
    root["children"] = [
        child
        for child in root.get("children") or []
        if child.get("meta", {}).get("name") != "ExpandArrowSideRow"
    ]
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def remove_site_name_settings_row(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    root = data["root"]
    root["children"] = [
        child
        for child in root.get("children") or []
        if child.get("meta", {}).get("name") != "SiteNameRow"
    ]
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_menu_settings_general_topbar_logo(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    root = data["root"]
    children = root["children"]
    if not any(child.get("meta", {}).get("name") == "TopBarSmallLogoRow" for child in children):
        insert_idx = next(
            (
                idx
                for idx, child in enumerate(children)
                if child.get("meta", {}).get("name") == "ShellFallbackEnabledRow"
            ),
            len(children),
        )
        children.insert(
            insert_idx,
            make_settings_row(
                name="TopBarSmallLogoRow",
                label_text="Top bar small logo",
                input_name="TopBarSmallLogoDropdown",
                session_key="showTopBarSmallLogo",
                input_type="dropdown",
                dropdown_options=[
                    {"label": "Show", "value": True},
                    {"label": "Hide", "value": False},
                ],
                save_script=TOPBAR_SMALL_LOGO_SAVE,
            ),
        )
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_menu_settings_general_footer_visibility(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    root = data["root"]
    children = root["children"]
    insert_after = next(
        (
            idx + 1
            for idx, child in enumerate(children)
            if child.get("meta", {}).get("name") == "TopBarSmallLogoRow"
        ),
        len(children),
    )
    rows = [
        (
            "FooterUserRow",
            "Menu footer user",
            "FooterUserDropdown",
            "showFooterUser",
            FOOTER_USER_SAVE,
        ),
        (
            "FooterSettingsRow",
            "Menu footer settings",
            "FooterSettingsDropdown",
            "showFooterSettings",
            FOOTER_SETTINGS_SAVE,
        ),
        (
            "FooterDiagnosticsRow",
            "Menu footer diagnostics",
            "FooterDiagnosticsDropdown",
            "showFooterDiagnostics",
            FOOTER_DIAGNOSTICS_SAVE,
        ),
    ]
    for offset, (row_name, label_text, input_name, session_key, save_script) in enumerate(rows):
        if any(child.get("meta", {}).get("name") == row_name for child in children):
            continue
        children.insert(
            insert_after + offset,
            make_settings_row(
                name=row_name,
                label_text=label_text,
                input_name=input_name,
                session_key=session_key,
                input_type="dropdown",
                dropdown_options=[
                    {"label": "Show", "value": True},
                    {"label": "Hide", "value": False},
                ],
                save_script=save_script,
            ),
        )
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_existing_shell_fallback_route_row(root: dict) -> None:
    for child in root.get("children") or []:
        if child.get("meta", {}).get("name") != "ShellFallbackRouteRow":
            continue
        for sub in child.get("children") or []:
            if sub.get("meta", {}).get("name") != "ShellFallbackRouteInput":
                continue
            sub.setdefault("props", {})["text"] = SHELL_FALLBACK_ROUTE
            prop_config = sub.setdefault("propConfig", {})
            text_binding = prop_config.setdefault("props.text", {}).setdefault("binding", {})
            transforms = text_binding.setdefault("transforms", [])
            if transforms:
                transforms[0]["code"] = f"\treturn str(value or '{SHELL_FALLBACK_ROUTE}')"
            sub["events"] = {
                "component": {
                    "onActionPerformed": {
                        "config": {"script": FALLBACK_ROUTE_SAVE},
                        "scope": "G",
                        "type": "script",
                    }
                },
                "dom": {
                    "onBlur": {
                        "config": {"script": FALLBACK_ROUTE_SAVE},
                        "scope": "G",
                        "type": "script",
                    }
                },
            }


def patch_menu_settings_general_fallback(view_path: Path) -> None:
    patch_settings_general_startup(view_path)
    patch_menu_settings_general_topbar_logo(view_path)
    patch_menu_settings_general_footer_visibility(view_path)
    remove_expand_arrow_side_settings_row(view_path)
    data = json.loads(view_path.read_text(encoding="utf-8"))
    root = data["root"]
    children = root["children"]
    runtime_scripts = {
        "PinnedInput": thin_settings_pinned_change(),
        "DockModeInput": thin_settings_dock_content_change(),
        "MenuWidthInput": thin_settings_menu_width_change(),
        "CloseOutsideInput": (
            "\texchange.cfm.runtime.set_state_field(self.session, "
            "'closeMenuOnOutsideClick', exchange.cfm.runtime.is_true(self.props.value))\n"
        ),
        "TopBarSmallLogoDropdown": TOPBAR_SMALL_LOGO_SAVE,
        "FooterUserDropdown": FOOTER_USER_SAVE,
        "FooterSettingsDropdown": FOOTER_SETTINGS_SAVE,
        "FooterDiagnosticsDropdown": FOOTER_DIAGNOSTICS_SAVE,
        "ShellFallbackEnabledDropdown": FALLBACK_ENABLED_SAVE,
        "ShellFallbackRouteInput": FALLBACK_ROUTE_SAVE,
    }

    def set_runtime_scripts(node: dict) -> None:
        name = (node.get("meta") or {}).get("name")
        if name in runtime_scripts:
            script = runtime_scripts[name]
            events = node.setdefault("events", {})
            component = events.setdefault("component", {})
            component["onActionPerformed"] = {
                "config": {"script": script},
                "scope": "G",
                "type": "script",
            }
            if node.get("type") == "ia.input.text-field":
                events.setdefault("dom", {})["onBlur"] = {
                    "config": {"script": script},
                    "scope": "G",
                    "type": "script",
                }
        for child in node.get("children") or []:
            set_runtime_scripts(child)

    set_runtime_scripts(root)
    remove_site_name_settings_row(view_path)
    if not any(child.get("meta", {}).get("name") == "ShellFallbackEnabledRow" for child in children):
        children.extend(
            [
                make_settings_row(
                    name="ShellFallbackEnabledRow",
                    label_text="Shell fallback navigation",
                    input_name="ShellFallbackEnabledDropdown",
                    session_key="shellFallbackEnabled",
                    input_type="dropdown",
                    dropdown_options=[
                        {"label": "Enabled", "value": True},
                        {"label": "Disabled", "value": False},
                    ],
                    save_script=FALLBACK_ENABLED_SAVE,
                ),
                make_settings_row(
                    name="ShellFallbackRouteRow",
                    label_text="Shell fallback route",
                    input_name="ShellFallbackRouteInput",
                    session_key="shellFallbackRoute",
                    save_script=FALLBACK_ROUTE_SAVE,
                ),
            ]
        )
    patch_existing_shell_fallback_route_row(root)
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


ARROW_SIDE_SESSION_EXPR = "'left'"

ARROW_SIDE_SESSION_LEFT_EXPR = "true"

ARROW_MARGIN_LEFT_EXPR = "'0px'"

ARROW_ORDER_EXPR = "'-1'"

EXPAND_ICON_MARGIN_LEFT_EXPR = "'0px'"

ARROW_DISPLAY_EXPR = "{view.params.showArrow}"

SECTION_ARROW_DISPLAY_EXPR = "len({view.params.items}) > 0"

ARROW_PATH_EXPR = (
    "if({view.params.expanded}, 'material/arrow_drop_down', 'material/arrow_right')"
)

SECTION_HEADER_ARROW_PATH = (
    "if({view.custom.isOpen}, 'material/arrow_drop_down', 'material/arrow_right')"
)

MENU_CHILD_CHILD_ORDER = ("Arrow", "Icon", "Label")

SECTION_HEADER_CLASSES_EXPR = (
    "concat('cfm-menu__link ',"
    "if(len({view.params.items})>0,'cfm-menu__link--arrow-left',''))"
)

SECTION_HEADER_CLASSES_BINDING = {
    "binding": {
        "config": {
            "struct": {
                "pagePath": "{view.custom.page}",
                "target": "{view.params.target}",
                "hasChildren": "len({view.params.items}) > 0",
            },
            "waitOnAll": True,
        },
        "transforms": [
            {
                "code": (
                    "\treturn exchange.cfm.runtime.section_header_classes("
                    "value.get('pagePath'), value.get('target'), value.get('hasChildren'))\n"
                ),
                "type": "script",
            }
        ],
        "type": "expr-struct",
    }
}

SECTION_TREE_CLASSES_EXPR = (
    "concat('cfm-menu__section cfm-menu__section-tree ',"
    "{view.custom.key},' cfm-menu__arrow-left')"
)

SECTION_KEY_TRANSFORM = (
    "\treturn exchange.cfm.runtime.section_classes("
    "value, self.view.params.target, self.view.params.label)"
)

MENU_CHILD_CLASSES_EXPR = (
    "concat('cfm-menu__link cfm-menu__direct-link ',"
    "{view.custom.key},"
    "if({view.params.showArrow},' cfm-menu__link--arrow-left',''))"
)

TREE_CLASSES_EXPR = "concat('cfm-menu__section-tree-items cfm-menu__arrow-left')"

MENU_CHILD_EMBED_CLASSES_EXPR = "'cfm-menu__arrow-left'"


def build_link_arrow(
    name: str,
    display_expr: str,
    path_expr: str,
    arrow_script: str,
) -> dict:
    return {
        "meta": {"name": name},
        "position": {"basis": "40px", "shrink": 0},
        "propConfig": {
            "position.display": {
                "binding": {"config": {"expression": display_expr}, "type": "expr"}
            },
            "props.path": {
                "binding": {"config": {"expression": path_expr}, "type": "expr"}
            },
            "props.style.marginLeft": {
                "binding": {
                    "config": {"expression": ARROW_MARGIN_LEFT_EXPR},
                    "type": "expr",
                }
            },
            "props.style.order": {
                "binding": {
                    "config": {"expression": ARROW_ORDER_EXPR},
                    "type": "expr",
                }
            },
        },
        "props": {
            "path": "material/arrow_right",
            "style": {
                "padding": "8px",
                "cursor": "pointer",
                "classes": "cfm-menu__link-arrow",
            },
        },
        "type": "ia.display.icon",
        "events": {
            "dom": {
                "onClick": {
                    "config": {"script": arrow_script},
                    "scope": "G",
                    "type": "script",
                }
            }
        },
    }


def build_section_header_row(arrow_script: str, body_script: str) -> dict:
    return {
        "meta": {"name": "SectionHeader"},
        "position": {"basis": "40px", "grow": 0, "shrink": 0},
        "propConfig": {
            "props.style.classes": {
                "binding": {
                    "config": {"expression": SECTION_HEADER_CLASSES_EXPR},
                    "type": "expr",
                }
            }
        },
        "props": {
            "direction": "row",
            "style": {
                "overflow": "hidden",
                "width": "100%",
            },
        },
        "type": "ia.container.flex",
        "children": [
            build_link_arrow(
                "Arrow",
                SECTION_ARROW_DISPLAY_EXPR,
                SECTION_HEADER_ARROW_PATH,
                arrow_script,
            ),
            {
                "meta": {"name": "Icon"},
                "position": {"basis": "40px", "shrink": 0},
                "propConfig": {
                    "props.path": {
                        "binding": {
                            "config": {"path": "view.params.icon"},
                            "type": "property",
                        }
                    }
                },
                "props": {
                    "style": {
                        "padding": "8px",
                        "cursor": "pointer",
                        "classes": "cfm-menu__link-icon",
                    }
                },
                "type": "ia.display.icon",
                "events": {
                    "dom": {
                        "onClick": {
                            "config": {"script": body_script},
                            "scope": "G",
                            "type": "script",
                        }
                    }
                },
            },
            {
                "meta": {"name": "Label"},
                "position": {"basis": "50px", "grow": 1},
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "config": {"path": "view.params.label"},
                            "type": "property",
                        }
                    }
                },
                "props": {
                    "style": {
                        "overflow": "hidden",
                        "cursor": "pointer",
                        "classes": "cfm-menu__link-label",
                    },
                    "textStyle": {"whiteSpace": "pre-wrap"},
                },
                "type": "ia.display.label",
                "events": {
                    "dom": {
                        "onClick": {
                            "config": {"script": body_script},
                            "scope": "G",
                            "type": "script",
                        }
                    }
                },
            },
        ],
    }


def build_menu_child_arrow(name: str, display_expr: str, arrow_script: str) -> dict:
    return build_link_arrow(name, display_expr, ARROW_PATH_EXPR, arrow_script)


def patch_menu_link_split_clicks(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    body_script = jython_menu_link_body_click_script()
    arrow_script = jython_section_arrow_click_script()
    data.setdefault("params", {})["arrowSide"] = "right"
    prop_config = data.setdefault("propConfig", {})
    prop_config["params.arrowSide"] = {
        "paramDirection": "input",
        "persistent": True,
    }
    root = data["root"]
    root.pop("events", None)
    root.setdefault("propConfig", {})
    root["propConfig"].pop("props.direction", None)
    root["propConfig"]["props.style.classes"] = {
        "binding": {"config": {"expression": MENU_CHILD_CLASSES_EXPR}, "type": "expr"}
    }
    root.setdefault("props", {})["direction"] = "row"

    children = root.get("children") or []
    by_name = {child.get("meta", {}).get("name", ""): child for child in children}
    for legacy in ("Arrow", "ArrowLeft", "ArrowRight"):
        by_name.pop(legacy, None)
    by_name["Arrow"] = build_menu_child_arrow("Arrow", ARROW_DISPLAY_EXPR, arrow_script)
    if "Icon" not in by_name or "Label" not in by_name:
        raise SystemExit(f"Menu Child view missing Icon/Label: {view_path}")
    root["children"] = [by_name[name] for name in MENU_CHILD_CHILD_ORDER]

    for child in root.get("children") or []:
        name = child.get("meta", {}).get("name", "")
        prop_config = child.setdefault("propConfig", {})
        prop_config.pop("position.order", None)
        prop_config.pop("props.style.order", None)
        if name == "Icon":
            child.setdefault("props", {}).setdefault("style", {})["classes"] = (
                "cfm-menu__link-icon"
            )
            child["props"]["style"]["cursor"] = "pointer"
        elif name == "Label":
            child.setdefault("props", {}).setdefault("style", {})["classes"] = (
                "cfm-menu__link-label"
            )
            child["props"]["style"]["cursor"] = "pointer"
        elif name == "Arrow":
            child.setdefault("props", {}).setdefault("style", {})["classes"] = (
                "cfm-menu__link-arrow"
            )
            child["props"]["style"]["cursor"] = "pointer"
        if name == "Arrow":
            child.setdefault("events", {}).setdefault("dom", {})["onClick"] = {
                "config": {"script": arrow_script},
                "scope": "G",
                "type": "script",
            }
        elif name in ("Icon", "Label"):
            child.setdefault("events", {}).setdefault("dom", {})["onClick"] = {
                "config": {"script": body_script},
                "scope": "G",
                "type": "script",
            }

    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_menu_section_tree_expanded(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    data.setdefault("params", {})["expanded"] = False
    prop_config = data.setdefault("propConfig", {})
    prop_config["params.expanded"] = {"paramDirection": "input", "persistent": True}
    data.setdefault("custom", {})["isOpen"] = False
    prop_config["custom.isOpen"] = {"persistent": True}

    page_sync = jython_section_tree_page_sync_script()
    prop_config["custom.page"]["binding"]["transforms"][0]["code"] = page_sync
    root = data["root"]
    root["propConfig"]["props.style.classes"]["binding"]["config"]["expression"] = (
        SECTION_TREE_CLASSES_EXPR
    )
    for child in root.get("children") or []:
        if child.get("meta", {}).get("name") == "SectionHeader":
            child.setdefault("propConfig", {})["props.style.classes"] = SECTION_HEADER_CLASSES_BINDING

    data.setdefault("scripts", {})["messageHandlers"] = [
        {
            "messageType": "cfm-menu-toggle-section",
            "pageScope": True,
            "sessionScope": True,
            "viewScope": True,
            "script": jython_section_toggle_message_script(),
        }
    ]
    root.setdefault("scripts", {})["messageHandlers"] = [
        {
            "messageType": "cfm-menu-toggle-section",
            "pageScope": True,
            "sessionScope": True,
            "viewScope": True,
            "script": jython_section_toggle_message_script(),
        }
    ]

    root.setdefault("events", {}).setdefault("component", {})["onStartup"] = {
        "config": {"script": jython_section_tree_startup_script()},
        "scope": "G",
        "type": "script",
    }

    arrow_script = jython_section_arrow_click_script()
    body_script = jython_section_header_body_click_script()
    children = root.get("children") or []
    children = [
        child
        for child in children
        if child.get("meta", {}).get("name")
        not in ("MenuChild", "MenuLink", "SectionHeader")
    ]
    tree_index = next(
        (i for i, child in enumerate(children) if child.get("meta", {}).get("name") == "Tree"),
        len(children),
    )
    children.insert(tree_index, build_section_header_row(arrow_script, body_script))
    root["children"] = children

    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


TREE_SELECTED_STYLE = {
    "overflow": "hidden",
    "backgroundColor": "var(--cfm-menu-selected-bg)",
    "color": "var(--cfm-menu-selected-color)",
    "fontWeight": "var(--cfm-menu-selected-weight)",
}


def patch_menu_section_tree_nav(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    tree_script = jython_tree_item_clicked_script()

    def walk(node: dict) -> None:
        meta = node.get("meta", {})
        name = meta.get("name", "")
        if name == "Tree":
            node["events"]["component"]["onItemClicked"]["config"]["script"] = tree_script
            node.setdefault("props", {}).setdefault("style", {})["classes"] = "cfm-menu__section-tree-items"
            appearance = node.setdefault("props", {}).setdefault("appearance", {})
            appearance["selectedStyle"] = dict(TREE_SELECTED_STYLE)
            node.setdefault("propConfig", {})["props.style.classes"] = {
                "binding": {"config": {"expression": TREE_CLASSES_EXPR}, "type": "expr"}
            }
            prop_config = node.setdefault("propConfig", {})
            for key in ("collapsed", "expanded", "empty"):
                prop_config[f"props.appearance.expandIcons.{key}.style.marginLeft"] = {
                    "binding": {
                        "config": {"expression": EXPAND_ICON_MARGIN_LEFT_EXPR},
                        "type": "expr",
                    }
                }
        for child in node.get("children") or []:
            walk(child)

    walk(data.get("root") or {})
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_menu_settings_topbar_logo_default(view_path: Path) -> None:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    script = data["root"]["events"]["component"]["onStartup"]["config"]["script"]
    changed = False
    if "showTopBarSmallLogo" not in script:
        marker = "\tstate.setdefault('logicalPagePath', '')\n"
        injection = marker + "\tstate.setdefault('showTopBarSmallLogo', True)\n"
        if marker in script:
            script = script.replace(marker, injection)
            changed = True
    if changed:
        data["root"]["events"]["component"]["onStartup"]["config"]["script"] = script
        view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def sync_perspective_stylesheet() -> None:
    """Ship CFM CSS via Advanced Stylesheet (loads after the active gateway theme)."""
    merge_css = PROJECT_ROOT / "config" / "cfm-menu-theme-merge.css"
    if not merge_css.is_file():
        raise SystemExit(f"Missing canonical CSS: {merge_css}")
    stylesheet_dir = PROJECT_ROOT / "com.inductiveautomation.perspective" / "stylesheet"
    stylesheet_dir.mkdir(parents=True, exist_ok=True)
    header = (
        "/* Config File Menu — Advanced Stylesheet (auto-synced from cfm-menu-theme-merge.css)\n"
        "   Loaded at project scope between gateway theme and style-classes.\n"
        "   Re-sync this file with the project build tooling.\n"
        "*/\n\n"
    )
    (stylesheet_dir / "stylesheet.css").write_text(
        header + merge_css.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (stylesheet_dir / "resource.json").write_text(
        json.dumps(
            {
                "scope": "G",
                "version": 1,
                "restricted": False,
                "overridable": True,
                "files": ["stylesheet.css"],
                "attributes": {
                    "lastModification": {
                        "actor": "content-author",
                        "timestamp": datetime.now(timezone.utc)
                        .replace(microsecond=0)
                        .isoformat()
                        .replace("+00:00", "Z"),
                    }
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Synced Advanced Stylesheet -> {stylesheet_dir.relative_to(PROJECT_ROOT)}")


def _menu_row_starts_with_arrow(view_path: Path) -> bool:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    children = (data.get("root") or {}).get("children") or []
    return bool(children) and children[0].get("meta", {}).get("name") == "Arrow"


def _menu_parent_has_ref_section_header(view_path: Path) -> bool:
    data = json.loads(view_path.read_text(encoding="utf-8"))
    children = (data.get("root") or {}).get("children") or []
    if not children or children[0].get("meta", {}).get("name") != "SectionHeader":
        return False
    header_children = children[0].get("children") or []
    return bool(header_children) and header_children[0].get("meta", {}).get("name") == "Arrow"


def patch_diagnostics_dashboard_theme(view_path: Path) -> None:
    if not view_path.is_file():
        return
    data = json.loads(view_path.read_text(encoding="utf-8"))
    root = data.get("root") or {}
    root_style = root.setdefault("props", {}).setdefault("style", {})
    root_style.pop("backgroundColor", None)
    classes = str(root_style.get("classes") or "").split()
    if "cfm-diag__page" not in classes:
        classes.insert(0, "cfm-diag__page")
        root_style["classes"] = " ".join(part for part in classes if part)
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_diagnostics_card_theme(view_path: Path) -> None:
    if not view_path.is_file():
        return
    data = json.loads(view_path.read_text(encoding="utf-8"))

    def walk(node: dict) -> None:
        style = (node.get("props") or {}).get("style")
        if isinstance(style, dict):
            classes = str(style.get("classes") or "")
            if "cfm-diag__card" in classes or "cfm-diag__embedded" in classes:
                style.pop("backgroundColor", None)
        for child in node.get("children") or []:
            walk(child)

    walk(data.get("root") or {})
    view_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_page_config_menu_site_name(
    page_config_path: Path,
    menu_content_path: Path,
) -> None:
    """Remove stale sharedDocks viewParams.siteName so MenuContent.params.siteName is authoritative."""
    if not page_config_path.is_file():
        return
    page_data = json.loads(page_config_path.read_text(encoding="utf-8"))
    shared = page_data.get("sharedDocks") or {}
    changed = False
    for dock in shared.get("left") or []:
        if dock.get("id") != "config-file-menu" and not str(dock.get("viewPath", "")).endswith(
            "MenuContent"
        ):
            continue
        view_params = dock.get("viewParams")
        if isinstance(view_params, dict) and "siteName" in view_params:
            view_params.pop("siteName", None)
            changed = True
        break
    if changed:
        page_config_path.write_text(json.dumps(page_data, indent=2) + "\n", encoding="utf-8")


def patch_shell_fallback_nav() -> None:
    menu_child = VIEWS / "Resources" / "Menu" / "Menu Child" / "view.json"
    menu_breadcrumb = VIEWS / "Resources" / "Menu" / "Menu Breadcrumb" / "view.json"
    menu_parent = VIEWS / "Resources" / "Menu" / "Menu Parent" / "view.json"
    menu_top_bar = VIEWS / "Resources" / "Menu" / "Menu Top Bar" / "view.json"
    menu_content = VIEWS / "MenuContent" / "view.json"
    menu_settings_general = VIEWS / "Resources" / "Menu" / "Menu Settings General" / "view.json"
    menu_settings = VIEWS / "Resources" / "Menu" / "Menu Settings" / "view.json"
    diagnostics_dashboard = VIEWS / "Resources" / "Diagnostics" / "Diagnostics Dashboard" / "view.json"
    diagnostics_card = VIEWS / "Resources" / "Diagnostics" / "Diagnostics Card" / "view.json"

    patch_diagnostics_dashboard_theme(diagnostics_dashboard)
    patch_diagnostics_card_theme(diagnostics_card)

    if not _menu_row_starts_with_arrow(menu_child):
        patch_menu_link_split_clicks(menu_child)
    set_onclick_script(menu_breadcrumb, MENU_LINK_NAV_SCRIPT)
    patch_effective_page_path_binding(menu_child, "custom.key")
    patch_effective_page_path_binding(menu_breadcrumb, "custom.key")
    patch_effective_page_path_binding(menu_parent, "custom.page")
    if not _menu_parent_has_ref_section_header(menu_parent):
        patch_menu_section_tree_expanded(menu_parent)
    patch_menu_section_tree_nav(menu_parent)
    patch_top_bar_fallback(menu_top_bar)
    patch_menu_settings_general_fallback(menu_settings_general)
    patch_menu_settings_topbar_logo_default(menu_settings)

    content = json.loads(menu_content.read_text(encoding="utf-8"))

    def walk_content(node: dict) -> None:
        if node.get("meta", {}).get("name") == "TopLogo":
            node["events"]["dom"]["onClick"]["config"]["script"] = LOGO_NAV_SCRIPT
            return
        if node.get("meta", {}).get("name") == "MenuDockModeButton":
            node["events"]["dom"]["onClick"]["config"]["script"] = thin_dock_mode_toggle()
        elif node.get("meta", {}).get("name") == "MenuDockPinButton":
            node["events"]["dom"]["onClick"]["config"]["script"] = thin_dock_pin_toggle()
        for child in node.get("children") or []:
            walk_content(child)

    walk_content(content.get("root") or {})
    component = content["root"].setdefault("events", {}).setdefault("component", {})
    component["onStartup"]["config"]["script"] = thin_menu_content_startup()
    component["onPropertyChange"] = {
        "config": {"script": thin_menu_content_property_change()},
        "scope": "G",
        "type": "script",
    }
    menu_content.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")

    if menu_settings.is_file():
        settings = json.loads(menu_settings.read_text(encoding="utf-8"))
        settings["root"]["events"]["component"]["onStartup"]["config"]["script"] = (
            "\texchange.cfm.runtime.init_settings_shell_state(self)\n"
        )
        settings["root"].setdefault("events", {}).setdefault("dom", {})["onClick"] = {
            "config": {"script": "\texchange.cfm.runtime.close_on_outside_click(self)\n"},
            "scope": "G",
            "type": "script",
        }
        menu_settings.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    if diagnostics_dashboard.is_file():
        diagnostics = json.loads(diagnostics_dashboard.read_text(encoding="utf-8"))
        diagnostics["root"].setdefault("events", {}).setdefault("dom", {})["onClick"] = {
            "config": {"script": "\texchange.cfm.runtime.close_on_outside_click(self)\n"},
            "scope": "G",
            "type": "script",
        }
        diagnostics_dashboard.write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")


def find_source_logo() -> Path:
    local = PROJECT_ROOT / "config" / "cfm-logo-source.png"
    if local.is_file():
        return local
    local.parent.mkdir(parents=True, exist_ok=True)
    create_placeholder_logo(local, 128, "CFM")
    return local


def patch_legacy_runtime_references() -> None:
    """Normalize legacy script-library call sites left in view templates."""
    legacy_runtime_module = "Config_File_Menu" + ".Runtime"
    for path in VIEWS.rglob("view.json"):
        text = path.read_text(encoding="utf-8")
        updated = text.replace(legacy_runtime_module, RUNTIME_MODULE)
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")


def main() -> None:
    install_script_library()
    sync_perspective_stylesheet()
    source_logo = find_source_logo()
    menu_yaml = sample_menu_yaml()
    items = parse_yaml_lite_items(menu_yaml)
    routes = walk_menu_items(items)

    write_menu_sample_json(menu_yaml, SAMPLE_MENU_JSON_PATH)

    SHELL_VIEW.mkdir(parents=True, exist_ok=True)
    (SHELL_VIEW / "view.json").write_text(
        json.dumps(build_shell_view(include_sample_menu_config=False, placeholder_kind="hmi"), indent=2) + "\n",
        encoding="utf-8",
    )
    (SHELL_VIEW / "resource.json").write_text(
        json.dumps(view_resource_json(), indent=2) + "\n",
        encoding="utf-8",
    )

    ROUTE_FALLBACK_VIEW.mkdir(parents=True, exist_ok=True)
    (ROUTE_FALLBACK_VIEW / "view.json").write_text(
        json.dumps(build_shell_view(include_sample_menu_config=False, placeholder_kind="route"), indent=2) + "\n",
        encoding="utf-8",
    )
    (ROUTE_FALLBACK_VIEW / "resource.json").write_text(
        json.dumps(view_resource_json(), indent=2) + "\n",
        encoding="utf-8",
    )

    LANDING_VIEW.mkdir(parents=True, exist_ok=True)
    (LANDING_VIEW / "view.json").write_text(
        json.dumps(build_landing_view(), indent=2) + "\n",
        encoding="utf-8",
    )
    (LANDING_VIEW / "resource.json").write_text(
        json.dumps(view_resource_json(), indent=2) + "\n",
        encoding="utf-8",
    )

    PAGE_CONFIG.write_text(
        json.dumps(build_library_page_config(), indent=2) + "\n",
        encoding="utf-8",
    )
    (PAGE_CONFIG.parent / "resource.json").write_text(
        json.dumps(page_config_resource_json(), indent=2) + "\n",
        encoding="utf-8",
    )

    write_project_json(library_project_json())
    write_image_resources(source_logo)

    patch_view_menu_config(VIEWS / "MenuContent" / "view.json", library_menu_stub(menu_yaml))
    patch_menu_footer(VIEWS / "MenuContent" / "view.json")
    patch_menu_settings_general(
        VIEWS / "Resources" / "Menu" / "Menu Settings General" / "view.json"
    )
    patch_menu_repeater_transform(VIEWS / "MenuContent" / "view.json")
    patch_menu_content_arrow_side(VIEWS / "MenuContent" / "view.json")
    patch_menu_views_lock_arrow_left()
    patch_menu_content_startup(VIEWS / "MenuContent" / "view.json")
    patch_logo_sources(VIEWS / "MenuContent" / "view.json")
    patch_header_layout(VIEWS / "MenuContent" / "view.json")
    patch_page_config_menu_site_name(PAGE_CONFIG, VIEWS / "MenuContent" / "view.json")
    patch_top_bar_small_logo(VIEWS / "Resources" / "Menu" / "Menu Top Bar" / "view.json")
    patch_top_bar_clock(VIEWS / "Resources" / "Menu" / "Menu Top Bar" / "view.json")
    patch_shell_fallback_nav()
    patch_legacy_runtime_references()

    thumbs = ensure_view_thumbnails(VIEWS)
    print(f"View thumbnails created: {thumbs}")
    print(f"Menu routes (sample): {len(routes)}")
    library_pages = len(json.loads(PAGE_CONFIG.read_text())["pages"])
    print(f"Library page-config: {library_pages} pages (Settings/Diagnostics) + sharedDocks")
    print(f"Project manifest: {LIBRARY_PROJECT_NAME} / {LIBRARY_PROJECT_TITLE} (inheritable)")
    print_logo_resource_paths()
    print("Done.")


if __name__ == "__main__":
    main()
