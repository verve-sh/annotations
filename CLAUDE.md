# annotations — Dev Notes

Per-file context annotations injected via PreToolUse hook. Pure Python — no build step.

## Architecture

```
scripts/
├── guard-file-annotations.py   — PreToolUse hook: reads annotation data, injects into context
├── annotate.py                 — CLI: create/append annotation for a source file
├── cleanup-annotations.py      — CLI: orphan/stale/drift analysis and pruning
└── gen-annotations-manifest.sh — regenerates .claude/annotations/MANIFEST.md
skills/
├── add/SKILL.md                — /annotations:add skill wrapper
└── cleanup/SKILL.md            — /annotations:cleanup skill wrapper
hooks/
└── hooks.json                  — PreToolUse hook on Read|Edit|Write
```

## Key Design Decisions

- **Data lives in the project, not the plugin.** `.claude/annotations/` is project-specific and version-controlled. The plugin only provides the engine.
- **Fail-open.** The hook script exits 0 on any error (bad JSON, missing git, no annotations dir). Never blocks the agent.
- **No external dependencies.** All scripts use Python stdlib only.
- **Glob matching is hand-rolled** to avoid importing `fnmatch` (which doesn't handle `**`). The `_glob_match` function is duplicated in `guard-file-annotations.py` and `cleanup-annotations.py` — intentional to keep each script self-contained.

## Commands

```bash
claude plugin validate plugins/annotations
```

## Testing

No automated tests. Verify manually:

1. Install the plugin, create `.claude/annotations/` in a test project
2. Add an annotation: `python3 scripts/annotate.py <file> "test note"`
3. Read the annotated file — the hook should inject `[File Annotation]`
4. Run cleanup: `python3 scripts/cleanup-annotations.py`
