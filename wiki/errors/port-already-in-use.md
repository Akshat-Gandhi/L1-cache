# Port Already In Use

## One-liner
Another process is already bound to the requested port.

## Common Patterns
- `lsof -ti:<port> | xargs kill -9` — find and kill process on port
- `ss -tlnp | grep <port>` — list what is listening on a port
- `fuser -k <port>/tcp` — kill process using the port (older systems)

## Errors & Fixes
- **EADDRINUSE / Address already in use**: `lsof -ti:PORT | xargs kill -9`
- **OSError: [Errno 98]**: same as above
- **Nginx: bind() to 0.0.0.0:80 failed**: `sudo lsof -ti:80 | xargs sudo kill -9`
- **Node.js EADDRINUSE**: `npx kill-port <port>` or `lsof -ti:<port> | xargs kill`

## Related
[[commands/lsof]] [[commands/ss]] [[errors/connection-refused]]

## Session Notes
