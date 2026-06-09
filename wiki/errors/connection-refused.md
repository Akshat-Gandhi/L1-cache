# Connection Refused

## One-liner
The target host is reachable but nothing is listening on the requested port.

## Common Patterns
- `ss -tlnp | grep <port>` — verify what is listening
- `curl -v http://localhost:<port>` — test connectivity verbosely
- `systemctl status <service>` — check if the service is running

## Errors & Fixes
- **curl: (7) Failed to connect**: service is not running; `systemctl start <service>`
- **Connection refused on localhost**: nothing bound to that port; start your server
- **SSH connection refused port 22**: `sudo systemctl start sshd`
- **Postgres connection refused**: `sudo systemctl start postgresql`

## Related
[[errors/port-already-in-use]] [[commands/ss]] [[commands/systemctl]]

## Session Notes
