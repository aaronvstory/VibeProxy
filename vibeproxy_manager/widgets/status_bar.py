"""Status bar widget showing tunnel, A0, and config status."""

from textual.widgets import Static
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Horizontal


class StatusBar(Static):
    """Live status bar showing system status."""

    tunnel_status = reactive("Checking...")
    a0_status = reactive("Checking...")
    config_name = reactive("Unknown")

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Horizontal(id="status-container"):
            yield Static(id="tunnel-status")
            yield Static(id="a0-status")
            yield Static(id="config-status")

    def on_mount(self) -> None:
        """Initialize and start status updates."""
        self.update_display()
        # Set up periodic refresh
        self.set_interval(5.0, self.refresh_status)
        # Initial async check
        self.call_later(self.refresh_status)

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

    def refresh_status(self) -> None:
        """Refresh all status values."""
        app = self.app

        # Tunnel status
        if hasattr(app, "tunnel"):
            running, msg = app.tunnel.get_status()
            if running:
                self.tunnel_status = f"✅ {msg}"
            else:
                self.tunnel_status = f"❌ {msg}"
        else:
            self.tunnel_status = "⚠️ N/A"

        # A0 status
        if hasattr(app, "docker"):
            running, msg = app.docker.get_status()
            if running:
                self.a0_status = f"🟢 {msg}"
            else:
                self.a0_status = f"🔴 {msg}"
        else:
            self.a0_status = "⚠️ N/A"

        # Config status
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
