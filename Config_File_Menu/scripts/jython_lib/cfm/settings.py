"""Settings tab helpers: YAML converter and menu routes generator."""


def convert_yaml_to_json(component):
	try:
		yaml_text = component.getSibling("YamlInput").props.text
		parsed = cfm.config.parse_yaml_lite(yaml_text, empty_root={"items": []})
		if isinstance(parsed, dict) and "menu" in parsed:
			obj = parsed["menu"]
		else:
			obj = parsed
		component.getSibling("JsonOutput").props.text = system.util.jsonEncode(obj, 2)
	except Exception as exc:
		cfm.log.log_always("settings", "warn", "YAML->JSON conversion failed", exc)
		component.getSibling("JsonOutput").props.text = "Conversion error: " + str(exc)


def set_session_block_field(session, block_key, field_key, value):
	state = cfm.config.get_state(session)
	block = cfm.config.dict_block(state, block_key)
	block[field_key] = value
	cfm.config.set_state_fields(session, {block_key: block})


def set_state_field(session, field_key, value):
	cfm.config.set_state_fields(session, {field_key: value})


def on_settings_perf_logging_change(component):
	# Settings toggle: write the perfLogging session property so operators can turn the
	# opt-in CFM.perf timing on/off from the app without gateway access.
	set_state_field(component.session, "perfLogging", cfm.config.is_true(component.props.value))


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
		return "cfm-menu__settings-tab cfm-menu__settings-tab--active"
	return "cfm-menu__settings-tab"


# Keys the Settings shell owns. Excludes contentSource/contentSourceType and the dock
# keys (dockPinned / dockContentPush / dockCloseOnOutsideClick / dockOpen).
# All config ships in the session object; these setdefaults are a safety net only.
SETTINGS_SHELL_OWNED_KEYS = (
	"contentDockId", "contentBreadcrumbPrefix",
	"layoutFont", "layoutFontSize", "layoutWidthOpen", "settingsTagMenu", "settingsMenuRoutes",
	"routeFallbackEnabled", "routeFallbackPath", "routeLogicalPath", "settingsCurrentTab",
	"showMenuLogo", "showTopBarClock", "clockRefreshSeconds", "showTopBarSmallLogo",
	"showFooterUser", "showFooterSettings", "showFooterDiagnostics",
	"perfLogging",
)


def init_settings_shell_state(component):
	state = cfm.config.get_state(component.session)
	state.setdefault("showMenuLogo", True)
	state.setdefault("contentDockId", "config-file-menu")
	state.setdefault("contentBreadcrumbPrefix", "cfm")
	state.setdefault("layoutFont", "")
	state.setdefault("layoutFontSize", "14px")
	state.setdefault("layoutWidthOpen", "220px")
	state.setdefault("settingsTagMenu", {
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
	state.setdefault("settingsMenuRoutes", {
		"menuInput": "",
		"menuType": "yaml",
		"outputMode": "dynamic",
		"shellViewPath": "Config File Menu/Resources/View Dynamic Fallback",
		"output": "",
		"viewsOutput": "",
	})
	state.setdefault("routeFallbackEnabled", True)
	state.setdefault("routeFallbackPath", "/cfm/target-no-route")
	state.setdefault("routeLogicalPath", "")
	state.setdefault("settingsCurrentTab", 0)
	state.setdefault("perfLogging", False)
	try:
		idx = int(getattr(component.view.params, "currentTabIndex", 0) or 0)
	except:
		idx = 0
	if idx < 0 or idx > 4:
		idx = 0
	component.view.custom.currentTabIndex = idx
	state["settingsCurrentTab"] = idx
	cfm.menu.ensure_show_topbar_small_logo_state(state)
	cfm.menu.ensure_footer_visibility_state(state)
	cfm.config.set_state_fields(
		component.session,
		dict((k, state[k]) for k in SETTINGS_SHELL_OWNED_KEYS if k in state),
	)


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
	state = cfm.config.get_state(session)
	tm = cfm.config.dict_block(state, "settingsTagMenu")
	tm["tagPath"] = cfm.ui.child_text(root, "TagPathInput", "")
	tm["routePrefix"] = cfm.ui.child_text(root, "RoutePrefixInput", "")
	tm["maxDepth"] = cfm.ui.child_text(root, "MaxDepthInput", "2")
	tm["includeMode"] = cfm.ui.child_value(root, "IncludeDropdown", "all")
	tm["outputFormat"] = cfm.ui.child_value(root, "OutputFormatDropdown", "yaml")
	tm["appendLeaves"] = cfm.ui.child_value(root, "AppendLeavesDropdown", "false")
	tm["folderIcon"] = cfm.ui.child_text(root, "FolderIconInput", "material/folder")
	tm["udtIcon"] = cfm.ui.child_text(root, "UdtIconInput", "material/settings")
	cfm.config.set_state_fields(session, {"settingsTagMenu": tm})


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
	# Perf gate (opt-in): this is a rare, user-triggered action, so resolving perfLogging via
	# get_state here adds no hot-path cost. Nothing is timed when perf logging is off.
	perf_prop = cfm.config.is_true(cfm.config.get_state(component.session).get("perfLogging", False))
	_perf = cfm.log.perf_enabled(perf_prop)
	_t0 = cfm.log.now_nanos() if _perf else 0
	try:
		root = cfm.ui.root_component(component)
		save_tag_menu_generator(component.session, root)
		tag_path = cfm.ui.child_text(root, "TagPathInput", "[default]")
		route_prefix = cfm.ui.child_text(root, "RoutePrefixInput", "/cfm/equipment")
		max_depth_raw = cfm.ui.child_text(root, "MaxDepthInput", "2") or "2"
		try:
			max_depth = int(float(max_depth_raw))
		except:
			max_depth = 2
		include_mode = cfm.ui.child_value(root, "IncludeDropdown", "all").lower()
		output_format = cfm.ui.child_value(root, "OutputFormatDropdown", "yaml").lower()
		folder_icon = cfm.ui.child_text(root, "FolderIconInput", "material/folder") or "material/folder"
		udt_icon = cfm.ui.child_text(root, "UdtIconInput", "material/settings") or "material/settings"
		append_leaves = cfm.config.is_true(cfm.ui.child_value(root, "AppendLeavesDropdown", "false"))
		max_depth = max(1, min(max_depth, 12))
		if not tag_path:
			raise Exception("Tag browse path is required.")
		if not route_prefix.startswith("/"):
			route_prefix = "/" + route_prefix
		output_box = cfm.ui.find_child(root, "TagMenuOutput")
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
		header = "# Generated from " + tag_path + " - review and merge into the session prop configFileMenu.contentSource\n"
		header += "# Max levels below browse path: " + str(max_depth) + "\n"
		header += "# Remove sourceTagPath keys before pasting if desired (menu ignores unknown keys).\n"
		if output_format == "json":
			output = header + system.util.jsonEncode(menu_obj, 2)
		else:
			output = header + _emit_yaml(menu_obj)
		output_box.props.text = output
		set_session_block_field(component.session, "settingsTagMenu", "output", output)
		status = cfm.ui.find_child(root, "StatusLabel")
		if status is not None:
			status.props.text = (
				"Generated " + str(len(branch_children)) + " children at max "
				+ str(max_depth) + " level(s) below browse path."
			)
		if _perf:
			cfm.log.perf("settings.tagMenu", cfm.log.now_nanos() - _t0,
				"children=%d depth=%d" % (len(branch_children), max_depth), force=perf_prop)
	except Exception as exc:
		cfm.log.log_always("settings", "warn", "Tag menu generation failed", exc)
		root = cfm.ui.root_component(component)
		out = cfm.ui.find_child(root, "TagMenuOutput")
		if out is not None:
			out.props.text = "Error: " + str(exc)
		status = cfm.ui.find_child(root, "StatusLabel")
		if status is not None:
			status.props.text = "Generation failed."


def save_menu_routes_generator(
	session,
	root,
	output_text=None,
	views_output_text=None,
	default_shell_path="Config File Menu/Resources/View Dynamic Fallback",
):
	cfg = cfm.config.get_state(session)
	mr = cfm.config.dict_block(cfg, "settingsMenuRoutes")
	mr["menuInput"] = cfm.ui.child_text_preserve(root, "MenuInput", "")
	mr["menuType"] = cfm.ui.child_value(root, "MenuTypeDropdown", "yaml")
	mr["outputMode"] = cfm.ui.child_value(root, "OutputModeDropdown", "dynamic")
	mr["shellViewPath"] = cfm.ui.child_text(root, "ShellViewInput", default_shell_path)
	if output_text is not None:
		mr["output"] = str(output_text)
	else:
		try:
			mr["output"] = cfm.ui.child_text_preserve(root, "RoutesOutput", "")
		except:
			pass
	if views_output_text is not None:
		mr["viewsOutput"] = str(views_output_text)
	else:
		try:
			mr["viewsOutput"] = cfm.ui.child_text_preserve(root, "ViewsOutput", "")
		except:
			pass
	cfm.config.set_state_fields(session, {"settingsMenuRoutes": mr})


def load_menu_routes_generator(component, default_menu_input, default_output, default_shell_path):
	try:
		cfg = component.session.custom.configFileMenu
		if cfg is None:
			return
		mr = cfg.get("settingsMenuRoutes")
		if mr is None or not hasattr(mr, "get"):
			return
		mr = dict(mr)
		root = cfm.ui.root_component(component)
		cfm.ui.set_text(root, "MenuInput", mr.get("menuInput"), default_menu_input)
		cfm.ui.set_value(root, "MenuTypeDropdown", mr.get("menuType"), "yaml")
		cfm.ui.set_value(root, "OutputModeDropdown", mr.get("outputMode"), "dynamic")
		cfm.ui.set_text(root, "ShellViewInput", mr.get("shellViewPath"), default_shell_path)
		if mr.get("output") not in (None, ""):
			cfm.ui.set_text(root, "RoutesOutput", mr.get("output"), default_output)
		if mr.get("viewsOutput") not in (None, ""):
			cfm.ui.set_text(root, "ViewsOutput", mr.get("viewsOutput"), "")
	except:
		pass


def shutdown_menu_routes_generator(component, default_shell_path):
	root = cfm.ui.root_component(component)
	save_menu_routes_generator(component.session, root, default_shell_path=default_shell_path)


def _parse_yaml_lite_menu(text):
	parsed = cfm.config.parse_yaml_lite(text, empty_root={"items": []})
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
			data = cfm.config.normalize_document(menu_text)
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
			return str(cfg.get("contentBreadcrumbPrefix") or "cfm")
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
			"requestedPath": "",
		},
		"propConfig": {
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
	# Perf gate (opt-in): rare, user-triggered action, so resolving perfLogging via get_state
	# here adds no hot-path cost. Nothing is timed when perf logging is off.
	perf_prop = cfm.config.is_true(cfm.config.get_state(component.session).get("perfLogging", False))
	_perf = cfm.log.perf_enabled(perf_prop)
	_t0 = cfm.log.now_nanos() if _perf else 0
	try:
		root = cfm.ui.root_component(component)
		save_menu_routes_generator(component.session, root, default_shell_path=default_shell_path)
		menu_text = cfm.ui.child_text_preserve(root, "MenuInput", "")
		menu_type = cfm.ui.child_value(root, "MenuTypeDropdown", "yaml")
		output_mode = str(cfm.ui.child_value(root, "OutputModeDropdown", "dynamic") or "dynamic").strip()
		shell_path = cfm.ui.child_text(root, "ShellViewInput", default_shell_path) or default_shell_path
		output_box = cfm.ui.find_child(root, "RoutesOutput")
		views_box = cfm.ui.find_child(root, "ViewsOutput")
		status = cfm.ui.find_child(root, "RoutesStatusLabel")
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
		if _perf:
			cfm.log.perf("settings.menuRoutes", cfm.log.now_nanos() - _t0,
				"routes=%d views=%d" % (len(pages), len(views_manifest)), force=perf_prop)
	except Exception as exc:
		cfm.log.log_always("settings", "warn", "Menu routes generation failed", exc)
		root = cfm.ui.root_component(component)
		out = cfm.ui.find_child(root, "RoutesOutput")
		if out is not None:
			out.props.text = "Error: " + str(exc)
		status = cfm.ui.find_child(root, "RoutesStatusLabel")
		if status is not None:
			status.props.text = "Generation failed."


def check_menu_health(items, registered_pages, fallback_enabled, fallback_path):
	# Pure, dependency-free menu-config health check. Walks the menu tree (via
	# cfm.config.get_children) and reports, for each item that carries a target:
	#   missingRoutes    - target has no registered page and no usable fallback
	#   duplicateTargets - a target used by more than one menu item
	#   roleWarnings     - labels of items that declare `roles` (a reminder that menu
	#                      roles are visibility-only; secure the destination pages)
	# Makes NO system calls (takes already-parsed items + page list), so it is unit-testable.
	pages = set(cfm.config.normalize_path(p) for p in (registered_pages or []))
	fallback = cfm.config.normalize_path(fallback_path) if fallback_path else ""
	fallback_ok = cfm.config.is_true(fallback_enabled) and bool(fallback) and fallback in pages
	result = {
		"itemCount": 0,
		"targetsChecked": 0,
		"missingRoutes": [],
		"duplicateTargets": [],
		"roleWarnings": [],
	}
	seen = {}

	def walk(node_items):
		for item in node_items or []:
			if not cfm.config.is_mapping(item):
				continue
			result["itemCount"] += 1
			target = str(cfm.config.get_prop(item, "target", "") or "").strip()
			if target:
				norm = cfm.config.normalize_path(target)
				result["targetsChecked"] += 1
				seen[norm] = seen.get(norm, 0) + 1
				if norm not in pages and not fallback_ok and norm not in result["missingRoutes"]:
					result["missingRoutes"].append(norm)
			if cfm.config.get_prop(item, "roles", None):
				label = str(cfm.config.get_prop(item, "label", "") or "").strip()
				result["roleWarnings"].append(label if label else "(unlabeled)")
			walk(cfm.config.get_children(item))

	walk(items)
	result["duplicateTargets"] = sorted([t for t in seen if seen[t] > 1])
	return result


def _format_menu_health_summary(health):
	# One-line human-readable summary; callers prefix it with [CFM health].
	missing = health.get("missingRoutes") or []
	dupes = health.get("duplicateTargets") or []
	roles = health.get("roleWarnings") or []
	parts = [
		str(health.get("itemCount", 0)) + " items",
		str(health.get("targetsChecked", 0)) + " targets",
	]
	if missing:
		parts.append(str(len(missing)) + " missing route(s): " + ", ".join(missing))
	if dupes:
		parts.append(str(len(dupes)) + " duplicate target(s): " + ", ".join(dupes))
	if roles:
		parts.append(str(len(roles)) + " item(s) use roles (visibility only; secure pages separately)")
	if not missing and not dupes:
		parts.append("OK")
	return "; ".join(parts)


def validate_menu_config(component):
	# Settings action: parse the current menu and report route/duplicate/role health into
	# the MenuHealthOutput label, plus one summary line to the CFM.health logger.
	try:
		session = component.session
		state = cfm.config.get_state(session)
		items = cfm.config.load_menu_items(
			state.get("contentSource", ""), str(state.get("contentSourceType", "yaml") or "yaml")
		)
		pages = cfm.nav.get_registered_pages()
		fallback_enabled = cfm.config.is_true(state.get("routeFallbackEnabled", True))
		fallback_path = state.get("routeFallbackPath") or "/cfm/target-no-route"
		health = check_menu_health(items, pages, fallback_enabled, fallback_path)
		summary = "[CFM health] " + _format_menu_health_summary(health)
		cfm.ui.set_text(cfm.ui.root_component(component), "MenuHealthOutput", summary)
		has_problems = bool(health["missingRoutes"] or health["duplicateTargets"])
		cfm.log.log_always("health", "warn" if has_problems else "info", summary)
	except Exception as exc:
		cfm.log.log_always("health", "warn", "Menu validation failed", exc)
		try:
			cfm.ui.set_text(
				cfm.ui.root_component(component), "MenuHealthOutput",
				"[CFM health] validation error: " + str(exc),
			)
		except:
			pass

