# File Annotations

Annotations capture hidden invariants and non-obvious constraints tied to specific source files. They are injected into context automatically when you read, edit, or write an annotated file.

## When to annotate

Annotate when you discover something about a file that is:
- **Long-lived** — true independent of any issue, PR, or fix
- **Non-obvious** — not inferable from reading the code
- **Actionable** — affects how a future agent should work with the file

Examples: race conditions, platform quirks, silent-failure modes, ordering dependencies, undocumented API contracts, invariants that the type system doesn't enforce.

## When NOT to annotate

- **Fixable problems** — file a GitHub issue instead. Annotations are for constraints you cannot change.
- **Bugs and workarounds** — these should be fixed, not documented around.
- **Restatements of code** — if the code already says it, don't repeat it.
- **Cross-cutting concerns** — use CLAUDE.md or project rules for things that span many files.
- **Issue/PR references** — these go stale after merge.

**Litmus test:** would this annotation still be true after every open issue is closed? If no, file an issue instead.

## How to annotate

```
/annotations:add <source-file> "<note>"
```

This creates or appends to `.claude/annotations/<path>.md`. One file, one annotation file. Multiple notes on the same file become bullets.

For patterns that apply to many files (e.g. all Rust source, all migrations), add a line to `.claude/annotations/_patterns.yaml`:

```yaml
"src/**/*.rs": All IPC commands must validate caller-controlled paths.
```

## When to create annotations

Capture annotations as you discover them during a session — don't wait until the end when details may be lost. When you encounter a file-specific trap, constraint, or invariant that would surprise a future agent, annotate it immediately.
