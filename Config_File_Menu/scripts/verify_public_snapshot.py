#!/usr/bin/env python3
"""Fail if a maintainer-only file has leaked into the public snapshot.

The public repository is not a merge of ``dev`` — the two have unrelated histories, so
each public release is a *snapshot*: ``dev``'s tree committed onto ``main`` as one commit.
A few files are deliberately kept out of that snapshot. Dropping them is a manual step,
and it has silently failed before (``EXCHANGE_SUBMISSION.md`` shipped publicly for two
releases despite its own header saying not to), so this check enforces it.

Two assertions per path:

1. **The path still exists locally.** If a file is renamed or deleted, the exclusion
   silently stops protecting anything — a stale guard is worse than no guard.
2. **The path is absent from the public ref's tree.** This is the real invariant.

Usage:
    python Config_File_Menu/scripts/verify_public_snapshot.py [ref]
Exit code 0 = clean (or the ref is unavailable to check), 1 = a private file is public.

Also backs the pre-push hook, which vets the commit *about to be pushed* rather than one
already published:
    python Config_File_Menu/scripts/verify_public_snapshot.py --pre-push <remote> <url>
reading git's pre-push records on stdin. Install with:
    git config core.hooksPath Config_File_Menu/scripts/hooks
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Repo-root-relative paths that must never appear in the public tree. Keep this list and
# the drop step in the release runbook in sync; the test below fails if an entry no longer
# exists locally, which is the signal that this list needs updating rather than ignoring.
PRIVATE_ONLY_PATHS = (
    "Config_File_Menu/EXCHANGE_SUBMISSION.md",
)

DEFAULT_REF = "origin/main"

DROP_HINT = (
    "Rebuild the snapshot with the drop step:\n"
    "    git checkout -B release-<version> {ref}\n"
    "    git read-tree --reset -u dev\n"
    "    git rm --cached {paths}\n"
    "    git commit"
)


def _git(*args):
    """Run a git command in the repo root. Returns (ok, stdout)."""
    try:
        result = subprocess.run(
            ("git",) + args,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
    except OSError:
        return False, ""
    return result.returncode == 0, result.stdout.strip()


def ref_available(ref=DEFAULT_REF):
    """True when `ref` resolves — false in a shallow CI clone or a fresh worktree."""
    ok, _ = _git("rev-parse", "--verify", "--quiet", ref + "^{commit}")
    return ok


def split_paths_by_presence():
    """(present, missing) for the guarded paths in this working tree."""
    present, missing = [], []
    for path in PRIVATE_ONLY_PATHS:
        (present if (REPO_ROOT / path).exists() else missing).append(path)
    return present, missing


def is_public_checkout():
    """True when no guarded path exists here — the signature of a public clone.

    The guarded files are *supposed* to be absent from a public checkout, so their absence
    there is correct, not drift. A partial absence is different: that means a maintainer
    renamed or deleted one, which `check_paths_exist` reports as a stale guard.
    """
    present, _ = split_paths_by_presence()
    return not present


def check_paths_exist():
    """The guarded paths must still be present locally, or the guard has gone stale."""
    present, missing = split_paths_by_presence()
    if missing and present:
        return False, (
            "Guarded path(s) no longer exist locally: %s.\n"
            "They were renamed or deleted, so PRIVATE_ONLY_PATHS in "
            "scripts/verify_public_snapshot.py no longer protects them. Update it."
            % ", ".join(missing)
        )
    if missing:
        return False, (
            "No guarded path exists locally (%s).\n"
            "Expected in a public checkout — run this from the maintainer repo instead."
            % ", ".join(missing)
        )
    return True, "All guarded paths present locally."


def check_ref_clean(ref=DEFAULT_REF):
    """The guarded paths must be absent from `ref`'s tree."""
    leaked = []
    for path in PRIVATE_ONLY_PATHS:
        ok, out = _git("ls-tree", "-r", "--name-only", ref, "--", path)
        if not ok:
            return False, "Could not read tree of %s." % ref
        if out:
            leaked.append(path)
    if leaked:
        return False, (
            "Maintainer-only file(s) present in %s: %s\n\n%s"
            % (
                ref,
                ", ".join(leaked),
                DROP_HINT.format(ref=ref, paths=" ".join(leaked)),
            )
        )
    return True, "No maintainer-only files in %s." % ref


def check(ref=DEFAULT_REF):
    """Both checks, for maintainer use — a public checkout is reported as an error here.

    The pytest wrapper skips instead; this script is run deliberately by a maintainer, so
    pointing it at the wrong clone should say so rather than silently pass.
    """
    ok, message = check_paths_exist()
    if not ok:
        return False, message
    if not ref_available(ref):
        return True, "%s not available; local-path check only." % ref
    return check_ref_clean(ref)


# --- pre-push enforcement -------------------------------------------------------------
#
# `check_ref_clean` inspects a ref that is already published, so it detects a bad snapshot
# after the fact. The hook below inspects the commit *about to be pushed*, which is the
# last moment a leak is still free to fix.

# A remote is treated as private when its name or URL matches one of these. Anything else
# is treated as public — an unrecognized remote gets the check rather than a free pass.
PRIVATE_REMOTE_MARKERS = ("Working-Private",)


def is_private_remote(name, url):
    """True when this remote is a known-private one, so its pushes are not checked."""
    haystack = ("%s %s" % (name or "", url or "")).lower()
    return any(marker.lower() in haystack for marker in PRIVATE_REMOTE_MARKERS)


def check_commit_clean(sha):
    """The guarded paths must be absent from the tree of `sha`."""
    leaked = []
    for path in PRIVATE_ONLY_PATHS:
        ok, out = _git("ls-tree", "-r", "--name-only", sha, "--", path)
        if not ok:
            return False, "Could not read tree of %s." % sha
        if out:
            leaked.append(path)
    if leaked:
        return False, "maintainer-only file(s) present: %s" % ", ".join(leaked)
    return True, "clean"


def _is_deletion(sha):
    return not sha.strip("0")


def pre_push(remote_name, remote_url, lines):
    """Vet the refs a push is about to publish. Returns (exit_code, message).

    `lines` are git's pre-push stdin records: `<local ref> <local sha> <remote ref>
    <remote sha>`. Every ref bound for a public remote is checked, not just `main` — a
    branch pushed there is just as public.
    """
    if is_private_remote(remote_name, remote_url):
        return 0, "Private remote (%s); snapshot check skipped." % (remote_name or remote_url)

    problems = []
    checked = 0
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        local_ref, local_sha, remote_ref, _remote_sha = parts[:4]
        if _is_deletion(local_sha):
            continue
        checked += 1
        ok, detail = check_commit_clean(local_sha)
        if not ok:
            problems.append("  %s -> %s: %s" % (local_ref, remote_ref, detail))

    if problems:
        return 1, (
            "Refusing to push to the public remote (%s):\n%s\n\n%s\n\n"
            "Override with --no-verify only if you are certain."
            % (
                remote_name or remote_url,
                "\n".join(problems),
                DROP_HINT.format(ref="origin/main", paths=" ".join(PRIVATE_ONLY_PATHS)),
            )
        )
    return 0, "Snapshot check passed (%d ref(s))." % checked


def main(argv):
    if len(argv) > 1 and argv[1] == "--pre-push":
        remote_name = argv[2] if len(argv) > 2 else ""
        remote_url = argv[3] if len(argv) > 3 else ""
        code, message = pre_push(remote_name, remote_url, sys.stdin.read().splitlines())
        stream = sys.stderr if code else sys.stdout
        print("cfm snapshot guard: " + message, file=stream)
        return code

    ref = argv[1] if len(argv) > 1 else DEFAULT_REF
    ok, message = check(ref)
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
