"""Tree expand/collapse and section header navigation."""

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
		cfm.nav.navigate_with_fallback(component, target, close_dock=True)


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
		if not cfm.config.is_true(link_view.params.showArrow):
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
		cfm.nav.navigate_with_fallback(component, target, close_dock=True)


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
		show_arrow = cfm.config.is_true(link_view.params.showArrow)
		is_link = cfm.config.is_true(link_view.params.isLink)
	except:
		target = ""
		show_arrow = False
		is_link = False
	if show_arrow:
		if target:
			cfm.nav.navigate_with_fallback(component, target, close_dock=True)
		return
	if is_link and target:
		cfm.nav.navigate_with_fallback(component, target, close_dock=True)


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
	component.view.custom.isOpen = cfm.config.is_true(expanded)


def page_belongs_to_section(page_path, section_target):
	page = cfm.config.normalize_path(page_path)
	target = cfm.config.normalize_path(section_target)
	if not target or not page:
		return False
	if page == target:
		return True
	return page.startswith(target + "/")


def section_classes(page_path, section_target, section_label):
	page = cfm.config.normalize_path(page_path)
	target = cfm.config.normalize_path(section_target)
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
	page = cfm.config.normalize_path(page_path)
	target = cfm.config.normalize_path(section_target)
	classes = ["cfm-menu__link", "cfm-menu__section-header"]
	if target and page == target:
		classes.append("cfm-menu__link--selected")
	if cfm.config.is_true(has_children):
		classes.append("cfm-menu__link--arrow-left")
	return " ".join(classes)


def sync_section_tree_page(component, page_path):
	try:
		previous_page = str(component.view.custom.page or "")
	except:
		previous_page = ""
	page_changed = cfm.config.normalize_path(page_path) != cfm.config.normalize_path(previous_page)

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
