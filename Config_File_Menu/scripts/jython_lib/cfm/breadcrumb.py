"""Top-bar breadcrumb FlexRepeater transform."""


def _add_lookup(items, trail, lookup):
	for item in items or []:
		if not cfm.config.is_mapping(item):
			continue
		label = cfm.config.get_prop(item, "label", "")
		if not label:
			continue
		current = trail + [cfm.config.slug(label)]
		target = cfm.config.get_prop(item, "target", "")
		if target:
			lookup[tuple(current)] = target
		children = cfm.config.get_children(item)
		_add_lookup(children, current, lookup)


def _menu_target_for(segments, lookup):
	for start in range(len(segments)):
		candidate = tuple(segments[start:])
		if candidate in lookup:
			return lookup[candidate]
	return ""


def _add_label_lookup(items, trail, lookup):
	for item in items or []:
		if not cfm.config.is_mapping(item):
			continue
		label = cfm.config.get_prop(item, "label", "")
		if not label:
			continue
		current = trail + [cfm.config.slug(label)]
		lookup[tuple(current)] = str(label)
		children = cfm.config.get_children(item)
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
		if not cfm.config.is_mapping(item):
			continue
		label = str(cfm.config.get_prop(item, "label", "")).strip().lower()
		target = str(cfm.config.get_prop(item, "target", "") or "").strip()
		if label == "home" and target and (target in pages or shell_fallback):
			return target
	for item in menu_items or []:
		if not cfm.config.is_mapping(item):
			continue
		target = str(cfm.config.get_prop(item, "target", "") or "").strip()
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
		session = page.session
		state = cfm.config.get_state(session)
		# Perf gate (opt-in): resolve perfLogging from the state we already read, so nothing
		# is timed/formatted when perf logging is off. This is the prime target — the build
		# re-parses config and calls getProjectInfo() on every navigation.
		perf_prop = cfm.config.is_true(state.get("perfLogging", False))
		_perf = cfm.log.perf_enabled(perf_prop)
		_t0 = cfm.log.now_nanos() if _perf else 0
		path = cfm.config.resolve_effective_page_path_from_value(value, page)
		viewport_width = cfm.config.get_prop(value, "viewportWidth", page.props.dimensions.viewport.width)
		# All menu config lives in the session object (shipped with the library).
		menu_config, menu_config_type = cfm.config.pick_menu_block(session, value)
		path_prefix = str(state.get("contentBreadcrumbPrefix", "cfm") or "cfm").strip().lower()
		# Shared caches: the registered page list (TTL'd, shared with nav) and the parsed menu
		# items (keyed by source, shared with the menu render + title resolvers). A burst of
		# breadcrumb builds on one navigation reuses both instead of re-parsing + re-fetching.
		all_pages = cfm.config.get_project_page_urls_cached()
		items = cfm.config.load_menu_items(menu_config, menu_config_type)
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
		dock_id = cfm.config.resolve_dock_id(state)
		shell_fallback = cfm.config.is_true(state.get("routeFallbackEnabled", True))
		home_target = _home_target_for(items, path_prefix, all_pages, shell_fallback)
		site_name = cfm.config.resolve_site_name(value, session)
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
		if _perf:
			cfm.log.perf("breadcrumb.build", cfm.log.now_nanos() - _t0,
				"items=%d pages=%d" % (len(items), len(all_pages)), force=perf_prop)
		return instances
	except Exception as exc:
		cfm.log.log_once("breadcrumb", "error", "Breadcrumb build failed", exc)
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
