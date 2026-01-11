"""VibeProxy Manager - Professional TUI for VibeProxy and Agent Zero."""

__version__ = "1.0.0"

from .app import VibeProxyApp


def main():
    """Entry point for the application."""
    app = VibeProxyApp()
    app.run()


__all__ = ["VibeProxyApp", "main"]
