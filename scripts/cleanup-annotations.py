#!/usr/bin/env python3
"""
Annotation health: orphan pruning + drift detection.

Usage:
  cleanup-annotations.py              # Analysis report
  cleanup-annotations.py --prune-orphans   # Remove orphaned annotation files
  cleanup-annotations.py --prune-patterns  # Rewrite _patterns.yaml without stale lines
  cleanup-annotations.py --regen           # Regenerate MANIFEST.md
"""
import os
import re
import subprocess
import sys
from pathlib import Path


def _glob_match(path, pattern):
    i, regex = 0, ""
    while i < len(pattern):
        if pattern[i] == "*" and i + 1 < len(pattern) and pattern[i + 1] == "*":
            i += 2
            if i < len(pattern) and pattern[i] == "/":
                regex += "(?:.+/)?"
                i += 1
            else:
                regex += ".*"
        elif pattern[i] == "*":
            regex += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            regex += "[^/]"
            i += 1
        else:
            regex += re.escape(pattern[i])
            i += 1
    try:
        return bool(re.fullmatch(regex, path))
    except re.error:
        return False


def git(*args, timeout=2):
    return subprocess.check_output(
        ["git", *args], text=True, stderr=subprocess.DEVNULL, timeout=timeout
    ).strip()


def repo_root():
    return Path(os.path.realpath(git("rev-parse", "--show-toplevel")))


def annotations_dir(root):
    return root / ".claude" / "annotations"


def within_boundary(path, boundary):
    return str(path.resolve()).startswith(str(boundary.resolve()))


def annotation_files(ann_dir):
    for p in sorted(ann_dir.rglob("*.md")):
        if p.name in ("MANIFEST.md",):
            continue
        yield p


def source_path(ann_file, ann_dir, root):
    relative = str(ann_file.relative_to(ann_dir))
    if relative.endswith(".md"):
        relative = relative[: -len(".md")]
    return root / relative


def find_orphans(ann_dir, root):
    orphans = []
    for ann in annotation_files(ann_dir):
        src = source_path(ann, ann_dir, root)
        if not src.exists():
            orphans.append((ann, src))
    return orphans


def find_stale_patterns(ann_dir, root):
    patterns_file = ann_dir / "_patterns.yaml"
    if not patterns_file.exists():
        return []

    try:
        tracked_files = git("ls-files", timeout=5).splitlines()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return []

    stale = []
    for lineno, line in enumerate(patterns_file.read_text().splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ": " not in stripped:
            continue
        pattern_part = stripped.split(": ", 1)[0].strip().strip('"')
        has_match = False
        for single in pattern_part.split(","):
            single = single.strip()
            if not single:
                continue
            for tracked_file in tracked_files:
                if _glob_match(tracked_file, single):
                    has_match = True
                    break
            if has_match:
                break
        if not has_match:
            stale.append((lineno, stripped))
    return stale


def find_drifted(ann_dir, root):
    drifted = []
    for ann in annotation_files(ann_dir):
        src = source_path(ann, ann_dir, root)
        if not src.exists():
            continue
        try:
            ann_epoch = int(git("log", "-1", "--format=%ct", "--", str(ann)))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            continue
        try:
            src_epoch = int(git("log", "-1", "--format=%ct", "--", str(src)))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            continue
        if src_epoch > ann_epoch:
            try:
                count = int(
                    git(
                        "rev-list", "--count",
                        f"--since={ann_epoch}", "HEAD", "--", str(src),
                        timeout=5,
                    )
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
                count = 0
            from datetime import datetime, timezone

            ann_date = datetime.fromtimestamp(ann_epoch, tz=timezone.utc).strftime(
                "%Y-%m-%d"
            )
            drifted.append(
                (str(src.relative_to(root)), count, ann_date)
            )
    return drifted


def count_current(ann_dir):
    return sum(1 for _ in annotation_files(ann_dir))


def count_patterns(ann_dir):
    patterns_file = ann_dir / "_patterns.yaml"
    if not patterns_file.exists():
        return 0
    count = 0
    for line in patterns_file.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


def report(ann_dir, root):
    orphans = find_orphans(ann_dir, root)
    stale = find_stale_patterns(ann_dir, root)
    drifted = find_drifted(ann_dir, root)
    current = count_current(ann_dir) - len(orphans)
    patterns = count_patterns(ann_dir) - len(stale)

    print("Annotation health report")
    print("========================")
    print()

    if orphans:
        print(f"Orphaned ({len(orphans)}) — source file deleted:")
        for ann, src in orphans:
            print(f"  {ann.relative_to(root)}")
            print(f"    → {src.relative_to(root)}")
        print()

    if stale:
        print(f"Stale patterns ({len(stale)}) — no matching files:")
        for lineno, line in stale:
            print(f"  line {lineno}: {line}")
        print()

    if drifted:
        print(f"Drifted ({len(drifted)}) — source modified since annotation:")
        for src_rel, commits, date in sorted(drifted, key=lambda x: -x[1]):
            print(f"  {src_rel} — {commits} commit{'s' if commits != 1 else ''} since {date}")
        print()

    print(f"Current: {current} annotations, {patterns} patterns")

    if orphans or stale:
        print()
        print("Run with --prune-orphans / --prune-patterns to clean up.")


def prune_orphans(ann_dir, root):
    orphans = find_orphans(ann_dir, root)
    if not orphans:
        print("No orphaned annotations found.")
        return

    removed = 0
    for ann, _src in orphans:
        if not within_boundary(ann, ann_dir):
            continue
        ann.unlink()
        removed += 1
        print(f"  Removed {ann.relative_to(root)}")

        parent = ann.parent
        while parent != ann_dir and parent.exists():
            if not within_boundary(parent, ann_dir):
                break
            try:
                parent.rmdir()
                print(f"  Removed empty dir {parent.relative_to(root)}")
                parent = parent.parent
            except OSError:
                break

    print(f"\nPruned {removed} orphaned annotation(s).")


def prune_patterns(ann_dir, root):
    patterns_file = ann_dir / "_patterns.yaml"
    if not patterns_file.exists():
        print("No _patterns.yaml found.")
        return

    stale = find_stale_patterns(ann_dir, root)
    if not stale:
        print("No stale patterns found.")
        return

    stale_linenos = {lineno for lineno, _ in stale}
    lines = patterns_file.read_text().splitlines()
    kept = [line for i, line in enumerate(lines, 1) if i not in stale_linenos]
    patterns_file.write_text("\n".join(kept) + "\n" if kept else "")

    for lineno, line in stale:
        print(f"  Removed line {lineno}: {line}")
    print(f"\nPruned {len(stale)} stale pattern(s).")


def regen(root):
    script = Path(__file__).resolve().parent / "gen-annotations-manifest.sh"
    if not script.exists():
        print(f"gen-annotations-manifest.sh not found at {script}", file=sys.stderr)
        sys.exit(1)
    subprocess.run(["bash", str(script)], check=True)


def main():
    try:
        root = repo_root()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print("Not in a git repository.", file=sys.stderr)
        sys.exit(1)

    ann_dir = annotations_dir(root)
    if not ann_dir.is_dir():
        print(f"Annotations directory not found: {ann_dir}", file=sys.stderr)
        sys.exit(1)

    args = set(sys.argv[1:])

    if "--prune-orphans" in args:
        prune_orphans(ann_dir, root)
    elif "--prune-patterns" in args:
        prune_patterns(ann_dir, root)
    elif "--regen" in args:
        regen(root)
    else:
        report(ann_dir, root)


if __name__ == "__main__":
    main()
