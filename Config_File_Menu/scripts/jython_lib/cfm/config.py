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
	try:
		device = session.props.device.type
	except:
		device = ""
	session_cfg = get_prop(data, "sessionMenuConfig", "")
	param_cfg = get_prop(data, "paramMenuConfig", "")
	if device == "designer":
		cfg = param_cfg if param_cfg not in (None, "") else session_cfg
	else:
		cfg = session_cfg if session_cfg not in (None, "") else param_cfg
	session_type = get_prop(data, "sessionMenuConfigType", "")
	param_type = get_prop(data, "paramMenuConfigType", "")
	if device == "designer":
		cfg_type = param_type if param_type not in (None, "") else session_type
	else:
		cfg_type = session_type if session_type not in (None, "") else param_type
	return cfg, str(cfg_type or "yaml")


def read_view_param(params, name, default=""):
	if params is None:
		return default
	val = get_prop(params, name, None)
	if val not in (None, ""):
		return str(val).strip()
	try:
		val = getattr(params, name, None)
		if val not in (None, ""):
			return str(val).strip()
	except:
		pass
	return default


def sync_site_name_from_view(session, view):
	param_site = read_view_param(getattr(view, "params", None), "siteName", "Default Site")
	if not param_site:
		param_site = "Default Site"
	state = get_state(session)
	if str(state.get("siteName") or "") != param_site:
		state["siteName"] = param_site
		session.custom.configFileMenu = state


def pick_site_name(session, data, default="Default Site"):
	try:
		device = session.props.device.type
	except:
		device = ""
	session_name = str(get_prop(data, "siteName", "") or "").strip()
	param_name = str(get_prop(data, "paramSiteName", "") or "").strip()
	if device == "designer":
		if param_name:
			return param_name
		if session_name:
			return session_name
		return default or "Default Site"
	if session_name:
		return session_name
	if param_name:
		return param_name
	return default or "Default Site"


def resolve_site_name(value, session, default="Default Site"):
	return pick_site_name(session, value, default)


def get_state(session):
	try:
		state = session.custom.configFileMenu
		if state is None:
			return {}
		return dict(state)
	except:
		return {}


def resolve_effective_page_path_from_value(value, page=None):
	requested = str(get_prop(value, "requestedPath", "") or "").strip()
	if requested:
		return normalize_path(requested)
	logical = str(get_prop(value, "logicalPagePath", "") or "").strip()
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
