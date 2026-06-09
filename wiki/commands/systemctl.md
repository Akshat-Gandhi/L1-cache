# Systemctl

## One-liner
Manage systemd services — start, stop, enable, disable, and inspect them.

## Common Patterns
- `sudo systemctl start <service>` — start a service now
- `sudo systemctl stop <service>` — stop a service
- `sudo systemctl restart <service>` — restart
- `sudo systemctl enable <service>` — start on boot
- `sudo systemctl disable <service>` — remove from boot
- `systemctl status <service>` — view status and recent logs
- `journalctl -u <service> -f` — follow live logs for a service

## Errors & Fixes
- **Permission denied**: prefix with `sudo`
- **Unit not found**: service is not installed; `sudo apt install <package>`
- **Failed to start (exit-code=1)**: `journalctl -u <service> -n 50` for details
- **Active: failed**: check `systemctl status <service>` for ExecStart errors

## Related
[[commands/journalctl]] [[errors/permission-denied]] [[errors/command-not-found]]

## Session Notes
