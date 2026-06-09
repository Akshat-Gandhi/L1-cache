#!/usr/bin/env bash
# Terminal Wiki Bash hook
# Add to your ~/.bashrc:  source /path/to/L1-cache/src/shell/hook.bash

_TWIKI_LAST_CMD=""
_TWIKI_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_twiki_preexec() {
    _TWIKI_LAST_CMD="$BASH_COMMAND"
}
trap '_twiki_preexec' DEBUG

_twiki_precmd() {
    local exit_code=$?
    if [[ $exit_code -ne 0 && -n "$_TWIKI_LAST_CMD" ]]; then
        local cmd="$_TWIKI_LAST_CMD"
        _TWIKI_LAST_CMD=""
        (
            result=$(TERMINAL_WIKI_ROOT="${TERMINAL_WIKI_ROOT:-$HOME/.terminal-wiki}" \
                python3 "$_TWIKI_SCRIPT_DIR/../../cli.py" query \
                --command "$cmd" \
                --exit-code "$exit_code" \
                2>/dev/null)
            if [[ -n "$result" ]]; then
                echo ""
                echo -e "\033[2m[wiki]\033[0m $result"
            fi
        ) &
    fi
}

PROMPT_COMMAND="_twiki_precmd${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
