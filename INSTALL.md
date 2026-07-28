# annotations — Quick Install

## 1. Install the plugin

**Marketplace:**
```bash
claude plugin install annotations@verve-sh/annotations
```

**Manual:**
```bash
git clone https://github.com/verve-sh/annotations.git
cp -r annotations/ <your-project>/.claude/plugins/annotations/
```

## 2. Create the data directory

```bash
mkdir -p .claude/annotations
touch .claude/annotations/_patterns.yaml
```

## 3. Set up agent rules

Copy the rules template and customize it for your workflow:

```bash
cp <plugin-root>/rules/annotations.md .claude/rules/annotations.md
```

Edit `.claude/rules/annotations.md` to define what agents should annotate, what belongs in issues instead, and when to capture.

## 4. Add your first annotation

```
/annotations:add src/main.rs "Entry point — restarts crash on panic"
```

## Requirements

- Python 3.8+
- Git
