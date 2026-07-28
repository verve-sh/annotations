# annotations

Agents forget what they learned last session. Annotations pin that knowledge — race conditions, hidden invariants, platform traps — directly to the files where it matters. When an agent reads or edits an annotated file, the context is injected automatically. No giant CLAUDE.md. No lost gotchas.

```
> Read src/pty.rs

[File Annotation — src/pty.rs]
waitpid races SIGKILL delivery — poll in 10ms loop, never raw waitpid

[File Annotation — pattern: src/**/*.rs]
All IPC commands must validate caller-controlled paths.
```

## Why

CLAUDE.md loads per-directory. Rules files load by glob. Both are all-or-nothing — the full file enters context whether the agent needs it or not. As a project grows, file-specific warnings either pile into a root CLAUDE.md that agents skim past, or scatter across directory files that still load more than needed.

Annotations are the missing layer: one note per file, injected at the exact moment the agent touches that file. Nothing loads until it's relevant. Nothing loads that isn't.

## How it works

**1. Agents capture knowledge.** As agents work with files, they discover gotchas worth preserving — race conditions, hidden invariants, undocumented constraints. The plugin ships a rules template (`rules/annotations.md`) that you copy into your project and tailor to your workflow — it teaches agents what to annotate, what belongs in an issue instead, and when to capture. Agents call `/annotations:add <file> "<note>"` to record what they find.

**2. Notes are stored per-file.** Each annotation lives at `.claude/annotations/<path>.md` — one file, one annotation file. Multiple notes on the same file become bullets. Glob patterns in `_patterns.yaml` cover conventions that apply across many files. All data lives in your project, not the plugin.

**3. Context is injected on contact.** A `PreToolUse` hook fires on every `Read`, `Edit`, and `Write`. It checks the target file against stored annotations and glob patterns, then injects matches as `additionalContext`. The agent sees them inline. All errors fail-open — the hook never blocks the agent.

## Install

```bash
claude plugin install annotations@verve-sh/annotations
```

Or from source:

```bash
git clone https://github.com/verve-sh/annotations.git
cp -r annotations/ <your-project>/.claude/plugins/annotations/
```

Then create your project's annotation data directory:

```bash
mkdir -p .claude/annotations
touch .claude/annotations/_patterns.yaml
```

Copy the agent rules template into your project and customize it for your workflow:

```bash
cp <plugin-root>/rules/annotations.md .claude/rules/annotations.md
```

Edit `.claude/rules/annotations.md` to match how you want agents to capture knowledge — what's worth annotating, what should be an issue instead, when to capture vs. skip. The plugin is the engine. Annotation data and rules live in your project — commit them with your code.

## Usage

### Annotate a file

```
/annotations:add src/pty.rs "waitpid races SIGKILL delivery — poll in 10ms loop"
```

Creates `.claude/annotations/src/pty.rs.md`:

```markdown
---
source: src/pty.rs
created: 2025-07-27
---
- waitpid races SIGKILL delivery — poll in 10ms loop
```

Run it again on the same file to append another bullet.

### Annotate a pattern

Add lines to `.claude/annotations/_patterns.yaml`:

```yaml
"src/**/*.rs": All IPC commands must validate caller-controlled paths.
"migrations/**": Migrations are append-only. Never edit an existing file.
"src/auth/**": Changes here require security review before merge.
```

Every file matching the pattern gets the note injected on read or edit.

### Clean up

```
/annotations:cleanup
```

Finds orphaned annotations (source deleted), stale patterns (no matches), and drifted annotations (source changed since the note was written). Offers to prune interactively.

## Requirements

- Python 3.8+ (stdlib only, no pip packages)
- Git

## License

[Apache-2.0](LICENSE)
