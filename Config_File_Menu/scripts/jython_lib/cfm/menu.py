"""Menu tree, footer visibility, and page title helpers."""


def menu_item_instances(menu_text, session, view, picked_type="yaml"):
	def allowed(item):
		if cfm.config.get_prop(item, "visible", True) is False:
			return False
		roles = cfm.config.get_prop(item, "roles", [])
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
			if not cfm.config.is_mapping(child) or not allowed(child):
				continue
			grandchildren = cfm.config.get_prop(child, "children", cfm.config.get_prop(child, "items", []))
			child_items = to_tree_items(grandchildren)
			tree_item = {
				"label": cfm.config.get_prop(child, "label", ""),
				"expanded": cfm.config.get_prop(child, "expanded", False),
				"data": {"target": cfm.config.get_prop(child, "target", "")},
				"items": child_items,
			}
			icon_obj = tree_node_icon(cfm.config.get_prop(child, "icon", ""))
			if icon_obj:
				tree_item["icon"] = icon_obj
			result.append(tree_item)
		return result

	def to_instance(item):
		children = cfm.config.get_prop(item, "children", cfm.config.get_prop(item, "items", []))
		embed_classes = "cfm-menu__menu-embed--leaf" if not children else ""
		instance_style = {"overflow": "visible"}
		if embed_classes:
			instance_style["classes"] = embed_classes
		return {
			"instancePosition": {"shrink": 0},
			"instanceStyle": instance_style,
			"icon": cfm.config.get_prop(item, "icon", ""),
			"label": cfm.config.get_prop(item, "label", ""),
			"target": cfm.config.get_prop(item, "target", ""),
			"expanded": cfm.config.is_true(cfm.config.get_prop(item, "expanded", False)),
			"items": to_tree_items(children),
		}

	try:
		cfg = cfm.config.load_config(menu_text, picked_type)
		menu = cfm.config.get_prop(cfg, "menu", cfg)
		items = cfm.config.get_prop(menu, "items", menu if cfm.config.is_sequence(menu) else [])
		return [to_instance(item) for item in items if cfm.config.is_mapping(item) and allowed(item)]
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
	cfm.config.sync_site_name_from_view(session, view)
	try:
		picked_cfg, picked_type = cfm.config.pick_menu_block(session, value)
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
		state = cfm.config.get_state(session)
		if session_key in state:
			return cfm.config.is_true(state.get(session_key))
		return default_val
	return default_val


def ensure_show_topbar_small_logo_state(state):
	state.setdefault("showTopBarSmallLogo", True)
	return state


def menu_panel_classes(session):
	state = cfm.config.get_state(session)
	try:
		device_type = str(session.props.device.type or "")
	except:
		device_type = ""
	if device_type == "designer":
		base = "cfm-menu cfm-menu--open cfm-menu__panel"
	elif cfm.config.is_true(state.get("isOpen", False)) or str(state.get("menuMode", "closed")).lower() == "open":
		base = "cfm-menu cfm-menu--open cfm-menu__panel"
	else:
		base = "cfm-menu cfm-menu--closed cfm-menu__panel"
	return base + " cfm-menu__arrow-left"


def menu_link_classes(page_path, target_path):
	page = cfm.config.normalize_path(page_path)
	target = cfm.config.normalize_path(target_path)
	if target and page == target:
		return "cfm-menu__link--selected"
	return ""


def resolve_logo_source(value, session, view):
	variant = str(cfm.config.get_prop(value, "variant", "large") or "large").lower()
	default_source = str(cfm.config.get_prop(value, "defaultSource", "") or "")
	state = cfm.config.get_state(session)
	key = "logoSmallPath" if variant == "small" else "logoLargePath"
	source = str(cfm.config.get_prop(value, "sessionSource", "") or state.get(key) or "").strip()
	if source:
		return source
	try:
		source = str(cfm.config.get_prop(value, "paramSource", "") or getattr(view.params, key, "") or "").strip()
	except:
		source = ""
	return source if source else default_source


def topbar_small_logo_visible(value, session):
	try:
		viewport = float(cfm.config.get_prop(value, "viewportWidth", 0) or 0)
	except:
		viewport = 0
	if viewport <= 450:
		return False
	state = cfm.config.get_state(session)
	if "showTopBarSmallLogo" in state:
		return cfm.config.is_true(state.get("showTopBarSmallLogo"))
	return True


def _find_label(items, target_path):
	for item in items or []:
		if not cfm.config.is_mapping(item):
			continue
		if cfm.config.normalize_path(cfm.config.get_prop(item, "target", "") or "") == target_path:
			return str(cfm.config.get_prop(item, "label", "") or "")
		found = _find_label(cfm.config.get_prop(item, "children", cfm.config.get_prop(item, "items", [])), target_path)
		if found:
			return found
	return ""


def _find_icon(items, target_path):
	for item in items or []:
		if not cfm.config.is_mapping(item):
			continue
		if cfm.config.normalize_path(cfm.config.get_prop(item, "target", "") or "") == target_path:
			return str(cfm.config.get_prop(item, "icon", "") or "")
		found = _find_icon(cfm.config.get_prop(item, "children", cfm.config.get_prop(item, "items", [])), target_path)
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
		path = cfm.config.resolve_effective_page_path_from_value(value, page)
		menu_config, menu_config_type = cfm.config.pick_menu_block(session, value)
		cfg = cfm.config.load_config(menu_config, menu_config_type)
		menu = cfm.config.get_prop(cfg, "menu", cfg)
		items = get_prop(menu, "items", menu if is_sequence(menu) else [])
		label = _find_label(items, path)
		return label if label else _fallback_title(path)
	except:
		return _fallback_title(getattr(page.props, "path", ""))


def resolve_title_icon(value, session, page):
	try:
		path = cfm.config.resolve_effective_page_path_from_value(value, page)
		menu_config, menu_config_type = cfm.config.pick_menu_block(session, value)
		cfg = cfm.config.load_config(menu_config, menu_config_type)
		menu = cfm.config.get_prop(cfg, "menu", cfg)
		items = get_prop(menu, "items", menu if is_sequence(menu) else [])
		icon = _find_icon(items, path)
		return icon if icon else "material/description"
	except:
		return "material/description"
