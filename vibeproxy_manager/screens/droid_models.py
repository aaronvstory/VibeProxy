"""Droid CLI model management screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header, OptionList
from textual.widgets.option_list import Option
from textual.binding import Binding
from textual.containers import Container


class DroidModelsScreen(Screen):
    """Screen for managing Droid CLI custom models."""

    BINDINGS = [
        Binding("1", "view_models", "View", show=True),
        Binding("2", "remove_model", "Remove", show=True),
        Binding("3", "sync_all", "Sync All", show=True),
        Binding("4", "clear_all", "Clear", show=True),
        Binding("escape", "app.back", "Back"),
        Binding("q", "app.quit", "Quit"),
    ]

    # Track current mode for model list interactions
    _mode: str = "view"  # "view", "remove"

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container(id="droid-container"):
            yield Static(
                "🤖 Manage Droid Models", id="droid-title", classes="section-title"
            )
            yield Static("", id="model-count")
            yield Static(
                "[dim]1=View  2=Remove  3=Sync All  4=Clear All[/dim]",
                id="droid-help",
            )
            yield OptionList(id="droid-options")
        yield Footer()

    def on_mount(self) -> None:
        """Load model count when screen mounts."""
        self._mode = "view"
        self.refresh_model_count()
        option_list = self.query_one("#droid-options", OptionList)
        option_list.focus()

    def refresh_model_count(self) -> None:
        """Update the model count display."""
        models = self.app.config_manager.get_factory_custom_models()
        count = len(models)
        display = self.query_one("#model-count", Static)

        if count == 0:
            display.update("[yellow]No custom models configured[/]")
        else:
            display.update(f"[green]{count} custom model(s) configured[/]")

    def show_model_list(self, mode: str = "view") -> None:
        """Display list of models in the option list.

        Args:
            mode: "view" for read-only, "remove" for removal selection
        """
        self._mode = mode
        option_list = self.query_one("#droid-options", OptionList)
        option_list.clear_options()

        models = self.app.config_manager.get_factory_custom_models()

        if not models:
            option_list.add_option(
                Option("No custom models configured", id="none", disabled=True)
            )
            return

        # Add header based on mode
        if mode == "remove":
            option_list.add_option(
                Option("[yellow]Select model to remove:[/]", id="header", disabled=True)
            )
        else:
            option_list.add_option(
                Option("[cyan]Custom Models:[/]", id="header", disabled=True)
            )

        for model in models:
            model_id = model.get("model", "unknown")
            display_name = model.get("model_display_name", model_id)
            base_url = model.get("base_url", "")

            # Truncate URL for display
            url_display = base_url[:40] + "..." if len(base_url) > 40 else base_url

            label = f"  {display_name}\n     [dim]{model_id}[/dim]\n     [dim]{url_display}[/dim]"
            option_list.add_option(Option(label, id=model_id))

    def action_view_models(self) -> None:
        """View all custom models."""
        self.show_model_list(mode="view")

    def action_remove_model(self) -> None:
        """Enter removal mode."""
        models = self.app.config_manager.get_factory_custom_models()

        if not models:
            self.notify("No custom models to remove", severity="warning")
            return

        self.show_model_list(mode="remove")
        self.notify(
            "Select a model to remove", title="Remove Mode", severity="information"
        )

    async def action_sync_all(self) -> None:
        """Sync all VibeProxy models to Droid."""
        self.notify("Fetching models from VibeProxy...", title="Syncing")

        try:
            # Fetch models from VibeProxy API
            models = await self.app.api.list_models(force_refresh=True)

            if not models:
                self.notify(
                    "No models found from VibeProxy. Is the tunnel running?",
                    severity="error",
                )
                return

            # Convert to (model_id, display_name) tuples
            model_tuples = [(m.id, m.display_name) for m in models]

            # Sync to Factory config
            success, msg = self.app.config_manager.sync_vibeproxy_to_factory(
                model_tuples
            )

            if success:
                self.notify(msg, title="Sync Complete", severity="information")
                self.refresh_model_count()
            else:
                self.notify(msg, title="Sync Failed", severity="error")

        except Exception as e:
            self.notify(f"Failed to sync: {e}", severity="error")

    def action_clear_all(self) -> None:
        """Clear all custom models after confirmation."""
        models = self.app.config_manager.get_factory_custom_models()

        if not models:
            self.notify("No custom models to clear", severity="warning")
            return

        # Show confirmation in option list
        option_list = self.query_one("#droid-options", OptionList)
        option_list.clear_options()

        option_list.add_option(
            Option(
                f"[red bold]Clear all {len(models)} custom models?[/]",
                id="header",
                disabled=True,
            )
        )
        option_list.add_option(Option("  [red]Yes, clear all models[/]", id="confirm"))
        option_list.add_option(Option("  [green]No, cancel[/]", id="cancel"))

        self._mode = "confirm_clear"

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection based on current mode."""
        option_id = event.option.id

        if option_id in ("none", "header"):
            return

        if self._mode == "remove":
            self._handle_remove_selection(option_id)
        elif self._mode == "confirm_clear":
            self._handle_clear_confirmation(option_id)
        # In view mode, selections do nothing

    def _handle_remove_selection(self, model_id: str) -> None:
        """Handle model removal."""
        success, msg = self.app.config_manager.remove_factory_model(model_id)

        if success:
            self.notify(msg, title="Removed", severity="information")
            self.refresh_model_count()
            # Refresh the list
            self.show_model_list(mode="remove")
        else:
            self.notify(msg, title="Failed", severity="error")

    def _handle_clear_confirmation(self, option_id: str) -> None:
        """Handle clear confirmation."""
        if option_id == "confirm":
            success, msg = self.app.config_manager.clear_factory_custom_models()

            if success:
                self.notify(msg, title="Cleared", severity="information")
            else:
                self.notify(msg, title="Failed", severity="error")
        else:
            self.notify("Cancelled", severity="information")

        # Reset mode and display
        self._mode = "view"
        self.refresh_model_count()

        # Clear the option list
        option_list = self.query_one("#droid-options", OptionList)
        option_list.clear_options()
