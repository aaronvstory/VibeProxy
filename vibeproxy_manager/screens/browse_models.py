"""Browse models screen with filtering and selection."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Static, Footer, Header, Input, Switch, SelectionList, LoadingIndicator
)
from textual.widgets.selection_list import Selection
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message

from ..models import Model, PROVIDER_ORDER


class BrowseModelsScreen(Screen):
    """Model browser with search, filtering, and actions."""

    BINDINGS = [
        Binding("enter", "chat", "Chat", show=False),
        Binding("c", "chat", "Chat", show=True),
        Binding("t", "test", "Test", show=True),
        Binding("p", "pick", "New A0 Cfg", show=True),  # Creates preset in configs/
        Binding("a", "apply_a0", "Apply A0", show=True),  # Copies preset to A0 settings
        Binding("d", "set_droid_default", "Droid Def", show=True),  # Sets Factory default
        Binding("f", "favorite", "Fav", show=True),
        Binding("o", "toggle_favorites", "Favs Only", show=True),
        Binding("s", "focus_search", "Search", show=False),
        Binding("/", "focus_search", "Search", show=False),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("?", "show_help", "Help", show=True),
        Binding("escape", "app.back", "Back"),
        Binding("q", "app.quit", "Quit"),
    ]

    def __init__(self):
        """Initialize the screen."""
        super().__init__()
        self.models: list[Model] = []
        self.search_filter: str = ""
        self.favorites_only: bool = False
        self.loading: bool = True

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container(id="browse-container"):
            # Search and filter bar
            with Horizontal(id="filter-bar"):
                yield Input(placeholder="🔍 Search models...", id="search-input")
                yield Static("⭐ Favorites:", id="fav-label")
                yield Switch(value=False, id="favorites-switch")
                yield Static("", id="token-display")

            # Model list
            yield SelectionList[str](id="model-list")

            # Loading indicator
            yield LoadingIndicator(id="loading")

        yield Footer()

    async def on_mount(self) -> None:
        """Load models when screen mounts."""
        self.update_token_display()
        # Check connection first
        connected, msg = await self.app.api.test_connection()
        if not connected:
            self.notify(
                f"Connection issue: {msg}",
                title="⚠️ Tunnel Check",
                severity="warning",
                timeout=10
            )
        await self.load_models()

    def update_token_display(self) -> None:
        """Update the max tokens display."""
        tokens = self.app.config_manager.get_max_tokens()
        display = self.query_one("#token-display", Static)
        display.update(f"Max: {tokens} tokens")

    async def load_models(self) -> None:
        """Load models from API."""
        self.loading = True
        loading = self.query_one("#loading", LoadingIndicator)
        loading.display = True

        model_list = self.query_one("#model-list", SelectionList)
        model_list.display = False

        try:
            self.models = await self.app.api.list_models()
            self.refresh_list()
            self.notify(f"Loaded {len(self.models)} models", severity="information")
        except ConnectionError as e:
            error_msg = str(e)
            if "refused" in error_msg.lower():
                self.notify(
                    "Is SSH tunnel running? Try: start-vibeproxy-tunnel.bat",
                    title="Connection Refused",
                    severity="error",
                    timeout=15
                )
            else:
                self.notify(f"Connection error: {error_msg}", severity="error")
            self.models = []
        except Exception as e:
            self.notify(f"Failed to load models: {e}", severity="error")
            self.models = []

        self.loading = False
        loading.display = False
        model_list.display = True
        model_list.focus()

    def on_selection_list_selection_toggled(
        self, event: SelectionList.SelectionToggled
    ) -> None:
        """Treat click/toggle as activate for model rows."""
        if event.selection.value is None:
            return
        self.action_chat()
        model_list = self.query_one("#model-list", SelectionList)
        model_list.deselect_all()

    def refresh_list(self) -> None:
        """Refresh the model list based on filters."""
        model_list = self.query_one("#model-list", SelectionList)
        model_list.clear_options()

        # Filter models
        filtered = self.models

        # Apply search filter
        if self.search_filter:
            search = self.search_filter.lower()
            filtered = [m for m in filtered if search in m.id.lower()]

        # Apply favorites filter
        favorites = self.app.config.favorites
        if self.favorites_only:
            filtered = [m for m in filtered if m.id in favorites]

        # Group by provider
        grouped: dict[str, list[Model]] = {}
        for model in filtered:
            provider = model.provider
            if provider not in grouped:
                grouped[provider] = []
            grouped[provider].append(model)

        # Sort providers
        sorted_providers = sorted(
            grouped.keys(),
            key=lambda p: PROVIDER_ORDER.index(p) if p in PROVIDER_ORDER else 999
        )

        # Build selection list
        for provider in sorted_providers:
            models = grouped[provider]
            count = len(models)

            # Add provider header (separator)
            model_list.add_option(
                Selection(f"── {provider} ({count}) ──", None, disabled=True)
            )

            # Sort models: favorites first, then alphabetically
            models.sort(key=lambda m: (0 if m.id in favorites else 1, m.id))

            # Add models
            for model in models:
                is_fav = model.id in favorites
                prefix = "⭐ " if is_fav else "   "
                label = f"{prefix}{model.id}"
                model_list.add_option(Selection(label, model.id))

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.search_filter = event.value
            self.refresh_list()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle favorites switch toggle."""
        if event.switch.id == "favorites-switch":
            self.favorites_only = event.value
            self.refresh_list()

    def get_selected_model(self) -> str | None:
        """Get the currently highlighted model ID."""
        model_list = self.query_one("#model-list", SelectionList)
        if model_list.highlighted is not None:
            option = model_list.get_option_at_index(model_list.highlighted)
            if option and option.value:
                return option.value
        return None

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search = self.query_one("#search-input", Input)
        search.focus()

    def action_chat(self) -> None:
        """Start chat with selected model."""
        model_id = self.get_selected_model()
        if model_id:
            from .chat import ChatScreen
            self.app.push_screen(ChatScreen(model_id))
        else:
            self.notify("Select a model first", severity="warning")

    async def action_test(self) -> None:
        """Test the selected model."""
        model_id = self.get_selected_model()
        if not model_id:
            self.notify("Select a model first", severity="warning")
            return

        self.notify(f"Testing {model_id}...", title="Model Test")

        success, msg = await self.app.api.preflight(model_id)

        if success:
            self.notify(f"{model_id}: {msg}", title="✅ Test Passed", severity="information")
        else:
            self.notify(f"{model_id}: {msg}", title="❌ Test Failed", severity="error")

    def action_pick(self) -> None:
        """Create A0 config for selected model."""
        model_id = self.get_selected_model()
        if not model_id:
            self.notify("Select a model first", severity="warning")
            return

        path = self.app.config_manager.create_config_for_model(model_id)
        if path:
            self.notify(
                f"Created A0 preset: {path.name} (apply in Config screen)",
                title="A0 Preset Created",
                severity="information"
            )
        else:
            self.notify("Failed to create config", severity="error")

    def action_set_droid_default(self) -> None:
        """Set selected model as default in Factory (droid-cli)."""
        model_id = self.get_selected_model()
        if not model_id:
            self.notify("Select a model first", severity="warning")
            return

        model_obj = next((m for m in self.models if m.id == model_id), None)
        display_name = model_obj.display_name if model_obj else model_id
        success, msg = self.app.config_manager.set_factory_default_model(model_id, display_name)

        if success:
            self.notify(
                f"{msg}. Use /model in droid to switch if needed.",
                title="Factory Config Updated",
                severity="information"
            )
        else:
            self.notify(msg, title="Factory Update Failed", severity="error")

    def action_favorite(self) -> None:
        """Toggle favorite status for selected model."""
        model_id = self.get_selected_model()
        if not model_id:
            self.notify("Select a model first", severity="warning")
            return

        is_now_fav = self.app.config_manager.toggle_favorite(model_id)
        # Reload config
        self.app.config = self.app.config_manager.load()

        if is_now_fav:
            self.notify(f"⭐ Added to favorites: {model_id}", severity="information")
        else:
            self.notify(f"Removed from favorites: {model_id}", severity="information")

        self.refresh_list()

    def action_toggle_favorites(self) -> None:
        """Toggle favorites-only filter."""
        switch = self.query_one("#favorites-switch", Switch)
        switch.value = not switch.value

    async def action_refresh(self) -> None:
        """Refresh model list from API."""
        await self.load_models()

    def action_apply_a0(self) -> None:
        """Create and immediately apply A0 config for selected model."""
        model_id = self.get_selected_model()
        if not model_id:
            self.notify("Select a model first", severity="warning")
            return

        # Create config if it doesn't exist
        path = self.app.config_manager.create_config_for_model(model_id)
        if not path:
            self.notify("Failed to create config", severity="error")
            return

        # Backup existing config before applying
        backup_path = self.app.config_manager.backup_a0_config()
        if backup_path:
            self.notify(f"Backup saved: {backup_path.name}", severity="information")

        # Build an A0Config object and apply it
        from ..models import A0Config
        a0_config = A0Config(
            name=path.stem,
            path=str(path),
            model=model_id,
        )

        success = self.app.config_manager.apply_a0_config(a0_config)
        if success:
            self.notify(
                f"Applied to A0: {model_id}. Restart A0 to use.",
                title="✅ A0 Config Applied",
                severity="information"
            )
        else:
            self.notify("Failed to apply config to A0", severity="error")

    def action_show_help(self) -> None:
        """Show help for model browser."""
        help_text = """[bold]Model Browser Help[/bold]

[cyan]Actions:[/cyan]
  [green]c[/green]/Enter  Chat with model
  [green]t[/green]        Test model connectivity
  [green]p[/green]        Create A0 preset (saves to configs/)
  [green]a[/green]        Apply to A0 (create + activate)
  [green]d[/green]        Set as Droid/Factory default
  [green]f[/green]        Toggle favorite

[cyan]Navigation:[/cyan]
  [green]↑↓[/green]       Move selection
  [green]/[/green] or [green]s[/green]  Focus search
  [green]o[/green]        Toggle favorites filter
  [green]r[/green]        Refresh models

[cyan]A0 vs Droid:[/cyan]
  • [yellow]A0 Preset[/yellow]: Creates config file in configs/
  • [yellow]Apply A0[/yellow]: Creates + copies to A0 settings
  • [yellow]Droid Def[/yellow]: Updates ~/.factory/config.json"""
        self.notify(help_text, title="Help", timeout=15)
