# Permission Denied

## One-liner
The current user lacks read, write, or execute permission on the target file, directory, or socket.

## Common Patterns
- `sudo <command>` — re-run as root when elevated privileges are needed
- `chmod +x ./script.sh` — add execute bit to a script
- `chown $USER:$USER /path/to/dir` — take ownership of a directory
- `ls -la /path` — inspect current permissions and owner

## Errors & Fixes
- **Permission denied on systemctl/service**: `sudo systemctl start <service>`
- **Permission denied on apt/dpkg lock**: `sudo apt install <package>`
- **Permission denied on file execute**: `chmod +x ./file && ./file`
- **Permission denied on directory write**: `sudo chown -R $USER:$USER /target/dir`
- **Permission denied on Docker socket**: `sudo usermod -aG docker $USER` then log out/in
- **Permission denied on npm global install**: use `nvm` or `sudo npm install -g <pkg>`

## Related
[[commands/chmod]] [[commands/chown]] [[concepts/file-permissions]]

## Session Notes
