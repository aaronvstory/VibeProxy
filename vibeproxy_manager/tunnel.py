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


def find_plink() -> Optional[str]:
    """Find PuTTY's plink executable (supports password auth on Windows)."""
    if platform.system() != "Windows":
        return None

    # Check if plink is in PATH
    plink_path = shutil.which("plink")
    if plink_path:
        return plink_path

    # Common PuTTY installation paths
    plink_locations = [
        Path("C:/Program Files/PuTTY/plink.exe"),
        Path("C:/Program Files (x86)/PuTTY/plink.exe"),
        Path(os.environ.get("ProgramFiles", "C:/Program Files"), "PuTTY/plink.exe"),
        Path(
            os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"),
            "PuTTY/plink.exe",
        ),
    ]

    for plink_loc in plink_locations:
        if plink_loc.exists():
            return str(plink_loc)

    return None


def install_putty() -> tuple[bool, str]:
    """Automatically install PuTTY using winget if not present.

    Returns (success, message) tuple.
    """
    if platform.system() != "Windows":
        return False, "PuTTY installation only supported on Windows"

    print("📦 PuTTY not found - attempting automatic installation...")
    print("   (Required for password-based SSH authentication)")
    print()

    # Check if winget is available
    try:
        result = subprocess.run(
            ["winget", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            raise FileNotFoundError("winget not available")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, (
            "winget not found - cannot auto-install PuTTY\n"
            "Please install manually:\n"
            "  1. Download from: https://www.putty.org/\n"
            "  2. Or install via chocolatey: choco install putty"
        )

    # Install PuTTY using winget
    try:
        print("🔄 Installing PuTTY via winget...")
        result = subprocess.run(
            [
                "winget",
                "install",
                "PuTTY.PuTTY",
                "--accept-source-agreements",
                "--accept-package-agreements",
                "--silent",
            ],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutes timeout for download+install
        )

        if result.returncode == 0:
            print("✅ PuTTY installed successfully!")
            print()

            # Wait a moment for installation to complete
            import time

            time.sleep(2)

            # Verify plink is now available
            plink_path = find_plink()
            if plink_path:
                return True, f"PuTTY installed at: {plink_path}"
            else:
                return False, (
                    "PuTTY installed but plink not found in expected locations.\n"
                    "Please restart your terminal or add PuTTY to PATH"
                )
        else:
            error = result.stderr.strip() if result.stderr else "Unknown error"
            return False, f"winget install failed: {error}"

    except subprocess.TimeoutExpired:
        return False, "PuTTY installation timed out (network issue?)"
    except Exception as e:
        return False, f"Installation error: {e}"


class TunnelManager:
    """Manages SSH tunnel to Mac for VibeProxy access."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize tunnel manager."""
        self.config_manager = config_manager or ConfigManager()
        self._config = self.config_manager.load()
        self._tunnel_pid: Optional[int] = None  # Track SSH process PID
        self._tunnel_process: Optional[subprocess.Popen] = None  # Track process object

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
        """Check if SSH tunnel is actually running.

        Multi-layer verification:
        1. Check if tracked PID exists and is alive
        2. Check if port is accepting connections
        3. Both must be true for "running" status
        """
        # Layer 1: PID check (if we have one)
        if self._tunnel_pid is not None:
            process_alive = False

            # Check if process exists (Windows-compatible)
            if self._tunnel_process is not None:
                # We have the process object - use poll()
                process_alive = self._tunnel_process.poll() is None
            else:
                # No process object (detached window) - use platform-specific check
                try:
                    if platform.system() == "Windows":
                        # Windows: use tasklist to check if PID exists
                        result = subprocess.run(
                            ["tasklist", "/FI", f"PID eq {self._tunnel_pid}", "/NH"],
                            capture_output=True,
                            text=True,
                            timeout=2,
                        )
                        # If PID exists, tasklist will show it; if not, shows "No tasks"
                        process_alive = "No tasks" not in result.stdout
                    else:
                        # Unix: use kill with signal 0 to check existence
                        os.kill(self._tunnel_pid, 0)
                        process_alive = True
                except (OSError, ProcessLookupError, subprocess.TimeoutExpired):
                    process_alive = False

            if not process_alive:
                # Process is dead - clear tracking info
                self._tunnel_pid = None
                self._tunnel_process = None
                return False

        # Layer 2: Port check
        port_open = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                port_open = s.connect_ex(("localhost", self.port)) == 0
        except Exception:
            port_open = False

        # Both checks must pass if we're tracking a PID
        if self._tunnel_pid is not None:
            # We have PID - require both PID and port
            return port_open  # PID check already passed above
        else:
            # No PID (old tunnel or external) - trust port check only
            return port_open

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
                    "sshpass",
                    "-p",
                    password,
                    ssh_exe,
                    "-fN",
                    "-o",
                    "StrictHostKeyChecking=no",
                    "-o",
                    "UserKnownHostsFile=/dev/null",
                    "-L",
                    local_forward,
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
                # Windows: Try plink (PuTTY) first for password auth
                plink_exe = find_plink()

                if plink_exe and password:
                    # Use plink with password parameter (PuTTY syntax, not OpenSSH)
                    cmd = [
                        plink_exe,
                        "-ssh",  # Use SSH protocol
                        "-batch",  # Disable interactive prompts
                        "-hostkey",
                        "SHA256:5XgC3h/+waae885A5/IORHon1HPf3QLQXbF84V+mj0Y",  # Mac host key
                        "-L",
                        local_forward,  # Local port forwarding
                        "-pw",
                        password,  # Password authentication
                        ssh_target,  # user@host
                        "-N",  # No command, just forward ports
                    ]
                elif password:
                    # No plink, but have password - try to install PuTTY
                    print("\n⚠️  Password authentication requires PuTTY")
                    success, message = install_putty()

                    if success:
                        # Installation succeeded - retry with plink
                        plink_exe = find_plink()
                        if plink_exe:
                            cmd = [
                                plink_exe,
                                "-ssh",
                                "-batch",
                                "-hostkey",
                                "SHA256:5XgC3h/+waae885A5/IORHon1HPf3QLQXbF84V+mj0Y",
                                "-L",
                                local_forward,
                                "-pw",
                                password,
                                ssh_target,
                                "-N",
                            ]
                        else:
                            return False, "PuTTY installed but plink not found"
                    else:
                        # Installation failed - return error with instructions
                        return False, (
                            f"PuTTY installation failed: {message}\n\n"
                            "Alternatives:\n"
                            "  1. Install manually from https://www.putty.org/\n"
                            "  2. Set up SSH keys for password-less auth"
                        )
                else:
                    # No password - use key-based auth with OpenSSH
                    cmd = [
                        ssh_exe,
                        "-N",
                        "-o",
                        "StrictHostKeyChecking=no",
                        "-o",
                        "BatchMode=yes",
                        "-L",
                        local_forward,
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

                # Save process tracking info
                self._tunnel_process = process
                self._tunnel_pid = process.pid

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
                    ssh_exe,
                    "-fN",
                    "-o",
                    "StrictHostKeyChecking=no",
                    "-o",
                    "BatchMode=yes",
                    "-L",
                    local_forward,
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
                    error = (
                        result.stderr.strip()
                        or result.stdout.strip()
                        or "Unknown error"
                    )
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

    def force_reset(self) -> tuple[bool, str]:
        """Force reset tunnel state (for zombie states).

        Clears tracked PID and attempts to kill any process on port.
        Use when tunnel appears stuck in "already running" state.

        Returns (success, message) tuple.
        """
        # Clear tracked state
        self._tunnel_pid = None
        self._tunnel_process = None

        # Try to kill process on port (Windows-specific)
        if platform.system() == "Windows":
            try:
                # Find process using port
                result = subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        f"(Get-NetTCPConnection -LocalPort {self.port} -ErrorAction SilentlyContinue).OwningProcess",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    pid = int(result.stdout.strip())
                    # Kill the process
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)], check=False, timeout=5
                    )
                    return True, f"Killed process {pid} on port {self.port}"
            except subprocess.TimeoutExpired:
                return True, "State reset (timeout finding process)"
            except Exception as e:
                return True, f"State reset (error: {e})"

        return True, "State reset (no process found to kill)"

    def start_in_terminal(self) -> str:
        """Generate command for user to run manually in terminal."""
        ssh_target = f"{self.mac_user}@{self.mac_ip}"
        local_forward = f"{self.port}:localhost:{self._config.remote_port}"

        return f"ssh -N -L {local_forward} {ssh_target}"

    def start_in_window(self) -> tuple[bool, str]:
        """Launch SSH tunnel in a new terminal window using the intelligent Python launcher.

        This method uses the new ssh-tunnel-intelligent.py script which provides:
        - Intelligent error detection and classification
        - Auto-discovery of Mac when IP changes
        - Auto-config update when Mac found at new IP
        - Smart retry logic (doesn't loop forever)
        - Clear, actionable error messages
        - Auto-reconnect on connection drop

        Returns (success, message) tuple.
        """
        if self.is_running():
            return True, "Tunnel already running"

        # Find the Python launcher script
        script_path = Path(__file__).parent.parent / "ssh-tunnel-intelligent.py"
        if not script_path.exists():
            return False, f"Intelligent launcher not found: {script_path}"

        try:
            # Launch Python script in new PowerShell window
            # Using CREATE_NEW_CONSOLE directly on PowerShell avoids cmd.exe /c start
            # parsing issues with window titles containing spaces/parentheses
            cmd = [
                "powershell",
                "-NoExit",
                "-Command",
                f"$host.UI.RawUI.WindowTitle = 'VibeProxy SSH Tunnel'; python '{script_path}' --monitor",
            ]

            # Launch the process in a new console window
            process = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=str(script_path.parent),
            )

            # Save PID for tracking (process runs in separate console)
            self._tunnel_pid = process.pid

            return (
                True,
                "Intelligent tunnel launcher started in new window. Check the terminal for status.",
            )

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
            local_ip = "192.168.50.1"  # Fallback

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

    def classify_ssh_error(self, error_message: str) -> tuple[str, str]:
        """Classify SSH connection error to determine root cause.

        Returns (error_type, user_message) tuple.
        Error types: IP_CHANGED, SSH_DOWN, AUTH_FAILED, NETWORK_DOWN, UNKNOWN
        """
        error_lower = error_message.lower()

        # Host unreachable / IP changed
        if any(
            phrase in error_lower
            for phrase in [
                "connection timed out",
                "no route to host",
                "host unreachable",
                "network is unreachable",
            ]
        ):
            return (
                "IP_CHANGED",
                "Mac not responding - IP may have changed or Mac is offline",
            )

        # SSH service not running
        if "connection refused" in error_lower:
            return "SSH_DOWN", "Mac is online but SSH (Remote Login) is disabled"

        # Authentication failed
        if any(
            phrase in error_lower
            for phrase in [
                "permission denied",
                "authentication failed",
                "host key verification failed",
            ]
        ):
            return "AUTH_FAILED", "Authentication failed - check password or SSH keys"

        # General network issues
        if "network error" in error_lower or "unreachable" in error_lower:
            return "NETWORK_DOWN", "Network connectivity issue - check WiFi/Ethernet"

        return "UNKNOWN", f"Connection failed: {error_message}"

    def try_discover_mac(self) -> Optional[Tuple[str, str]]:
        """Try to find Mac on network using SSH port scanning.

        Returns (ip, label) if found, None otherwise.
        """
        print(f"🔍 Scanning network for Mac (looking for SSH on port 22)...")

        devices = self.scan_network()

        if not devices:
            return None

        # Filter to SSH-capable devices (exclude VibeProxy-only)
        ssh_devices = [
            (ip, label) for ip, label in devices if "SSH" in label or "8317" in label
        ]

        if len(ssh_devices) == 1:
            # Found exactly one SSH device - assume it's the Mac
            ip, label = ssh_devices[0]
            print(f"✓ Found potential Mac at {ip} ({label})")
            return (ip, label)
        elif len(ssh_devices) > 1:
            # Multiple SSH devices - try to find the one with VibeProxy
            vibeproxy_devices = [
                (ip, label) for ip, label in ssh_devices if "8317" in label
            ]
            if len(vibeproxy_devices) == 1:
                ip, label = vibeproxy_devices[0]
                print(f"✓ Found Mac with VibeProxy at {ip}")
                return (ip, label)

            # Multiple candidates - show user
            print(f"⚠ Found {len(ssh_devices)} devices with SSH:")
            for ip, label in ssh_devices:
                print(f"  - {ip}: {label}")
            return None

        return None

    def auto_update_ip(self, new_ip: str) -> bool:
        """Update config with new Mac IP address.

        Returns True if updated successfully, False otherwise.
        """
        try:
            self._config.mac_ip = new_ip
            self.config_manager.save(self._config)
            print(f"✓ Config updated: Mac IP changed to {new_ip}")
            return True
        except Exception as e:
            print(f"✗ Failed to update config: {e}")
            return False

    def connect_with_retry(
        self, max_attempts: int = 3, auto_discover: bool = True
    ) -> tuple[bool, str]:
        """Intelligent connection with auto-discovery and smart retry.

        Args:
            max_attempts: Maximum connection attempts before network scan
            auto_discover: If True, scan network when host unreachable

        Returns (success, message) tuple.
        """
        for attempt in range(1, max_attempts + 1):
            print(
                f"🔌 Attempt {attempt}/{max_attempts} - Connecting to {self.mac_user}@{self.mac_ip}..."
            )

            success, message = self.start()

            if success:
                return True, message

            # Classify the error
            error_type, user_message = self.classify_ssh_error(message)

            print(f"❌ {user_message}")

            # If IP changed/unreachable and auto-discover enabled
            if error_type == "IP_CHANGED" and auto_discover and attempt >= 2:
                print(f"\n💡 Mac not found at {self.mac_ip}. Scanning network...")

                discovered = self.try_discover_mac()

                if discovered:
                    new_ip, label = discovered

                    if new_ip != self.mac_ip:
                        print(f"\n🎯 Mac found at NEW IP: {new_ip} (was {self.mac_ip})")
                        print(f"   Updating config automatically...")

                        if self.auto_update_ip(new_ip):
                            # Retry with new IP
                            print(f"\n🔄 Retrying connection with new IP...")
                            return self.start()
                    else:
                        print(f"⚠ Mac is at expected IP but not responding")
                        break
                else:
                    print(f"\n❌ Could not find Mac on network")
                    print(f"   Please check:")
                    print(f"   1. Mac is powered on and awake")
                    print(f"   2. Mac is connected to same network")
                    print(f"   3. SSH (Remote Login) is enabled on Mac")
                    break

            # For other errors, provide specific guidance
            elif error_type == "SSH_DOWN":
                print(
                    f"\n💡 To fix: Mac → System Settings → Sharing → Enable 'Remote Login'"
                )
                break
            elif error_type == "AUTH_FAILED":
                print(f"\n💡 To fix: Check SSH password in config or set up SSH keys")
                break
            elif error_type == "NETWORK_DOWN":
                print(f"\n💡 Check your network connection (WiFi/Ethernet)")
                break

            # Wait before retry
            if attempt < max_attempts:
                import time

                print(f"⏳ Waiting 2 seconds before retry...")
                time.sleep(2)

        return False, "Connection failed after all attempts"
