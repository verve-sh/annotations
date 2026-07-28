#!/usr/bin/env python3
"""
Usage: python3 annotate.py <source-file> "<note>"
Creates or appends to the annotation file for the given source file.
"""
import sys, os, subprocess
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: annotate.py <source-file> '<note>'", file=sys.stderr)
    sys.exit(1)

source = sys.argv[1]
note = sys.argv[2]

repo_root = subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"],
    text=True,
).strip()

# Accept absolute or relative paths; resolve symlinks to avoid
# macOS /var → /private/var divergence in os.path.relpath
if os.path.isabs(source):
    relative = os.path.relpath(os.path.realpath(source), os.path.realpath(repo_root))
else:
    relative = source

annotation_path = Path(repo_root) / ".claude" / "annotations" / (relative + ".md")
annotation_path.parent.mkdir(parents=True, exist_ok=True)

if annotation_path.exists():
    existing = annotation_path.read_text()
    annotation_path.write_text(existing.rstrip() + f"\n\n{note}\n")
    print(f"Appended to {annotation_path.relative_to(repo_root)}")
else:
    annotation_path.write_text(f"---\nseverity: warning\n---\n\n{note}\n")
    print(f"Created {annotation_path.relative_to(repo_root)}")

# Regenerate MANIFEST so it stays in sync
manifest_script = Path(__file__).resolve().parent / "gen-annotations-manifest.sh"
if manifest_script.exists():
    subprocess.run(["bash", str(manifest_script)], check=True, capture_output=True)
