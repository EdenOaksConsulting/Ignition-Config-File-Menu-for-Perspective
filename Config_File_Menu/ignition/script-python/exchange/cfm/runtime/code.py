"""CFM bundled runtime for Config File Menu (auto-generated).
Deployed as exchange.cfm.runtime in the Project Script Library.
"""

# --- log.py ---
# Bounded module-level de-dup cache. The gateway interpreter is long-lived, so the
# cache is capped and cleared wholesale when it fills — it cannot grow without limit.
_LOG_ONCE_CACHE = {}
_LOG_ONCE_CACHE_CAP = 200

_LEVELS = ("error", "warn", "info", "debug")


def get_logger(name=""):
	# Stable CFM.* logger name. Every review/alert mechanism keys off this prefix.
	suffix = "." + name if name else ""
	return system.util.getLogger("CFM" + suffix)


def _should_emit(cache, key, message):
	# Pure, unit-testable de-dup core. Emit when this key has not been seen, or when
	# its stored message changed. Bounds the cache: clear it wholesale once it reaches
	# the cap so a long-lived interpreter cannot grow it without limit.
	if cache.get(key) == message:
		return False
	if len(cache) >= _LOG_ONCE_CACHE_CAP:
		cache.clear()
	cache[key] = message
	return True


def _emit(area, level, message, exc):
	lvl = str(level or "info").lower()
	if lvl not in _LEVELS:
		lvl = "info"
	text = message
	if exc is not None:
		# Do not assume a Java Throwable; str() works for Jython and Python exceptions.
		text = text + ": " + str(exc)
	logger = get_logger(area)
	if lvl == "error":
		logger.error(text)
	elif lvl == "warn":
		logger.warn(text)
	elif lvl == "debug":
		logger.debug(text)
		if exc is not None:
			try:
				import traceback
				logger.debug(traceback.format_exc())
			except:
				pass
	else:
		logger.info(text)


def log_always(area, level, message, exc=None):
	# Log every time (no de-dup). For low-frequency, user-triggered paths (Settings
	# actions), where each occurrence is worth a line.
	try:
		_emit(area, level, message, exc)
	except:
		pass


def log_once(area, level, message, exc=None):
	# Log only when this (area, message) has not been seen (or its message changed).
	# For high-frequency render / navigation / binding paths, so a repeating fault
	# produces one line rather than a flood.
	try:
		key = str(area) + "|" + str(message)
		if _should_emit(_LOG_ONCE_CACHE, key, message):
			_emit(area, level, message, exc)
	except:
		pass


# --- Performance logging (opt-in, zero-overhead when off) -------------------
#
# Timing/formatting must never run on a hot path unless perf logging is actually
# enabled, so callers GATE with ``perf_enabled(...)`` BEFORE they call ``now_nanos``
# or build the ``extra`` string:
#
#     perf_prop = is_true(state.get("perfLogging", False))
#     _perf = perf_enabled(perf_prop)
#     _t0 = now_nanos() if _perf else 0
#     ... work ...
#     if _perf:
#         perf("breadcrumb.build", now_nanos() - _t0,
#             "items=%d" % len(items), force=perf_prop)
#
# Two independent gates: the ``CFM.perf`` logger's TRACE level (Gateway -> Status ->
# Diagnostics -> Logs) and the resolved ``perfLogging`` session property (passed in as
# ``force`` so operators can toggle it from the app without gateway access). ``log.py``
# stays free of a ``config`` dependency: the caller resolves ``perfLogging`` from state
# it already read, so no extra session read happens on a hot path. The ``[CFM perf]``
# marker is stable for alert scraping (matching ``[CFM ...]`` / ``[CFM health]``).


def now_nanos():
	# Monotonic-ish nanosecond counter. Uses java.lang.System.nanoTime() under Jython
	# and falls back to the wall clock under CPython (tests). Never raises.
	try:
		from java.lang import System as _JavaSystem
		return _JavaSystem.nanoTime()
	except:
		try:
			import time
			return int(time.time() * 1000000000.0)
		except:
			return 0


def perf_enabled(perf_prop=False):
	# True when perf logging should run: either the caller-resolved perfLogging property
	# is on, or the CFM.perf logger has TRACE enabled. Wrapped so a broken logger can never
	# make a hot path throw; defaults to False (off) on any error.
	try:
		return bool(perf_prop) or bool(get_logger("perf").isTraceEnabled())
	except:
		return False


def perf(label, nanos, extra="", threshold_ms=0, force=False):
	# Emit one timing line under the CFM.perf logger. Callers must already have gated the
	# measurement with perf_enabled(); this re-checks so a stray call is still cheap/safe.
	# threshold_ms > 0 suppresses fast cases (surface only slow ones). When forced (the
	# perfLogging property is on) it logs at INFO so it is visible at default gateway
	# levels; otherwise it logs at TRACE. Never raises into a handler.
	try:
		logger = get_logger("perf")
		trace_on = logger.isTraceEnabled()
		if not (force or trace_on):
			return
		ms = nanos / 1000000.0
		if threshold_ms and ms < threshold_ms:
			return
		msg = "[CFM perf] " + str(label) + " " + ("%.1f" % ms) + "ms"
		if extra:
			msg = msg + " " + str(extra)
		if force:
			logger.info(msg)
		else:
			logger.trace(msg)
	except:
		pass

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


def get_children(item):
	# A menu item's children, accepting either the `children:` or legacy `items:` key.
	return get_prop(item, "children", get_prop(item, "items", []))


def dict_block(container, key):
	# A mutable dict copy of a nested block container[key], or {} if absent/not a mapping.
	# Used to read-modify-write a nested session object (e.g. the Settings generator scratch).
	blk = container.get(key)
	if blk is None or not hasattr(blk, "get"):
		return {}
	return dict(blk)


# Bounded parse cache. The menu render, breadcrumbs, and page-title resolvers all parse the
# same session menu source, and they re-run on every navigation, so the parse is cached by
# (type, source). The gateway interpreter is long-lived; the cache is capped and cleared
# wholesale when it fills so it cannot grow without limit if operators paste many configs.
_MENU_ITEMS_CACHE = {}
_MENU_ITEMS_CACHE_CAP = 4


def _load_menu_items_uncached(menu_config, menu_config_type):
	cfg = load_config(menu_config, menu_config_type)
	menu = get_prop(cfg, "menu", cfg)
	return get_prop(menu, "items", menu if is_sequence(menu) else [])


def load_menu_items(menu_config, menu_config_type):
	# Parse a menu config and return its top-level item list, unwrapping the optional
	# `menu:` root and tolerating a bare list. Shared by the menu render, breadcrumbs,
	# and page-title resolvers.
	#
	# For a string source (the hot-path shape — session contentSource is a string) the result
	# is cached by (type, source): a changed source/type is a new key, so the cache self-
	# invalidates and never serves a stale parse. The returned list is SHARED and must be
	# treated READ-ONLY — callers iterate it (menu render / lookups) and never mutate it in
	# place. A non-string source (an already-parsed document) is unhashable and off the hot
	# path, so it bypasses the cache.
	if isinstance(menu_config, basestring):
		cfg_type = str(menu_config_type or "yaml").lower().strip()
		key = (cfg_type, menu_config)
		cached = _MENU_ITEMS_CACHE.get(key)
		if cached is not None:
			return cached
		items = _load_menu_items_uncached(menu_config, menu_config_type)
		if len(_MENU_ITEMS_CACHE) >= _MENU_ITEMS_CACHE_CAP:
			_MENU_ITEMS_CACHE.clear()
		_MENU_ITEMS_CACHE[key] = items
		return items
	return _load_menu_items_uncached(menu_config, menu_config_type)


# Bounded, TTL'd cache of the registered page-url list. A single navigation triggers a burst
# of breadcrumb/nav binding evaluations that each call getProjectInfo(); caching the url list
# for a short window lets that burst share ONE gateway call. TTL-based so no session write is
# needed to invalidate; on error the last good list is served.
_PAGE_URLS_CACHE = {"urls": None, "at": 0}
_PAGE_URLS_TTL_NANOS = 2000000000  # ~2 seconds


def get_project_page_urls_cached():
	# The raw page-url list from getProjectInfo()["pageConfigs"], cached for ~2s. nav
	# normalizes these (leading slash); breadcrumb uses them as-is, which matches its previous
	# inline read (Perspective page urls already start with "/"). Refreshes when the entry is
	# missing or older than the TTL (a non-positive elapsed also forces a refresh).
	try:
		now = now_nanos()
	except:
		now = 0
	cached = _PAGE_URLS_CACHE.get("urls")
	elapsed = now - _PAGE_URLS_CACHE.get("at", 0)
	if cached is not None and 0 < elapsed < _PAGE_URLS_TTL_NANOS:
		return cached
	try:
		urls = [page["url"] for page in system.perspective.getProjectInfo()["pageConfigs"]]
	except:
		return cached if cached is not None else []
	_PAGE_URLS_CACHE["urls"] = urls
	_PAGE_URLS_CACHE["at"] = now
	return urls


def should_write_route_logical(current, new):
	# True when routeLogicalPath actually needs to change. Skipping a no-op write avoids a
	# whole-object session write that would needlessly re-fire the breadcrumb binding on
	# navigation. Compares as strings so None and "" are equivalent.
	return str(current or "") != str(new or "")


def resolve_dock_id(state):
	# The Perspective dock id the menu operates on; falls back to the shipped default.
	return str(state.get("contentDockId") or "config-file-menu")


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
	# The menu source lives in the session object (contentSource / contentSourceType),
	# shipped with the library. Read it directly so every caller (menu render, page title)
	# resolves the same config regardless of its binding struct. `data` is unused but kept
	# for a stable signature.
	state = get_state(session)
	return state.get("contentSource", ""), str(state.get("contentSourceType", "yaml") or "yaml")


def resolve_site_name(value, session, default="Default Site"):
	# Site name lives in the session object (brandSiteName), shipped with the library.
	name = str(get_state(session).get("brandSiteName", "") or "").strip()
	return name if name else (default or "Default Site")


def get_state(session):
	try:
		state = session.custom.configFileMenu
		if state is None:
			return {}
		return dict(state)
	except Exception as exc:
		# DEBUG only: this can fire often (e.g. before the session object is materialized);
		# it is a diagnostic breadcrumb, not a fault worth WARN/ERROR volume.
		log_once("config", "debug", "get_state fell back to empty", exc)
		return {}


def set_state_fields(session, fields):
	# Merge the given keys into session.custom.configFileMenu with a WHOLE-OBJECT
	# read-modify-write: read the current object, overwrite just these keys, write the
	# whole object back. This is last-writer-wins, NOT a per-key isolated write. If two
	# handlers run concurrently (e.g. onStartup handlers racing at session load), each
	# reads its own snapshot and rewrites the whole object, so the later write can revert
	# sibling keys the earlier write set (its stale snapshot didn't include them). In
	# practice handlers fire sequentially per session and each writes a distinct set of
	# keys, so the lost-update window is small — but it is real. Returns the merged dict
	# this writer produced (its own view; may be stale by the time callers use it).
	state = get_state(session)
	if fields:
		for key in fields:
			state[key] = fields[key]
	session.custom.configFileMenu = state
	return state


def resolve_effective_page_path_from_value(value, page=None):
	requested = str(get_prop(value, "requestedPath", "") or "").strip()
	if requested:
		return normalize_path(requested)
	logical = str(get_prop(value, "routeLogicalPath", "") or "").strip()
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
	# Normalized registered page urls. Backed by the shared, TTL'd page-url cache so a burst of
	# nav/breadcrumb evaluations on one navigation shares a single getProjectInfo() call.
	try:
		return [normalize_page_url(url) for url in get_project_page_urls_cached()]
	except:
		return []


def navigate_with_fallback(component, target_path, close_dock=False):
	target = normalize_page_url(target_path)
	if not target:
		return
	# Read state first so the perf gate can resolve perfLogging without an extra session
	# read, and time the whole navigation — including get_registered_pages()/getProjectInfo(),
	# which is the real cost here. Nothing is timed when perf logging is off.
	state = get_state(component.session)
	perf_prop = is_true(state.get("perfLogging", False))
	_perf = perf_enabled(perf_prop)
	_t0 = now_nanos() if _perf else 0
	pages = get_registered_pages()
	dock_id = resolve_dock_id(state)
	pinned = is_true(state.get("dockPinned", False))
	fallback_enabled = is_true(state.get("routeFallbackEnabled", True))
	fallback_route = normalize_page_url(state.get("routeFallbackPath") or "/cfm/target-no-route")
	if target in pages:
		# Only clear routeLogicalPath when it is actually set — a no-op write would re-fire the
		# breadcrumb binding for nothing.
		if should_write_route_logical(state.get("routeLogicalPath"), ""):
			set_state_fields(component.session, {"routeLogicalPath": ""})
		system.perspective.navigate(page=target)
		outcome = "direct"
	elif fallback_enabled and fallback_route in pages:
		# Only write when the logical target actually changes.
		if should_write_route_logical(state.get("routeLogicalPath"), target):
			set_state_fields(component.session, {"routeLogicalPath": target})
		system.perspective.navigate(page=fallback_route, params={"requestedPath": target})
		outcome = "fallback"
	else:
		log_once("nav", "warn", "Navigation target has no route and no fallback: " + str(target))
		if _perf:
			perf("nav.navigate", now_nanos() - _t0,
				"pages=%d unrouted" % len(pages), force=perf_prop)
		return
	if _perf:
		perf("nav.navigate", now_nanos() - _t0,
			"pages=%d %s" % (len(pages), outcome), force=perf_prop)
	if close_dock and not pinned:
		system.perspective.closeDock(dock_id)
		# Only change open/closed state; never touch dockPinned / dockContentPush on navigation.
		set_state_fields(component.session, {
			"dockOpen": False,
		})


def on_menu_link_click(component):
	target = str(component.view.params.target or "").strip()
	if not is_true(component.view.params.isLink) or not target:
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

# --- dock.py ---
def _dock_content(state):
	# Derive the Perspective "push"/"cover" content string from the boolean dockContentPush.
	return "push" if is_true(state.get("dockContentPush", True)) else "cover"


def init_topbar_state(component):
	# The Top Bar shares the session object; nothing to seed (it ships populated). Kept as a
	# stable onStartup entry point that simply re-affirms the identity keys it reads.
	state = get_state(component.session)
	set_state_fields(component.session, {
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
	pinned = is_true(state.get("dockPinned", False))
	session_open = is_true(state.get("dockOpen", False))
	if dock_content == "push" or pinned:
		return _layout_is_open(component) or session_open
	return session_open


def topbar_toggle_icon(component):
	state = get_state(component.session)
	return "material/menu_open" if _topbar_is_open(component, state) else "material/menu"


def topbar_toggle_classes(component):
	state = get_state(component.session)
	if _topbar_is_open(component, state):
		return "cfm-menu__button cfm-menu__button--close-menu"
	return "cfm-menu__button cfm-menu__button--open-menu"


def on_menu_toggle_click(component):
	state = get_state(component.session)
	dock_id = resolve_dock_id(state)
	pinned = is_true(state.get("dockPinned", False))
	dock_content = _dock_content(state)
	if pinned:
		dock_content = "push"
	session_open = is_true(state.get("dockOpen", False))
	if dock_content == "push" or pinned:
		currently_open = _layout_is_open(component) or session_open
	else:
		currently_open = session_open
	if currently_open:
		system.perspective.closeDock(dock_id)
		set_state_fields(component.session, {
			"dockOpen": False,
			"dockPinned": pinned, "dockContentPush": dock_content == "push",
		})
	else:
		system.perspective.alterDock(dock_id, {"content": dock_content})
		system.perspective.openDock(dock_id)
		set_state_fields(component.session, {
			"dockOpen": True,
			"dockPinned": pinned, "dockContentPush": dock_content == "push",
		})


def on_dock_mode_toggle(component):
	state = get_state(component.session)
	dock_id = resolve_dock_id(state)
	current = _dock_content(state)
	new_mode = "push" if current == "cover" else "cover"
	new_pinned = False if new_mode == "cover" else is_true(state.get("dockPinned", False))
	system.perspective.alterDock(dock_id, {"content": new_mode})
	system.perspective.openDock(dock_id)
	set_state_fields(component.session, {
		"dockOpen": True,
		"dockPinned": new_pinned, "dockContentPush": new_mode == "push",
	})


def on_dock_pin_toggle(component):
	state = get_state(component.session)
	dock_id = resolve_dock_id(state)
	pinned = is_true(state.get("dockPinned", False))
	dock_content = _dock_content(state)
	if pinned:
		system.perspective.alterDock(dock_id, {"content": dock_content})
		is_open = is_true(state.get("dockOpen", True))
		fields = {
			"dockOpen": is_open,
			"dockPinned": False,
			"dockContentPush": dock_content == "push",
		}
	else:
		system.perspective.alterDock(dock_id, {"content": "push"})
		system.perspective.openDock(dock_id)
		fields = {"dockOpen": True, "dockPinned": True, "dockContentPush": True}
	set_state_fields(component.session, fields)


def on_settings_pinned_change(component):
	state = get_state(component.session)
	dock_id = resolve_dock_id(state)
	pinned = is_true(component.props.value)
	if pinned:
		system.perspective.alterDock(dock_id, {"content": "push"})
		system.perspective.openDock(dock_id)
		fields = {
			"dockOpen": True,
			"dockPinned": True, "dockContentPush": True,
		}
	else:
		fields = {"dockPinned": False}
	set_state_fields(component.session, fields)


def on_settings_dock_content_change(component):
	state = get_state(component.session)
	push = is_true(component.props.value)
	mode = "push" if push else "cover"
	dock_id = resolve_dock_id(state)
	system.perspective.alterDock(dock_id, {"content": mode})
	fields = {"dockContentPush": push}
	if not push:
		fields["dockPinned"] = False
	set_state_fields(component.session, fields)


def on_settings_menu_width_change(component):
	state = get_state(component.session)
	width_text = str(component.props.text or "").strip()
	dock_id = resolve_dock_id(state)
	try:
		system.perspective.alterDock(dock_id, {"size": _parse_width(width_text)})
	except:
		pass
	set_state_fields(component.session, {"layoutWidthOpen": width_text})


def close_on_outside_click(component):
	state = get_state(component.session)
	# The dock defaults ship in the session object, so dockCloseOnOutsideClick / dockPinned /
	# dockOpen are always present here. A pinned dock never dismisses on an outside click.
	if not is_true(state.get("dockCloseOnOutsideClick", True)):
		return
	if is_true(state.get("dockPinned", False)):
		return
	if not is_true(state.get("dockOpen", True)):
		return
	dock_id = resolve_dock_id(state)
	system.perspective.closeDock(dock_id)
	# Only change open/closed state. Never write dockPinned / dockContentPush here — an
	# outside click closes the menu but must not alter the session's dock settings.
	set_state_fields(component.session, {
		"dockOpen": False,
	})


def _apply_physical_dock(session):
	# Push the physical Perspective dock (content mode, size, open/closed) to match the
	# session dock state. Reads state from the session only, so it can run from either the
	# shared dock's onStartup OR a binding transform. Idempotent: it only syncs the physical
	# dock to the current dockOpen, so it never fights a live Settings/toggle change.
	state = get_state(session)
	dock_id = resolve_dock_id(state)
	pinned = is_true(state.get("dockPinned", False))
	# Invariant: a pinned dock is always push + open. Otherwise honor dockContentPush/dockOpen.
	dock_content = "push" if pinned else _dock_content(state)
	want_open = True if pinned else is_true(state.get("dockOpen", False))
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
		state = get_state(component.session)
		if should_write_route_logical(state.get("routeLogicalPath"), requested):
			set_state_fields(component.session, {"routeLogicalPath": requested})


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
						# Deliberate FAIL-OPEN: if the role check itself errors (e.g. an
						# unexpected user-source arg on this gateway), show the menu item
						# rather than hide it. `roles` is a visibility convenience only —
						# real access control is enforced on the destination pages
						# (see the README security note), so a broken check must not lock
						# users out of navigation.
						log_once("menu", "warn", "Role check errored; showing item (fail-open) for role=" + str(role))
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
			grandchildren = get_children(child)
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
		children = get_children(item)
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

	# Perf gate (opt-in): the menu-structure transform deliberately avoids a session read
	# (see menu_items_transform), so perf here is gated on the CFM.perf TRACE logger only,
	# never forced by the perfLogging property — nothing is timed when perf logging is off.
	_perf = perf_enabled()
	_t0 = now_nanos() if _perf else 0
	try:
		items = load_menu_items(menu_text, picked_type)
		result = [to_instance(item) for item in items if is_mapping(item) and allowed(item)]
		if _perf:
			perf("menu.render", now_nanos() - _t0, "items=%d" % len(items))
		return result
	except Exception as exc:
		log_once("menu", "error", "Menu config parse failed", exc)
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
	# the user navigates. The binding passes the session menu source (see MenuContent
	# MenuItems struct: menuConfig/menuConfigType bound to configFileMenu.contentSource /
	# contentSourceType), so navigation-time session writes no longer re-trigger this
	# expensive full re-render. All config ships in the session object, so there is nothing
	# to seed here.
	#
	# A shared dock's onStartup does not reliably fire in Perspective 8.3.3, but this binding
	# always runs on menu render — so this is where the authored startup open/closed state
	# (dockOpen, including "start closed") is reliably pushed to the physical dock.
	try:
		apply_startup_dock_state(session)
	except:
		pass
	try:
		picked_cfg, picked_type = pick_menu_block(session, value)
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
	return is_true(value)


def ensure_show_topbar_small_logo_state(state):
	state.setdefault("showTopBarClock", True)
	state.setdefault("clockRefreshSeconds", 5)
	state.setdefault("showTopBarSmallLogo", True)
	return state


def _panel_classes(state, device_type):
	if device_type == "designer":
		base = "cfm-menu cfm-menu--open cfm-menu__panel"
	elif is_true(state.get("dockOpen", False)):
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
	state = get_state(session)
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
	page = normalize_path(page_path)
	target = normalize_path(target_path)
	if target and page == target:
		return "cfm-menu__link--selected"
	return ""


def resolve_logo_source(value, session, view):
	# The logo source ships in the session object (brandLogoLarge / brandLogoSmall). `value`
	# carries variant + sessionSource (bound to those keys) + defaultSource (the embedded PNG).
	variant = str(get_prop(value, "variant", "large") or "large").lower()
	default_source = str(get_prop(value, "defaultSource", "") or "")
	state = get_state(session)
	key = "brandLogoSmall" if variant == "small" else "brandLogoLarge"
	source = str(get_prop(value, "sessionSource", "") or state.get(key) or "").strip()
	return source if source else default_source


def topbar_small_logo_visible(value, session):
	# value carries viewportWidth and showTopBarSmallLogo from the Top Bar small-logo
	# struct, so read the flag straight from value (same pattern as footer_visible); a
	# missing session key resolves to None -> default visible. session is kept only for
	# a stable transform signature.
	try:
		viewport = float(get_prop(value, "viewportWidth", 0) or 0)
	except:
		viewport = 0
	if viewport <= 450:
		return False
	flag = get_prop(value, "showTopBarSmallLogo", None)
	if flag is None:
		return True
	return is_true(flag)


def _find_label(items, target_path):
	for item in items or []:
		if not is_mapping(item):
			continue
		if normalize_path(get_prop(item, "target", "") or "") == target_path:
			return str(get_prop(item, "label", "") or "")
		found = _find_label(get_children(item), target_path)
		if found:
			return found
	return ""


def _find_icon(items, target_path):
	for item in items or []:
		if not is_mapping(item):
			continue
		if normalize_path(get_prop(item, "target", "") or "") == target_path:
			return str(get_prop(item, "icon", "") or "")
		found = _find_icon(get_children(item), target_path)
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
	_perf = perf_enabled()
	_t0 = now_nanos() if _perf else 0
	try:
		path = resolve_effective_page_path_from_value(value, page)
		menu_config, menu_config_type = pick_menu_block(session, value)
		items = load_menu_items(menu_config, menu_config_type)
		label = _find_label(items, path)
		if _perf:
			perf("menu.title", now_nanos() - _t0, "path=" + str(path))
		return label if label else _fallback_title(path)
	except:
		return _fallback_title(getattr(page.props, "path", ""))


def resolve_title_icon(value, session, page):
	try:
		path = resolve_effective_page_path_from_value(value, page)
		menu_config, menu_config_type = pick_menu_block(session, value)
		items = load_menu_items(menu_config, menu_config_type)
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
			section_key = slug(section_label)
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
		children = get_children(item)
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
		children = get_children(item)
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
		session = page.session
		state = get_state(session)
		# Perf gate (opt-in): resolve perfLogging from the state we already read, so nothing
		# is timed/formatted when perf logging is off. This is the prime target — the build
		# re-parses config and calls getProjectInfo() on every navigation.
		perf_prop = is_true(state.get("perfLogging", False))
		_perf = perf_enabled(perf_prop)
		_t0 = now_nanos() if _perf else 0
		path = resolve_effective_page_path_from_value(value, page)
		viewport_width = get_prop(value, "viewportWidth", page.props.dimensions.viewport.width)
		# All menu config lives in the session object (shipped with the library).
		menu_config, menu_config_type = pick_menu_block(session, value)
		path_prefix = str(state.get("contentBreadcrumbPrefix", "cfm") or "cfm").strip().lower()
		# Shared caches: the registered page list (TTL'd, shared with nav) and the parsed menu
		# items (keyed by source, shared with the menu render + title resolvers). A burst of
		# breadcrumb builds on one navigation reuses both instead of re-parsing + re-fetching.
		all_pages = get_project_page_urls_cached()
		items = load_menu_items(menu_config, menu_config_type)
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
		dock_id = resolve_dock_id(state)
		shell_fallback = is_true(state.get("routeFallbackEnabled", True))
		home_target = _home_target_for(items, path_prefix, all_pages, shell_fallback)
		site_name = resolve_site_name(value, session)
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
			perf("breadcrumb.build", now_nanos() - _t0,
				"items=%d pages=%d" % (len(items), len(all_pages)), force=perf_prop)
		return instances
	except Exception as exc:
		log_once("breadcrumb", "error", "Breadcrumb build failed", exc)
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
		log_always("settings", "warn", "YAML->JSON conversion failed", exc)
		component.getSibling("JsonOutput").props.text = "Conversion error: " + str(exc)


def set_session_block_field(session, block_key, field_key, value):
	state = get_state(session)
	block = dict_block(state, block_key)
	block[field_key] = value
	set_state_fields(session, {block_key: block})


def set_state_field(session, field_key, value):
	set_state_fields(session, {field_key: value})


def on_settings_perf_logging_change(component):
	# Settings toggle: write the perfLogging session property so operators can turn the
	# opt-in CFM.perf timing on/off from the app without gateway access.
	set_state_field(component.session, "perfLogging", is_true(component.props.value))


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
	state = get_state(component.session)
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
	ensure_show_topbar_small_logo_state(state)
	ensure_footer_visibility_state(state)
	set_state_fields(
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
	state = get_state(session)
	tm = dict_block(state, "settingsTagMenu")
	tm["tagPath"] = child_text(root, "TagPathInput", "")
	tm["routePrefix"] = child_text(root, "RoutePrefixInput", "")
	tm["maxDepth"] = child_text(root, "MaxDepthInput", "2")
	tm["includeMode"] = child_value(root, "IncludeDropdown", "all")
	tm["outputFormat"] = child_value(root, "OutputFormatDropdown", "yaml")
	tm["appendLeaves"] = child_value(root, "AppendLeavesDropdown", "false")
	tm["folderIcon"] = child_text(root, "FolderIconInput", "material/folder")
	tm["udtIcon"] = child_text(root, "UdtIconInput", "material/settings")
	set_state_fields(session, {"settingsTagMenu": tm})


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
	perf_prop = is_true(get_state(component.session).get("perfLogging", False))
	_perf = perf_enabled(perf_prop)
	_t0 = now_nanos() if _perf else 0
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
		header = "# Generated from " + tag_path + " - review and merge into the session prop configFileMenu.contentSource\n"
		header += "# Max levels below browse path: " + str(max_depth) + "\n"
		header += "# Remove sourceTagPath keys before pasting if desired (menu ignores unknown keys).\n"
		if output_format == "json":
			output = header + system.util.jsonEncode(menu_obj, 2)
		else:
			output = header + _emit_yaml(menu_obj)
		output_box.props.text = output
		set_session_block_field(component.session, "settingsTagMenu", "output", output)
		status = find_child(root, "StatusLabel")
		if status is not None:
			status.props.text = (
				"Generated " + str(len(branch_children)) + " children at max "
				+ str(max_depth) + " level(s) below browse path."
			)
		if _perf:
			perf("settings.tagMenu", now_nanos() - _t0,
				"children=%d depth=%d" % (len(branch_children), max_depth), force=perf_prop)
	except Exception as exc:
		log_always("settings", "warn", "Tag menu generation failed", exc)
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
	cfg = get_state(session)
	mr = dict_block(cfg, "settingsMenuRoutes")
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
	set_state_fields(session, {"settingsMenuRoutes": mr})


def load_menu_routes_generator(component, default_menu_input, default_output, default_shell_path):
	try:
		cfg = component.session.custom.configFileMenu
		if cfg is None:
			return
		mr = cfg.get("settingsMenuRoutes")
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
	perf_prop = is_true(get_state(component.session).get("perfLogging", False))
	_perf = perf_enabled(perf_prop)
	_t0 = now_nanos() if _perf else 0
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
		if _perf:
			perf("settings.menuRoutes", now_nanos() - _t0,
				"routes=%d views=%d" % (len(pages), len(views_manifest)), force=perf_prop)
	except Exception as exc:
		log_always("settings", "warn", "Menu routes generation failed", exc)
		root = root_component(component)
		out = find_child(root, "RoutesOutput")
		if out is not None:
			out.props.text = "Error: " + str(exc)
		status = find_child(root, "RoutesStatusLabel")
		if status is not None:
			status.props.text = "Generation failed."


def check_menu_health(items, registered_pages, fallback_enabled, fallback_path):
	# Pure, dependency-free menu-config health check. Walks the menu tree (via
	# get_children) and reports, for each item that carries a target:
	#   missingRoutes    - target has no registered page and no usable fallback
	#   duplicateTargets - a target used by more than one menu item
	#   roleWarnings     - labels of items that declare `roles` (a reminder that menu
	#                      roles are visibility-only; secure the destination pages)
	# Makes NO system calls (takes already-parsed items + page list), so it is unit-testable.
	pages = set(normalize_path(p) for p in (registered_pages or []))
	fallback = normalize_path(fallback_path) if fallback_path else ""
	fallback_ok = is_true(fallback_enabled) and bool(fallback) and fallback in pages
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
			if not is_mapping(item):
				continue
			result["itemCount"] += 1
			target = str(get_prop(item, "target", "") or "").strip()
			if target:
				norm = normalize_path(target)
				result["targetsChecked"] += 1
				seen[norm] = seen.get(norm, 0) + 1
				if norm not in pages and not fallback_ok and norm not in result["missingRoutes"]:
					result["missingRoutes"].append(norm)
			if get_prop(item, "roles", None):
				label = str(get_prop(item, "label", "") or "").strip()
				result["roleWarnings"].append(label if label else "(unlabeled)")
			walk(get_children(item))

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
		state = get_state(session)
		items = load_menu_items(
			state.get("contentSource", ""), str(state.get("contentSourceType", "yaml") or "yaml")
		)
		pages = get_registered_pages()
		fallback_enabled = is_true(state.get("routeFallbackEnabled", True))
		fallback_path = state.get("routeFallbackPath") or "/cfm/target-no-route"
		health = check_menu_health(items, pages, fallback_enabled, fallback_path)
		summary = "[CFM health] " + _format_menu_health_summary(health)
		set_text(root_component(component), "MenuHealthOutput", summary)
		has_problems = bool(health["missingRoutes"] or health["duplicateTargets"])
		log_always("health", "warn" if has_problems else "info", summary)
	except Exception as exc:
		log_always("health", "warn", "Menu validation failed", exc)
		try:
			set_text(
				root_component(component), "MenuHealthOutput",
				"[CFM health] validation error: " + str(exc),
			)
		except:
			pass
