"""Network configuration and scanning screen."""

import threading
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header, OptionList, Input, Button, Label
from textual.widgets.option_list import Option
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal
from textual.worker import Worker

class NetworkSettingsScreen(Screen):
    """Screen for managing network connection settings."""

    BINDINGS = [
        Binding("escape", "app.back", "Back"),
        Binding("s", "scan_network", "Scan"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container(id="network-container"):
            yield Static("🌐 Network Settings", classes="section-title")
            
            with Vertical(classes="box"):
                yield Label("Target Mac IP:")
                with Horizontal():
                    yield Input(placeholder="192.168.x.x", id="ip-input")
                    yield Button("Save", id="save-btn", variant="primary")
            
            yield Static("Scan Network", classes="section-header")
            yield Static("Press 's' to scan local network for VibeProxy hosts", id="scan-status")
            yield OptionList(id="scan-results")
            
        yield Footer()

    def on_mount(self) -> None:
        """Load current settings."""
        config = self.app.config_manager.load()
        self.query_one("#ip-input", Input).value = config.mac_ip
        self.query_one("#scan-results", OptionList).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle save button."""
        if event.button.id == "save-btn":
            self.save_ip()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter on input."""
        self.save_ip()

    def save_ip(self) -> None:
        """Save the manually entered IP."""
        new_ip = self.query_one("#ip-input", Input).value.strip()
        if not new_ip:
            self.notify("IP cannot be empty", severity="error")
            return

        config = self.app.config_manager.load()
        config.mac_ip = new_ip
        self.app.config_manager.save(config)
        self.notify(f"Updated IP to {new_ip}", title="Saved")

    def action_scan_network(self) -> None:
        """Start network scan in background."""
        self.query_one("#scan-status", Static).update("🔄 Scanning network (this may take 10-20s)...")
        self.run_worker(self.perform_scan, exclusive=True, thread=True)

    def perform_scan(self) -> None:
        """Worker function to scan network."""
        results = self.app.tunnel.scan_network()
        self.call_from_thread(self.update_scan_results, results)

    def update_scan_results(self, results: list) -> None:
        """Update the list with scan results."""
        status = self.query_one("#scan-status", Static)
        option_list = self.query_one("#scan-results", OptionList)
        option_list.clear_options()

        if not results:
            status.update("❌ No devices found. Check your network or firewall.")
            option_list.add_option(Option("No devices found", disabled=True))
            return

        status.update(f"✅ Found {len(results)} devices:")
        
        for ip, label in results:
            option_list.add_option(Option(f"{ip} - {label}", id=ip))
            
        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle selection from scan results."""
        if not event.option.id:
            return
            
        selected_ip = event.option.id
        self.query_one("#ip-input", Input).value = selected_ip
        self.save_ip()
