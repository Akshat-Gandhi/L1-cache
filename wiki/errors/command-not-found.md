# Command Not Found

## One-liner
The shell cannot find the executable — either not installed or not in PATH.

## Common Patterns
- `which <cmd>` — check if command exists in PATH
- `sudo apt install <package>` / `sudo dnf install <package>` — install the package
- `export PATH="$PATH:/new/path"` — add directory to PATH for current session
- `echo $PATH` — inspect current PATH

## Errors & Fixes
- **netstat not found**: `sudo apt install net-tools` or use `ss -tulpn` instead
- **ifconfig not found**: `sudo apt install net-tools` or use `ip addr` instead
- **make not found**: `sudo apt install build-essential`
- **pip not found**: `sudo apt install python3-pip` or `python3 -m ensurepip`
- **node not found**: install via `nvm install --lts`
- **docker not found**: `curl -fsSL https://get.docker.com | sh`

## Related
[[concepts/path]] [[commands/which]]

## Session Notes
