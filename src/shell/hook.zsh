#!/usr/bin/env zsh
# Terminal Wiki ZSH hook
# Source this in your ~/.zshrc:  source /path/to/L1-cache/src/shell/hook.zsh

_TWIKI_LAST_CMD=""
_TWIKI_LAST_EXIT=0

# Capture command before it runs
preexec() {
    _TWIKI_LAST_CMD="$1"
}

# Check exit code after command finishes
precmd() {
    local exit_code=$?
    _TWIKI_LAST_EXIT=$exit_code

    # Only trigger on failure and if we have a command
    if [[ $exit_code -ne 0 && -n "$_TWIKI_LAST_CMD" ]]; then
        _twiki_suggest "$_TWIKI_LAST_CMD" "$exit_code"
    fi
    _TWIKI_LAST_CMD=""
}

_twiki_suggest() {
    local cmd="$1"
    local code="$2"

    # Run async to avoid blocking the prompt
    (
        local result
        result=$(TERMINAL_WIKI_ROOT="${TERMINAL_WIKI_ROOT:-$HOME/.terminal-wiki}" \
            python3 "$(dirname "$0")/../../cli.py" query \
            --command "$cmd" \
            --exit-code "$code" \
            2>/dev/null)

        if [[ -n "$result" ]]; then
            echo ""
            echo "\033[2m[wiki]\033[0m $result"
        fi
    ) &
}

# Tab-to-accept last suggestion (stores last suggestion in file for pickup)
_twiki_accept() {
    local suggestion_file="${TMPDIR:-/tmp}/.twiki_last_suggestion"
    if [[ -f "$suggestion_file" ]]; then
        BUFFER=$(cat "$suggestion_file")
        rm -f "$suggestion_file"
        zle end-of-line
    fi
}
zle -N _twiki_accept
# Uncomment to bind Tab to accept suggestions (may conflict with completion):
# bindkey '\t' _twiki_accept
