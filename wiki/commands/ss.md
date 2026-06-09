# Ss

## One-liner
Socket statistics — modern replacement for netstat; shows listening ports and connections.

## Common Patterns
- `ss -tlnp` — TCP listening ports with process names
- `ss -tulnp` — TCP + UDP listening ports
- `ss -tlnp | grep <port>` — check if a specific port is in use
- `ss -tp` — established TCP connections with process info
- `ss -s` — summary statistics

## Errors & Fixes
- **ss not found**: install `iproute2` — `sudo apt install iproute2`
- **No process shown** (empty PROCESS column): run with `sudo` for full info

## Related
[[commands/lsof]] [[errors/port-already-in-use]] [[errors/connection-refused]]

## Session Notes
