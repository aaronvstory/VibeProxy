"""Docker container management for Agent Zero."""

import subprocess
from typing import Optional


class DockerManager:
    """Manages Agent Zero Docker container."""

    CONTAINER_NAME = "agent-zero-instance"

    def get_status(self) -> tuple[bool, str]:
        """Get container status.

        Returns (is_running, status_message) tuple.
        """
        try:
            result = subprocess.run(
                [
                    "docker", "ps",
                    "--filter", f"name={self.CONTAINER_NAME}",
                    "--format", "{{.Status}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return False, "Docker command failed"

            status = result.stdout.strip()
            if status:
                # Parse status like "Up 2 hours" or "Up 2 hours (healthy)"
                if status.startswith("Up"):
                    return True, status
                return False, status
            return False, "Not running"

        except subprocess.TimeoutExpired:
            return False, "Docker timeout"
        except FileNotFoundError:
            return False, "Docker not found"
        except Exception as e:
            return False, str(e)

    def is_running(self) -> bool:
        """Check if container is running."""
        running, _ = self.get_status()
        return running

    def restart(self) -> tuple[bool, str]:
        """Restart the Agent Zero container."""
        try:
            result = subprocess.run(
                ["docker", "restart", self.CONTAINER_NAME],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                return True, "Container restarted successfully"

            error = result.stderr.strip() or result.stdout.strip()
            return False, f"Restart failed: {error}"

        except subprocess.TimeoutExpired:
            return False, "Restart timeout (container may still be starting)"
        except FileNotFoundError:
            return False, "Docker not found"
        except Exception as e:
            return False, str(e)

    def stop(self) -> tuple[bool, str]:
        """Stop the Agent Zero container."""
        try:
            result = subprocess.run(
                ["docker", "stop", self.CONTAINER_NAME],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return True, "Container stopped"

            error = result.stderr.strip() or result.stdout.strip()
            return False, f"Stop failed: {error}"

        except Exception as e:
            return False, str(e)

    def start(self) -> tuple[bool, str]:
        """Start the Agent Zero container."""
        try:
            result = subprocess.run(
                ["docker", "start", self.CONTAINER_NAME],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return True, "Container started"

            error = result.stderr.strip() or result.stdout.strip()
            return False, f"Start failed: {error}"

        except Exception as e:
            return False, str(e)

    def get_logs(self, lines: int = 50) -> str:
        """Get recent container logs."""
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), self.CONTAINER_NAME],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return result.stdout + result.stderr
            return f"Failed to get logs: {result.stderr}"

        except Exception as e:
            return f"Error: {e}"

    def exec_command(self, command: str) -> tuple[bool, str]:
        """Execute a command inside the container."""
        try:
            result = subprocess.run(
                ["docker", "exec", self.CONTAINER_NAME, "sh", "-c", command],
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = result.stdout + result.stderr
            return result.returncode == 0, output.strip()

        except Exception as e:
            return False, str(e)
