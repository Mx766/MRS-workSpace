#!/usr/bin/env bash
# install.sh — install proofread-docx skill to any AgentSkills-compatible runtime
# Usage: bash install.sh [--runtime claude|codex|copilot|gemini|all]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/proofread-docx"

# Detect available runtimes
detect_runtimes() {
    local runtimes=()
    [ -d "$HOME/.claude/skills" ] && runtimes+=(claude)
    [ -d "$HOME/.codex/skills" ] && runtimes+=(codex)
    [ -d "$HOME/.gemini/skills" ] && runtimes+=(gemini)
    [ -d "$HOME/.agents/skills" ] && runtimes+=(agents)
    echo "${runtimes[@]}"
}

install_to() {
    local runtime="$1"
    local target
    case "$runtime" in
        claude)  target="$HOME/.claude/skills/proofread-docx" ;;
        codex)   target="$HOME/.codex/skills/proofread-docx" ;;
        copilot) target="$HOME/.agents/skills/proofread-docx" ;;
        gemini)  target="$HOME/.gemini/skills/proofread-docx" ;;
        agents)  target="$HOME/.agents/skills/proofread-docx" ;;
        *) echo "Unknown runtime: $runtime"; return 1 ;;
    esac

    if [ -e "$target" ] || [ -L "$target" ]; then
        echo "  [$runtime] Already exists at $target — skipping"
        return 0
    fi

    # Prefer symlink if we're already in a permanent location
    if [[ "$SKILL_DIR" == /opt/* ]] || [[ "$SKILL_DIR" == "$HOME"/* ]] || [[ "$SKILL_DIR" == /mnt/* ]]; then
        ln -s "$SKILL_DIR" "$target"
        echo "  [$runtime] Symlinked → $target"
    else
        cp -r "$SKILL_DIR" "$target"
        echo "  [$runtime] Copied → $target"
    fi
}

print_deps() {
    echo ""
    echo "Python dependencies required:"
    echo "  pip install python-docx openpyxl lxml PyMuPDF"
    echo ""
}

main() {
    echo "=== proofread-docx skill installer ==="
    echo ""

    # Determine install targets
    if [ $# -gt 0 ] && [ "$1" != "--runtime" ]; then
        echo "Usage: bash install.sh [--runtime claude|codex|copilot|gemini|all]"
        exit 1
    fi

    RUNTIME="${2:-}"
    if [ -z "$RUNTIME" ]; then
        RUNS=($(detect_runtimes))
        if [ ${#RUNS[@]} -eq 0 ]; then
            echo "No supported Agent runtimes detected."
            echo "Create one of: ~/.claude/skills/  ~/.codex/skills/  ~/.gemini/skills/  ~/.agents/skills/"
            echo "Then re-run this script."
            print_deps
            exit 1
        fi
        echo "Detected runtimes: ${RUNS[*]}"
    elif [ "$RUNTIME" = "all" ]; then
        RUNS=(claude codex copilot gemini agents)
    else
        RUNS=("$RUNTIME")
    fi

    for rt in "${RUNS[@]}"; do
        install_to "$rt"
    done

    echo ""
    echo "✓ Install complete. Open a new Agent session and type:"
    echo "  '帮我校对翻译文件'"
    echo ""
    echo "If the Agent follows the Phase 0→7 pipeline, the skill is active."
    print_deps
}

main "$@"
