#!/usr/bin/env python3
"""Install bundled exchange.cfm.runtime Project Script Library into the Ignition project tree."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = Path(__file__).resolve().parent / "jython_lib" / "cfm"
# Platform scripts live under ignition/ (not com.inductiveautomation.ignition/).
RUNTIME_MODULE = "exchange.cfm.runtime"
DEST_ROOT = PROJECT_ROOT / "ignition" / "script-python" / "exchange" / "cfm" / "runtime"
LEGACY_ROOTS = (
	PROJECT_ROOT / "ignition" / "script-python" / "Config_File_Menu",
	PROJECT_ROOT / "ignition" / "script-python" / "cfm",
	PROJECT_ROOT / "com.inductiveautomation.ignition",
)
RESOURCE_ACTOR = "content-author"
SCRIPT_FILES = ("code.py",)

# Dependency-safe merge order for a single runtime module.
BUNDLE_ORDER = ("log", "config", "ui", "nav", "dock", "menu", "tree", "breadcrumb", "settings")


def normalize_lf_bytes(path: Path) -> bytes:
	text = path.read_text(encoding="utf-8")
	return text.replace("\r\n", "\n").encode("utf-8")


def content_signature(module_dir: Path) -> str:
	digest = hashlib.sha256()
	for name in SCRIPT_FILES:
		code_path = module_dir / name
		if code_path.is_file():
			digest.update(normalize_lf_bytes(code_path))
	return digest.hexdigest()


def strip_module_docstring(source: str) -> str:
	text = source.lstrip("\ufeff")
	if not text.startswith('"""'):
		return text
	end = text.find('"""', 3)
	if end == -1:
		return text
	return text[end + 3 :].lstrip("\n")


def strip_cross_module_refs(source: str) -> str:
	for module in BUNDLE_ORDER:
		source = source.replace(f"cfm.{module}.", "")
	return source


def build_runtime_source() -> str:
	chunks = [
		'"""CFM bundled runtime for Config File Menu (auto-generated).',
		"Deployed as exchange.cfm.runtime in the Project Script Library.",
		'"""',
		"",
	]
	for module in BUNDLE_ORDER:
		src_path = SRC_ROOT / f"{module}.py"
		if not src_path.is_file():
			raise SystemExit(f"Missing runtime source module: {src_path}")
		body = strip_cross_module_refs(strip_module_docstring(src_path.read_text(encoding="utf-8")))
		chunks.append(f"# --- {module}.py ---")
		chunks.append(body.rstrip())
		chunks.append("")
	return "\n".join(chunks).rstrip() + "\n"


def script_resource_json(*, signature: str) -> dict:
	ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
	return {
		"scope": "A",
		"version": 1,
		"restricted": False,
		"overridable": True,
		"files": list(SCRIPT_FILES),
		"attributes": {
			"lastModification": {"actor": RESOURCE_ACTOR, "timestamp": ts},
			"lastModificationSignature": signature,
			"hintScope": 2,
		},
	}


def write_code_py(content: str, dest: Path) -> None:
	dest.write_bytes(content.replace("\r\n", "\n").encode("utf-8"))


def remove_legacy_modules() -> None:
	for legacy_root in LEGACY_ROOTS:
		if not legacy_root.exists():
			continue
		shutil.rmtree(legacy_root, ignore_errors=True)
		if legacy_root.exists() and os.name == "nt":
			# OneDrive placeholder dirs can defeat shutil.rmtree with WinError 5;
			# native rmdir removes them.
			subprocess.run(
				["cmd", "/c", "rmdir", "/s", "/q", str(legacy_root)],
				check=False,
				capture_output=True,
			)
		if legacy_root.exists():
			print(f"WARNING: could not remove legacy module dir: {legacy_root}")


def install_script_library() -> list[str]:
	if not SRC_ROOT.is_dir():
		raise SystemExit(f"Missing script library source: {SRC_ROOT}")

	DEST_ROOT.mkdir(parents=True, exist_ok=True)
	runtime_source = build_runtime_source()
	write_code_py(runtime_source, DEST_ROOT / "code.py")
	signature = content_signature(DEST_ROOT)
	(DEST_ROOT / "resource.json").write_text(
		json.dumps(script_resource_json(signature=signature), indent=2) + "\n",
		encoding="utf-8",
		newline="\n",
	)
	remove_legacy_modules()

	print("Installed Project Script Library modules:")
	print(f"  {RUNTIME_MODULE} (bundled)")
	return [RUNTIME_MODULE]


def main() -> None:
	install_script_library()


if __name__ == "__main__":
	main()
