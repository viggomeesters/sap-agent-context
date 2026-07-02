#!/usr/bin/env python3
"""Clean generated, ignored build artifacts without touching source files."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ALLOWED_TARGETS = {
    "reports": Path("build/reports"),
    "build": Path("build"),
}


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip())


def is_ignored(root: Path, relative_path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--", relative_path.as_posix()],
        cwd=root,
    )
    return result.returncode == 0


def remove_contents(target: Path) -> list[str]:
    removed: list[str] = []
    if not target.exists():
        return removed
    if not target.is_dir():
        raise SystemExit(f"Refusing to clean non-directory target: {target}")

    for child in sorted(target.iterdir()):
        removed.append(child.as_posix())
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    return removed


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in ALLOWED_TARGETS:
        allowed = ", ".join(sorted(ALLOWED_TARGETS))
        raise SystemExit(f"Usage: clean_generated.py <{allowed}>")

    mode = argv[1]
    relative_target = ALLOWED_TARGETS[mode]
    root = repo_root()
    target = root / relative_target

    if not is_ignored(root, relative_target):
        raise SystemExit(f"Refusing to clean non-ignored target: {relative_target.as_posix()}")

    removed = remove_contents(target)
    if removed:
        print(f"cleaned {relative_target.as_posix()}:")
        for path in removed:
            print(f"  {path}")
    else:
        print(f"nothing to clean in {relative_target.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
