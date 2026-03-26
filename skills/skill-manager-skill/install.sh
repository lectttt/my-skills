#!/usr/bin/env bash
# install.sh — Wrapper; delegates to skill_manager.py for cross-platform support.
# Usage: bash install.sh [--all] [--platform <name>] [--dry-run]
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SKILL_DIR/scripts/skill_manager.py" install "$@"
