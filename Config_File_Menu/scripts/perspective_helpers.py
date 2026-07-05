"""Shared Perspective component-tree helpers for embedded Jython scripts."""

from __future__ import annotations

from jython_thin import (
	SHELL_VIEW_PATH,
	RUNTIME_MODULE,
	build_routes_load_script,
	jython_tab,
	thin_convert_yaml,
	thin_footer_visible,
	thin_generate_tag_menu,
	thin_topbar_small_logo_visible,
	thin_generate_routes,
	thin_logo_click,
	thin_menu_link_body_click,
	thin_menu_link_click,
	thin_routes_shutdown,
	thin_section_arrow_click,
	thin_section_header_body_click,
	thin_section_toggle_message,
	thin_section_tree_page_sync,
	thin_section_tree_startup,
	thin_tree_item_clicked,
)

EFFECTIVE_PAGE_PATH_EXPR = (
	"if(len(trim(coalesce(toString({session.custom.configFileMenu.logicalPagePath}),'')))>0,"
	"toString({session.custom.configFileMenu.logicalPagePath}),"
	"toString({page.props.path}))"
)

PATH_LABEL_EXPR = (
	"if(len(trim(coalesce(toString({view.params.requestedPath}),'')))>0,"
	"toString({view.params.requestedPath}),"
	"if(len(trim(coalesce(toString({session.custom.configFileMenu.logicalPagePath}),'')))>0,"
	"toString({session.custom.configFileMenu.logicalPagePath}),"
	"toString({page.props.path})))"
)


def jython_get_state() -> str:
	return jython_tab(f"state = {RUNTIME_MODULE}.get_state(self.session)")


def jython_is_true() -> str:
	return jython_tab(f"return {RUNTIME_MODULE}.is_true(value)")


def jython_navigate_menu_target(*, include_dock_close: bool = True, use_logo_target: bool = False) -> str:
	if use_logo_target:
		return thin_logo_click()
	return thin_menu_link_click()


def jython_tree_item_clicked_script() -> str:
	return thin_tree_item_clicked()


def jython_menu_link_body_click_script() -> str:
	return thin_menu_link_body_click()


def jython_section_arrow_click_script() -> str:
	return thin_section_arrow_click()


def jython_section_header_body_click_script() -> str:
	return thin_section_header_body_click()


def jython_section_toggle_message_script() -> str:
	return thin_section_toggle_message()


def jython_section_tree_startup_script() -> str:
	return thin_section_tree_startup()


def jython_section_tree_page_sync_script() -> str:
	return thin_section_tree_page_sync()


def jython_footer_visibility_script(key: str, *, default: bool = True) -> str:
	return thin_footer_visible(key, default=default)


def jython_topbar_small_logo_visible_script() -> str:
	return thin_topbar_small_logo_visible()


def jython_session_block_save(state_key: str, field_key: str, value_expr: str) -> str:
	return jython_tab(
		f"{RUNTIME_MODULE}.set_session_block_field(self.session, '{state_key}', '{field_key}', {value_expr})"
	)


def jython_tag_menu_generate_script() -> str:
	return thin_generate_tag_menu()


def jython_save_menu_routes_generator(shell_view_path: str) -> str:
	return jython_tab(
		f"root = {RUNTIME_MODULE}.root_component(self)\n"
		f"{RUNTIME_MODULE}.save_menu_routes_generator(self.session, root, default_shell_path='{shell_view_path}')"
	)


def jython_menu_routes_shutdown_script(shell_view_path: str) -> str:
	return thin_routes_shutdown(shell_view_path)


def jython_menu_routes_load_script(
	menu_input_default: str,
	output_default: str,
	shell_view_path: str,
) -> str:
	return build_routes_load_script(menu_input_default, output_default, shell_view_path)


def jython_converter_script() -> str:
	return thin_convert_yaml()


def jython_routes_generate_script(shell_view_path: str, *, root_helper: str = "", save_helper: str = "") -> str:
	del root_helper, save_helper
	return thin_generate_routes(shell_view_path)
