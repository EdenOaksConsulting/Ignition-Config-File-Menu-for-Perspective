"""Navigation helpers and click handlers."""


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
	state = cfm.config.get_state(component.session)
	cfm.dock.ensure_dock_defaults(state)
	dock_id = str(
		state.get("menuDockId")
		or str(getattr(component.view.params, "menuDockId", None) or "")
		or "config-file-menu"
	)
	pinned = cfm.config.is_true(state.get("isPinned", False))
	dock_content = str(state.get("dockContent", "push")).lower()
	if dock_content not in ("cover", "push"):
		dock_content = "push"
	fallback_enabled = cfm.config.is_true(state.get("shellFallbackEnabled", True))
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
	if not cfm.config.is_true(component.view.params.isLink) or not target:
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
