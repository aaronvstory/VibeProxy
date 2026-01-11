"""SSH tunnel management for VibeProxy."""

import socket
import subprocess
from pathlib import Path
from typing import Optional

from .config import ConfigManager


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

        # Build SSH command
        ssh_target = f"{self.mac_user}@{self.mac_ip}"
        local_forward = f"{self.port}:localhost:{self._config.remote_port}"

        # Check if sshpass is available for password auth
        password = self._config.ssh_password

        try:
            if password:
                # Use sshpass for password auth
                cmd = [
                    "sshpass", "-p", password,
                    "ssh", "-fN",
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    "-L", local_forward,
                    ssh_target,
                ]
            else:
                # Use key-based auth (assumes ssh-agent or key file)
                cmd = [
                    "ssh", "-fN",
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
