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
						# Deliberate FAIL-OPEN: if the role check itself errors (e.g. an
						# unexpected user-source arg on this gateway), show the menu item
						# rather than hide it. `roles` is a visibility convenience only —
						# real access control is enforced on the destination pages
						# (see the README security note), so a broken check must not lock
						# users out of navigation.
						cfm.log.log_once("menu", "warn", "Role check errored; showing item (fail-open) for role=" + str(role))
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
			grandchildren = cfm.config.get_children(child)
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
		children = cfm.config.get_children(item)
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

	# Perf gate (opt-in): the menu-structure transform deliberately avoids a session read
	# (see menu_items_transform), so perf here is gated on the CFM.perf TRACE logger only,
	# never forced by the perfLogging property — nothing is timed when perf logging is off.
	_perf = cfm.log.perf_enabled()
	_t0 = cfm.log.now_nanos() if _perf else 0
	try:
		items = cfm.config.load_menu_items(menu_text, picked_type)
		result = [to_instance(item) for item in items if cfm.config.is_mapping(item) and allowed(item)]
		if _perf:
			cfm.log.perf("menu.render", cfm.log.now_nanos() - _t0, "items=%d" % len(items))
		return result
	except Exception as exc:
		cfm.log.log_once("menu", "error", "Menu config parse failed", exc)
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
	# The menu STRUCTURE only depends on the authored menu config; it does not change when
	# the user navigates. The MenuItems struct depends on contentSource/contentSourceType
	# only, so navigation-time session writes no longer re-trigger this expensive full
	# re-render. `value` is unused — the menu is read from the session object below — and
	# all config ships there, so there is nothing to seed here.
	#
	# A shared dock's onStartup does not reliably fire in Perspective 8.3.3, but this binding
	# always runs on menu render — so this is where the authored startup open/closed state
	# (dockOpen, including "start closed") is reliably pushed to the physical dock.
	try:
		cfm.dock.apply_startup_dock_state(session)
	except:
		pass
	try:
		picked_cfg, picked_type = cfm.config.pick_menu_block(session, value)
	except:
		picked_cfg, picked_type = value, "yaml"
	return menu_item_instances(picked_cfg, session, view, picked_type)


def ensure_footer_visibility_state(state):
	state.setdefault("showFooterUser", True)
	state.setdefault("showFooterSettings", True)
	state.setdefault("showFooterDiagnostics", True)
	return state


def footer_visible(value, session, flag_key, default_val=True):
	# The footer position.display bindings point directly at
	# session.custom.configFileMenu.showFooter* (see build-hmi-menu-sample
	# footer_visibility_binding), so `value` already carries that flag; a missing
	# key resolves to None -> use the default. session/flag_key are kept only for a
	# stable transform signature.
	if value is None:
		return default_val
	return cfm.config.is_true(value)


def ensure_show_topbar_small_logo_state(state):
	state.setdefault("showTopBarClock", True)
	state.setdefault("clockRefreshSeconds", 5)
	state.setdefault("showTopBarSmallLogo", True)
	return state


def _panel_classes(state, device_type):
	if device_type == "designer":
		base = "cfm-menu cfm-menu--open cfm-menu__panel"
	elif cfm.config.is_true(state.get("dockOpen", False)):
		base = "cfm-menu cfm-menu--open cfm-menu__panel"
	else:
		base = "cfm-menu cfm-menu--closed cfm-menu__panel"
	return base + " cfm-menu__arrow-left"


def _device_type(session):
	try:
		return str(session.props.device.type or "")
	except:
		return ""


def menu_panel_style(session):
	# Return the whole style object in one write. Perspective's JsonPath parser
	# rejects dotted targets that start with "--" (style.--cfm-menu-width-open),
	# so CSS custom properties must be set as keys inside a whole-object bind,
	# not via individual props.style.--cfm-* bindings. Read state once and reuse it
	# for the classes so the transform does a single get_state, not two.
	state = cfm.config.get_state(session)
	font = str(state.get("layoutFont") or "").strip()
	return {
		"classes": _panel_classes(state, _device_type(session)),
		"height": "100%",
		"minHeight": "100%",
		"backgroundColor": "var(--neutral-10)",
		"--cfm-menu-font-family": font if font else "inherit",
		"--cfm-menu-font-size": str(state.get("layoutFontSize") or "14px"),
		"--cfm-menu-width-open": str(state.get("layoutWidthOpen") or "220px"),
	}


def menu_link_classes(page_path, target_path):
	page = cfm.config.normalize_path(page_path)
	target = cfm.config.normalize_path(target_path)
	if target and page == target:
		return "cfm-menu__link--selected"
	return ""


def resolve_logo_source(value, session, view):
	# The logo source ships in the session object (brandLogoLarge / brandLogoSmall). `value`
	# carries variant + sessionSource (bound to those keys) + defaultSource (the embedded PNG).
	variant = str(cfm.config.get_prop(value, "variant", "large") or "large").lower()
	default_source = str(cfm.config.get_prop(value, "defaultSource", "") or "")
	state = cfm.config.get_state(session)
	key = "brandLogoSmall" if variant == "small" else "brandLogoLarge"
	source = str(cfm.config.get_prop(value, "sessionSource", "") or state.get(key) or "").strip()
	return source if source else default_source


def topbar_small_logo_visible(value, session):
	# value carries viewportWidth and showTopBarSmallLogo from the Top Bar small-logo
	# struct, so read the flag straight from value (same pattern as footer_visible); a
	# missing session key resolves to None -> default visible. session is kept only for
	# a stable transform signature.
	try:
		viewport = float(cfm.config.get_prop(value, "viewportWidth", 0) or 0)
	except:
		viewport = 0
	if viewport <= 450:
		return False
	flag = cfm.config.get_prop(value, "showTopBarSmallLogo", None)
	if flag is None:
		return True
	return cfm.config.is_true(flag)


def _find_label(items, target_path):
	for item in items or []:
		if not cfm.config.is_mapping(item):
			continue
		if cfm.config.normalize_path(cfm.config.get_prop(item, "target", "") or "") == target_path:
			return str(cfm.config.get_prop(item, "label", "") or "")
		found = _find_label(cfm.config.get_children(item), target_path)
		if found:
			return found
	return ""


def _find_icon(items, target_path):
	for item in items or []:
		if not cfm.config.is_mapping(item):
			continue
		if cfm.config.normalize_path(cfm.config.get_prop(item, "target", "") or "") == target_path:
			return str(cfm.config.get_prop(item, "icon", "") or "")
		found = _find_icon(cfm.config.get_children(item), target_path)
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
	# Perf gate (opt-in): title resolution runs per page and parses the menu each call.
	# Gated on the CFM.perf TRACE logger only (no session read added to this per-nav path).
	_perf = cfm.log.perf_enabled()
	_t0 = cfm.log.now_nanos() if _perf else 0
	try:
		path = cfm.config.resolve_effective_page_path_from_value(value, page)
		menu_config, menu_config_type = cfm.config.pick_menu_block(session, value)
		items = cfm.config.load_menu_items(menu_config, menu_config_type)
		label = _find_label(items, path)
		if _perf:
			cfm.log.perf("menu.title", cfm.log.now_nanos() - _t0, "path=" + str(path))
		return label if label else _fallback_title(path)
	except:
		return _fallback_title(getattr(page.props, "path", ""))


def resolve_title_icon(value, session, page):
	try:
		path = cfm.config.resolve_effective_page_path_from_value(value, page)
		menu_config, menu_config_type = cfm.config.pick_menu_block(session, value)
		items = cfm.config.load_menu_items(menu_config, menu_config_type)
		icon = _find_icon(items, path)
		return icon if icon else "material/description"
	except:
		return "material/description"
