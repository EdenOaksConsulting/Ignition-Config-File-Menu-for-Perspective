"""CFM bundled runtime for Config File Menu (auto-generated).
Deployed as exchange.cfm.runtime in the Project Script Library.
"""

# --- config.py ---
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

# --- ui.py ---
def root_component(component):
	node = component
	for _ in range(32):
		try:
			parent = node.parent
		except:
			parent = None
		if parent is None:
			return node
		node = parent
	return node


def find_child(root, name):
	if root is None:
		return None
	try:
		if str(root.name) == name:
			return root
	except:
		pass
	try:
		match = root.getChild(name)
		if match is not None:
			return match
	except:
		pass
	try:
		for child in root.getChildren():
			found = find_child(child, name)
			if found is not None:
				return found
	except:
		pass
	return None


def child_text(root, name, default=""):
	try:
		node = find_child(root, name)
		if node is None:
			return default
		return str(node.props.text or default).strip()
	except:
		return default


def child_text_preserve(root, name, default=""):
	try:
		node = find_child(root, name)
		if node is None:
			return default
		val = node.props.text
		return str(val if val is not None else default)
	except:
		return default


def child_value(root, name, default):
	try:
		node = find_child(root, name)
		if node is None:
			return default
		val = node.props.value
		return str(val if val is not None else default).strip()
	except:
		return default


def set_text(root, name, value, default=""):
	try:
		node = find_child(root, name)
		if node is not None:
			node.props.text = str(value if value not in (None, "") else default)
	except:
		pass


def set_value(root, name, value, default):
	try:
		node = find_child(root, name)
		if node is not None:
			node.props.value = str(value if value not in (None, "") else default)
	except:
		pass

# --- nav.py ---
def normalize_page_url(url):
	path = str(url or "").strip()
	if path and not path.startswith("/"):
		path = "/" + path
	return path


def get_registered_pages():
	try:
		return [normalize_page_url(page["url"]) for page in system.perspective.getProjectInfo()["pageConfigs"]]
	except:
		return []


def navigate_with_fallback(component, target_path, close_dock=False):
	target = normalize_page_url(target_path)
	if not target:
		return
	pages = get_registered_pages()
	state = get_state(component.session)
	ensure_dock_defaults(state)
	dock_id = str(
		state.get("menuDockId")
		or str(getattr(component.view.params, "menuDockId", None) or "")
		or "config-file-menu"
	)
	pinned = is_true(state.get("isPinned", False))
	dock_content = str(state.get("dockContent", "push")).lower()
	if dock_content not in ("cover", "push"):
		dock_content = "push"
	fallback_enabled = is_true(state.get("shellFallbackEnabled", True))
	fallback_route = normalize_page_url(state.get("shellFallbackRoute") or "/cfm/target-no-route")
	if target in pages:
		state["logicalPagePath"] = ""
		component.session.custom.configFileMenu = state
		system.perspective.navigate(page=target)
	elif fallback_enabled and fallback_route in pages:
		state["logicalPagePath"] = target
		component.session.custom.configFileMenu = state
		system.perspective.navigate(page=fallback_route, params={"requestedPath": target})
	else:
		return
	if close_dock and not pinned:
		system.perspective.closeDock(dock_id)
		state["isOpen"] = False
		state["menuMode"] = "closed"
		state["isPinned"] = False
		state["dockContent"] = dock_content
		component.session.custom.configFileMenu = state


def on_menu_link_click(component):
	target = str(component.view.params.target or "").strip()
	if not is_true(component.view.params.isLink) or not target:
		return
	navigate_with_fallback(component, target, close_dock=True)


def on_logo_click(component):
	target = ""
	try:
		target = str(getattr(component.view.params, "logoLinkTarget", None) or "")
	except:
		target = ""
	if not target:
		try:
			state = component.session.custom.configFileMenu
			if state is not None:
				target = str(state.get("logoLinkTarget") or "")
		except:
			pass
	if not target:
		target = "/"
	navigate_with_fallback(component, target, close_dock=False)

# --- dock.py ---
DOCK_DEFAULTS_VERSION = "2026-07-04-pinned-open-push"


def ensure_dock_defaults(state):
	if str(state.get("dockDefaultsVersion", "")) != DOCK_DEFAULTS_VERSION:
		state["isOpen"] = True
		state["menuMode"] = "open"
		state["isPinned"] = True
		state["dockContent"] = "push"
		state["dockDefaultsVersion"] = DOCK_DEFAULTS_VERSION
		return
	state.setdefault("isOpen", True)
	state.setdefault("menuMode", "open")
	state.setdefault("isPinned", True)
	state.setdefault("dockContent", "push")


def init_topbar_state(component):
	state = get_state(component.session)
	ensure_dock_defaults(state)
	state.setdefault("closeMenuOnOutsideClick", True)
	state.setdefault("logoVariant", "large")
	state.setdefault("menuConfigType", "yaml")
	state.setdefault("menuDockId", "config-file-menu")
	state.setdefault("breadcrumbPathPrefix", "cfm")
	component.session.custom.configFileMenu = state


def format_topbar_clock():
	try:
		from java.text import SimpleDateFormat
		from java.util import Date
		return SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(Date())
	except:
		return ""


def _layout_is_open(component):
	try:
		viewport_width = float(component.page.props.dimensions.viewport.width or 0)
		primary_width = float(component.page.props.dimensions.primaryView.width or 0)
		return (viewport_width - primary_width) > 40
	except:
		return False


def _dock_id(component, state):
	return str(
		state.get("menuDockId")
		or str(getattr(component.view.params, "menuDockId", None) or "")
		or "config-file-menu"
	)


def _dock_content(state):
	dock_content = str(state.get("dockContent", "push")).lower()
	if dock_content not in ("cover", "push"):
		dock_content = "push"
	return dock_content


def _topbar_is_open(component, state):
	try:
		device_type = str(component.session.props.device.type or "")
	except:
		device_type = ""
	if device_type == "designer":
		return True
	dock_content = _dock_content(state)
	pinned = is_true(state.get("isPinned", False))
	session_open = is_true(state.get("isOpen", False))
	if dock_content == "push" or pinned:
		return _layout_is_open(component) or session_open
	return session_open


def topbar_toggle_icon(component):
	state = get_state(component.session)
	return "material/menu_open" if _topbar_is_open(component, state) else "material/menu"


def topbar_toggle_classes(component):
	state = get_state(component.session)
	suffix = "close-menu" if _topbar_is_open(component, state) else "open-menu"
	return "cfm-menu__button cfm-menu__button--" + suffix


def on_menu_toggle_click(component):
	state = get_state(component.session)
	dock_id = _dock_id(component, state)
	pinned = is_true(state.get("isPinned", False))
	dock_content = _dock_content(state)
	if pinned:
		dock_content = "push"
	session_open = is_true(state.get("isOpen", False))
	if dock_content == "push" or pinned:
		currently_open = _layout_is_open(component) or session_open
	else:
		currently_open = session_open
	if currently_open:
		system.perspective.closeDock(dock_id)
		state["isOpen"] = False
		state["menuMode"] = "closed"
		state["isPinned"] = pinned
		state["dockContent"] = dock_content
		component.session.custom.configFileMenu = state
	else:
		system.perspective.alterDock(dock_id, {"content": dock_content})
		system.perspective.openDock(dock_id)
		state["isOpen"] = True
		state["menuMode"] = "open"
		state["isPinned"] = pinned
		state["dockContent"] = dock_content
		component.session.custom.configFileMenu = state


def on_dock_mode_toggle(component):
	state = get_state(component.session)
	dock_id = _dock_id(component, state)
	current = _dock_content(state)
	new_mode = "push" if current == "cover" else "cover"
	new_pinned = False if new_mode == "cover" else is_true(state.get("isPinned", False))
	system.perspective.alterDock(dock_id, {"content": new_mode})
	system.perspective.openDock(dock_id)
	state["isOpen"] = True
	state["menuMode"] = "open"
	state["isPinned"] = new_pinned
	state["dockContent"] = new_mode
	component.session.custom.configFileMenu = state


def on_dock_pin_toggle(component):
	state = get_state(component.session)
	dock_id = _dock_id(component, state)
	pinned = is_true(state.get("isPinned", False))
	dock_content = _dock_content(state)
	if pinned:
		system.perspective.alterDock(dock_id, {"content": dock_content})
		state["isOpen"] = is_true(state.get("isOpen", True))
		state["menuMode"] = "open" if state["isOpen"] else "closed"
		state["isPinned"] = False
		state["dockContent"] = dock_content
	else:
		system.perspective.alterDock(dock_id, {"content": "push"})
		system.perspective.openDock(dock_id)
		state["isOpen"] = True
		state["menuMode"] = "open"
		state["isPinned"] = True
		state["dockContent"] = "push"
	component.session.custom.configFileMenu = state


def on_settings_pinned_change(component):
	state = get_state(component.session)
	dock_id = _dock_id(component, state)
	pinned = is_true(component.props.value)
	dock_content = _dock_content(state)
	if pinned:
		dock_content = "push"
		system.perspective.alterDock(dock_id, {"content": dock_content})
		system.perspective.openDock(dock_id)
		state["menuMode"] = "open"
		state["isOpen"] = True
		state["isPinned"] = True
		state["dockContent"] = dock_content
	else:
		state["isPinned"] = False
	component.session.custom.configFileMenu = state


def on_settings_dock_content_change(component):
	state = get_state(component.session)
	mode = str(component.props.value or "push").lower()
	if mode not in ("push", "cover"):
		mode = "push"
	dock_id = _dock_id(component, state)
	system.perspective.alterDock(dock_id, {"content": mode})
	state["dockContent"] = mode
	if mode == "cover":
		state["isPinned"] = False
	component.session.custom.configFileMenu = state


def on_settings_menu_width_change(component):
	state = get_state(component.session)
	width_text = str(component.props.text or "").strip()
	state["menuWidthOpen"] = width_text
	dock_id = _dock_id(component, state)
	try:
		system.perspective.alterDock(dock_id, {"size": _parse_width(width_text)})
	except:
		pass
	component.session.custom.configFileMenu = state


def close_on_outside_click(component):
	state = get_state(component.session)
	flag = state.get("closeMenuOnOutsideClick")
	if flag is None:
		try:
			flag = component.view.params.closeMenuOnOutsideClick
		except:
			flag = True
	if not is_true(flag):
		return
	dock_id = str(
		state.get("menuDockId")
		or str(getattr(component.view.params, "menuDockId", None) or "")
		or "config-file-menu"
	)
	if is_true(state.get("isPinned", False)):
		return
	if not is_true(state.get("isOpen", True)):
		return
	system.perspective.closeDock(dock_id)
	dock_content = str(state.get("dockContent", "push")).lower()
	if dock_content not in ("cover", "push"):
		dock_content = "push"
	state["isOpen"] = False
	state["menuMode"] = "closed"
	state["isPinned"] = False
	state["dockContent"] = dock_content
	component.session.custom.configFileMenu = state


def _apply_menu_dock_state(component, state):
	dock_id = str(
		state.get("menuDockId")
		or str(getattr(component.view.params, "menuDockId", None) or "")
		or "config-file-menu"
	)
	dock_content = _dock_content(state)
	if is_true(state.get("isPinned", False)):
		dock_content = "push"
		state["isOpen"] = True
		state["menuMode"] = "open"
		state["dockContent"] = "push"
	try:
		system.util.getLogger("exchange.cfm.Runtime").debug(
			"Applying dock state id=%s open=%s pinned=%s content=%s"
			% (
				dock_id,
				str(state.get("isOpen")),
				str(state.get("isPinned")),
				str(dock_content),
			)
		)
	except:
		pass
	try:
		system.perspective.alterDock(
			dock_id,
			{
				"content": dock_content,
				"size": _parse_width(state.get("menuWidthOpen", "220px")),
			},
		)
	except:
		pass
	try:
		if is_true(state.get("isOpen", False)):
			system.perspective.openDock(dock_id)
		else:
			system.perspective.closeDock(dock_id)
	except:
		pass


def sync_shell_session(component):
	state = get_state(component.session)
	if not str(state.get("menuConfig") or "").strip():
		try:
			state["menuConfig"] = getattr(component.view.params, "menuConfig", "") or ""
		except:
			state["menuConfig"] = ""
	if not str(state.get("menuConfigType") or "").strip():
		try:
			state["menuConfigType"] = str(getattr(component.view.params, "menuConfigType", "yaml") or "yaml")
		except:
			state["menuConfigType"] = "yaml"
	state.setdefault("logicalPagePath", "")
	try:
		requested = str(getattr(component.view.params, "requestedPath", "") or "").strip()
	except:
		requested = ""
	if requested:
		state["logicalPagePath"] = requested
	component.session.custom.configFileMenu = state


def _parse_width(raw, default=220):
	s = str(raw or "").strip().lower()
	if s.endswith("px"):
		s = s[:-2].strip()
	try:
		w = int(float(s))
		return max(120, min(w, 800))
	except:
		return default


def sync_menu_content_site_name(component):
	sync_site_name_from_view(component.session, component.view)


def on_menu_content_property_change(component, event):
	path = ""
	try:
		prop = event.property
		path = str(getattr(prop, "path", "") or getattr(prop, "propertyPath", "") or "")
	except:
		pass
	if path in ("params", "params.siteName") or path.endswith(".siteName") or path.endswith(".params"):
		sync_menu_content_site_name(component)


def init_menu_content_state(component):
	state = get_state(component.session)
	ensure_dock_defaults(state)
	state.setdefault("menuFont", "")
	state.setdefault("menuFontSize", "14px")
	state.setdefault("menuWidthOpen", "220px")
	state.setdefault("menuDockId", "config-file-menu")
	dock_id = str(
		state.get("menuDockId")
		or str(getattr(component.view.params, "menuDockId", None) or "")
		or "config-file-menu"
	)
	try:
		system.perspective.alterDock(dock_id, {"size": _parse_width(state.get("menuWidthOpen", "220px"))})
	except:
		pass
	try:
		state["menuConfig"] = getattr(component.view.params, "menuConfig", "") or ""
	except:
		state["menuConfig"] = ""
	try:
		state["menuConfigType"] = str(getattr(component.view.params, "menuConfigType", "yaml") or "yaml")
	except:
		state["menuConfigType"] = "yaml"
	state.setdefault("breadcrumbPathPrefix", "cfm")
	try:
		state["logoLargePath"] = str(getattr(component.view.params, "logoLargePath", "") or "")
	except:
		state["logoLargePath"] = ""
	try:
		state["logoSmallPath"] = str(getattr(component.view.params, "logoSmallPath", "") or "")
	except:
		state["logoSmallPath"] = ""
	try:
		state["logoLinkTarget"] = str(getattr(component.view.params, "logoLinkTarget", "") or "/")
	except:
		state["logoLinkTarget"] = "/"
	# Breadcrumb site name comes from MenuContent.params.siteName (copied to session).
	sync_site_name_from_view(component.session, component.view)
	state = get_state(component.session)
	state.setdefault("shellFallbackEnabled", True)
	state.setdefault("shellFallbackRoute", "/cfm/target-no-route")
	state.setdefault("logicalPagePath", "")
	ensure_show_topbar_small_logo_state(state)
	ensure_footer_visibility_state(state)
	_apply_menu_dock_state(component, state)
	component.session.custom.configFileMenu = state


def init_settings_general_state(component):
	state = get_state(component.session)
	ensure_dock_defaults(state)
	state.setdefault("closeMenuOnOutsideClick", False)
	state.setdefault("menuWidthOpen", "220px")
	state.setdefault("menuDockId", "config-file-menu")
	dock_id = str(state.get("menuDockId") or "config-file-menu")
	try:
		system.perspective.alterDock(dock_id, {"size": _parse_width(state.get("menuWidthOpen", "220px"))})
	except:
		pass
	state.setdefault("shellFallbackEnabled", True)
	state.setdefault("shellFallbackRoute", "/cfm/target-no-route")
	state.setdefault("logicalPagePath", "")
	ensure_show_topbar_small_logo_state(state)
	ensure_footer_visibility_state(state)
	_apply_menu_dock_state(component, state)
	component.session.custom.configFileMenu = state

# --- menu.py ---
def menu_item_instances(menu_text, session, view, picked_type="yaml"):
	def allowed(item):
		if get_prop(item, "visible", True) is False:
			return False
		roles = get_prop(item, "roles", [])
		if isinstance(roles, basestring):
			roles = [roles]
		if roles:
			username = session.props.auth.user.userName
			for role in roles:
				try:
					if system.security.hasRole(str(role), username, "default"):
						return True
				except:
					try:
						if system.security.hasRole(str(role), username):
							return True
					except:
						return True
			return False
		return True

	def tree_node_icon(icon):
		path = str(icon or "").strip()
		if not path:
			return None
		return {"path": path}

	def to_tree_items(children):
		result = []
		for child in children or []:
			if not is_mapping(child) or not allowed(child):
				continue
			grandchildren = get_prop(child, "children", get_prop(child, "items", []))
			child_items = to_tree_items(grandchildren)
			tree_item = {
				"label": get_prop(child, "label", ""),
				"expanded": get_prop(child, "expanded", False),
				"data": {"target": get_prop(child, "target", "")},
				"items": child_items,
			}
			icon_obj = tree_node_icon(get_prop(child, "icon", ""))
			if icon_obj:
				tree_item["icon"] = icon_obj
			result.append(tree_item)
		return result

	def to_instance(item):
		children = get_prop(item, "children", get_prop(item, "items", []))
		embed_classes = "cfm-menu__menu-embed--leaf" if not children else ""
		instance_style = {"overflow": "visible"}
		if embed_classes:
			instance_style["classes"] = embed_classes
		return {
			"instancePosition": {"shrink": 0},
			"instanceStyle": instance_style,
			"icon": get_prop(item, "icon", ""),
			"label": get_prop(item, "label", ""),
			"target": get_prop(item, "target", ""),
			"expanded": is_true(get_prop(item, "expanded", False)),
			"items": to_tree_items(children),
		}

	try:
		cfg = load_config(menu_text, picked_type)
		menu = get_prop(cfg, "menu", cfg)
		items = get_prop(menu, "items", menu if is_sequence(menu) else [])
		return [to_instance(item) for item in items if is_mapping(item) and allowed(item)]
	except Exception as exc:
		config_type = str(picked_type or "yaml").upper()
		return [{
			"instancePosition": {"shrink": 0},
			"instanceStyle": {"overflow": "visible"},
			"icon": "material/error",
			"label": "Menu " + config_type + " Error: " + str(exc),
			"target": "",
			"items": [],
		}]


def menu_items_transform(value, session, view):
	sync_site_name_from_view(session, view)
	try:
		picked_cfg, picked_type = pick_menu_block(session, value)
	except:
		picked_cfg, picked_type = value, "yaml"
	try:
		view.params.menuConfigType = picked_type
	except:
		pass
	return menu_item_instances(picked_cfg, session, view, picked_type)


FOOTER_SESSION_KEYS = {
	"showUser": "showFooterUser",
	"showSettings": "showFooterSettings",
	"showDiagnostics": "showFooterDiagnostics",
}


def ensure_footer_visibility_state(state):
	state.setdefault("showFooterUser", True)
	state.setdefault("showFooterSettings", True)
	state.setdefault("showFooterDiagnostics", True)
	return state


def footer_visible(value, session, flag_key, default_val=True):
	session_key = FOOTER_SESSION_KEYS.get(flag_key)
	if session_key:
		state = get_state(session)
		if session_key in state:
			return is_true(state.get(session_key))
		return default_val
	return default_val


def ensure_show_topbar_small_logo_state(state):
	state.setdefault("showTopBarSmallLogo", True)
	return state


def menu_panel_classes(session):
	state = get_state(session)
	try:
		device_type = str(session.props.device.type or "")
	except:
		device_type = ""
	if device_type == "designer":
		base = "cfm-menu cfm-menu--open cfm-menu__panel"
	elif is_true(state.get("isOpen", False)) or str(state.get("menuMode", "closed")).lower() == "open":
		base = "cfm-menu cfm-menu--open cfm-menu__panel"
	else:
		base = "cfm-menu cfm-menu--closed cfm-menu__panel"
	return base + " cfm-menu__arrow-left"


def menu_link_classes(page_path, target_path):
	page = normalize_path(page_path)
	target = normalize_path(target_path)
	if target and page == target:
		return "cfm-menu__link--selected"
	return ""


def resolve_logo_source(value, session, view):
	variant = str(get_prop(value, "variant", "large") or "large").lower()
	default_source = str(get_prop(value, "defaultSource", "") or "")
	state = get_state(session)
	key = "logoSmallPath" if variant == "small" else "logoLargePath"
	source = str(get_prop(value, "sessionSource", "") or state.get(key) or "").strip()
	if source:
		return source
	try:
		source = str(get_prop(value, "paramSource", "") or getattr(view.params, key, "") or "").strip()
	except:
		source = ""
	return source if source else default_source


def topbar_small_logo_visible(value, session):
	try:
		viewport = float(get_prop(value, "viewportWidth", 0) or 0)
	except:
		viewport = 0
	if viewport <= 450:
		return False
	state = get_state(session)
	if "showTopBarSmallLogo" in state:
		return is_true(state.get("showTopBarSmallLogo"))
	return True


def _find_label(items, target_path):
	for item in items or []:
		if not is_mapping(item):
			continue
		if normalize_path(get_prop(item, "target", "") or "") == target_path:
			return str(get_prop(item, "label", "") or "")
		found = _find_label(get_prop(item, "children", get_prop(item, "items", [])), target_path)
		if found:
			return found
	return ""


def _find_icon(items, target_path):
	for item in items or []:
		if not is_mapping(item):
			continue
		if normalize_path(get_prop(item, "target", "") or "") == target_path:
			return str(get_prop(item, "icon", "") or "")
		found = _find_icon(get_prop(item, "children", get_prop(item, "items", [])), target_path)
		if found:
			return found
	return ""


def _fallback_title(path):
	segments = [segment for segment in str(path or "").split("/") if segment != ""]
	if not segments:
		return "HMI Page"
	last = segments[-1]
	if last.lower() == "io":
		return "IO"
	return last.replace("-", " ").title()


def resolve_title(value, session, page):
	try:
		path = resolve_effective_page_path_from_value(value, page)
		menu_config, menu_config_type = pick_menu_block(session, value)
		cfg = load_config(menu_config, menu_config_type)
		menu = get_prop(cfg, "menu", cfg)
		items = get_prop(menu, "items", menu if is_sequence(menu) else [])
		label = _find_label(items, path)
		return label if label else _fallback_title(path)
	except:
		return _fallback_title(getattr(page.props, "path", ""))


def resolve_title_icon(value, session, page):
	try:
		path = resolve_effective_page_path_from_value(value, page)
		menu_config, menu_config_type = pick_menu_block(session, value)
		cfg = load_config(menu_config, menu_config_type)
		menu = get_prop(cfg, "menu", cfg)
		items = get_prop(menu, "items", menu if is_sequence(menu) else [])
		icon = _find_icon(items, path)
		return icon if icon else "material/description"
	except:
		return "material/description"

# --- tree.py ---
SECTION_TOGGLE_MESSAGE = "cfm-menu-toggle-section"


def on_tree_item_clicked(component, event):
	try:
		target = str(component.props.selectionData[0].value.target or "").strip()
	except:
		target = ""
	if not target:
		try:
			items = component.props.items
			path = [int(x) for x in list(event.itemPath)]
			node = items
			for idx in path:
				node = node[idx]
				if idx != path[-1]:
					node = node.get("items") or []
			target = str((node.get("data") or {}).get("target") or "").strip()
		except:
			target = ""
	if target:
		navigate_with_fallback(component, target, close_dock=True)


def is_section_tree_view(view):
	try:
		return hasattr(view.custom, "isOpen") and hasattr(view.custom, "page")
	except:
		return False


def get_section_tree_view(component):
	try:
		view = component.view
		if is_section_tree_view(view):
			return view
	except:
		pass
	node = component
	start_view = None
	try:
		start_view = component.view
	except:
		start_view = None
	for _ in range(24):
		try:
			node = node.parent
		except:
			return None
		if node is None:
			return None
		try:
			view = node.view
		except:
			view = None
		if view is None or view is start_view:
			continue
		if is_section_tree_view(view):
			return view
	return None


def toggle_section_open(section_view):
	try:
		has_children = len(section_view.params.items) > 0
	except:
		has_children = False
	if has_children:
		section_view.custom.isOpen = not bool(section_view.custom.isOpen)


def send_section_toggle_message(component, label):
	label = str(label or "").strip()
	if not label:
		return
	payload = {"label": label}
	try:
		system.perspective.sendMessage(
			messageType=SECTION_TOGGLE_MESSAGE,
			payload=payload,
			scope="page",
		)
	except:
		try:
			system.perspective.sendMessage(
				messageType=SECTION_TOGGLE_MESSAGE,
				payload=payload,
				scope="session",
			)
		except:
			pass


def on_section_arrow_click(component):
	section_view = get_section_tree_view(component)
	if section_view is not None:
		try:
			has_children = len(section_view.params.items) > 0
		except:
			has_children = False
		if has_children:
			toggle_section_open(section_view)
		return
	try:
		link_view = component.view
	except:
		return
	try:
		if not is_true(link_view.params.showArrow):
			return
	except:
		return
	try:
		label = str(link_view.params.label or "").strip()
	except:
		label = ""
	send_section_toggle_message(component, label)


def on_section_header_body_click(component):
	section_view = get_section_tree_view(component)
	if section_view is None:
		try:
			section_view = component.view
		except:
			section_view = None
	if section_view is None or not is_section_tree_view(section_view):
		return
	target = str(section_view.params.target or "").strip()
	if target:
		navigate_with_fallback(component, target, close_dock=True)


def on_menu_link_body_click(component):
	section_view = get_section_tree_view(component)
	if section_view is not None and is_section_tree_view(section_view):
		on_section_header_body_click(component)
		return
	try:
		link_view = component.view
	except:
		return
	try:
		target = str(link_view.params.target or "").strip()
		show_arrow = is_true(link_view.params.showArrow)
		is_link = is_true(link_view.params.isLink)
	except:
		target = ""
		show_arrow = False
		is_link = False
	if show_arrow:
		if target:
			navigate_with_fallback(component, target, close_dock=True)
		return
	if is_link and target:
		navigate_with_fallback(component, target, close_dock=True)


def on_section_toggle_message(component, payload):
	try:
		label = str((payload or {}).get("label") or "").strip()
	except:
		label = ""
	if not label:
		return
	try:
		section_view = component.view
	except:
		return
	if not is_section_tree_view(section_view):
		return
	try:
		section_label = str(section_view.params.label or "").strip()
	except:
		section_label = ""
	if label != section_label:
		return
	toggle_section_open(section_view)


def init_section_tree_state(component):
	try:
		expanded = component.view.params.expanded
	except:
		expanded = False
	component.view.custom.isOpen = is_true(expanded)


def page_belongs_to_section(page_path, section_target):
	page = normalize_path(page_path)
	target = normalize_path(section_target)
	if not target or not page:
		return False
	if page == target:
		return True
	return page.startswith(target + "/")


def section_classes(page_path, section_target, section_label):
	page = normalize_path(page_path)
	target = normalize_path(section_target)
	classes = []
	if target and page == target:
		classes.append("cfm-menu__link--selected")
	if page_belongs_to_section(page, target):
		classes.append("cfm-menu__section--open")
	elif not target:
		try:
			section_key = str(section_label or "").strip().lower().replace(" ", "-")
			if section_key and page.split("/")[1] == section_key:
				classes.append("cfm-menu__section--open")
		except:
			pass
	return " ".join(classes)


def section_header_classes(page_path, section_target, has_children):
	page = normalize_path(page_path)
	target = normalize_path(section_target)
	classes = ["cfm-menu__link", "cfm-menu__section-header"]
	if target and page == target:
		classes.append("cfm-menu__link--selected")
	if is_true(has_children):
		classes.append("cfm-menu__link--arrow-left")
	return " ".join(classes)


def sync_section_tree_page(component, page_path):
	try:
		previous_page = str(component.view.custom.page or "")
	except:
		previous_page = ""
	page_changed = normalize_path(page_path) != normalize_path(previous_page)

	tree = component.getChild("root").getChild("Tree")
	items, selection, selectionData = tree.updateTreeSelection(
		component.view.params.items, page_path
	)
	tree.props.items = items
	tree.props.selection = selection
	tree.props.selectionData = selectionData
	try:
		section_target = str(component.view.params.target or "").strip()
	except:
		section_target = ""
	if page_changed and page_belongs_to_section(page_path, section_target):
		component.view.custom.isOpen = True
	return page_path

# --- breadcrumb.py ---
def _add_lookup(items, trail, lookup):
	for item in items or []:
		if not is_mapping(item):
			continue
		label = get_prop(item, "label", "")
		if not label:
			continue
		current = trail + [slug(label)]
		target = get_prop(item, "target", "")
		if target:
			lookup[tuple(current)] = target
		children = get_prop(item, "children", get_prop(item, "items", []))
		_add_lookup(children, current, lookup)


def _menu_target_for(segments, lookup):
	for start in range(len(segments)):
		candidate = tuple(segments[start:])
		if candidate in lookup:
			return lookup[candidate]
	return ""


def _add_label_lookup(items, trail, lookup):
	for item in items or []:
		if not is_mapping(item):
			continue
		label = get_prop(item, "label", "")
		if not label:
			continue
		current = trail + [slug(label)]
		lookup[tuple(current)] = str(label)
		children = get_prop(item, "children", get_prop(item, "items", []))
		_add_label_lookup(children, current, lookup)


def _menu_label_for(segments, lookup):
	for start in range(len(segments)):
		candidate = tuple(segments[start:])
		if candidate in lookup:
			return lookup[candidate]
	return ""


def _home_target_for(menu_items, prefix, pages, shell_fallback=False):
	if "/" in pages or shell_fallback:
		return "/"
	for item in menu_items or []:
		if not is_mapping(item):
			continue
		label = str(get_prop(item, "label", "")).strip().lower()
		target = str(get_prop(item, "target", "") or "").strip()
		if label == "home" and target and (target in pages or shell_fallback):
			return target
	for item in menu_items or []:
		if not is_mapping(item):
			continue
		target = str(get_prop(item, "target", "") or "").strip()
		if target and (target in pages or shell_fallback):
			return target
	if prefix:
		candidate = "/" + prefix + "/dashboard"
		if candidate in pages or shell_fallback:
			return candidate
	return ""


def _crumb_style():
	return {
		"classes": "",
		"height": "40px",
		"maxHeight": "40px",
		"minHeight": "40px",
		"display": "flex",
		"alignItems": "center",
		"overflow": "visible",
	}


def build_instances(value, page):
	try:
		path = resolve_effective_page_path_from_value(value, page)
		viewport_width = get_prop(value, "viewportWidth", page.props.dimensions.viewport.width)
		menu_config = get_prop(value, "menuConfig", "")
		menu_config_type = str(get_prop(value, "menuConfigType", "yaml") or "yaml")
		path_prefix = str(get_prop(value, "pathPrefix", "cfm") or "cfm").strip().lower()
		all_pages = [i["url"] for i in system.perspective.getProjectInfo()["pageConfigs"]]
		cfg = load_config(menu_config, menu_config_type)
		menu = get_prop(cfg, "menu", cfg)
		items = get_prop(menu, "items", menu if is_sequence(menu) else [])
		lookup = {}
		_add_lookup(items, [], lookup)
		label_lookup = {}
		_add_label_lookup(items, [], label_lookup)
		all_segments = [segment for segment in str(path or "").split("/")[1:] if segment != ""]
		if path_prefix and all_segments and all_segments[0] == path_prefix:
			display_segments = all_segments[1:]
			prefix_count = 1
		else:
			display_segments = all_segments
			prefix_count = 0
		dock_id = str(
			get_prop(value, "prefMenuDockId", "")
			or get_prop(value, "menuDockId", "config-file-menu")
			or "config-file-menu"
		)
		shell_fallback = is_true(get_prop(value, "shellFallbackEnabled", True))
		home_target = _home_target_for(items, path_prefix, all_pages, shell_fallback)
		site_name = resolve_site_name(value, page.session)
		instances = [{
			"instanceStyle": _crumb_style(),
			"instancePosition": {},
			"icon": "",
			"isLink": home_target != "",
			"label": site_name,
			"isHome": True,
			"preserveLabelCase": True,
			"menuDockId": dock_id,
			"parentIndex": 0,
			"showArrow": False,
			"target": home_target,
		}]
		for index, label in enumerate(display_segments):
			segment_slice = all_segments[: prefix_count + index + 1]
			current_path = "/" + "/".join(segment_slice)
			configured_target = _menu_target_for(segment_slice, lookup)
			shell_fallback = is_true(get_prop(value, "shellFallbackEnabled", True))
			if configured_target and configured_target in all_pages:
				target = configured_target
				is_link = True
			elif current_path in all_pages:
				target = current_path
				is_link = True
			elif shell_fallback and configured_target:
				target = configured_target
				is_link = True
			else:
				target = ""
				is_link = False
			menu_label = _menu_label_for(segment_slice, label_lookup)
			display_label = menu_label if menu_label else label
			crumb = {
				"instanceStyle": _crumb_style(),
				"instancePosition": {},
				"icon": "material/arrow_right",
				"isLink": is_link,
				"label": display_label,
				"preserveLabelCase": menu_label != "",
				"menuDockId": dock_id,
				"parentIndex": 0,
				"showArrow": False,
				"target": target,
			}
			if viewport_width <= 450:
				instances = [instances[0], crumb]
			else:
				instances.append(crumb)
		return instances
	except Exception as exc:
		return [{
			"instanceStyle": _crumb_style(),
			"instancePosition": {},
			"icon": "material/error",
			"isLink": False,
			"label": "Breadcrumb Error: " + str(exc),
			"parentIndex": 0,
			"showArrow": False,
			"target": "",
		}]

# --- settings.py ---
def convert_yaml_to_json(component):
	try:
		yaml_text = component.getSibling("YamlInput").props.text
		parsed = parse_yaml_lite(yaml_text, empty_root={"items": []})
		if isinstance(parsed, dict) and "menu" in parsed:
			obj = parsed["menu"]
		else:
			obj = parsed
		component.getSibling("JsonOutput").props.text = system.util.jsonEncode(obj, 2)
	except Exception as exc:
		component.getSibling("JsonOutput").props.text = "Conversion error: " + str(exc)


def set_session_block_field(session, block_key, field_key, value):
	state = get_state(session)
	block = state.get(block_key)
	if block is None or not hasattr(block, "get"):
		block = {}
	else:
		block = dict(block)
	block[field_key] = value
	state[block_key] = block
	session.custom.configFileMenu = state


def set_state_field(session, field_key, value):
	state = get_state(session)
	state[field_key] = value
	session.custom.configFileMenu = state


def settings_tab_view_path(index):
	paths = [
		"Config File Menu/Resources/Menu/Menu Settings General",
		"Config File Menu/Resources/Menu/Menu Settings Help",
		"Config File Menu/Resources/Menu/Menu Settings Tag Menu",
		"Config File Menu/Resources/Menu/Menu Settings Menu Routes",
		"Config File Menu/Resources/Menu/Menu Settings Config Converter",
	]
	try:
		idx = int(index if index is not None else 0)
	except:
		idx = 0
	if idx < 0 or idx >= len(paths):
		idx = 0
	return paths[idx]


def settings_tab_class(tab_index, active_index):
	try:
		tab_idx = int(tab_index)
	except:
		tab_idx = 0
	try:
		active_idx = int(active_index if active_index is not None else 0)
	except:
		active_idx = 0
	if tab_idx == active_idx:
		return "cfm-menu__settings-tab cfm-menu__settings-tab--active cfm-diag__title"
	return "cfm-menu__settings-tab"


def init_settings_shell_state(component):
	state = get_state(component.session)
	state.setdefault("closeMenuOnOutsideClick", False)
	state.setdefault("logoVariant", "large")
	state.setdefault("menuConfigType", "yaml")
	state.setdefault("menuDockId", "config-file-menu")
	state.setdefault("breadcrumbPathPrefix", "cfm")
	ensure_dock_defaults(state)
	state.setdefault("menuFont", "")
	state.setdefault("menuFontSize", "14px")
	state.setdefault("menuWidthOpen", "220px")
	state.setdefault("tagMenuGenerator", {
		"tagPath": "[default]",
		"routePrefix": "/cfm",
		"maxDepth": "2",
		"includeMode": "all",
		"outputFormat": "yaml",
		"appendLeaves": "false",
		"folderIcon": "material/folder",
		"udtIcon": "material/settings",
		"output": "",
	})
	state.setdefault("menuRoutesGenerator", {
		"menuInput": "",
		"menuType": "yaml",
		"outputMode": "dynamic",
		"shellViewPath": "Config File Menu/Resources/View Dynamic Fallback",
		"output": "",
		"viewsOutput": "",
	})
	state.setdefault("shellFallbackEnabled", True)
	state.setdefault("shellFallbackRoute", "/cfm/target-no-route")
	state.setdefault("logicalPagePath", "")
	state.setdefault("currentTabIndex", 0)
	try:
		idx = int(getattr(component.view.params, "currentTabIndex", 0) or 0)
	except:
		idx = 0
	if idx < 0 or idx > 4:
		idx = 0
	component.view.custom.currentTabIndex = idx
	state["currentTabIndex"] = idx
	ensure_show_topbar_small_logo_state(state)
	ensure_footer_visibility_state(state)
	component.session.custom.configFileMenu = state


def _tag_slugify(name):
	import re

	s = str(name or "").strip().lower()
	s = re.sub(r"[^a-z0-9]+", "-", s)
	s = s.strip("-")
	return s if s else "item"


def _row_get(row, key, default=None):
	try:
		if hasattr(row, "get"):
			val = row.get(key, default)
			if val is not None:
				return val
		return getattr(row, key, default)
	except:
		return default


def _yaml_quote(value):
	text = str(value or "")
	if text == "":
		return '""'
	if any(ch in text for ch in ':"{}[],&*#?|-<>=!%@`'):
		return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
	return text


def _emit_yaml(value, indent=0):
	pad = "  " * indent
	if isinstance(value, list):
		if not value:
			return pad + "[]"
		lines = []
		for item in value:
			if isinstance(item, dict):
				lines.append(pad + "- label: " + _yaml_quote(item.get("label", "")))
				for key in ("icon", "target", "sourceTagPath", "expanded"):
					if key in item and item.get(key) not in (None, ""):
						lines.append(pad + "  " + key + ": " + _yaml_quote(item.get(key)))
				children = item.get("children")
				if children:
					lines.append(pad + "  children:")
					lines.extend(_emit_yaml(children, indent + 2).splitlines())
			else:
				lines.append(pad + "- " + _yaml_quote(item))
		return "\n".join(lines)
	if isinstance(value, dict):
		lines = []
		for key, val in value.items():
			if isinstance(val, (dict, list)):
				lines.append(pad + str(key) + ":")
				lines.extend(_emit_yaml(val, indent + 1).splitlines())
			else:
				lines.append(pad + str(key) + ": " + _yaml_quote(val))
		return "\n".join(lines)
	return pad + _yaml_quote(value)


def save_tag_menu_generator(session, root):
	state = get_state(session)
	tm = state.get("tagMenuGenerator")
	if tm is None or not hasattr(tm, "get"):
		tm = {}
	else:
		tm = dict(tm)
	tm["tagPath"] = child_text(root, "TagPathInput", "")
	tm["routePrefix"] = child_text(root, "RoutePrefixInput", "")
	tm["maxDepth"] = child_text(root, "MaxDepthInput", "2")
	tm["includeMode"] = child_value(root, "IncludeDropdown", "all")
	tm["outputFormat"] = child_value(root, "OutputFormatDropdown", "yaml")
	tm["appendLeaves"] = child_value(root, "AppendLeavesDropdown", "false")
	tm["folderIcon"] = child_text(root, "FolderIconInput", "material/folder")
	tm["udtIcon"] = child_text(root, "UdtIconInput", "material/settings")
	state["tagMenuGenerator"] = tm
	session.custom.configFileMenu = state


def _tag_kind(path, browse_tag_type):
	tag_type = str(browse_tag_type or "")
	if "UdtInstance" in tag_type or tag_type in ("UdtInstance", "UdtType"):
		return "udt"
	if tag_type == "Folder":
		return "folder"
	try:
		cfg = system.tag.getConfiguration(path, False)
		if cfg:
			row = cfg[0] if hasattr(cfg, "__getitem__") and len(cfg) > 0 else cfg
			cfg_tag_type = str(_row_get(row, "tagType", "") or "")
			if "UdtInstance" in cfg_tag_type or cfg_tag_type in ("UdtInstance", "UdtType"):
				return "udt"
			if cfg_tag_type == "Folder":
				return "folder"
	except:
		pass
	return "other"


def _browse_tag_menu_items(tag_path, route_prefix, levels_below, include_mode, folder_icon, udt_icon, append_leaves):
	items = []
	if levels_below <= 0:
		return items
	try:
		results = system.tag.browse(path=tag_path).getResults()
	except Exception as exc:
		raise Exception("Browse failed for " + str(tag_path) + ": " + str(exc))
	for row in results:
		name = str(_row_get(row, "name", "") or "")
		if name == "":
			continue
		tag_type = str(_row_get(row, "tagType", "") or "")
		has_children = bool(_row_get(row, "hasChildren", False))
		child_tag_path = tag_path.rstrip("/") + "/" + name
		kind = _tag_kind(child_tag_path, tag_type)
		is_folder = kind == "folder"
		is_udt = kind == "udt"
		if include_mode == "udt" and not is_udt and not (is_folder and has_children):
			continue
		if include_mode == "folder" and not is_folder:
			continue
		slug = _tag_slugify(name)
		prefix = route_prefix.rstrip("/")
		target = prefix + "/" + slug if prefix else "/" + slug
		icon = udt_icon if is_udt else folder_icon
		node = {
			"label": name,
			"icon": icon,
			"target": target,
			"sourceTagPath": child_tag_path,
		}
		children = []
		if has_children and levels_below > 1:
			children = _browse_tag_menu_items(
				child_tag_path,
				target,
				levels_below - 1,
				include_mode,
				folder_icon,
				udt_icon,
				append_leaves,
			)
		if append_leaves and is_udt:
			children = list(children or [])
			children.extend([
				{"label": "Overview", "icon": "material/dashboard", "target": target + "/overview"},
				{"label": "Details", "icon": "material/info", "target": target + "/details"},
			])
		if children:
			node["children"] = children
		items.append(node)
	return items


def generate_tag_menu(component):
	try:
		root = root_component(component)
		save_tag_menu_generator(component.session, root)
		tag_path = child_text(root, "TagPathInput", "[default]")
		route_prefix = child_text(root, "RoutePrefixInput", "/cfm/equipment")
		max_depth_raw = child_text(root, "MaxDepthInput", "2") or "2"
		try:
			max_depth = int(float(max_depth_raw))
		except:
			max_depth = 2
		include_mode = child_value(root, "IncludeDropdown", "all").lower()
		output_format = child_value(root, "OutputFormatDropdown", "yaml").lower()
		folder_icon = child_text(root, "FolderIconInput", "material/folder") or "material/folder"
		udt_icon = child_text(root, "UdtIconInput", "material/settings") or "material/settings"
		append_leaves = is_true(child_value(root, "AppendLeavesDropdown", "false"))
		max_depth = max(1, min(max_depth, 12))
		if not tag_path:
			raise Exception("Tag browse path is required.")
		if not route_prefix.startswith("/"):
			route_prefix = "/" + route_prefix
		output_box = find_child(root, "TagMenuOutput")
		if output_box is None:
			raise Exception("Output field TagMenuOutput not found.")
		output_box.props.text = ""
		root_name = tag_path.split("/")[-1] or "Equipment"
		root_slug = _tag_slugify(root_name)
		root_target = route_prefix.rstrip("/") + "/" + root_slug if route_prefix not in ("", "/") else "/" + root_slug
		branch_children = _browse_tag_menu_items(
			tag_path,
			root_target,
			max_depth,
			include_mode,
			folder_icon,
			udt_icon,
			append_leaves,
		)
		branch = {
			"label": root_name,
			"icon": folder_icon,
			"target": root_target,
			"sourceTagPath": tag_path,
		}
		if branch_children:
			branch["children"] = branch_children
		menu_obj = {"menu": {"items": [branch]}}
		header = "# Generated from " + tag_path + " - review and merge into MenuContent.params.menuConfig\n"
		header += "# Max levels below browse path: " + str(max_depth) + "\n"
		header += "# Remove sourceTagPath keys before pasting if desired (menu ignores unknown keys).\n"
		if output_format == "json":
			output = header + system.util.jsonEncode(menu_obj, 2)
		else:
			output = header + _emit_yaml(menu_obj)
		output_box.props.text = output
		set_session_block_field(component.session, "tagMenuGenerator", "output", output)
		status = find_child(root, "StatusLabel")
		if status is not None:
			status.props.text = (
				"Generated " + str(len(branch_children)) + " children at max "
				+ str(max_depth) + " level(s) below browse path."
			)
	except Exception as exc:
		root = root_component(component)
		out = find_child(root, "TagMenuOutput")
		if out is not None:
			out.props.text = "Error: " + str(exc)
		status = find_child(root, "StatusLabel")
		if status is not None:
			status.props.text = "Generation failed."


def save_menu_routes_generator(
	session,
	root,
	output_text=None,
	views_output_text=None,
	default_shell_path="Config File Menu/Resources/View Dynamic Fallback",
):
	try:
		cfg = session.custom.configFileMenu
		if cfg is None:
			cfg = {}
		else:
			cfg = dict(cfg)
	except:
		cfg = {}
	mr = cfg.get("menuRoutesGenerator")
	if mr is None or not hasattr(mr, "get"):
		mr = {}
	else:
		mr = dict(mr)
	mr["menuInput"] = child_text_preserve(root, "MenuInput", "")
	mr["menuType"] = child_value(root, "MenuTypeDropdown", "yaml")
	mr["outputMode"] = child_value(root, "OutputModeDropdown", "dynamic")
	mr["shellViewPath"] = child_text(root, "ShellViewInput", default_shell_path)
	if output_text is not None:
		mr["output"] = str(output_text)
	else:
		try:
			mr["output"] = child_text_preserve(root, "RoutesOutput", "")
		except:
			pass
	if views_output_text is not None:
		mr["viewsOutput"] = str(views_output_text)
	else:
		try:
			mr["viewsOutput"] = child_text_preserve(root, "ViewsOutput", "")
		except:
			pass
	cfg["menuRoutesGenerator"] = mr
	session.custom.configFileMenu = cfg


def load_menu_routes_generator(component, default_menu_input, default_output, default_shell_path):
	try:
		cfg = component.session.custom.configFileMenu
		if cfg is None:
			return
		mr = cfg.get("menuRoutesGenerator")
		if mr is None or not hasattr(mr, "get"):
			return
		mr = dict(mr)
		root = root_component(component)
		set_text(root, "MenuInput", mr.get("menuInput"), default_menu_input)
		set_value(root, "MenuTypeDropdown", mr.get("menuType"), "yaml")
		set_value(root, "OutputModeDropdown", mr.get("outputMode"), "dynamic")
		set_text(root, "ShellViewInput", mr.get("shellViewPath"), default_shell_path)
		if mr.get("output") not in (None, ""):
			set_text(root, "RoutesOutput", mr.get("output"), default_output)
		if mr.get("viewsOutput") not in (None, ""):
			set_text(root, "ViewsOutput", mr.get("viewsOutput"), "")
	except:
		pass


def shutdown_menu_routes_generator(component, default_shell_path):
	root = root_component(component)
	save_menu_routes_generator(component.session, root, default_shell_path=default_shell_path)


def _parse_yaml_lite_menu(text):
	parsed = parse_yaml_lite(text, empty_root={"items": []})
	if isinstance(parsed, dict) and "menu" in parsed:
		menu = parsed["menu"]
		if isinstance(menu, dict):
			return menu
	return parsed


def _load_menu(menu_text, menu_type):
	cfg_type = str(menu_type or "yaml").lower().strip()
	if cfg_type == "json":
		if isinstance(menu_text, basestring):
			data = system.util.jsonDecode(menu_text)
		else:
			data = normalize_document(menu_text)
	else:
		data = _parse_yaml_lite_menu(menu_text)
	if isinstance(data, dict):
		items = data.get("items", [])
		if items:
			return items
		menu = data.get("menu", {})
		if isinstance(menu, dict):
			return menu.get("items", [])
	if isinstance(data, list):
		return data
	return []


def _walk_menu(items, trail):
	trail = trail or []
	routes = []
	for item in items or []:
		if not hasattr(item, "get"):
			continue
		label = str(item.get("label", "") or "Page")
		target = str(item.get("target", "") or "").strip()
		path = trail + [label]
		title = " - ".join(path)
		if target:
			if not target.startswith("/"):
				target = "/" + target
			routes.append((target, title))
		children = item.get("children", item.get("items", []))
		if children:
			routes.extend(_walk_menu(children, path))
	return routes


def _get_path_prefix(session):
	try:
		cfg = session.custom.configFileMenu
		if cfg and hasattr(cfg, "get"):
			return str(cfg.get("breadcrumbPathPrefix") or "cfm")
	except:
		pass
	return "cfm"


def _slug_to_title(slug):
	import re

	parts = re.split(r"[-_]+", str(slug or "").strip())
	words = [p.capitalize() for p in parts if p]
	return " ".join(words) if words else "Page"


def target_to_view_path(target, path_prefix="cfm"):
	target = str(target or "").strip()
	if not target.startswith("/"):
		target = "/" + target
	segments = [s for s in target.split("/") if s]
	prefix = str(path_prefix or "cfm").strip().lower()
	if segments and segments[0].lower() == prefix:
		segments = segments[1:]
	if not segments:
		return "Page"
	return "/".join(_slug_to_title(s) for s in segments)


def _build_view_template(title):
	page_title = str(title or "Page")
	return {
		"custom": {},
		"params": {
			"menuDockId": "config-file-menu",
			"closeMenuOnOutsideClick": True,
			"requestedPath": "",
		},
		"propConfig": {
			"params.menuDockId": {"paramDirection": "input", "persistent": True},
			"params.closeMenuOnOutsideClick": {"paramDirection": "input", "persistent": True},
			"params.requestedPath": {"paramDirection": "input", "persistent": True},
		},
		"props": {"defaultSize": {"height": 900, "width": 1200}},
		"root": {
			"meta": {"name": "root"},
			"type": "ia.container.flex",
			"props": {
				"style": {
					"height": "100%",
					"backgroundColor": "var(--neutral-10, #f7f8fa)",
				}
			},
			"events": {
				"component": {
					"onStartup": {
						"config": {"script": "\texchange.cfm.runtime.sync_shell_session(self)\n"},
						"scope": "G",
						"type": "script",
					}
				},
				"dom": {
					"onClick": {
						"config": {"script": "\texchange.cfm.runtime.close_on_outside_click(self)\n"},
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
								"style": {
									"backgroundColor": "var(--container--background, white)",
									"border": "1px solid var(--neutral-30, #d8dee4)",
									"borderRadius": "8px",
									"padding": "24px",
								},
							},
							"children": [
								{
									"meta": {"name": "TitleLabel"},
									"type": "ia.display.label",
									"position": {"basis": "48px", "shrink": 0},
									"props": {
										"text": page_title,
										"textStyle": {
											"fontSize": "1.75em",
											"fontWeight": "600",
										},
									},
								},
								{
									"meta": {"name": "Placeholder"},
									"type": "ia.display.label",
									"position": {"grow": 1},
									"props": {
										"alignVertical": "top",
										"text": "Replace this placeholder with your HMI screen content.",
										"textStyle": {
											"color": "var(--neutral-60, #7b8794)",
											"fontSize": "1.1em",
										},
									},
								},
							],
						}
					],
				}
			],
		},
	}


def generate_output(component, default_shell_path):
	try:
		root = root_component(component)
		save_menu_routes_generator(component.session, root, default_shell_path=default_shell_path)
		menu_text = child_text_preserve(root, "MenuInput", "")
		menu_type = child_value(root, "MenuTypeDropdown", "yaml")
		output_mode = str(child_value(root, "OutputModeDropdown", "dynamic") or "dynamic").strip()
		shell_path = child_text(root, "ShellViewInput", default_shell_path) or default_shell_path
		output_box = find_child(root, "RoutesOutput")
		views_box = find_child(root, "ViewsOutput")
		status = find_child(root, "RoutesStatusLabel")
		if output_box is None:
			raise Exception("Output field RoutesOutput not found.")
		output_box.props.text = ""
		if views_box is not None:
			views_box.props.text = ""
		items = _load_menu(menu_text, menu_type)
		if not items:
			raise Exception("No menu items found. Paste menu YAML or JSON with an items array.")
		routes = _walk_menu(items, [])
		path_prefix = _get_path_prefix(component.session)
		pages = {}
		views_manifest = {}
		seen = set()
		for target, title in routes:
			if target in seen:
				continue
			seen.add(target)
			if output_mode == "createViews":
				view_path = target_to_view_path(target, path_prefix)
				pages[target] = {"title": title, "viewPath": view_path}
				views_manifest[view_path] = _build_view_template(title)
			else:
				pages[target] = {"title": title, "viewPath": shell_path}
		payload = {
			"_comment": "Merge these pages into com.inductiveautomation.perspective/page-config/config.json. Preserve sharedDocks and existing fixed routes.",
			"pages": pages,
		}
		output = system.util.jsonEncode(payload, 2)
		output_box.props.text = output
		views_output = ""
		if output_mode == "createViews" and views_box is not None:
			views_payload = {
				"_comment": "Create these Perspective views under com.inductiveautomation.perspective/views/. Each key is a view path; value is view.json content.",
				"views": views_manifest,
			}
			views_output = system.util.jsonEncode(views_payload, 2)
			views_box.props.text = views_output
		save_menu_routes_generator(
			component.session,
			root,
			output,
			views_output_text=views_output,
			default_shell_path=default_shell_path,
		)
		if status is not None:
			if output_mode == "createViews":
				status.props.text = (
					"Generated " + str(len(pages)) + " page routes and " + str(len(views_manifest)) + " views."
				)
			else:
				status.props.text = "Generated " + str(len(pages)) + " page routes."
	except Exception as exc:
		root = root_component(component)
		out = find_child(root, "RoutesOutput")
		if out is not None:
			out.props.text = "Error: " + str(exc)
		status = find_child(root, "RoutesStatusLabel")
		if status is not None:
			status.props.text = "Generation failed."
