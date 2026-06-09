#!/usr/bin/env bash
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_ROOT="${TERMINAL_WIKI_ROOT:-$HOME/.terminal-wiki}"

echo "==> Terminal Wiki installer"
echo "    Repo:      $REPO_DIR"
echo "    Wiki root: $WIKI_ROOT"
echo ""

# Python deps
echo "==> Installing Python dependencies..."
pip install -e "$REPO_DIR" --quiet

# Create wiki root symlink or copy
if [[ ! -d "$WIKI_ROOT" ]]; then
    echo "==> Linking wiki root to $WIKI_ROOT"
    ln -sf "$REPO_DIR" "$WIKI_ROOT"
fi

# Shell hook
detect_shell() {
    basename "$SHELL"
}

SHELL_NAME=$(detect_shell)
echo "==> Detected shell: $SHELL_NAME"

if [[ "$SHELL_NAME" == "zsh" ]]; then
    RCFILE="$HOME/.zshrc"
    HOOK_LINE="source \"$REPO_DIR/src/shell/hook.zsh\""
elif [[ "$SHELL_NAME" == "bash" ]]; then
    RCFILE="$HOME/.bashrc"
    HOOK_LINE="source \"$REPO_DIR/src/shell/hook.bash\""
else
    echo "    Unknown shell — manually source src/shell/hook.zsh or hook.bash"
    exit 0
fi

if grep -qF "terminal-wiki" "$RCFILE" 2>/dev/null; then
    echo "==> Shell hook already present in $RCFILE"
else
    echo "" >> "$RCFILE"
    echo "# terminal-wiki L1 cache hook" >> "$RCFILE"
    echo "$HOOK_LINE" >> "$RCFILE"
    echo "==> Added hook to $RCFILE"
fi

echo ""
echo "Done. Start a new shell session or run: source $RCFILE"
echo ""
echo "Quick test:"
echo "  ANTHROPIC_API_KEY=<key> python $REPO_DIR/cli.py query \\"
echo "    --command 'systemctl start nginx' \\"
echo "    --stderr 'Permission denied'"
