#!/usr/bin/env python3
import json, sys, os, re, subprocess
from pathlib import Path

try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    sys.exit(0)
file_path = data.get("tool_input", {}).get("file_path", "")
if not file_path:
    sys.exit(0)

try:
    repo_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
    ).strip()
except (subprocess.CalledProcessError, FileNotFoundError, OSError):
    sys.exit(0)
# Resolve symlinks to avoid macOS /var → /private/var divergence
relative = os.path.relpath(os.path.realpath(file_path), os.path.realpath(repo_root))
annotations_dir = Path(repo_root) / ".claude" / "annotations"

messages = []

# Phase 1: exact-path annotation
annotation_path = annotations_dir / (relative + ".md")
if annotation_path.exists():
    content = annotation_path.read_text()
    lines = content.split("\n")
    if lines and lines[0].strip() == "---":
        try:
            end = lines.index("---", 1)
            content = "\n".join(lines[end + 1:]).strip()
        except ValueError:
            pass
    if content:
        messages.append(content)

def _glob_match(path, pattern):
    i, regex = 0, ''
    while i < len(pattern):
        if pattern[i] == '*' and i + 1 < len(pattern) and pattern[i + 1] == '*':
            i += 2
            if i < len(pattern) and pattern[i] == '/':
                regex += '(?:.+/)?'
                i += 1
            else:
                regex += '.*'
        elif pattern[i] == '*':
            regex += '[^/]*'
            i += 1
        elif pattern[i] == '?':
            regex += '[^/]'
            i += 1
        else:
            regex += re.escape(pattern[i])
            i += 1
    return bool(re.fullmatch(regex, path))

# Phase 2: glob-pattern cross-cutting rules
patterns_file = annotations_dir / "_patterns.yaml"
if patterns_file.exists():
    for line in patterns_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ": " in line:
            pattern, note = line.split(": ", 1)
            pattern = pattern.strip().strip('"')
            for single_pattern in pattern.split(","):
                single_pattern = single_pattern.strip()
                try:
                    if _glob_match(relative, single_pattern):
                        messages.append(note.strip())
                        break
                except (re.error, ValueError, IndexError):
                    pass

if messages:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": "[File Annotation]\n" + "\n\n---\n\n".join(messages)
        }
    }))
