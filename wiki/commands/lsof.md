# Lsof

## One-liner
List open files and the processes that opened them — including network sockets.

## Common Patterns
- `lsof -i :<port>` — show process using a port
- `lsof -ti:<port> | xargs kill -9` — kill process on a port
- `lsof -p <pid>` — list all files opened by a process
- `lsof +D /path` — list all processes with files open in a directory
- `lsof -u <user>` — list all open files by a user

## Errors & Fixes
- **lsof not found**: `sudo apt install lsof`
- **Permission denied on some entries**: run with `sudo` for complete results

## Related
[[commands/ss]] [[errors/port-already-in-use]]

## Session Notes
