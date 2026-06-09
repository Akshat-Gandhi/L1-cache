# Chmod

## One-liner
Change file or directory permissions using symbolic or octal notation.

## Common Patterns
- `chmod +x script.sh` — add execute permission for all
- `chmod 755 script.sh` — rwxr-xr-x (owner full, others read+exec)
- `chmod 644 file.txt` — rw-r--r-- (owner read+write, others read)
- `chmod -R 755 /dir` — recursive permission change
- `chmod u+rw,g+r,o-rwx file` — symbolic notation

## Errors & Fixes
- **Operation not permitted**: you don't own the file; use `sudo chmod ...`
- **Cannot access: No such file**: `ls -la` to verify path

## Related
[[commands/chown]] [[concepts/file-permissions]] [[errors/permission-denied]]

## Session Notes
