"""Dock open/close, session bootstrap, and shell page behaviors."""


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
	state = cfm.config.get_state(component.session)
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
	pinned = cfm.config.is_true(state.get("isPinned", False))
	session_open = cfm.config.is_true(state.get("isOpen", False))
	if dock_content == "push" or pinned:
		return _layout_is_open(component) or session_open
	return session_open


def topbar_toggle_icon(component):
	state = cfm.config.get_state(component.session)
	return "material/menu_open" if _topbar_is_open(component, state) else "material/menu"


def topbar_toggle_classes(component):
	state = cfm.config.get_state(component.session)
	suffix = "close-menu" if _topbar_is_open(component, state) else "open-menu"
	return "cfm-menu__button cfm-menu__button--" + suffix


def on_menu_toggle_click(component):
	state = cfm.config.get_state(component.session)
	dock_id = _dock_id(component, state)
	pinned = cfm.config.is_true(state.get("isPinned", False))
	dock_content = _dock_content(state)
	if pinned:
		dock_content = "push"
	session_open = cfm.config.is_true(state.get("isOpen", False))
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
	state = cfm.config.get_state(component.session)
	dock_id = _dock_id(component, state)
	current = _dock_content(state)
	new_mode = "push" if current == "cover" else "cover"
	new_pinned = False if new_mode == "cover" else cfm.config.is_true(state.get("isPinned", False))
	system.perspective.alterDock(dock_id, {"content": new_mode})
	system.perspective.openDock(dock_id)
	state["isOpen"] = True
	state["menuMode"] = "open"
	state["isPinned"] = new_pinned
	state["dockContent"] = new_mode
	component.session.custom.configFileMenu = state


def on_dock_pin_toggle(component):
	state = cfm.config.get_state(component.session)
	dock_id = _dock_id(component, state)
	pinned = cfm.config.is_true(state.get("isPinned", False))
	dock_content = _dock_content(state)
	if pinned:
		system.perspective.alterDock(dock_id, {"content": dock_content})
		state["isOpen"] = cfm.config.is_true(state.get("isOpen", True))
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
	state = cfm.config.get_state(component.session)
	dock_id = _dock_id(component, state)
	pinned = cfm.config.is_true(component.props.value)
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
	state = cfm.config.get_state(component.session)
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
	state = cfm.config.get_state(component.session)
	width_text = str(component.props.text or "").strip()
	state["menuWidthOpen"] = width_text
	dock_id = _dock_id(component, state)
	try:
		system.perspective.alterDock(dock_id, {"size": _parse_width(width_text)})
	except:
		pass
	component.session.custom.configFileMenu = state


def close_on_outside_click(component):
	state = cfm.config.get_state(component.session)
	flag = state.get("closeMenuOnOutsideClick")
	if flag is None:
		try:
			flag = component.view.params.closeMenuOnOutsideClick
		except:
			flag = True
	if not cfm.config.is_true(flag):
		return
	dock_id = str(
		state.get("menuDockId")
		or str(getattr(component.view.params, "menuDockId", None) or "")
		or "config-file-menu"
	)
	if cfm.config.is_true(state.get("isPinned", False)):
		return
	if not cfm.config.is_true(state.get("isOpen", True)):
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
	if cfm.config.is_true(state.get("isPinned", False)):
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
		if cfm.config.is_true(state.get("isOpen", False)):
			system.perspective.openDock(dock_id)
		else:
			system.perspective.closeDock(dock_id)
	except:
		pass


def sync_shell_session(component):
	state = cfm.config.get_state(component.session)
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
	cfm.config.sync_site_name_from_view(component.session, component.view)


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
	state = cfm.config.get_state(component.session)
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
	cfm.config.sync_site_name_from_view(component.session, component.view)
	state = cfm.config.get_state(component.session)
	state.setdefault("shellFallbackEnabled", True)
	state.setdefault("shellFallbackRoute", "/cfm/target-no-route")
	state.setdefault("logicalPagePath", "")
	cfm.menu.ensure_show_topbar_small_logo_state(state)
	cfm.menu.ensure_footer_visibility_state(state)
	_apply_menu_dock_state(component, state)
	component.session.custom.configFileMenu = state


def init_settings_general_state(component):
	state = cfm.config.get_state(component.session)
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
	cfm.menu.ensure_show_topbar_small_logo_state(state)
	cfm.menu.ensure_footer_visibility_state(state)
	_apply_menu_dock_state(component, state)
	component.session.custom.configFileMenu = state
