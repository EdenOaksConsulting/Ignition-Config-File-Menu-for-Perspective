"""Navigation helpers and click handlers."""


def normalize_page_url(url):
	path = str(url or "").strip()
	if path and not path.startswith("/"):
		path = "/" + path
	return path


def get_registered_pages():
	# Normalized registered page urls. Backed by the shared, TTL'd page-url cache so a burst of
	# nav/breadcrumb evaluations on one navigation shares a single getProjectInfo() call.
	try:
		return [normalize_page_url(url) for url in cfm.config.get_project_page_urls_cached()]
	except:
		return []


def navigate_with_fallback(component, target_path, close_dock=False):
	target = normalize_page_url(target_path)
	if not target:
		return
	# Read state first so the perf gate can resolve perfLogging without an extra session
	# read, and time the whole navigation — including get_registered_pages()/getProjectInfo(),
	# which is the real cost here. Nothing is timed when perf logging is off.
	state = cfm.config.get_state(component.session)
	perf_prop = cfm.config.is_true(state.get("perfLogging", False))
	_perf = cfm.log.perf_enabled(perf_prop)
	_t0 = cfm.log.now_nanos() if _perf else 0
	pages = get_registered_pages()
	dock_id = cfm.config.resolve_dock_id(state)
	pinned = cfm.config.is_true(state.get("dockPinned", False))
	fallback_enabled = cfm.config.is_true(state.get("routeFallbackEnabled", True))
	fallback_route = normalize_page_url(state.get("routeFallbackPath") or "/cfm/target-no-route")
	if target in pages:
		# Only clear routeLogicalPath when it is actually set — a no-op write would re-fire the
		# breadcrumb binding for nothing.
		if cfm.config.should_write_route_logical(state.get("routeLogicalPath"), ""):
			cfm.config.set_state_fields(component.session, {"routeLogicalPath": ""})
		system.perspective.navigate(page=target)
		outcome = "direct"
	elif fallback_enabled and fallback_route in pages:
		# Only write when the logical target actually changes.
		if cfm.config.should_write_route_logical(state.get("routeLogicalPath"), target):
			cfm.config.set_state_fields(component.session, {"routeLogicalPath": target})
		system.perspective.navigate(page=fallback_route, params={"requestedPath": target})
		outcome = "fallback"
	else:
		cfm.log.log_once("nav", "warn", "Navigation target has no route and no fallback: " + str(target))
		if _perf:
			cfm.log.perf("nav.navigate", cfm.log.now_nanos() - _t0,
				"pages=%d unrouted" % len(pages), force=perf_prop)
		return
	if _perf:
		cfm.log.perf("nav.navigate", cfm.log.now_nanos() - _t0,
			"pages=%d %s" % (len(pages), outcome), force=perf_prop)
	if close_dock and not pinned:
		system.perspective.closeDock(dock_id)
		# Only change open/closed state; never touch dockPinned / dockContentPush on navigation.
		cfm.config.set_state_fields(component.session, {
			"dockOpen": False,
		})


def on_menu_link_click(component):
	target = str(component.view.params.target or "").strip()
	if not cfm.config.is_true(component.view.params.isLink) or not target:
		return
	navigate_with_fallback(component, target, close_dock=True)


def on_logo_click(component):
	target = ""
	try:
		state = component.session.custom.configFileMenu
		if state is not None:
			target = str(state.get("brandLogoLink") or "")
	except:
		target = ""
	if not target:
		target = "/"
	navigate_with_fallback(component, target, close_dock=False)
