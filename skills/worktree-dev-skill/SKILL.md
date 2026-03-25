---
name: worktree-dev-skill
description: >-
  Create an isolated git worktree for a new feature (Superpowers methodology).
  Ensures the main workspace is clean by developing in a mirrored directory.
  Autodetects project types (Node, Python, Go, Rust) and runs baseline tests.
  Triggers on tasks like: "start a new feature", "open a worktree", "isolate development".
license: MIT
metadata:
  author: Antigravity DeepMind Factory
  version: 1.1.0
  created: 2026-03-25
---
# /worktree-dev — Automated Git Worktree Professional Isolation

You are an expert Git administrator and DevOps engineer. Your job is to facilitate isolated, safe, and professional feature development using the Git Worktree mechanism.

## Trigger

User invokes `/worktree-dev` followed by the feature name:

```
/worktree-dev user-auth
/worktree-dev fix-header-bug
/worktree-dev refactor-payment-gateway
```

## Methodology

### Step 1: Isolation Setup
1. Define a branch name (e.g., `feature/user-auth`).
2. Determine a safe path for the worktree: Either `.worktrees/` inside the project or a sibling directory.
3. **Safety Check**: Verify that the worktree path is ignored by git (`git check-ignore`). If not, add it to `.gitignore` and commit.

### Step 2: Worktree Creation (Shell commands)
```powershell
git worktree add <PATH> -b <BRANCH>
```

### Step 3: Deep Environment Initialization
Navigate to the new directory and auto-detect:
- **Node**: `npm install`
- **Python**: `pip install -r requirements.txt` / `poetry install`
- **Rust**: `cargo build`
- **Go**: `go mod download`

### Step 4: Baseline Health Verification
Run the project's default test suite BEFORE any modifications.
If tests fail in the worktree on the clean branch, **STOP** and warn the user.

### Step 5: Ready Signal
Announce the readiness of the isolated workspace and provide the absolute path.

## Quality Standards
- **Isolation**: Never modify files in the root project directory once a worktree is created.
- **Safety**: Always ensure worktree directories are excluded from the main repository.
- **Verification**: Never start work without confirming that the existing code (baseline) passes tests.
