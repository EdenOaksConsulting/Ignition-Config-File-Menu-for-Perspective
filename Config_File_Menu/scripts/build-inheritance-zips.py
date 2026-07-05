#!/usr/bin/env python3
"""Build library + site + sample import zips for Ignition project inheritance."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path

from build_paths import (
    LIBRARY_ZIP,
    PROJECT_ROOT,
    SAMPLE_ZIP,
    SITE_ZIP,
    STAGING_ROOT,
)
from menu_samples import library_menu_stub

LIBRARY_INCLUDE_ROOTS = (
    "project.json",
    "com.inductiveautomation.perspective",
    "ignition",
)
# Child packages are thin: page-config, editable menu/shell views, and logo PNGs.
CHILD_INCLUDE_ROOTS = (
    "project.json",
    "com.inductiveautomation.perspective",
)

CHILD_RELATIVE_PATHS = (
    "project.json",
    "com.inductiveautomation.perspective/views/Config File Menu/MenuContent",
    "com.inductiveautomation.perspective/views/Config File Menu/Resources/Menu/Menu Top Bar",
    "com.inductiveautomation.perspective/views/Config File Menu/Resources/View Dynamic Fallback",
)

LOGO_UPLOAD_NAMES = ("cfm-logo-large.png", "cfm-logo-small.png")
LOGOS_DIR = PROJECT_ROOT / "config" / "cfm-logos"


def load_build_module():
    script = PROJECT_ROOT / "scripts" / "build-hmi-menu-sample.py"
    spec = importlib.util.spec_from_file_location("build_hmi_menu_sample", script)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Unable to load build module: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_json_files(root: Path) -> None:
    errors: list[str] = []
    for path in sorted(root.rglob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle)
        except Exception as exc:  # noqa: BLE001 - report all parse failures
            errors.append(f"{path.relative_to(root)}: {exc}")
    if errors:
        raise SystemExit("Invalid JSON in project:\n" + "\n".join(errors))


def iter_zip_files(
    root: Path,
    *,
    include_logo_upload: bool,
    include_roots: tuple[str, ...],
) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for name in include_roots:
        path = root / name
        if not path.exists():
            raise SystemExit(f"Missing required import path: {path}")
        if path.is_file():
            files.append((path, name.replace("\\", "/")))
            continue
        for file_path in sorted(path.rglob("*")):
            if file_path.is_file():
                arcname = file_path.relative_to(root).as_posix()
                files.append((file_path, arcname))
    if include_logo_upload:
        for name in LOGO_UPLOAD_NAMES:
            file_path = LOGOS_DIR / name
            if not file_path.is_file():
                raise SystemExit(f"Missing logo PNG for zip: {file_path}")
            files.append((file_path, f"logo-upload/cfm/{name}"))
    return files


def write_zip(
    root: Path,
    output: Path,
    *,
    include_logo_upload: bool,
    include_roots: tuple[str, ...],
) -> None:
    validate_json_files(root)
    files = iter_zip_files(
        root,
        include_logo_upload=include_logo_upload,
        include_roots=include_roots,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path, arcname in files:
            archive.write(file_path, arcname)
    with zipfile.ZipFile(output, "r") as archive:
        names = archive.namelist()
        dir_entries = [name for name in names if name.endswith("/")]
        if dir_entries:
            raise SystemExit(f"Zip contains directory entries: {dir_entries}")
        if "project.json" not in names:
            raise SystemExit(f"Zip is missing project.json: {output.name}")
        perspective_files = [name for name in names if name.startswith("com.inductiveautomation.perspective/")]
        if not perspective_files:
            raise SystemExit(f"Zip is missing Perspective resources: {output.name}")
        script_files = [name for name in names if name.startswith("ignition/script-python/exchange/cfm/runtime/")]
        if include_logo_upload and output == LIBRARY_ZIP and not script_files:
            raise SystemExit(f"Zip is missing exchange.cfm.runtime script library: {output.name}")
    print(f"Wrote {output}")
    print(f"  files: {len(files)}")
    print(f"  perspective resources: {len(perspective_files)}")


def new_staging_dir() -> Path:
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)
    staging = STAGING_ROOT / uuid.uuid4().hex[:10]
    staging.mkdir(parents=True, exist_ok=False)
    return staging


def copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "build"),
        dirs_exist_ok=True,
    )


def stage_library(staging: Path) -> Path:
    dest = staging / "library"
    copy_tree(PROJECT_ROOT, dest)
    return dest


def resolve_logo_paths() -> tuple[Path, Path]:
    paths: list[Path] = []
    for name in LOGO_UPLOAD_NAMES:
        src = LOGOS_DIR / name
        if not src.is_file():
            raise SystemExit(f"Missing logo PNG: {src}")
        paths.append(src)
    return paths[0], paths[1]


def stage_child(
    build_mod,
    staging: Path,
    *,
    dest_name: str,
    project_json: dict,
    menu_yaml: str,
    page_config: dict,
) -> Path:
    dest = staging / dest_name
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)

    (dest / "project.json").write_text(
        json.dumps(project_json, indent=2) + "\n",
        encoding="utf-8",
    )

    page_config_dir = dest / "com.inductiveautomation.perspective" / "page-config"
    page_config_dir.mkdir(parents=True, exist_ok=True)
    (page_config_dir / "config.json").write_text(
        json.dumps(page_config, indent=2) + "\n",
        encoding="utf-8",
    )
    (page_config_dir / "resource.json").write_text(
        json.dumps(build_mod.page_config_resource_json(), indent=2) + "\n",
        encoding="utf-8",
    )

    for relative in CHILD_RELATIVE_PATHS[1:]:
        src = PROJECT_ROOT / relative
        target = dest / relative
        if not src.exists():
            raise SystemExit(f"Missing child resource: {src}")
        if src.is_dir():
            copy_tree(src, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)

    menu_content = (
        dest
        / "com.inductiveautomation.perspective"
        / "views"
        / "Config File Menu"
        / "MenuContent"
        / "view.json"
    )
    build_mod.patch_view_menu_config(menu_content, menu_yaml)
    logo_large, logo_small = resolve_logo_paths()
    build_mod.patch_logo_sources(menu_content, logo_large=logo_large, logo_small=logo_small)
    build_mod.patch_top_bar_small_logo(
        dest
        / "com.inductiveautomation.perspective"
        / "views"
        / "Config File Menu"
        / "Resources"
        / "Menu"
        / "Menu Top Bar"
        / "view.json"
    )
    build_mod.patch_page_config_menu_site_name(
        page_config_dir / "config.json",
        menu_content,
    )
    return dest


def stage_site(build_mod, staging: Path) -> Path:
    return stage_child(
        build_mod,
        staging,
        dest_name="site",
        project_json=build_mod.site_project_json(),
        menu_yaml=library_menu_stub(),
        page_config=build_mod.build_library_page_config(),
    )


def stage_sample(build_mod, staging: Path) -> Path:
    menu_yaml = build_mod.sample_menu_yaml()
    items = build_mod.parse_yaml_lite_items(menu_yaml)
    routes = build_mod.walk_menu_items(items)
    return stage_child(
        build_mod,
        staging,
        dest_name="sample",
        project_json=build_mod.sample_project_json(),
        menu_yaml=menu_yaml,
        page_config=build_mod.build_sample_page_config(routes),
    )


def main() -> None:
    build_script = PROJECT_ROOT / "scripts" / "build-hmi-menu-sample.py"
    settings_script = PROJECT_ROOT / "scripts" / "build-settings-generator-tabs.py"
    verify_script = PROJECT_ROOT / "scripts" / "verify-theme-css.py"
    subprocess.run([sys.executable, str(build_script)], check=True)
    subprocess.run([sys.executable, str(verify_script)], check=True)
    subprocess.run([sys.executable, str(settings_script)], check=True)
    build_mod = load_build_module()

    staging = new_staging_dir()
    library_root = stage_library(staging)
    site_root = stage_site(build_mod, staging)
    sample_root = stage_sample(build_mod, staging)

    write_zip(
        library_root,
        LIBRARY_ZIP,
        include_logo_upload=True,
        include_roots=LIBRARY_INCLUDE_ROOTS,
    )
    write_zip(
        site_root,
        SITE_ZIP,
        include_logo_upload=True,
        include_roots=CHILD_INCLUDE_ROOTS,
    )
    write_zip(
        sample_root,
        SAMPLE_ZIP,
        include_logo_upload=True,
        include_roots=CHILD_INCLUDE_ROOTS,
    )
    verify_library_zip(LIBRARY_ZIP)
    verify_site_zip(SITE_ZIP)
    verify_sample_zip(SAMPLE_ZIP)
    shutil.rmtree(STAGING_ROOT, ignore_errors=True)
    print("Import order: library first, then site or sample child.")


def verify_library_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        required_pages = (
            "/cfm/settings",
            "/cfm/diagnostics",
        )
        page_config = json.loads(
            archive.read("com.inductiveautomation.perspective/page-config/config.json")
        )
        pages = page_config.get("pages") or {}
        missing_routes = [route for route in required_pages if route not in pages]
        if missing_routes:
            raise SystemExit(f"Library zip missing required pages: {missing_routes}")
        required_views = (
            "com.inductiveautomation.perspective/views/Config File Menu/Resources/Menu/Menu Settings/view.json",
            "com.inductiveautomation.perspective/views/Config File Menu/Resources/Diagnostics/Diagnostics Dashboard/view.json",
        )
        missing_views = [view for view in required_views if view not in names]
        if missing_views:
            raise SystemExit(f"Library zip missing required views: {missing_views}")
        script_modules = (
            "ignition/script-python/exchange/cfm/runtime/code.py",
        )
        missing_scripts = [path for path in script_modules if path not in names]
        if missing_scripts:
            raise SystemExit(f"Library zip missing Config_File_Menu script modules: {missing_scripts}")
        stylesheet_files = (
            "com.inductiveautomation.perspective/stylesheet/stylesheet.css",
            "com.inductiveautomation.perspective/stylesheet/resource.json",
        )
        missing_stylesheet = [path for path in stylesheet_files if path not in names]
        if missing_stylesheet:
            raise SystemExit(f"Library zip missing Advanced Stylesheet: {missing_stylesheet}")
        theme_files = [
            name for name in names if name.startswith("com.inductiveautomation.perspective/themes/")
        ]
        if theme_files:
            raise SystemExit(f"Library zip must not bundle Perspective themes: {theme_files}")
        page_count = len(pages)
    print(f"Verified {path.name}: {page_count} library pages, Settings + Diagnostics views present")


def _verify_child_zip(path: Path, *, label: str, max_pages: int | None = None) -> None:
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        inherited_from_library = [
            name
            for name in names
            if name.startswith("ignition/script-python/")
        ]
        if inherited_from_library:
            raise SystemExit(
                f"{label} zip must not bundle exchange.cfm.runtime "
                f"(inherit from library): {inherited_from_library}"
            )
        theme_files = [
            name
            for name in names
            if name.startswith("com.inductiveautomation.perspective/themes/")
        ]
        if theme_files:
            raise SystemExit(
                f"{label} zip must not bundle Perspective themes "
                f"(inherit from library): {theme_files}"
            )
        stylesheet_files = [
            name
            for name in names
            if name.startswith("com.inductiveautomation.perspective/stylesheet/")
        ]
        if stylesheet_files:
            raise SystemExit(
                f"{label} zip must not bundle Advanced Stylesheet "
                f"(inherit from library): {stylesheet_files}"
            )
        required = (
            "com.inductiveautomation.perspective/page-config/config.json",
            "com.inductiveautomation.perspective/page-config/resource.json",
            "com.inductiveautomation.perspective/views/Config File Menu/Resources/Menu/Menu Top Bar/view.json",
        )
        missing = [name for name in required if name not in names]
        if missing:
            raise SystemExit(f"{label} zip missing required page-config files: {missing}")
        logo_files = [f"logo-upload/cfm/{name}" for name in LOGO_UPLOAD_NAMES]
        missing_logos = [name for name in logo_files if name not in names]
        if missing_logos:
            raise SystemExit(f"{label} zip missing logo PNGs: {missing_logos}")
        page_config = json.loads(
            archive.read("com.inductiveautomation.perspective/page-config/config.json")
        )
        pages = page_config.get("pages") or {}
        docks = page_config.get("sharedDocks") or {}
        if not pages:
            raise SystemExit(f"{label} zip page-config has no pages")
        if not docks.get("left") or not docks.get("top"):
            raise SystemExit(f"{label} zip page-config must include sharedDocks (child replaces parent)")
        if max_pages is not None and len(pages) > max_pages:
            raise SystemExit(
                f"{label} zip expected at most {max_pages} pages, found {len(pages)}"
            )
        page_count = len(pages)
    print(f"Verified {path.name}: {page_count} pages, sharedDocks + logo PNGs present")


def verify_site_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "r") as archive:
        pages = json.loads(
            archive.read("com.inductiveautomation.perspective/page-config/config.json")
        ).get("pages") or {}
        library_only = {"/cfm/target-no-route", "/cfm/settings", "/cfm/tools", "/cfm/tools/config-converter", "/cfm/diagnostics"}
        sample_routes = [route for route in pages if route.startswith("/cfm/") and route not in library_only]
        if sample_routes:
            raise SystemExit(
                f"Site zip must not include sample HMI routes: {sample_routes[:5]}"
            )
    _verify_child_zip(path, label="Site")


def verify_sample_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "r") as archive:
        pages = json.loads(
            archive.read("com.inductiveautomation.perspective/page-config/config.json")
        ).get("pages") or {}
        if "/cfm/dashboard" not in pages:
            raise SystemExit("Sample zip missing reference route /cfm/dashboard")
    _verify_child_zip(path, label="Sample")


if __name__ == "__main__":
    main()
