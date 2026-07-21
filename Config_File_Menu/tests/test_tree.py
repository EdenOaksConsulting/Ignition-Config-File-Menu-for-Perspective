"""Tests for cfm.tree pure helpers (section membership + class strings)."""


def test_page_belongs_to_section(cfm):
    b = cfm.tree.page_belongs_to_section
    assert b("/plant/area-1", "/plant") is True        # descendant
    assert b("/plant", "/plant") is True               # exact match
    assert b("/plant/area-1", "/plant/area-1") is True
    assert b("/plant2", "/plant") is False             # not a real child (prefix without /)
    assert b("/other", "/plant") is False
    assert b("/plant", "") is False                    # no target
    assert b("", "/plant") is False                    # no page


def test_section_classes_selected_and_open(cfm):
    # Exact match -> selected + open
    classes = cfm.tree.section_classes("/plant", "/plant", "Plant").split()
    assert "cfm-menu__link--selected" in classes
    assert "cfm-menu__section--open" in classes

    # Descendant page -> open but not selected
    classes = cfm.tree.section_classes("/plant/area-1", "/plant", "Plant").split()
    assert "cfm-menu__section--open" in classes
    assert "cfm-menu__link--selected" not in classes

    # Unrelated page -> neither
    assert cfm.tree.section_classes("/other", "/plant", "Plant") == ""


def test_section_classes_targetless_open_by_label(cfm):
    # No target: opens when the first path segment matches the slugified label.
    classes = cfm.tree.section_classes("/plant-room/x", "", "Plant Room").split()
    assert "cfm-menu__section--open" in classes
    assert cfm.tree.section_classes("/elsewhere/x", "", "Plant Room") == ""


def test_section_header_classes(cfm):
    base = cfm.tree.section_header_classes("/x", "/y", False).split()
    assert base == ["cfm-menu__link", "cfm-menu__section-header"]

    with_children = cfm.tree.section_header_classes("/x", "/y", True).split()
    assert "cfm-menu__link--arrow-left" in with_children

    selected = cfm.tree.section_header_classes("/x", "/x", False).split()
    assert "cfm-menu__link--selected" in selected
