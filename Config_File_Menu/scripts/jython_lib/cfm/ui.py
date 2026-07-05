"""Perspective component tree helpers for Settings generator views."""


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
