"""Dock open/close and shell page behaviors.

All project configuration lives in one session custom object,
session.custom.configFileMenu, which ships with the library (session-props resource)
fully populated with defaults. The runtime reads/writes that object directly; there is
no view-param seeding. Keys are flat and group-prefixed (dock* / content* / brand* /
layout* / show* / route*). The dock open/pin/content mode are stored as:
    dockOpen         bool   menu currently open (its shipped default is the initial state)
    dockPinned       bool   pinned (blocks outside-click dismiss; implies push+open)
    dockContentPush  bool   True -> push, False -> cover
The Perspective dock API and CSS want a "push"/"cover" string, so dockContentPush is
converted to that string only at the alterDock boundary (see _dock_content).
"""


def _dock_content(state):
	# Derive the Perspective "push"/"cover" content string from the boolean dockContentPush.
	return "push" if cfm.config.is_true(state.get("dockContentPush", True)) else "cover"


def init_topbar_state(component):
	# The Top Bar shares the session object; nothing to seed (it ships populated). Kept as a
	# stable onStartup entry point that simply re-affirms the identity keys it reads.
	state = cfm.config.get_state(component.session)
	cfm.config.set_state_fields(component.session, {
		"contentDockId": state.get("contentDockId", "config-file-menu"),
		"contentBreadcrumbPrefix": state.get("contentBreadcrumbPrefix", "cfm"),
	})


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


def _topbar_is_open(component, state):
	try:
		device_type = str(component.session.props.device.type or "")
	except:
		device_type = ""
	if device_type == "designer":
		return True
	dock_content = _dock_content(state)
	pinned = cfm.config.is_true(state.get("dockPinned", False))
	session_open = cfm.config.is_true(state.get("dockOpen", False))
	if dock_content == "push" or pinned:
		return _layout_is_open(component) or session_open
	return session_open


def topbar_toggle_icon(component):
	state = cfm.config.get_state(component.session)
	return "material/menu_open" if _topbar_is_open(component, state) else "material/menu"


def topbar_toggle_classes(component):
	state = cfm.config.get_state(component.session)
	if _topbar_is_open(component, state):
		return "cfm-menu__button cfm-menu__button--close-menu"
	return "cfm-menu__button cfm-menu__button--open-menu"


def on_menu_toggle_click(component):
	state = cfm.config.get_state(component.session)
	dock_id = cfm.config.resolve_dock_id(state)
	pinned = cfm.config.is_true(state.get("dockPinned", False))
	dock_content = _dock_content(state)
	if pinned:
		dock_content = "push"
	session_open = cfm.config.is_true(state.get("dockOpen", False))
	if dock_content == "push" or pinned:
		currently_open = _layout_is_open(component) or session_open
	else:
		currently_open = session_open
	if currently_open:
		system.perspective.closeDock(dock_id)
		cfm.config.set_state_fields(component.session, {
			"dockOpen": False,
			"dockPinned": pinned, "dockContentPush": dock_content == "push",
		})
	else:
		system.perspective.alterDock(dock_id, {"content": dock_content})
		system.perspective.openDock(dock_id)
		cfm.config.set_state_fields(component.session, {
			"dockOpen": True,
			"dockPinned": pinned, "dockContentPush": dock_content == "push",
		})


def on_dock_mode_toggle(component):
	state = cfm.config.get_state(component.session)
	dock_id = cfm.config.resolve_dock_id(state)
	current = _dock_content(state)
	new_mode = "push" if current == "cover" else "cover"
	new_pinned = False if new_mode == "cover" else cfm.config.is_true(state.get("dockPinned", False))
	system.perspective.alterDock(dock_id, {"content": new_mode})
	system.perspective.openDock(dock_id)
	cfm.config.set_state_fields(component.session, {
		"dockOpen": True,
		"dockPinned": new_pinned, "dockContentPush": new_mode == "push",
	})


def on_dock_pin_toggle(component):
	state = cfm.config.get_state(component.session)
	dock_id = cfm.config.resolve_dock_id(state)
	pinned = cfm.config.is_true(state.get("dockPinned", False))
	dock_content = _dock_content(state)
	if pinned:
		system.perspective.alterDock(dock_id, {"content": dock_content})
		is_open = cfm.config.is_true(state.get("dockOpen", True))
		fields = {
			"dockOpen": is_open,
			"dockPinned": False,
			"dockContentPush": dock_content == "push",
		}
	else:
		system.perspective.alterDock(dock_id, {"content": "push"})
		system.perspective.openDock(dock_id)
		fields = {"dockOpen": True, "dockPinned": True, "dockContentPush": True}
	cfm.config.set_state_fields(component.session, fields)


def on_settings_pinned_change(component):
	state = cfm.config.get_state(component.session)
	dock_id = cfm.config.resolve_dock_id(state)
	pinned = cfm.config.is_true(component.props.value)
	if pinned:
		system.perspective.alterDock(dock_id, {"content": "push"})
		system.perspective.openDock(dock_id)
		fields = {
			"dockOpen": True,
			"dockPinned": True, "dockContentPush": True,
		}
	else:
		fields = {"dockPinned": False}
	cfm.config.set_state_fields(component.session, fields)


def on_settings_dock_content_change(component):
	state = cfm.config.get_state(component.session)
	push = cfm.config.is_true(component.props.value)
	mode = "push" if push else "cover"
	dock_id = cfm.config.resolve_dock_id(state)
	system.perspective.alterDock(dock_id, {"content": mode})
	fields = {"dockContentPush": push}
	if not push:
		fields["dockPinned"] = False
	cfm.config.set_state_fields(component.session, fields)


def on_settings_menu_width_change(component):
	state = cfm.config.get_state(component.session)
	width_text = str(component.props.text or "").strip()
	dock_id = cfm.config.resolve_dock_id(state)
	try:
		system.perspective.alterDock(dock_id, {"size": _parse_width(width_text)})
	except:
		pass
	cfm.config.set_state_fields(component.session, {"layoutWidthOpen": width_text})


def close_on_outside_click(component):
	state = cfm.config.get_state(component.session)
	# The dock defaults ship in the session object, so dockCloseOnOutsideClick / dockPinned /
	# dockOpen are always present here. A pinned dock never dismisses on an outside click.
	if not cfm.config.is_true(state.get("dockCloseOnOutsideClick", True)):
		return
	if cfm.config.is_true(state.get("dockPinned", False)):
		return
	if not cfm.config.is_true(state.get("dockOpen", True)):
		return
	dock_id = cfm.config.resolve_dock_id(state)
	system.perspective.closeDock(dock_id)
	# Only change open/closed state. Never write dockPinned / dockContentPush here — an
	# outside click closes the menu but must not alter the session's dock settings.
	cfm.config.set_state_fields(component.session, {
		"dockOpen": False,
	})


def _apply_physical_dock(session):
	# Push the physical Perspective dock (content mode, size, open/closed) to match the
	# session dock state. Reads state from the session only, so it can run from either the
	# shared dock's onStartup OR a binding transform. Idempotent: it only syncs the physical
	# dock to the current dockOpen, so it never fights a live Settings/toggle change.
	state = cfm.config.get_state(session)
	dock_id = cfm.config.resolve_dock_id(state)
	pinned = cfm.config.is_true(state.get("dockPinned", False))
	# Invariant: a pinned dock is always push + open. Otherwise honor dockContentPush/dockOpen.
	dock_content = "push" if pinned else _dock_content(state)
	want_open = True if pinned else cfm.config.is_true(state.get("dockOpen", False))
	try:
		system.perspective.alterDock(
			dock_id,
			{
				"content": dock_content,
				"size": _parse_width(state.get("layoutWidthOpen", "220px")),
			},
		)
	except:
		pass
	try:
		if want_open:
			system.perspective.openDock(dock_id)
		else:
			system.perspective.closeDock(dock_id)
	except:
		pass


def apply_startup_dock_state(session):
	# Public entry point called from the MenuItems binding transform (see menu.py). A shared
	# dock's onStartup does not reliably fire in Perspective 8.3.3, but the MenuItems binding
	# always runs on menu render — so this is where the authored startup open/closed state
	# (dockOpen, incl. "start closed") is reliably applied to the physical dock. Because the
	# binding depends on contentSource (not on dock state), it runs about once per session and
	# does not loop when the dock opens/closes.
	_apply_physical_dock(session)


def sync_shell_session(component):
	# Shell/fallback pages track the requested logical path for breadcrumb/title use. The
	# menu config now ships in the session object (contentSource), so no backfill is needed.
	try:
		requested = str(getattr(component.view.params, "requestedPath", "") or "").strip()
	except:
		requested = ""
	if requested:
		# Only write when it actually changes — a no-op write re-fires the breadcrumb binding.
		state = cfm.config.get_state(component.session)
		if cfm.config.should_write_route_logical(state.get("routeLogicalPath"), requested):
			cfm.config.set_state_fields(component.session, {"routeLogicalPath": requested})


def _parse_width(raw, default=220):
	s = str(raw or "").strip().lower()
	if s.endswith("px"):
		s = s[:-2].strip()
	try:
		w = int(float(s))
		return max(120, min(w, 800))
	except:
		return default


def init_menu_content_state(component):
	# Best-effort physical dock apply on the shared dock's onStartup (unreliable in
	# Perspective; apply_startup_dock_state from the MenuItems binding is the reliable path).
	# All config ships in the session object, so there is nothing to seed here.
	_apply_physical_dock(component.session)


def init_settings_general_state(component):
	# Apply the current dock size/content to the physical dock when Settings opens.
	_apply_physical_dock(component.session)
