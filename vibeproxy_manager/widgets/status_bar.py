"""Status bar widget showing tunnel, A0, and config status."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple
from textual.widgets import Static
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Horizontal


# Thread pool for running blocking I/O without blocking the UI
_status_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="status_check")


class StatusBar(Static):
    """Live status bar showing system status."""

    tunnel_status = reactive("Checking...")
    a0_status = reactive("Checking...")
    config_name = reactive("Unknown")

    def __init__(self, **kwargs):
        """Initialize status bar with health check caching."""
        super().__init__(**kwargs)
        self._last_health_check: Optional[Tuple[bool, str]] = None
        self._health_check_time: float = 0
        self._health_check_interval: float = 10.0  # Cache for 10 seconds

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Horizontal(id="status-container"):
            yield Static(id="tunnel-status")
            yield Static(id="a0-status")
            yield Static(id="config-status")

    def on_mount(self) -> None:
        """Initialize and start status updates."""
        self.update_display()
        # Set up periodic refresh (async to avoid blocking)
        self.set_interval(5.0, self._schedule_refresh)
        # Initial async check
        self.call_later(self._schedule_refresh)

    def _schedule_refresh(self) -> None:
        """Schedule async refresh (wrapper for set_interval compatibility)."""
        asyncio.create_task(self.refresh_status_async())

    def update_display(self) -> None:
        """Update the display with current values."""
        tunnel_widget = self.query_one("#tunnel-status", Static)
        a0_widget = self.query_one("#a0-status", Static)
        config_widget = self.query_one("#config-status", Static)

        tunnel_widget.update(f"SSH: {self.tunnel_status}")
        a0_widget.update(f"A0: {self.a0_status}")
        config_widget.update(f"Config: {self.config_name}")

    def watch_tunnel_status(self, value: str) -> None:
        """React to tunnel_status changes."""
        self.update_display()

    def watch_a0_status(self, value: str) -> None:
        """React to a0_status changes."""
        self.update_display()

    def watch_config_name(self, value: str) -> None:
        """React to config_name changes."""
        self.update_display()

    async def refresh_status_async(self) -> None:
        """Refresh all status values asynchronously (non-blocking)."""
        app = self.app
        loop = asyncio.get_event_loop()

        # Tunnel status with health check caching
        if hasattr(app, "tunnel"):
            try:
                # Quick PID+port check
                running = await loop.run_in_executor(
                    _status_executor, app.tunnel.is_running
                )

                # Periodic deep health check (every 10s)
                now = time.time()
                if now - self._health_check_time > self._health_check_interval:
                    # Time for fresh health check
                    if running and hasattr(app, "api"):
                        try:
                            success, msg = await app.api.test_connection()
                            self._last_health_check = (success, msg)
                            self._health_check_time = now
                        except Exception:
                            # Health check failed - mark as unknown
                            self._last_health_check = (False, "Health check error")
                            self._health_check_time = now

                # Display status based on PID check and cached health check
                if running:
                    if self._last_health_check and not self._last_health_check[0]:
                        # Port open but health check failed (zombie state)
                        self.tunnel_status = "⚠️ Port Open (API not responding)"
                    else:
                        # Healthy or no health check yet
                        self.tunnel_status = f"✅ Connected (port {app.tunnel.port})"
                else:
                    self.tunnel_status = f"❌ Not connected (port {app.tunnel.port})"
            except Exception as e:
                self.tunnel_status = f"⚠️ Error: {str(e)}"
        else:
            self.tunnel_status = "⚠️ N/A"

        # A0 status - run in thread pool to avoid blocking
        if hasattr(app, "docker"):
            try:
                running, msg = await loop.run_in_executor(
                    _status_executor, app.docker.get_status
                )
                if running:
                    self.a0_status = f"🟢 {msg}"
                else:
                    self.a0_status = f"🔴 {msg}"
            except Exception:
                self.a0_status = "⚠️ Error"
        else:
            self.a0_status = "⚠️ N/A"

        # Config status (fast - no I/O, just reads cached data)
        if hasattr(app, "config_manager"):
            current = app.config_manager.get_current_a0_config()
            if current and current.model:
                # Shorten model name for display
                model = current.model
                if len(model) > 20:
                    model = model[:17] + "..."
                self.config_name = model
            else:
                self.config_name = "Not set"
        else:
            self.config_name = "Unknown"

    def refresh_status(self) -> None:
        """Sync wrapper for backwards compatibility - schedules async refresh."""
        self._schedule_refresh()
