"""SSH tunnel management for VibeProxy."""

import os
import platform
import shutil
import socket
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, List, Tuple

from .config import ConfigManager


def find_ssh() -> Optional[str]:
    """Find the ssh executable on the system."""
    # Check if ssh is in PATH
    ssh_path = shutil.which("ssh")
    if ssh_path:
        return ssh_path

    # Windows-specific paths
    if platform.system() == "Windows":
        # OpenSSH in Windows
        windows_ssh = Path("C:/Windows/System32/OpenSSH/ssh.exe")
        if windows_ssh.exists():
            return str(windows_ssh)

        # Git for Windows ssh
        git_ssh_paths = [
            Path("C:/Program Files/Git/usr/bin/ssh.exe"),
            Path("C:/Program Files (x86)/Git/usr/bin/ssh.exe"),
            Path(os.environ.get("USERPROFILE", ""), "scoop/shims/ssh.exe"),
        ]
        for git_ssh in git_ssh_paths:
            if git_ssh.exists():
                return str(git_ssh)

    return None


class TunnelManager:
    """Manages SSH tunnel to Mac for VibeProxy access."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize tunnel manager."""
        self.config_manager = config_manager or ConfigManager()
        self._config = self.config_manager.load()

    @property
    def port(self) -> int:
        """Get the local tunnel port."""
        return self._config.local_port

    @property
    def mac_user(self) -> str:
        """Get Mac username."""
        return self._config.mac_user

    @property
    def mac_ip(self) -> str:
        """Get Mac IP address."""
        return self._config.mac_ip

    def is_running(self) -> bool:
        """Check if the tunnel port is listening."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex(("localhost", self.port)) == 0
        except Exception:
            return False

    def get_status(self) -> tuple[bool, str]:
        """Get tunnel status with message."""
        if self.is_running():
            return True, f"Connected (port {self.port})"
        return False, f"Not connected (port {self.port})"

    def start(self) -> tuple[bool, str]:
        """Start SSH tunnel using sshpass or ssh-agent.

        Returns (success, message) tuple.
        """
        if self.is_running():
            return True, "Tunnel already running"

        # Find ssh executable
        ssh_exe = find_ssh()
        if not ssh_exe:
            return False, "SSH not found - install OpenSSH or Git for Windows"

        # Build SSH command
        ssh_target = f"{self.mac_user}@{self.mac_ip}"
        local_forward = f"{self.port}:localhost:{self._config.remote_port}"
        is_windows = platform.system() == "Windows"

        # Check if sshpass is available for password auth
        password = self._config.ssh_password

        try:
            if password and not is_windows:
                # Use sshpass for password auth (Unix only)
                cmd = [
                    "sshpass", "-p", password,
                    ssh_exe, "-fN",
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    "-L", local_forward,
                    ssh_target,
                ]
                # Start tunnel in background
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            elif is_windows:
                # Windows: -f doesn't work, use Popen to run in background
                cmd = [
                    ssh_exe, "-N",
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "BatchMode=yes",
                    "-L", local_forward,
                    ssh_target,
                ]
                # Start as background process (no console window)
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )

                # Wait briefly for connection
                import time
                time.sleep(2)

                # Check if process died immediately
                if process.poll() is not None:
                    _, stderr = process.communicate()
                    error = stderr.decode().strip() if stderr else "Unknown error"
                    return False, f"SSH failed: {error}"

                if self.is_running():
                    return True, f"Tunnel started on port {self.port}"
                return False, "SSH process started but port not listening"
            else:
                # Unix: use key-based auth with -f for background
                cmd = [
                    ssh_exe, "-fN",
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "BatchMode=yes",
                    "-L", local_forward,
                    ssh_target,
                ]
                # Start tunnel in background
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

            # For non-Windows path (sshpass or Unix key-based)
            if not is_windows:
                if result.returncode == 0:
                    # Verify it's actually running
                    import time
                    time.sleep(0.5)
                    if self.is_running():
                        return True, f"Tunnel started on port {self.port}"
                    return False, "Tunnel process started but port not listening"
                else:
                    error = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                    return False, f"SSH failed: {error}"

            return False, "Unexpected code path"

        except subprocess.TimeoutExpired:
            return False, "SSH connection timeout"
        except FileNotFoundError as e:
            if "sshpass" in str(e):
                return False, "sshpass not found - install it or use key-based auth"
            return False, f"Command not found: {e}"
        except Exception as e:
            return False, str(e)

    def stop(self) -> tuple[bool, str]:
        """Stop SSH tunnel by killing the process."""
        if not self.is_running():
            return True, "Tunnel not running"

        try:
            # Find and kill SSH processes for our tunnel
            # On Windows, use tasklist/taskkill; on Unix, use pkill
            import platform

            if platform.system() == "Windows":
                # Find SSH processes listening on our port
                # This is tricky on Windows - just report that manual stop is needed
                return False, "Manual stop required: kill SSH process or close terminal"
            else:
                # Unix-like: pkill matching our tunnel
                cmd = ["pkill", "-f", f"ssh.*{self.port}:localhost"]
                subprocess.run(cmd, capture_output=True)

                import time
                time.sleep(0.5)
                if not self.is_running():
                    return True, "Tunnel stopped"
                return False, "Failed to stop tunnel"

        except Exception as e:
            return False, str(e)

    def start_in_terminal(self) -> str:
        """Generate command for user to run manually in terminal."""
        ssh_target = f"{self.mac_user}@{self.mac_ip}"
        local_forward = f"{self.port}:localhost:{self._config.remote_port}"

        return f"ssh -N -L {local_forward} {ssh_target}"

    def start_in_window(self) -> tuple[bool, str]:
        """Launch SSH tunnel in a new terminal window using the PowerShell script.

        This method uses the existing ssh-tunnel-vibeproxy.ps1 script which handles:
        - Password storage and auto-login
        - Auto-reconnect on connection drop
        - Nice status display
        - plink/sshpass password automation

        Returns (success, message) tuple.
        """
        if self.is_running():
            return True, "Tunnel already running"

        # Find the PowerShell script
        script_path = Path(__file__).parent.parent / "ssh-tunnel-vibeproxy.ps1"
        if not script_path.exists():
            return False, f"Script not found: {script_path}"

        try:
            # Launch in new PowerShell window using 'start' command
            # -NoExit keeps window open, -ExecutionPolicy Bypass allows script execution
            cmd = [
                "cmd.exe", "/c", "start",
                "VibeProxy SSH Tunnel",  # Window title
                "powershell", "-NoExit", "-ExecutionPolicy", "Bypass",
                "-File", str(script_path)
            ]

            # Launch the process (detached, will survive parent exit)
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=str(script_path.parent),
            )

            return True, f"Tunnel launcher started in new window. Check the terminal for status."

        except Exception as e:
            return False, f"Failed to launch tunnel: {e}"

    def ensure_password_saved(self) -> bool:
        """Check if SSH password is saved in config. Prompt if missing.

        Returns True if password is saved (or was just saved), False if user cancelled.
        """
        if self._config.ssh_password and self._config.ssh_password.strip():
            return True

        # Password missing - this is a TUI, can't prompt interactively
        # Return False to indicate password needs to be entered via the PowerShell script
        return False

    def scan_network(self, progress_callback=None) -> List[Tuple[str, str]]:
        """Scan local network for devices with SSH (22) or VibeProxy (8317) open.
        
        Returns list of (ip, label) tuples.
        """
        # Get local IP and subnet
        try:
            # Connect to a public IP to get the interface used for routing
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            local_ip = "192.168.50.1" # Fallback

        subnet = ".".join(local_ip.split(".")[:3])
        found_devices = []
        lock = threading.Lock()
        
        def check_host(ip):
            try:
                # Check VibeProxy port first (most specific)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.2)
                    if s.connect_ex((ip, 8317)) == 0:
                        with lock:
                            found_devices.append((ip, "VibeProxy Host (8317)"))
                        return

                # Check SSH port
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.2)
                    if s.connect_ex((ip, 22)) == 0:
                        with lock:
                            found_devices.append((ip, "SSH Host (22)"))
            except:
                pass

        # Scan 1-254
        ips = [f"{subnet}.{i}" for i in range(1, 255)]
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            list(executor.map(check_host, ips))
            
        return sorted(found_devices)
