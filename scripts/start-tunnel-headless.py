#!/usr/bin/env python3
"""Headless SSH tunnel launcher for automation.

Usage:
    python start-tunnel-headless.py [--timeout 30] [--check-only]

Returns exit code 0 on success, 1 on failure.
Reads SSH password from vibeproxy-config.json.
"""

import argparse
import json
import socket
import subprocess
import sys
import time
from pathlib import Path


def load_config() -> dict:
    """Load VibeProxy config."""
    config_path = Path(__file__).parent.parent / "vibeproxy-config.json"
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def is_port_open(port: int, timeout: float = 1.0) -> bool:
    """Check if a port is accepting connections."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex(("localhost", port)) == 0
    except Exception:
        return False


def find_plink() -> str | None:
    """Find PuTTY plink executable."""
    import shutil

    plink = shutil.which("plink")
    if plink:
        return plink

    paths = [
        Path("C:/Program Files/PuTTY/plink.exe"),
        Path("C:/Program Files (x86)/PuTTY/plink.exe"),
    ]
    for p in paths:
        if p.exists():
            return str(p)
    return None


def start_tunnel(config: dict, timeout: int = 30) -> bool:
    """Start SSH tunnel and wait for it to be ready.

    Returns True if tunnel is up and accepting connections.
    """
    port = config.get("LocalPort", 8317)
    remote_port = config.get("RemotePort", 8317)
    mac_user = config.get("MacUser", "")
    mac_ip = config.get("MacIP", "")
    password = config.get("SSHPassword", "")

    if not mac_user or not mac_ip:
        print("ERROR: MacUser and MacIP must be set in config", file=sys.stderr)
        return False

    if not password:
        print(
            "ERROR: SSHPassword must be set in config for headless mode",
            file=sys.stderr,
        )
        return False

    # Check if already running
    if is_port_open(port):
        print(f"Tunnel already running on port {port}")
        return True

    # Find plink
    plink = find_plink()
    if not plink:
        print(
            "ERROR: PuTTY plink not found. Install PuTTY for headless SSH.",
            file=sys.stderr,
        )
        return False

    # Build plink command
    ssh_target = f"{mac_user}@{mac_ip}"
    local_forward = f"{port}:localhost:{remote_port}"

    cmd = [
        plink,
        "-ssh",
        "-batch",  # Non-interactive
        "-hostkey",
        "SHA256:5XgC3h/+waae885A5/IORHon1HPf3QLQXbF84V+mj0Y",
        "-L",
        local_forward,
        "-pw",
        password,
        ssh_target,
        "-N",  # No command, just forward
    ]

    print(f"Starting tunnel: localhost:{port} -> {mac_ip}:{remote_port}")

    # Start process in background (hidden window)
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception as e:
        print(f"ERROR: Failed to start tunnel: {e}", file=sys.stderr)
        return False

    # Wait for tunnel to be ready
    print(f"Waiting for tunnel (timeout: {timeout}s)...", end="", flush=True)
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check if process died
        if process.poll() is not None:
            _, stderr = process.communicate()
            error = stderr.decode().strip() if stderr else "Unknown error"
            print(f"\nERROR: Tunnel process died: {error}", file=sys.stderr)
            return False

        # Check if port is open
        if is_port_open(port):
            print(f" ready! (PID: {process.pid})")
            return True

        print(".", end="", flush=True)
        time.sleep(1)

    print(f"\nERROR: Timeout waiting for tunnel", file=sys.stderr)
    process.terminate()
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Start SSH tunnel for VibeProxy (headless)"
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Only check if tunnel is running"
    )
    args = parser.parse_args()

    config = load_config()
    port = config.get("LocalPort", 8317)

    if args.check_only:
        if is_port_open(port):
            print(f"Tunnel is running on port {port}")
            sys.exit(0)
        else:
            print(f"Tunnel is NOT running on port {port}")
            sys.exit(1)

    success = start_tunnel(config, args.timeout)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
