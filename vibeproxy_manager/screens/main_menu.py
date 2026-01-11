"""Main menu screen for VibeProxy Manager."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header
from textual.widgets import OptionList
from textual.widgets.option_list import Option
from textual.binding import Binding
from textual.containers import Container, Vertical

from ..widgets.status_bar import StatusBar


class MainMenuScreen(Screen):
    """Main menu with primary actions."""

    BINDINGS = [
        Binding("1", "select_tunnel", "Tunnel", show=False),
        Binding("2", "select_config", "Config", show=False),
        Binding("3", "select_test", "Test", show=False),
        Binding("4", "select_browse", "Browse", show=False),
        Binding("5", "select_restart", "Restart", show=False),
        Binding("6", "select_verify", "Verify", show=False),
        Binding("7", "select_help", "Help", show=False),
        Binding("?", "select_help", "Help", show=False),
        Binding("q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container(id="main-container"):
            yield StatusBar(id="status-bar")
            yield Static("Main Menu", id="menu-title", classes="section-title")
            yield OptionList(
                Option("🔌 Start SSH Tunnel", id="tunnel"),
                Option("⚙️  Switch A0 Config", id="config"),
                Option("🧪 Test VibeProxy", id="test"),
                Option("📋 Browse Models", id="browse"),
                Option("🔄 Restart Agent Zero", id="restart"),
                Option("✅ Verify Setup", id="verify"),
                Option("❓ Help", id="help"),
                id="menu-options",
            )
        yield Footer()

    def on_mount(self) -> None:
        """Focus the menu list on load."""
        menu = self.query_one("#menu-options", OptionList)
        menu.focus()

    async def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle menu option selection."""
        option_id = event.option.id

        if option_id == "tunnel":
            self.action_select_tunnel()
        elif option_id == "config":
            self.action_select_config()
        elif option_id == "test":
            await self.action_select_test()
        elif option_id == "browse":
            self.action_select_browse()
        elif option_id == "restart":
            self.action_select_restart()
        elif option_id == "verify":
            await self.action_select_verify()
        elif option_id == "help":
            self.action_select_help()

    def action_select_tunnel(self) -> None:
        """Start/stop SSH tunnel."""
        tunnel = self.app.tunnel

        if tunnel.is_running():
            self.notify("Tunnel already running", title="SSH Tunnel")
        else:
            success, msg = tunnel.start()
            if success:
                self.notify(msg, title="SSH Tunnel", severity="information")
                # Refresh status bar
                status_bar = self.query_one("#status-bar", StatusBar)
                status_bar.refresh_status()
            else:
                self.notify(msg, title="SSH Tunnel Failed", severity="error")
                # Show manual command
                cmd = tunnel.start_in_terminal()
                self.notify(f"Try: {cmd}", title="Manual Command", timeout=10)

    def action_select_config(self) -> None:
        """Switch A0 configuration."""
        from .config_menu import ConfigMenuScreen
        self.app.push_screen(ConfigMenuScreen())

    async def action_select_test(self) -> None:
        """Test VibeProxy connection."""
        self.notify("Testing connection...", title="VibeProxy")

        success, msg = await self.app.api.test_connection()

        if success:
            self.notify(msg, title="VibeProxy", severity="information")
        else:
            self.notify(msg, title="Connection Failed", severity="error")

    def action_select_browse(self) -> None:
        """Browse available models."""
        from .browse_models import BrowseModelsScreen
        self.app.push_screen(BrowseModelsScreen())

    def action_select_restart(self) -> None:
        """Restart Agent Zero container."""
        self.notify("Restarting Agent Zero...", title="Docker")

        success, msg = self.app.docker.restart()

        if success:
            self.notify(msg, title="Docker", severity="information")
            # Refresh status bar
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.refresh_status()
        else:
            self.notify(msg, title="Restart Failed", severity="error")

    async def action_select_verify(self) -> None:
        """Verify complete setup."""
        from .status import StatusScreen
        self.app.push_screen(StatusScreen())

    def action_select_help(self) -> None:
        """Show comprehensive help."""
        help_text = """[bold]VibeProxy Manager[/bold]

[cyan]What is VibeProxy?[/cyan]
Routes AI model requests through a Mac-hosted proxy,
giving access to all models via a single SSH tunnel.

[cyan]Quick Start:[/cyan]
1. [green]Start SSH Tunnel[/green] - Connect to Mac proxy
2. [green]Test VibeProxy[/green] - Verify connection works
3. [green]Browse Models[/green] - Select and configure models

[cyan]For Agent Zero (A0):[/cyan]
• [green]Switch A0 Config[/green] - Apply a preset config
• [green]Browse Models[/green] → [green]a[/green] to apply directly

[cyan]For Droid/Factory:[/cyan]
• [green]Browse Models[/green] → [green]d[/green] to set default

[cyan]Keyboard Shortcuts:[/cyan]
  ↑↓   Navigate menus
  Enter Select option
  Esc   Go back
  Q     Quit
  ?     Show help"""
        self.notify(help_text, title="Help", timeout=20)
