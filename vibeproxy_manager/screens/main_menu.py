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
        Binding("2", "select_network", "Network", show=False),
        Binding("3", "select_config", "Config", show=False),
        Binding("4", "select_test", "Test", show=False),
        Binding("5", "select_browse", "Browse", show=False),
        Binding("6", "select_restart", "Restart", show=False),
        Binding("7", "select_verify", "Verify", show=False),
        Binding("8", "select_droid", "Droid", show=False),
        Binding("9", "select_kill_port", "Kill Port", show=False),
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
                Option("🌐 Network Settings", id="network"),
                Option("⚙️  Switch A0 Config", id="config"),
                Option("🧪 Test VibeProxy", id="test"),
                Option("📋 Browse Models", id="browse"),
                Option("🔄 Restart Agent Zero", id="restart"),
                Option("✅ Verify Setup", id="verify"),
                Option("🤖 Manage Droid Models", id="droid"),
                Option("🔪 Kill Port Process", id="kill_port"),
                Option("❓ Help", id="help"),
                id="menu-options",
            )
        yield Footer()

    def on_mount(self) -> None:
        """Focus the menu list on load."""
        menu = self.query_one("#menu-options", OptionList)
        menu.focus()

    async def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Handle menu option selection."""
        option_id = event.option.id

        if option_id == "tunnel":
            await self.action_select_tunnel()
        elif option_id == "network":
            self.action_select_network()
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
        elif option_id == "droid":
            self.action_select_droid()
        elif option_id == "kill_port":
            await self.action_select_kill_port()
        elif option_id == "help":
            self.action_select_help()

    async def action_select_tunnel(self) -> None:
        """Start SSH tunnel in a new terminal window with zombie state detection."""
        tunnel = self.app.tunnel

        if tunnel.is_running():
            # Tunnel appears to be running - perform health check to detect zombie states
            try:
                success, msg = await self.app.api.test_connection()

                if success:
                    # Healthy tunnel - already running
                    self.notify(
                        "Tunnel is already running and healthy.\n\n" + msg,
                        title="SSH Tunnel",
                        severity="information",
                    )
                else:
                    # Zombie state detected: port open but API not responding
                    self.notify(
                        "⚠️ Zombie state detected!\n\n"
                        "Port is open but API not responding.\n"
                        "Force restarting tunnel...",
                        title="Zombie State",
                        severity="warning",
                        timeout=5,
                    )

                    # Clear zombie state
                    tunnel._tunnel_pid = None
                    tunnel._tunnel_process = None

                    # Wait a moment for port to release
                    import asyncio

                    await asyncio.sleep(1)

                    # Try starting fresh
                    success, msg = tunnel.start_in_window()
                    if success:
                        self.notify(
                            "🔄 Tunnel restarted successfully!\n\n" + msg,
                            title="Tunnel Restarted",
                            severity="information",
                            timeout=10,
                        )
                        # Refresh status bar
                        await asyncio.sleep(3)
                        status_bar = self.query_one("#status-bar", StatusBar)
                        status_bar.refresh_status()
                    else:
                        self.notify(msg, title="Restart Failed", severity="error")
            except Exception as e:
                # Health check failed - treat as unknown state
                self.notify(
                    f"Unable to verify tunnel state: {e}\n\nTunnel appears to be running.",
                    title="SSH Tunnel",
                    severity="warning",
                )
        else:
            # Tunnel not running - start normally
            success, msg = tunnel.start_in_window()
            if success:
                self.notify(
                    "🚀 Tunnel launcher started!\n\n"
                    "A new terminal window has opened with:\n"
                    "  • Auto-reconnect on connection drop\n"
                    "  • Password auto-login (saved in config)\n"
                    "  • Live connection status\n\n"
                    "Keep that window open while using VibeProxy!",
                    title="SSH Tunnel",
                    severity="information",
                    timeout=15,
                )
                # Refresh status bar after brief delay
                import asyncio

                async def delayed_refresh():
                    await asyncio.sleep(3)  # Wait for tunnel to establish
                    status_bar = self.query_one("#status-bar", StatusBar)
                    status_bar.refresh_status()

                self.app.call_later(lambda: asyncio.create_task(delayed_refresh()))
            else:
                self.notify(msg, title="SSH Tunnel Failed", severity="error")
                # Show manual command as fallback
                cmd = tunnel.start_in_terminal()
                self.notify(f"Try manually: {cmd}", title="Manual Command", timeout=10)

    def action_select_network(self) -> None:
        """Open network settings."""
        from .network_settings import NetworkSettingsScreen

        self.app.push_screen(NetworkSettingsScreen())

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

    def action_select_droid(self) -> None:
        """Manage Droid CLI models."""
        from .droid_models import DroidModelsScreen

        self.app.push_screen(DroidModelsScreen())

    def action_select_kill_port(self) -> None:
        """Kill any process using the tunnel port with confirmation."""
        tunnel = self.app.tunnel
        port = tunnel.port

        # First check what processes are using the port (show before killing)
        import subprocess

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | "
                    "ForEach-Object {{ (Get-Process -Id $_.OwningProcess).Name }} | "
                    "Sort-Object -Unique",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            procs = result.stdout.strip()
            if procs:
                self.notify(
                    f"⚠️ Killing processes on port {port}:\n{procs}",
                    title="Kill Port",
                    severity="warning",
                    timeout=3,
                )
            else:
                self.notify(f"No processes found on port {port}", title="Kill Port")
                return
        except Exception:
            pass  # Continue with force_reset even if check fails

        success, msg = tunnel.force_reset()

        if success:
            self.notify(
                f"✅ {msg}\n\nPort {port} should now be available.",
                title="Port Cleared",
                severity="information",
                timeout=5,
            )
            # Refresh status bar
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.refresh_status()
        else:
            self.notify(
                f"⚠️ {msg}",
                title="Kill Port",
                severity="warning",
            )

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
• [green]Manage Droid Models[/green] - View, sync, remove models

[cyan]Keyboard Shortcuts:[/cyan]
  ↑↓   Navigate menus
  Enter Select option
  Esc   Go back
  Q     Quit
  ?     Show help"""
        self.notify(help_text, title="Help", timeout=20)
