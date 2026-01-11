"""Configuration selection screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header, OptionList
from textual.widgets.option_list import Option
from textual.binding import Binding
from textual.containers import Container


class ConfigMenuScreen(Screen):
    """Screen for selecting A0 configuration presets."""

    BINDINGS = [
        Binding("r", "restart_a0", "Restart A0", show=True),
        Binding("escape", "app.back", "Back"),
        Binding("q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container(id="config-container"):
            yield Static("⚙️  Select A0 Configuration", id="config-title", classes="section-title")
            yield Static("", id="current-config")
            yield OptionList(id="config-options")
        yield Footer()

    def on_mount(self) -> None:
        """Load configs when screen mounts."""
        self.load_configs()
        self.update_current_display()
        option_list = self.query_one("#config-options", OptionList)
        option_list.focus()

    def update_current_display(self) -> None:
        """Update the current config display."""
        current = self.app.config_manager.get_current_a0_config()
        display = self.query_one("#current-config", Static)

        if current and current.model:
            display.update(f"[green]Current:[/] {current.model}")
        else:
            display.update("[yellow]Current: Not configured[/]")

    def load_configs(self) -> None:
        """Load available configuration presets."""
        option_list = self.query_one("#config-options", OptionList)
        option_list.clear_options()

        configs = self.app.config_manager.get_a0_configs()

        if not configs:
            option_list.add_option(Option("No configs found in configs/", id="none", disabled=True))
            return

        current = self.app.config_manager.get_current_a0_config()
        current_model = current.model if current else ""

        for config in configs:
            # Mark current config
            prefix = "✓ " if config.model == current_model else "  "
            label = f"{prefix}{config.name}"
            if config.model:
                label += f" ({config.model})"

            option_list.add_option(Option(label, id=config.path))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle config selection."""
        if event.option.id == "none":
            return

        config_path = event.option.id

        # Find the config by path
        configs = self.app.config_manager.get_a0_configs()
        selected = None
        for config in configs:
            if config.path == config_path:
                selected = config
                break

        if not selected:
            self.notify("Config not found", severity="error")
            return

        # Apply the config
        success = self.app.config_manager.apply_a0_config(selected)

        if success:
            self.notify(f"Applied: {selected.name}", title="Config Updated", severity="information")
            self.update_current_display()
            self.load_configs()  # Refresh list to show new current

            # Ask about restart
            self.notify("Press R to restart Agent Zero", title="Restart?", timeout=5)
        else:
            self.notify("Failed to apply config", severity="error")

    def action_restart_a0(self) -> None:
        """Restart Agent Zero after config change."""
        self.notify("Restarting Agent Zero...", title="Docker")

        success, msg = self.app.docker.restart()

        if success:
            self.notify(msg, title="Docker", severity="information")
        else:
            self.notify(msg, title="Restart Failed", severity="error")
