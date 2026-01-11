"""Interactive chat screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header, Input, RichLog
from textual.binding import Binding
from textual.containers import Container, Vertical

from ..models import ChatMessage


class ChatScreen(Screen):
    """Interactive chat with a selected model."""

    BINDINGS = [
        Binding("ctrl+l", "clear_chat", "Clear", show=True),
        Binding("ctrl+t", "set_tokens", "Tokens", show=True),
        Binding("escape", "app.back", "Exit Chat"),
        Binding("q", "app.quit", "Quit"),
    ]

    def __init__(self, model_id: str):
        """Initialize chat with a specific model."""
        super().__init__()
        self.model_id = model_id
        self.messages: list[dict] = []
        self.total_tokens: int = 0

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container(id="chat-container"):
            yield Static(f"💬 Chat: {self.model_id}", id="chat-header")
            yield RichLog(id="chat-log", wrap=True, highlight=True, markup=True)
            yield Static("", id="chat-status")
            yield Input(placeholder="Type message... (/help for commands)", id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize chat on mount."""
        log = self.query_one("#chat-log", RichLog)
        log.write("[dim]Chat started. Type a message and press Enter.[/]")
        log.write(f"[dim]Model: {self.model_id}[/]")
        log.write(f"[dim]Max tokens: {self.app.config_manager.get_max_tokens()}[/]")
        log.write("[dim]Commands: /help, /clear, /tokens N, /exit[/]")
        log.write("")

        self.update_status()

        # Focus input
        input_widget = self.query_one("#chat-input", Input)
        input_widget.focus()

    def update_status(self) -> None:
        """Update the status line."""
        status = self.query_one("#chat-status", Static)
        max_tokens = self.app.config_manager.get_max_tokens()
        msg_count = len([m for m in self.messages if m["role"] == "user"])
        status.update(f"[dim]Messages: {msg_count} | Tokens used: {self.total_tokens} | Max: {max_tokens}[/]")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle message submission."""
        if event.input.id != "chat-input":
            return

        text = event.value.strip()
        if not text:
            return

        # Clear input
        event.input.value = ""

        log = self.query_one("#chat-log", RichLog)

        # Handle commands
        if text.startswith("/"):
            await self.handle_command(text, log)
            return

        # Add user message
        self.messages.append({"role": "user", "content": text})
        log.write(f"[bold green]You:[/] {text}")

        # Show loading indicator
        log.write("[dim]AI is thinking...[/]")

        # Call API
        max_tokens = self.app.config_manager.get_max_tokens()
        response = await self.app.api.chat(
            model=self.model_id,
            messages=self.messages,
            max_tokens=max_tokens,
        )

        # Remove loading indicator (write over it)
        # Note: RichLog doesn't support removing lines, so we just continue

        # Add assistant response
        if response.finish_reason != "error":
            self.messages.append({"role": "assistant", "content": response.content})
            log.write(f"[bold magenta]AI:[/] {response.content}")
            log.write(f"[dim][{response.tokens} tokens · {response.elapsed:.1f}s][/]")
            self.total_tokens += response.tokens
        else:
            log.write(f"[bold red]Error:[/] {response.content}")

        log.write("")
        self.update_status()

    async def handle_command(self, text: str, log: RichLog) -> None:
        """Handle chat commands."""
        parts = text[1:].split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "help":
            log.write("[bold cyan]Commands:[/]")
            log.write("  /help       - Show this help")
            log.write("  /clear      - Clear chat history")
            log.write("  /tokens N   - Set max tokens (e.g., /tokens 1000)")
            log.write("  /model      - Show current model")
            log.write("  /exit       - Exit chat")
            log.write("")

        elif cmd == "clear":
            self.messages.clear()
            self.total_tokens = 0
            log.clear()
            log.write("[dim]Chat cleared.[/]")
            log.write("")
            self.update_status()

        elif cmd == "tokens":
            if arg:
                try:
                    new_tokens = int(arg)
                    self.app.config_manager.set_max_tokens(new_tokens)
                    log.write(f"[green]Max tokens set to {new_tokens}[/]")
                except ValueError:
                    log.write(f"[red]Invalid number: {arg}[/]")
            else:
                current = self.app.config_manager.get_max_tokens()
                log.write(f"[cyan]Current max tokens: {current}[/]")
            log.write("")
            self.update_status()

        elif cmd == "model":
            log.write(f"[cyan]Model: {self.model_id}[/]")
            log.write("")

        elif cmd == "exit":
            self.app.pop_screen()

        else:
            log.write(f"[yellow]Unknown command: /{cmd}[/]")
            log.write("[dim]Type /help for available commands[/]")
            log.write("")

    def action_clear_chat(self) -> None:
        """Clear chat via keyboard shortcut."""
        log = self.query_one("#chat-log", RichLog)
        self.messages.clear()
        self.total_tokens = 0
        log.clear()
        log.write("[dim]Chat cleared.[/]")
        log.write("")
        self.update_status()

    def action_set_tokens(self) -> None:
        """Prompt for new token count."""
        log = self.query_one("#chat-log", RichLog)
        current = self.app.config_manager.get_max_tokens()
        log.write(f"[cyan]Current max tokens: {current}[/]")
        log.write("[dim]Use /tokens N to change (e.g., /tokens 1000)[/]")
        log.write("")
