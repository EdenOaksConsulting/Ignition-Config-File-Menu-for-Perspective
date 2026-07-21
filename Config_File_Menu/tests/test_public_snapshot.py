"""Snapshot guard: maintainer-only files must not reach the public tree.

Wraps ``scripts/verify_public_snapshot.py`` so the check runs as part of pytest. See that
module for why this exists — the public repo is a squashed snapshot of ``dev``, and
dropping the private files is a manual step that has failed silently before.
"""

import importlib.util
from pathlib import Path

import pytest


def _load_verifier():
    path = Path(__file__).resolve().parents[1] / "scripts" / "verify_public_snapshot.py"
    spec = importlib.util.spec_from_file_location("verify_public_snapshot", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFIER = _load_verifier()


def test_guard_is_not_stale():
    """Every guarded path still exists locally, so the exclusion still protects something.

    Skipped in a public checkout, where the guarded files are *correctly* absent — this
    suite ships publicly, so it must pass for someone who clones the public repo.
    """
    if VERIFIER.is_public_checkout():
        pytest.skip("public checkout: guarded files are absent by design")
    ok, message = VERIFIER.check_paths_exist()
    assert ok, message


def test_public_ref_has_no_maintainer_files():
    """The published tree carries none of the maintainer-only files."""
    ref = VERIFIER.DEFAULT_REF
    if not VERIFIER.ref_available(ref):
        pytest.skip("%s not available (shallow clone or no remote)" % ref)
    ok, message = VERIFIER.check_ref_clean(ref)
    assert ok, message


# --- pre-push hook logic --------------------------------------------------------------

PUBLIC_URL = "https://github.com/EdenOaksConsulting/Ignition-Config-File-Menu-for-Perspective.git"
PRIVATE_URL = PUBLIC_URL.replace(".git", "-Working-Private.git")
ZERO = "0" * 40


def _record(local_sha, remote_ref="refs/heads/main"):
    return "refs/heads/x %s %s %s" % (local_sha, remote_ref, ZERO)


def test_private_remote_is_recognized():
    assert VERIFIER.is_private_remote("private-origin", PRIVATE_URL)
    assert not VERIFIER.is_private_remote("origin", PUBLIC_URL)


def test_unknown_remote_is_treated_as_public():
    """An unrecognized remote gets checked rather than waved through."""
    assert not VERIFIER.is_private_remote("some-fork", "https://example.invalid/thing.git")


def test_pre_push_skips_private_remote():
    code, _ = VERIFIER.pre_push("private-origin", PRIVATE_URL, [_record("HEAD")])
    assert code == 0


def test_pre_push_allows_a_clean_commit():
    if not VERIFIER.ref_available(VERIFIER.DEFAULT_REF):
        pytest.skip("origin/main not available")
    code, message = VERIFIER.pre_push("origin", PUBLIC_URL, [_record(VERIFIER.DEFAULT_REF)])
    assert code == 0, message


def test_pre_push_ignores_branch_deletions():
    """A deletion pushes no tree, so there is nothing to inspect."""
    code, message = VERIFIER.pre_push("origin", PUBLIC_URL, [_record(ZERO)])
    assert code == 0
    assert "0 ref(s)" in message


def test_pre_push_blocks_a_commit_carrying_a_guarded_file():
    """HEAD of dev holds the maintainer-only file, so it must never reach a public remote."""
    ok, _ = VERIFIER.check_commit_clean("HEAD")
    if ok:
        pytest.skip("HEAD carries no guarded file (public checkout)")
    code, message = VERIFIER.pre_push("origin", PUBLIC_URL, [_record("HEAD")])
    assert code == 1
    assert VERIFIER.PRIVATE_ONLY_PATHS[0] in message
