#!/usr/bin/env python3
"""Fetch the stock profile trees pinned in upstream.lock.toml into a cache keyed by commit.

Usage: fetch.py [TARGET ...]   (default: every target)
Each tree lands in $SLICER_PROFILES_CACHE (default ~/.cache/slicer-profiles/upstream) as
<owner>__<repo>@<commit>, holding only the JSON files of resources/profiles. A fetch is accepted only when
the checked-out commit, the git tree id of resources/profiles and every vendor index version match the
lock; the cache is never committed or uploaded. src/resolve.py uses a fetched tree before an installed app.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import cast

from targets import NAMES, Target, load

PROFILES = "resources/profiles"


def cache_root() -> Path:
    """Return the folder that holds the fetched trees."""
    return Path(os.environ.get("SLICER_PROFILES_CACHE") or Path.home() / ".cache" / "slicer-profiles" / "upstream")


def tree_dir(t: Target) -> Path:
    """Return the checkout folder of one target's pinned commit."""
    return cache_root() / f"{t['repository'].replace('/', '__')}@{t['commit']}"


def _git(*args: str, cwd: Path) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)  # noqa: S603, S607 (git from PATH, arguments from the lock)
    return done.stdout.strip()


def problems(t: Target, checkout: Path) -> list[str]:
    """Return how a checkout differs from its lock entry (empty when it matches)."""
    found: list[str] = []
    if (head := _git("rev-parse", "HEAD", cwd=checkout)) != t["commit"]:
        found.append(f"commit {head}, lock {t['commit']}")
    if (tree := _git("rev-parse", f"HEAD:{PROFILES}", cwd=checkout)) != t["tree"]:
        found.append(f"tree {tree}, lock {t['tree']}")
    for vendor, version in t["vendors"].items():
        index = cast("dict[str, object]", json.loads((checkout / PROFILES / f"{vendor}.json").read_text("utf-8-sig")))
        if index.get("version") != version:
            found.append(f"{vendor}.json version {index.get('version')}, lock {version}")
    return found


def fetch(name: str, t: Target) -> Path:
    """Return the verified profile folder of one target, fetching it first when it is not cached."""
    dest = tree_dir(t)
    if not dest.is_dir():
        dest.parent.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(dir=dest.parent, prefix=".fetch-"))
        url = f"https://github.com/{t['repository']}.git"
        _ = _git(
            "clone",
            "--quiet",
            "--filter=blob:none",
            "--no-checkout",
            "--depth=1",
            "--branch",
            t["tag"],
            url,
            ".",
            cwd=work,
        )
        _ = _git("sparse-checkout", "set", "--no-cone", f"/{PROFILES}/**/*.json", f"/{PROFILES}/*.json", cwd=work)
        _ = _git("checkout", "--quiet", cwd=work)
        if found := problems(t, work):
            shutil.rmtree(work)
            msg = f"{name}: {t['repository']} {t['tag']} does not match upstream.lock.toml: {'; '.join(found)}"
            raise RuntimeError(msg)
        _ = work.rename(dest)
    elif found := problems(t, dest):
        msg = f"{name}: cached tree {dest} does not match upstream.lock.toml: {'; '.join(found)}"
        raise RuntimeError(msg)
    return dest / PROFILES


def main(argv: list[str]) -> int:
    """Fetch and verify the requested targets; print one `SLICER_PROFILES_<TARGET>=<folder>` line each."""
    lock = load()
    names = argv or list(NAMES)
    if unknown := [n for n in names if n not in lock]:
        print(f"unknown targets {unknown}; known: {', '.join(NAMES)}", file=sys.stderr)
        return 64
    for name in names:
        print(f"SLICER_PROFILES_{name.upper()}={fetch(name, lock[name])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
