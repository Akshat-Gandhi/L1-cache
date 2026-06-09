"""
Ground-truth test cases for benchmarking L1 cache vs RAG.
Each case has an error, the command that caused it, and ground-truth fix keywords.
"""
from dataclasses import dataclass


@dataclass
class TestCase:
    id: str
    command: str
    stderr: str
    category: str
    # A fix is "correct" if any of these strings appear in the response
    ground_truth_keywords: list[str]
    canonical_fix: str  # the most common correct fix, for display


TEST_CASES: list[TestCase] = [
    TestCase("tc001", "systemctl start nginx",
             "Failed to start nginx.service: Permission denied",
             "permissions", ["sudo", "root"], "sudo systemctl start nginx"),

    TestCase("tc002", "python -m http.server 8080",
             "OSError: [Errno 98] Address already in use",
             "networking", ["lsof", "fuser", "kill"], "lsof -ti:8080 | xargs kill -9"),

    TestCase("tc003", "apt install curl",
             "E: Could not open lock file /var/lib/dpkg/lock-frontend - open (13: Permission denied)",
             "permissions", ["sudo"], "sudo apt install curl"),

    TestCase("tc004", "ssh user@server",
             "Permission denied (publickey)",
             "ssh", ["ssh-add", "-i", "identity", "key"], "ssh -i ~/.ssh/id_rsa user@server"),

    TestCase("tc005", "chmod +x script.sh",
             "chmod: cannot access 'script.sh': No such file or directory",
             "files", ["ls", "pwd", "path", "exist"], "ls -la to verify file exists"),

    TestCase("tc006", "git push origin main",
             "error: failed to push some refs to 'origin'\nhint: Updates were rejected",
             "git", ["pull", "fetch", "rebase", "--force"], "git pull --rebase origin main"),

    TestCase("tc007", "npm install",
             "EACCES: permission denied, mkdir '/usr/local/lib/node_modules'",
             "nodejs", ["sudo", "nvm", "prefix", "--prefix"], "nvm use or sudo npm install"),

    TestCase("tc008", "docker run ubuntu",
             "permission denied while trying to connect to the Docker daemon socket",
             "docker", ["sudo", "usermod", "docker", "group"], "sudo usermod -aG docker $USER"),

    TestCase("tc009", "./myapp",
             "bash: ./myapp: Permission denied",
             "permissions", ["chmod", "+x", "execute"], "chmod +x ./myapp"),

    TestCase("tc010", "kill 99999",
             "bash: kill: (99999) - No such process",
             "processes", ["ps", "pgrep", "pidof"], "ps aux | grep process_name"),

    TestCase("tc011", "df -h",
             "df: /proc/...: No such file or directory",
             "filesystem", ["mount", "proc", "tmpfs"], "mount -t proc proc /proc"),

    TestCase("tc012", "curl http://localhost:3000",
             "curl: (7) Failed to connect to localhost port 3000: Connection refused",
             "networking", ["ss", "netstat", "lsof", "listening"], "ss -tlnp | grep 3000"),

    TestCase("tc013", "cp -r /src /dst",
             "cp: cannot create directory '/dst': Permission denied",
             "permissions", ["sudo", "chown", "mkdir"], "sudo cp -r /src /dst"),

    TestCase("tc014", "pip install requests",
             "error: externally-managed-environment",
             "python", ["venv", "--break-system", "virtualenv", "--user"], "python -m venv venv && source venv/bin/activate"),

    TestCase("tc015", "mount /dev/sdb1 /mnt",
             "mount: /mnt: special device /dev/sdb1 does not exist",
             "filesystem", ["lsblk", "fdisk", "blkid"], "lsblk to find correct device name"),

    TestCase("tc016", "service apache2 restart",
             "Failed to restart apache2.service: Unit not found",
             "services", ["systemctl", "install", "apt"], "sudo apt install apache2"),

    TestCase("tc017", "tar -xzf archive.tar.gz",
             "tar: archive.tar.gz: Cannot open: No such file or directory",
             "files", ["ls", "pwd", "path"], "ls -la to verify archive path"),

    TestCase("tc018", "mysql -u root -p",
             "ERROR 1698 (28000): Access denied for user 'root'@'localhost'",
             "mysql", ["sudo", "auth_socket", "ALTER USER"], "sudo mysql -u root"),

    TestCase("tc019", "ping google.com",
             "ping: google.com: Temporary failure in name resolution",
             "networking", ["resolv.conf", "dns", "nameserver", "systemd-resolve"], "echo 'nameserver 8.8.8.8' | sudo tee /etc/resolv.conf"),

    TestCase("tc020", "python3 script.py",
             "ModuleNotFoundError: No module named 'requests'",
             "python", ["pip", "install", "pip3"], "pip install requests"),

    TestCase("tc021", "useradd newuser",
             "useradd: Permission denied.\nuseradd: cannot lock /etc/passwd; try again later.",
             "users", ["sudo"], "sudo useradd newuser"),

    TestCase("tc022", "crontab -e",
             "/usr/bin/editor: not found",
             "cron", ["EDITOR", "VISUAL", "nano", "vim"], "EDITOR=nano crontab -e"),

    TestCase("tc023", "find / -name '*.log'",
             "find: '/proc/tty/driver': Permission denied",
             "find", ["2>/dev/null", "sudo", "-readable"], "find / -name '*.log' 2>/dev/null"),

    TestCase("tc024", "git clone git@github.com:user/repo.git",
             "git@github.com: Permission denied (publickey)",
             "git", ["ssh-add", "ssh-keygen", "key"], "ssh-add ~/.ssh/id_rsa"),

    TestCase("tc025", "netstat -tulpn",
             "bash: netstat: command not found",
             "networking", ["ss", "net-tools", "apt install"], "ss -tulpn  # or: sudo apt install net-tools"),
]


def get_test_case(tc_id: str) -> TestCase | None:
    return next((t for t in TEST_CASES if t.id == tc_id), None)


def score_response(response: str, case: TestCase) -> dict:
    """Returns partial and exact match scores."""
    resp_lower = response.lower()
    matched = [kw for kw in case.ground_truth_keywords if kw.lower() in resp_lower]
    partial = len(matched) / len(case.ground_truth_keywords)
    exact = 1.0 if partial == 1.0 else 0.0
    return {
        "partial": partial,
        "exact": exact,
        "matched_keywords": matched,
        "total_keywords": len(case.ground_truth_keywords),
    }
