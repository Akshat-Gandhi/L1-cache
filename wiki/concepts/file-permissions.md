# File Permissions

## One-liner
Linux file permissions control read (r=4), write (w=2), and execute (x=1) access per owner/group/other.

## Common Patterns
- `ls -la` — view permissions in long format: `-rwxr-xr-x 1 user group size date name`
- `stat file` — numeric permissions + full metadata
- `chmod 755 file` — common: owner full (7=rwx), group/other read+exec (5=r-x)
- `chmod 644 file` — common: owner read+write (6=rw-), group/other read (4=r--)
- `umask 022` — default new file permission mask

## Errors & Fixes
- **Permission denied on execution**: `chmod +x ./file`
- **Permission denied on directory**: you need execute bit on directory to enter it
- **Sticky bit on /tmp**: files can only be deleted by owner — this is intentional

## Related
[[commands/chmod]] [[commands/chown]] [[errors/permission-denied]]

## Session Notes
