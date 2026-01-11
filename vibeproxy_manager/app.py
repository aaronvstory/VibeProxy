"""Main Textual application for VibeProxy Manager."""

from pathlib import Path

from textual.app import App
from textual.binding import Binding

from .config import ConfigManager
from .api import VibeProxyClient
from .docker import DockerManager
from .tunnel import TunnelManager


class VibeProxyApp(App):
    """VibeProxy Manager - Professional TUI for managing VibeProxy and Agent Zero."""

    TITLE = "VibeProxy Manager"
    SUB_TITLE = "All Models via SSH Tunnel"

    CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("escape", "back", "Back"),
        Binding("?", "help", "Help"),
    ]

    def __init__(self):
        """Initialize the application."""
        super().__init__()

        # Initialize managers
        self.config_manager = ConfigManager()
        self.api = VibeProxyClient()
        self.docker = DockerManager()
        self.tunnel = TunnelManager(self.config_manager)

        # Load config
        self.config = self.config_manager.load()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        from .screens.main_menu import MainMenuScreen
        self.push_screen(MainMenuScreen())

    def action_back(self) -> None:
        """Go back to previous screen."""
        if len(self.screen_stack) > 1:
            self.pop_screen()

    def action_help(self) -> None:
        """Show context-aware help information."""
        current_screen = self.screen.__class__.__name__
        
        if current_screen == "BrowseModelsScreen":
            # Let the screen handle its own help
            return
        
        base_help = "↑↓ Navigate | Enter Select | Q Quit | Esc Back"
        
        context_hints = {
            "MainMenuScreen": "1-6 Quick select | Select option to proceed",
            "ConfigMenuScreen": "Enter to apply config | Configs from configs/",
            "ChatScreen": "Enter to send | Ctrl+C to exit chat",
            "StatusScreen": "Shows tunnel, docker, API status",
        }
        
        hint = context_hints.get(current_screen, "")
        full_help = f"{base_help}\n{hint}" if hint else base_help
        
        self.notify(full_help, title="Keyboard Shortcuts", timeout=5)

    async def on_unmount(self) -> None:
        """Cleanup when app closes."""
        await self.api.close()
