#!/usr/bin/env bash
# install.sh — Cross-platform auto-installer for skill-manager-skill
# Usage:
#   ./install.sh                  # Auto-detect platform and install
#   ./install.sh --platform gemini
#   ./install.sh --all            # Install to all detected platforms
#   ./install.sh --dry-run        # Preview without making changes

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="skill-manager-skill"
DRY_RUN=false
PLATFORM=""
INSTALL_ALL=false

# Color output
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RED="\033[0;31m"
NC="\033[0m"

log()     { echo -e "${CYAN}[install]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; }

# ----- Argument Parsing -----
while [[ $# -gt 0 ]]; do
    case "$1" in
        --platform) PLATFORM="$2"; shift 2 ;;
        --all)      INSTALL_ALL=true; shift ;;
        --dry-run)  DRY_RUN=true; shift ;;
        -h|--help)
            echo "Usage: ./install.sh [--platform <name>] [--all] [--dry-run]"
            echo "Platforms: antigravity, gemini, claude, universal, cursor, windsurf, cline, kiro"
            exit 0 ;;
        *) error "Unknown argument: $1"; exit 1 ;;
    esac
done

# ----- Platform Detection -----
declare -A PLATFORM_PATHS=(
    ["antigravity"]="$HOME/.gemini/antigravity/skills"
    ["gemini"]="$HOME/.gemini/skills"
    ["claude"]="$HOME/.claude/skills"
    ["universal"]="$HOME/.agents/skills"
    ["cursor"]="$HOME/.cursor/skills"
    ["windsurf"]="$HOME/.codeium/windsurf/skills"
    ["cline"]="$HOME/.clinerules/skills"
    ["kiro"]="$HOME/.kiro/skills"
)

detect_platforms() {
    local detected=()
    [[ -d "$HOME/.gemini/antigravity" ]] && detected+=("antigravity")
    [[ -d "$HOME/.gemini" && ! -d "$HOME/.gemini/antigravity" ]] && detected+=("gemini")
    [[ -d "$HOME/.claude" ]] && detected+=("claude")
    [[ -d "$HOME/.agents" ]] && detected+=("universal")
    [[ -d "$HOME/.cursor" ]] && detected+=("cursor")
    [[ -d "$HOME/.codeium/windsurf" ]] && detected+=("windsurf")
    [[ -d "$HOME/.clinerules" ]] && detected+=("cline")
    [[ -d "$HOME/.kiro" ]] && detected+=("kiro")
    echo "${detected[@]}"
}

do_install() {
    local plat="$1"
    local dest_dir="${PLATFORM_PATHS[$plat]}"
    if [[ -z "$dest_dir" ]]; then
        error "Unknown platform: $plat"
        return 1
    fi
    local dest="$dest_dir/$SKILL_NAME"
    log "Installing to $plat → $dest"
    if $DRY_RUN; then
        warn "[DRY RUN] Would create: $dest → $SKILL_DIR"
        return 0
    fi
    mkdir -p "$dest_dir"
    if [[ -L "$dest" ]]; then
        warn "Removing existing symlink: $dest"
        rm "$dest"
    elif [[ -d "$dest" ]]; then
        warn "Destination already exists as directory: $dest (skipping)"
        return 0
    fi
    ln -s "$SKILL_DIR" "$dest"
    success "Installed $SKILL_NAME at $dest"
}

# ----- Main -----
echo ""
log "skill-manager-skill — Auto-Installer"
log "Skill source: $SKILL_DIR"
echo ""

if [[ -n "$PLATFORM" ]]; then
    do_install "$PLATFORM"
elif $INSTALL_ALL; then
    log "Installing to ALL detected platforms..."
    all_platforms=$(detect_platforms)
    if [[ -z "$all_platforms" ]]; then
        warn "No supported platforms detected."
    else
        for plat in $all_platforms; do
            do_install "$plat"
        done
    fi
else
    log "Auto-detecting platform..."
    detected=$(detect_platforms)
    if [[ -z "$detected" ]]; then
        warn "No supported platforms detected automatically."
        echo ""
        echo "Available platforms: ${!PLATFORM_PATHS[*]}"
        echo "Run: ./install.sh --platform <name>"
        exit 1
    fi
    # Install to the first (highest priority) detected platform
    first_plat=$(echo "$detected" | awk '{print $1}')
    do_install "$first_plat"
fi

echo ""
if ! $DRY_RUN; then
    success "Installation complete. Open a new session and type:"
    echo ""
    echo "  /skill-manager"
    echo ""
fi
