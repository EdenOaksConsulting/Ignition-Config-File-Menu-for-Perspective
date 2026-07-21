"""Shared menu config parsing and session helpers (Project Script Library)."""


def is_true(value):
	return value is True or str(value).lower() in ("true", "1", "yes", "on")


def scalar(raw):
	value = str(raw or "").strip()
	if value == "":
		return ""
	low = value.lower()
	if low in ("true", "yes", "on"):
		return True
	if low in ("false", "no", "off"):
		return False
	if low in ("null", "none"):
		return None
	if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
		return value[1:-1]
	return value


def clean_lines(text):
	lines = []
	for raw in str(text or "").splitlines():
		if raw.strip() == "" or raw.lstrip().startswith("#"):
			continue
		indent = len(raw) - len(raw.lstrip(" "))
		lines.append((indent, raw.strip()))
	return lines


def parse_block(lines, index, indent):
	if index >= len(lines):
		return {}, index
	if lines[index][0] == indent and lines[index][1].startswith("- "):
		result = []
		while index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
			content = lines[index][1][2:].strip()
			item = {}
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
	result_dict = {}
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


def parse_yaml_lite(text, empty_root=None):
	if empty_root is None:
		empty_root = {"menu": {"items": []}}
	lines = clean_lines(text or "")
	if not lines:
		return empty_root
	parsed, _ = parse_block(lines, 0, lines[0][0])
	return parsed


def get_prop(obj, key, default=None):
	try:
		return obj.get(key, default)
	except:
		try:
			return obj[key]
		except:
			return default


def is_mapping(obj):
	if isinstance(obj, dict):
		return True
	try:
		obj.keys()
		return True
	except:
		return False


def is_sequence(obj):
	if isinstance(obj, list):
		return True
	try:
		return not isinstance(obj, basestring) and hasattr(obj, "__iter__")
	except:
		return False


def normalize_document(obj):
	try:
		return system.util.jsonDecode(system.util.jsonEncode(obj))
	except:
		return obj


def load_config(menu_config, menu_config_type):
	config_type = str(menu_config_type or "yaml").lower().strip()
	if config_type == "json":
		if isinstance(menu_config, basestring):
			return system.util.jsonDecode(menu_config)
		return normalize_document(menu_config)
	return parse_yaml_lite(menu_config)


def get_children(item):
	# A menu item's children, accepting either the `children:` or legacy `items:` key.
	return get_prop(item, "children", get_prop(item, "items", []))


def dict_block(container, key):
	# A mutable dict copy of a nested block container[key], or {} if absent/not a mapping.
	# Used to read-modify-write a nested session object (e.g. the Settings generator scratch).
	blk = container.get(key)
	if blk is None or not hasattr(blk, "get"):
		return {}
	return dict(blk)


def load_menu_items(menu_config, menu_config_type):
	# Parse a menu config and return its top-level item list, unwrapping the optional
	# `menu:` root and tolerating a bare list. Shared by the menu render, breadcrumbs,
	# and page-title resolvers.
	cfg = load_config(menu_config, menu_config_type)
	menu = get_prop(cfg, "menu", cfg)
	return get_prop(menu, "items", menu if is_sequence(menu) else [])


def resolve_dock_id(state):
	# The Perspective dock id the menu operates on; falls back to the shipped default.
	return str(state.get("contentDockId") or "config-file-menu")


def normalize_path(path):
	p = str(path or "").strip()
	if p == "":
		return ""
	if not p.startswith("/"):
		p = "/" + p
	while "//" in p:
		p = p.replace("//", "/")
	return p.rstrip("/") if p != "/" else p


def pick_menu_block(session, data):
	# The menu source lives in the session object (contentSource / contentSourceType),
	# shipped with the library. Read it directly so every caller (menu render, page title)
	# resolves the same config regardless of its binding struct. `data` is unused but kept
	# for a stable signature.
	state = get_state(session)
	return state.get("contentSource", ""), str(state.get("contentSourceType", "yaml") or "yaml")


def resolve_site_name(value, session, default="Default Site"):
	# Site name lives in the session object (brandSiteName), shipped with the library.
	name = str(get_state(session).get("brandSiteName", "") or "").strip()
	return name if name else (default or "Default Site")


def get_state(session):
	try:
		state = session.custom.configFileMenu
		if state is None:
			return {}
		return dict(state)
	except Exception as exc:
		# DEBUG only: this can fire often (e.g. before the session object is materialized);
		# it is a diagnostic breadcrumb, not a fault worth WARN/ERROR volume.
		cfm.log.log_once("config", "debug", "get_state fell back to empty", exc)
		return {}


def set_state_fields(session, fields):
	# Merge the given keys into session.custom.configFileMenu with a WHOLE-OBJECT
	# read-modify-write: read the current object, overwrite just these keys, write the
	# whole object back. This is last-writer-wins, NOT a per-key isolated write. If two
	# handlers run concurrently (e.g. onStartup handlers racing at session load), each
	# reads its own snapshot and rewrites the whole object, so the later write can revert
	# sibling keys the earlier write set (its stale snapshot didn't include them). In
	# practice handlers fire sequentially per session and each writes a distinct set of
	# keys, so the lost-update window is small — but it is real. Returns the merged dict
	# this writer produced (its own view; may be stale by the time callers use it).
	state = get_state(session)
	if fields:
		for key in fields:
			state[key] = fields[key]
	session.custom.configFileMenu = state
	return state


def resolve_effective_page_path_from_value(value, page=None):
	requested = str(get_prop(value, "requestedPath", "") or "").strip()
	if requested:
		return normalize_path(requested)
	logical = str(get_prop(value, "routeLogicalPath", "") or "").strip()
	if logical:
		return normalize_path(logical)
	path = str(get_prop(value, "path", "") or "").strip()
	if path:
		return normalize_path(path)
	try:
		return normalize_path(page.props.path)
	except:
		return ""


def slug(value):
	return str(value or "").strip().lower().replace(" ", "-")
