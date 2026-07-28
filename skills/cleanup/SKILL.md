---
name: annotations:cleanup
description: "Analyze annotation health and prune orphans/stale patterns. Reports orphaned files, stale glob patterns, and drifted annotations."
user-invocable: true
allowed-tools: Bash, AskUserQuestion
---

Run the annotation health analysis, then guide the user through cleanup.

## Step 1 — Analysis

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cleanup-annotations.py"
```

Present the full report to the user.

## Step 2 — Prune orphans (if any)

If orphaned annotations were found, show the list and use `AskUserQuestion` to ask:
- "Prune N orphaned annotation files?" with options "Yes, prune" / "No, skip"

If approved:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cleanup-annotations.py" --prune-orphans
```

## Step 3 — Prune stale patterns (if any)

If stale patterns were found, show the list and use `AskUserQuestion` to ask:
- "Remove N stale pattern lines from _patterns.yaml?" with options "Yes, remove" / "No, skip"

If approved:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cleanup-annotations.py" --prune-patterns
```

## Step 4 — Drift report (informational)

If drifted annotations were found, present the list. No auto-action — these need manual review to determine if the annotation content is still valid.

## Step 5 — Regenerate MANIFEST

If any pruning was performed in steps 2 or 3:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cleanup-annotations.py" --regen
```

## Step 6 — Final state

Re-run the analysis to show the updated state:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cleanup-annotations.py"
```

Report a one-line summary of what changed.
