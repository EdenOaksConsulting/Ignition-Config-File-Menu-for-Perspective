"""Thin Perspective script/transform call sites into the Project Script Library.

Ignition Project Library scripts must be called by full path (exchange.cfm.runtime.fn).
Do not use `import` for project-library scripts.
"""

from __future__ import annotations

RUNTIME_MODULE = "exchange.cfm.runtime"
SHELL_VIEW_PATH = "Config File Menu/Resources/View Dynamic Fallback"


def jython_tab(script: str) -> str:
	lines = script.strip().splitlines()
	if not lines:
		return "\n"
	return "\n".join(("\t" + line if line else "") for line in lines) + "\n"


def rt(name: str) -> str:
	return f"{RUNTIME_MODULE}.{name}"


def thin_menu_link_click() -> str:
	return jython_tab(f"{rt('on_menu_link_click')}(self)")


def thin_menu_link_body_click() -> str:
	return jython_tab(f"{rt('on_menu_link_body_click')}(self)")


def thin_section_header_body_click() -> str:
	return jython_tab(f"{rt('on_section_header_body_click')}(self)")


def thin_section_arrow_click() -> str:
	return jython_tab(f"{rt('on_section_arrow_click')}(self)")


def thin_section_toggle_message() -> str:
	return jython_tab(f"{rt('on_section_toggle_message')}(self, payload)")


def thin_logo_click() -> str:
	return jython_tab(f"{rt('on_logo_click')}(self)")


def thin_tree_item_clicked() -> str:
	return jython_tab(f"{rt('on_tree_item_clicked')}(self, event)")


def thin_section_tree_startup() -> str:
	return jython_tab(f"{rt('init_section_tree_state')}(self)")


def thin_section_tree_page_sync() -> str:
	return jython_tab(f"return {rt('sync_section_tree_page')}(self, value)")


def thin_menu_items_transform() -> str:
	return jython_tab(f"return {rt('menu_items_transform')}(value, self.session, self.view)")


def thin_breadcrumb_instances() -> str:
	return jython_tab(f"return {rt('build_instances')}(value, self.page)")


def thin_footer_visible(flag_key: str, *, default: bool = True) -> str:
	default_literal = "True" if default else "False"
	return jython_tab(
		f"return {rt('footer_visible')}(value, self.session, '{flag_key}', {default_literal})"
	)


def thin_topbar_small_logo_visible() -> str:
	return jython_tab(f"return {rt('topbar_small_logo_visible')}(value, self.session)")


def thin_resolve_title() -> str:
	return jython_tab(f"return {rt('resolve_title')}(value, self.session, self.page)")


def thin_resolve_title_icon() -> str:
	return jython_tab(f"return {rt('resolve_title_icon')}(value, self.session, self.page)")


def thin_topbar_startup() -> str:
	return jython_tab(f"{rt('init_topbar_state')}(self)")


def thin_menu_toggle_click() -> str:
	return jython_tab(f"{rt('on_menu_toggle_click')}(self)")


def thin_shell_startup() -> str:
	return jython_tab(f"{rt('sync_shell_session')}(self)")


def thin_close_outside_click() -> str:
	return jython_tab(f"{rt('close_on_outside_click')}(self)")


def thin_topbar_toggle_icon() -> str:
	return jython_tab(f"return {rt('topbar_toggle_icon')}(self)")


def thin_topbar_toggle_classes() -> str:
	return jython_tab(f"return {rt('topbar_toggle_classes')}(self)")


def thin_dock_mode_toggle() -> str:
	return jython_tab(f"{rt('on_dock_mode_toggle')}(self)")


def thin_dock_pin_toggle() -> str:
	return jython_tab(f"{rt('on_dock_pin_toggle')}(self)")


def thin_settings_pinned_change() -> str:
	return jython_tab(f"{rt('on_settings_pinned_change')}(self)")


def thin_settings_dock_content_change() -> str:
	return jython_tab(f"{rt('on_settings_dock_content_change')}(self)")


def thin_settings_menu_width_change() -> str:
	return jython_tab(f"{rt('on_settings_menu_width_change')}(self)")


def thin_settings_shell_startup() -> str:
	return jython_tab(f"{rt('init_settings_shell_state')}(self)")


def thin_menu_content_startup() -> str:
	return jython_tab(f"{rt('init_menu_content_state')}(self)")


def thin_settings_general_startup() -> str:
	return jython_tab(f"{rt('init_settings_general_state')}(self)")


def thin_convert_yaml() -> str:
	return jython_tab(f"{rt('convert_yaml_to_json')}(self)")


def thin_generate_tag_menu() -> str:
	return jython_tab(f"{rt('generate_tag_menu')}(self)")


def thin_generate_routes(shell_view_path: str = SHELL_VIEW_PATH) -> str:
	return jython_tab(f"{rt('generate_output')}(self, '{shell_view_path}')")


def thin_routes_shutdown(shell_view_path: str = SHELL_VIEW_PATH) -> str:
	return jython_tab(f"{rt('shutdown_menu_routes_generator')}(self, '{shell_view_path}')")


def build_routes_load_script(
	menu_input_default: str,
	output_default: str,
	shell_view_path: str = SHELL_VIEW_PATH,
) -> str:
	import json

	menu_json = json.dumps(menu_input_default)
	output_json = json.dumps(output_default)
	return jython_tab(
		f"{rt('load_menu_routes_generator')}(self, {menu_json}, {output_json}, '{shell_view_path}')"
	)
