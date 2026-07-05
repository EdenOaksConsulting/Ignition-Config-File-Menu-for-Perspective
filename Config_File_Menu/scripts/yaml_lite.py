"""Shared YAML-lite parser for menu config (Python build-time + Jython embed strings)."""

from __future__ import annotations

import json
from typing import Any

# --- Python (build scripts) ---------------------------------------------------


def scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    low = value.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "none"):
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def clean_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw in str(text or "").splitlines():
        if raw.strip() == "" or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))
    return lines


def parse_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    if lines[index][0] == indent and lines[index][1].startswith("- "):
        result: list[dict] = []
        while index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
            content = lines[index][1][2:].strip()
            item: Any = {}
            index += 1
            if content != "":
                if ":" in content:
                    key, val = content.split(":", 1)
                    item[key.strip()] = scalar(val.strip()) if val.strip() != "" else {}
                else:
                    item = scalar(content)
            while index < len(lines) and lines[index][0] > indent:
                child_indent = lines[index][0]
                if lines[index][1].startswith("- "):
                    child, index = parse_block(lines, index, child_indent)
                    if isinstance(item, dict):
                        item.setdefault("children", child)
                else:
                    key, val = lines[index][1].split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    index += 1
                    if val == "" and index < len(lines) and lines[index][0] > child_indent:
                        child, index = parse_block(lines, index, lines[index][0])
                        item[key] = child
                    elif val == "":
                        item[key] = {}
                    elif isinstance(item, dict):
                        item[key] = scalar(val)
            result.append(item)
        return result, index
    result_dict: dict = {}
    while index < len(lines) and lines[index][0] == indent and not lines[index][1].startswith("- "):
        key, val = lines[index][1].split(":", 1)
        key = key.strip()
        val = val.strip()
        index += 1
        if val == "" and index < len(lines) and lines[index][0] > indent:
            child, index = parse_block(lines, index, lines[index][0])
            result_dict[key] = child
        elif val == "":
            result_dict[key] = {}
        else:
            result_dict[key] = scalar(val)
    return result_dict, index


def parse_yaml_lite(text: str) -> dict:
    lines = clean_lines(text)
    if not lines:
        return {"items": []}
    parsed, _ = parse_block(lines, 0, lines[0][0])
    return parsed if isinstance(parsed, dict) else {"items": parsed}


def parse_yaml_lite_items(text: str) -> list[dict]:
    parsed = parse_yaml_lite(text)
    if isinstance(parsed, dict):
        if "menu" in parsed:
            menu = parsed["menu"]
            if isinstance(menu, dict):
                items = menu.get("items", [])
                return items if isinstance(items, list) else []
        items = parsed.get("items", [])
        return items if isinstance(items, list) else []
    return parsed if isinstance(parsed, list) else []


def walk_menu_items(
    items: list[dict],
    trail: list[str] | None = None,
    *,
    title_sep: str = " — ",
) -> list[tuple[str, str, str]]:
    """Return (target, page_title, breadcrumb_title) for every menu item."""
    trail = trail or []
    routes: list[tuple[str, str, str]] = []
    for item in items:
        label = str(item.get("label", "") or "Page")
        target = str(item.get("target", "") or "").strip()
        path = trail + [label]
        title = title_sep.join(path)
        if target:
            routes.append((target, label, title))
        children = item.get("children", item.get("items", []))
        if children:
            routes.extend(walk_menu_items(children, path, title_sep=title_sep))
    return routes


def yaml_to_json_menu(text: str) -> dict:
    parsed = parse_yaml_lite(text)
    if isinstance(parsed, dict) and "menu" in parsed:
        menu = parsed["menu"]
        if isinstance(menu, dict):
            return menu
    if isinstance(parsed, dict):
        return parsed
    return {"items": parsed if isinstance(parsed, list) else []}


def write_menu_sample_json(yaml_text: str, path) -> None:
    menu_json = yaml_to_json_menu(yaml_text)
    payload = {
        "_comment": (
            "SAMPLE ONLY - Copy/paste into MenuContent.params.menuConfig with menuConfigType=json."
        ),
        **menu_json,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


# --- Jython fragments (embedded in Perspective views at build time) ------------

JYTHON_SCALAR = r"""
	def scalar(raw):
		value = str(raw or '').strip()
		if value == '':
			return ''
		low = value.lower()
		if low in ('true', 'yes', 'on'):
			return True
		if low in ('false', 'no', 'off'):
			return False
		if low in ('null', 'none'):
			return None
		if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
			return value[1:-1]
		return value
"""

JYTHON_CLEAN_LINES = r"""
	def clean_lines(text):
		lines = []
		for raw in str(text or '').splitlines():
			if raw.strip() == '' or raw.lstrip().startswith('#'):
				continue
			indent = len(raw) - len(raw.lstrip(' '))
			lines.append((indent, raw.strip()))
		return lines
"""

JYTHON_PARSE_BLOCK = r"""
	def parse_block(lines, index, indent):
		if index >= len(lines):
			return {}, index
		if lines[index][0] == indent and lines[index][1].startswith('- '):
			result = []
			while index < len(lines) and lines[index][0] == indent and lines[index][1].startswith('- '):
				content = lines[index][1][2:].strip()
				item = {}
				index += 1
				if content != '':
					if ':' in content:
						key, val = content.split(':', 1)
						item[key.strip()] = scalar(val.strip()) if val.strip() != '' else {}
					else:
						item = scalar(content)
				while index < len(lines) and lines[index][0] > indent:
					child_indent = lines[index][0]
					if lines[index][1].startswith('- '):
						child, index = parse_block(lines, index, child_indent)
						if isinstance(item, dict):
							item.setdefault('children', child)
					else:
						key, val = lines[index][1].split(':', 1)
						key = key.strip()
						val = val.strip()
						index += 1
						if val == '' and index < len(lines) and lines[index][0] > child_indent:
							child, index = parse_block(lines, index, lines[index][0])
							item[key] = child
						elif val == '':
							item[key] = {}
						elif isinstance(item, dict):
							item[key] = scalar(val)
				result.append(item)
			return result, index
		result = {}
		while index < len(lines) and lines[index][0] == indent and not lines[index][1].startswith('- '):
			key, val = lines[index][1].split(':', 1)
			key = key.strip()
			val = val.strip()
			index += 1
			if val == '' and index < len(lines) and lines[index][0] > indent:
				child, index = parse_block(lines, index, lines[index][0])
				result[key] = child
			elif val == '':
				result[key] = {}
			else:
				result[key] = scalar(val)
		return result, index
"""

JYTHON_GET_PROP = r"""
	def get_prop(obj, key, default=None):
		try:
			return obj.get(key, default)
		except:
			try:
				return obj[key]
			except:
				return default
"""

JYTHON_MENU_PICK_AND_MAPPING = r"""
	def is_mapping(obj):
		try:
			return obj is not None and (hasattr(obj, 'get') or hasattr(obj, 'keys'))
		except:
			return False

	def normalize_path(path):
		p = str(path or '').strip()
		if p == '':
			return ''
		if not p.startswith('/'):
			p = '/' + p
		while '//' in p:
			p = p.replace('//', '/')
		return p.rstrip('/') if p != '/' else p

	def pick_menu_block(data):
		try:
			device = self.session.props.device.type
		except:
			device = ''
		session_cfg = get_prop(data, 'sessionMenuConfig', '')
		param_cfg = get_prop(data, 'paramMenuConfig', '')
		if device == 'designer':
			cfg = param_cfg if param_cfg not in (None, '') else session_cfg
		else:
			cfg = session_cfg if session_cfg not in (None, '') else param_cfg
		session_type = get_prop(data, 'sessionMenuConfigType', '')
		param_type = get_prop(data, 'paramMenuConfigType', '')
		if device == 'designer':
			cfg_type = param_type if param_type not in (None, '') else session_type
		else:
			cfg_type = session_type if session_type not in (None, '') else param_type
		return cfg, str(cfg_type or 'yaml')
"""


def jython_title_resolve_script() -> str:
	from jython_thin import thin_resolve_title

	return thin_resolve_title()


def jython_title_icon_resolve_script() -> str:
	from jython_thin import thin_resolve_title_icon

	return thin_resolve_title_icon()


def jython_converter_script() -> str:
	from perspective_helpers import jython_converter_script as converter

	return converter()


def jython_routes_generate_script(shell_view_path: str, *, root_helper: str, save_helper: str) -> str:
	from perspective_helpers import jython_routes_generate_script as generate

	return generate(shell_view_path, root_helper=root_helper, save_helper=save_helper)


def jython_menu_repeater_transform_script() -> str:
	from jython_thin import thin_menu_items_transform

	return thin_menu_items_transform()
