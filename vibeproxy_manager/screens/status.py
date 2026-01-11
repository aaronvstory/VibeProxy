"""Status and verification screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header, RichLog, Button
from textual.binding import Binding
from textual.containers import Container, Horizontal


class StatusScreen(Screen):
    """Screen showing complete system status and verification."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=True),
        Binding("escape", "app.back", "Back"),
        Binding("q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container(id="status-container"):
            yield Static("✅ System Status", id="status-title", classes="section-title")
            yield RichLog(id="status-log", wrap=True, highlight=True, markup=True)
            with Horizontal(id="status-buttons"):
                yield Button("Refresh", id="btn-refresh", variant="primary")
                yield Button("Test API", id="btn-test-api", variant="default")
                yield Button("Restart A0", id="btn-restart", variant="warning")
        yield Footer()

    async def on_mount(self) -> None:
        """Run verification on mount."""
        await self.run_verification()

    async def run_verification(self) -> None:
        """Run complete system verification."""
        log = self.query_one("#status-log", RichLog)
        log.clear()

        log.write("[bold cyan]═══ VibeProxy Setup Verification ═══[/]")
        log.write("")

        # 1. SSH Tunnel
        log.write("[bold]1. SSH Tunnel[/]")
        running, msg = self.app.tunnel.get_status()
        if running:
            log.write(f"   [green]✓[/] {msg}")
        else:
            log.write(f"   [red]✗[/] {msg}")
            log.write(f"   [dim]Command: {self.app.tunnel.start_in_terminal()}[/]")
        log.write("")

        # 2. VibeProxy API
        log.write("[bold]2. VibeProxy API[/]")
        success, msg = await self.app.api.test_connection()
        if success:
            log.write(f"   [green]✓[/] {msg}")
        else:
            log.write(f"   [red]✗[/] {msg}")
        log.write("")

        # 3. Docker / Agent Zero
        log.write("[bold]3. Agent Zero Container[/]")
        running, msg = self.app.docker.get_status()
        if running:
            log.write(f"   [green]✓[/] {msg}")
        else:
            log.write(f"   [red]✗[/] {msg}")
        log.write("")

        # 4. A0 Configuration
        log.write("[bold]4. A0 Configuration[/]")
        current = self.app.config_manager.get_current_a0_config()
        if current and current.model:
            log.write(f"   [green]✓[/] Model: {current.model}")
        else:
            log.write(f"   [yellow]⚠[/] No model configured")
        log.write("")

        # 5. Available Configs
        log.write("[bold]5. Available Configs[/]")
        configs = self.app.config_manager.get_a0_configs()
        if configs:
            log.write(f"   [green]✓[/] {len(configs)} presets found")
            for config in configs[:5]:  # Show first 5
                log.write(f"      · {config.name}")
            if len(configs) > 5:
                log.write(f"      · ... and {len(configs) - 5} more")
        else:
            log.write(f"   [yellow]⚠[/] No configs in configs/ directory")
        log.write("")

        # 6. Manager Config
        log.write("[bold]6. Manager Settings[/]")
        config = self.app.config_manager.load()
        log.write(f"   Mac: {config.mac_user}@{config.mac_ip}")
        log.write(f"   Port: {config.local_port}")
        log.write(f"   Favorites: {len(config.favorites)}")
        log.write(f"   Max tokens: {config.max_tokens}")
        log.write("")

        # Summary
        log.write("[bold cyan]═══════════════════════════════════════[/]")

        issues = []
        if not self.app.tunnel.is_running():
            issues.append("SSH tunnel not running")
        if not success:
            issues.append("API not reachable")
        if not self.app.docker.is_running():
            issues.append("A0 container not running")

        if issues:
            log.write(f"[yellow]⚠ Issues found: {len(issues)}[/]")
            for issue in issues:
                log.write(f"   · {issue}")
        else:
            log.write("[green]✓ All systems operational![/]")

    async def action_refresh(self) -> None:
        """Refresh status."""
        await self.run_verification()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-refresh":
            await self.run_verification()

        elif event.button.id == "btn-test-api":
            log = self.query_one("#status-log", RichLog)
            log.write("")
            log.write("[bold]Testing API...[/]")
            success, msg = await self.app.api.test_connection()
            if success:
                log.write(f"[green]✓[/] {msg}")
            else:
                log.write(f"[red]✗[/] {msg}")

        elif event.button.id == "btn-restart":
            log = self.query_one("#status-log", RichLog)
            log.write("")
            log.write("[bold]Restarting Agent Zero...[/]")
            success, msg = self.app.docker.restart()
            if success:
                log.write(f"[green]✓[/] {msg}")
            else:
                log.write(f"[red]✗[/] {msg}")
