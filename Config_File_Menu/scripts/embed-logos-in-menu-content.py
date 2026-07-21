#!/usr/bin/env python3
"""Refresh embedded menu logo URIs from logo-upload PNGs in an extracted child zip."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MENU_CONTENT_REL = (
    "com.inductiveautomation.perspective/views/Config File Menu/MenuContent/view.json"
)
MENU_TOP_BAR_REL = (
    "com.inductiveautomation.perspective/views/Config File Menu/Resources/Menu/Menu Top Bar/view.json"
)
LOGO_UPLOAD_DIR = "logo-upload/cfm"
LOGO_NAMES = ("cfm-logo-large.png", "cfm-logo-small.png")


def png_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


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


def resolve_logos(root: Path, large: Path | None, small: Path | None) -> tuple[Path, Path]:
    if large and small:
        return large, small
    candidates = (
        root / "logo-upload" / "cfm",
        root / "config" / "cfm-logos",
        PROJECT_ROOT / "config" / "cfm-logos",
    )
    for base in candidates:
        large_path = base / LOGO_NAMES[0]
        small_path = base / LOGO_NAMES[1]
        if large_path.is_file() and small_path.is_file():
            return large_path, small_path
    raise SystemExit(
        f"Logo PNGs not found under {root / 'logo-upload' / 'cfm'} "
        f"(expected {LOGO_NAMES[0]} and {LOGO_NAMES[1]})"
    )


def patch_menu_content_logo_sources(menu_content_path: Path, logo_large: Path, logo_small: Path) -> None:
    if not menu_content_path.is_file():
        raise SystemExit(f"MenuContent view not found: {menu_content_path}")

    large_uri = png_data_uri(logo_large)
    small_uri = png_data_uri(logo_small)
    data = json.loads(menu_content_path.read_text(encoding="utf-8"))

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
                **logo_source_binding("large", large_uri)
            }
        for child in node.get("children") or []:
            walk(child)

    walk(data.get("root") or {})
    params = data.setdefault("params", {})
    params["logoLargePath"] = ""
    params["logoSmallPath"] = ""
    params.setdefault("logoLinkTarget", "/")
    prop_config = data.setdefault("propConfig", {})
    prop_config["params.logoLargePath"] = {"paramDirection": "input", "persistent": True}
    prop_config["params.logoSmallPath"] = {"paramDirection": "input", "persistent": True}
    prop_config.setdefault("params.logoLinkTarget", {"paramDirection": "input", "persistent": True})
    menu_content_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_top_bar_logo_source(top_bar_path: Path, logo_small: Path) -> None:
    if not top_bar_path.is_file():
        raise SystemExit(f"Menu Top Bar view not found: {top_bar_path}")

    small_uri = png_data_uri(logo_small)
    data = json.loads(top_bar_path.read_text(encoding="utf-8"))

    def walk(node: dict) -> bool:
        if not isinstance(node, dict):
            return False
        meta = node.get("meta") or {}
        if meta.get("name") == "TopBarSmallLogo":
            node.setdefault("propConfig", {})["props.source"] = {
                **logo_source_binding("small", small_uri)
            }
            return True
        for child in node.get("children") or []:
            if walk(child):
                return True
        return False

    if not walk(data.get("root") or {}):
        raise SystemExit(f"TopBarSmallLogo component not found: {top_bar_path}")

    top_bar_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Embed logo-upload PNGs into menu view data URIs "
            "(run after replacing logos in an extracted site or sample zip)."
        )
    )
    parser.add_argument(
        "extracted_root",
        type=Path,
        help="Folder containing project.json and logo-upload/cfm/*.png",
    )
    parser.add_argument("--large", type=Path, default=None, help="Override large logo PNG path")
    parser.add_argument("--small", type=Path, default=None, help="Override small logo PNG path")
    args = parser.parse_args()
    root = args.extracted_root.resolve()
    menu_content = root / MENU_CONTENT_REL
    menu_top_bar = root / MENU_TOP_BAR_REL

    logo_large, logo_small = resolve_logos(root, args.large, args.small)
    patch_menu_content_logo_sources(menu_content, logo_large, logo_small)
    patch_top_bar_logo_source(menu_top_bar, logo_small)
    print(f"Updated embedded logos in {menu_content}")
    print(f"Updated embedded top-bar logo in {menu_top_bar}")
    print(f"  large: {logo_large}")
    print(f"  small: {logo_small}")


if __name__ == "__main__":
    main()
