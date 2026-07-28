---
name: annotations:add
description: "Add/append a gotcha annotation to a source file. Use when recording file-specific warnings, traps, or pitfalls found during review, debug, or refactor."
user-invocable: true
allowed-tools: Bash
---

Parse `$ARGUMENTS` as `<source-file> "<note>"` and run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/annotate.py" "$FILE" "$NOTE"
```

The first argument is the source file path (relative to repo root or absolute). The rest of the arguments form the note text. If only one argument is given, ask for the note text.
