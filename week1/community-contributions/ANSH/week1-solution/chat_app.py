"""
chat_app.py — TUI Chat Interface for the AI Tutor
Run with: python chat_app.py
"""

from __future__ import annotations

from typing import Generator

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Footer, Header, Input, Markdown as MarkdownWidget, Static
from textual import work

from tutor import Constants, Tutor

# ---------------------------------------------------------------------------
# Static content
# ---------------------------------------------------------------------------

WELCOME_MD = f"""\
# 🎓 AI Tutor  ·  `{Constants.MODEL}`

I'm here to help you build **genuine, lasting understanding** of technical topics —
software engineering, machine learning, data science, and more.

**Quick start**
- Just type a question and press **Enter**
- Use `/context path/to/file.py` to load a file you want to study
- Use `/context <text>` to paste in inline reference material
- Type `/help` to see all commands

*What would you like to learn today?*
"""

HELP_MD = """\
## 📖 Available Commands

| Command | Description |
|---|---|
| `/context <text>` | Set inline text as session context |
| `/context path/to/file` | Load a file's content as context |
| `/show-context` | Preview the currently active context |
| `/clear` | Wipe the chat and reset session history |
| `/exit` | Quit the application |
| `/help` | Show this message |

## ⌨️  Keyboard Shortcuts

| Key | Action |
|---|---|
| `Enter` | Send message |
| `Ctrl+L` | Clear chat |
| `Ctrl+C` | Quit |
"""


# ---------------------------------------------------------------------------
# Widget definitions
# ---------------------------------------------------------------------------

class UserBubble(Vertical):
    """A styled bubble for the learner's message."""

    DEFAULT_CSS = """
    UserBubble {
        margin: 1 0 0 0;
        padding: 0 2 1 2;
        background: #1c2128;
        border-left: thick #58a6ff;
        height: auto;
    }
    UserBubble .bubble-label {
        color: #58a6ff;
        text-style: bold;
        margin-bottom: 1;
    }
    UserBubble .bubble-content {
        color: #cdd9e5;
    }
    """

    def __init__(self, text: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._text = text

    def compose(self) ->  Generator[ComposeResult, None, None]:
        yield Static("You  ▶", classes="bubble-label")
        yield Static(self._text, classes="bubble-content")


class TutorBubble(Vertical):
    """A styled bubble for the tutor's response (renders Markdown)."""

    DEFAULT_CSS = """
    TutorBubble {
        margin: 1 0 0 0;
        padding: 0 2 1 2;
        background: #161b22;
        border-left: thick #3fb950;
        height: auto;
    }
    TutorBubble .bubble-label {
        color: #3fb950;
        text-style: bold;
        margin-bottom: 1;
    }
    TutorBubble Markdown {
        color: #cdd9e5;
        background: #161b22;
    }
    """

    def __init__(self, text: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._text = text

    def compose(self) ->  Generator[ComposeResult, None, None]:
        yield Static("Tutor  ▶", classes="bubble-label")
        yield MarkdownWidget(self._text)


class SystemMessage(Static):
    """Dim centred line for command feedback / errors."""

    DEFAULT_CSS = """
    SystemMessage {
        color: #8b949e;
        text-align: center;
        padding: 0 2;
        margin: 0 0;
        height: auto;
    }
    """

    def __init__(self, text: str, **kwargs) -> None:
        super().__init__(text, **kwargs)  # type: ignore[arg-type]


class ThinkingBubble(Static):
    """Animated spinner shown while the LLM call is in-flight."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    DEFAULT_CSS = """
    ThinkingBubble {
        color: #e3b341;
        padding: 0 2;
        margin: 1 0 0 0;
        height: auto;
    }
    """

    def on_mount(self) -> None:
        self._frame = 0
        self.set_interval(0.1, self._tick)
        self._refresh()

    def _tick(self) -> None:
        self._frame = (self._frame + 1) % len(self.FRAMES)
        self._refresh()

    def _refresh(self) -> None:
        self.update(f"{self.FRAMES[self._frame]}  Tutor is thinking…")


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class TutorApp(App):
    """AI Tutor — TUI chat interface powered by Ollama."""

    TITLE = "🎓 AI Tutor"
    SUB_TITLE = "Type /help for commands"

    CSS = """
    Screen {
        background: #0d1117;
        layout: vertical;
    }

    Header {
        background: #161b22;
        color: #58a6ff;
    }

    Footer {
        background: #161b22;
        color: #8b949e;
    }

    /* ── Chat scroll area ── */
    #chat-view {
        height: 1fr;
        background: #0d1117;
        padding: 1 2;
        overflow-y: auto;
    }

    /* Welcome markdown */
    .welcome {
        padding: 0 0 1 0;
        color: #8b949e;
        background: #0d1117;
    }

    /* ── Input bar ── */
    #input-bar {
        dock: bottom;
        height: auto;
        background: #161b22;
        border-top: solid #21262d;
        padding: 0 1;
    }

    #chat-input {
        height: 3;
        background: #0d1117;
        border: solid #30363d;
        color: #e6edf3;
    }

    #chat-input:focus {
        border: solid #58a6ff;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_chat", "Clear"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.tutor = Tutor()
        self.history: str = ""
        self.context: str = ""
        self.turn: int = 0
        self._thinking_widget: ThinkingBubble | None = None

    # ── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Header()
        with ScrollableContainer(id="chat-view"):
            yield MarkdownWidget(WELCOME_MD, classes="welcome")
        with Horizontal(id="input-bar"):
            yield Input(
                placeholder=" Ask a question… (/help for commands)",
                id="chat-input",
            )
        yield Footer()

    # ── Input routing ─────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.clear()
        if not text:
            return
        if text.startswith("/"):
            self._handle_command(text)
        else:
            self._send_question(text)

    # ── Slash-command dispatcher ──────────────────────────────────────────────

    def _handle_command(self, raw: str) -> None:
        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        dispatch = {
            "/clear":        lambda: self.action_clear_chat(),
            "/exit":         lambda: self.exit(),
            "/help":         lambda: self._add_tutor_bubble(HELP_MD),
            "/show-context": lambda: self._cmd_show_context(),
            "/context":      lambda: self._cmd_set_context(arg),
        }

        handler = dispatch.get(cmd)
        if handler:
            handler()
        else:
            self._add_system(f"⚠️  Unknown command `{cmd}`. Type `/help` for all commands.")

    # ── /context ──────────────────────────────────────────────────────────────

    def _cmd_set_context(self, arg: str) -> None:
        """
        How it works
        ────────────
        1. If `arg` looks like a readable file path → read the whole file.
           This is the "study a codebase / document" flow.
        2. Otherwise treat `arg` as inline text.

        The loaded text is stored in `self.context`, which gets injected into
        every subsequent `tutor.ask()` call as the RAG context block.
        """
        if not arg:
            self._add_system("Usage: `/context <text>` or `/context path/to/file`")
            return

        path = Path(arg)
        if path.exists() and path.is_file():
            try:
                self.context = path.read_text(encoding="utf-8")
                word_count = len(self.context.split())
                self._add_system(
                    f"✅  Context loaded from **{path.name}** "
                    f"({len(self.context):,} chars · ~{word_count:,} words)"
                )
            except OSError as exc:
                self._add_system(f"❌  Could not read file: {exc}")
        else:
            self.context = arg
            self._add_system(
                f"✅  Inline context set ({len(self.context):,} chars)"
            )

    def _cmd_show_context(self) -> None:
        if not self.context:
            self._add_system("No context is set. Use `/context` to add one.")
            return
        ctx = str(self.context)
        preview = (ctx[:400] + "…") if len(ctx) > 400 else ctx
        self._add_tutor_bubble(
            f"**Active context** ({len(self.context):,} chars)\n\n```\n{preview}\n```"
        )

    # ── LLM call — runs in a background thread so the UI never blocks ─────────

    @work(thread=True)
    def _send_question(self, question: str) -> None:
        """
        How the threading works
        ───────────────────────
        `@work(thread=True)` runs this method in a thread-pool worker,
        completely off the main UI thread.

        Inside a worker you cannot mutate the UI directly — Textual is not
        thread-safe. Instead you use `self.call_from_thread(fn, *args)` which
        schedules `fn` to run safely on the event loop.

        Flow:
          1. Mount UserBubble  (call_from_thread)
          2. Mount ThinkingBubble spinner (call_from_thread)
          3. Block on tutor.ask()  ← this is the slow part, fine on a thread
          4. Remove spinner, mount TutorBubble  (call_from_thread)
          5. Update turn counter in subtitle
        """
        self.call_from_thread(self._add_user_bubble, question)
        self.call_from_thread(self._show_thinking)

        try:
            answer = self.tutor.ask(
                question=question,
                context=self.context,
                history=self.history,
            )
            self.history += f"\nQ: {question}\nA: {answer}\n"
            self.turn += 1
            self.call_from_thread(self._hide_thinking)
            self.call_from_thread(self._add_tutor_bubble, answer)
            self.call_from_thread(self._update_subtitle)

        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(self._hide_thinking)
            self.call_from_thread(
                self._add_system,
                f"❌  Model error: {exc}\n\n"
                "Check that Ollama is running (`ollama serve`) and the model is pulled.",
            )

    # ── UI mutation helpers (always called on the main thread) ────────────────

    def _add_user_bubble(self, text: str) -> None:
        self.query_one("#chat-view").mount(UserBubble(text))
        self._scroll_bottom()

    def _add_tutor_bubble(self, text: str) -> None:
        self.query_one("#chat-view").mount(TutorBubble(text))
        self._scroll_bottom()

    def _add_system(self, text: str) -> None:
        self.query_one("#chat-view").mount(SystemMessage(text))
        self._scroll_bottom()

    def _show_thinking(self) -> None:
        widget = ThinkingBubble()
        self._thinking_widget = widget
        self.query_one("#chat-view").mount(widget)
        self._scroll_bottom()

    def _hide_thinking(self) -> None:
        widget = self._thinking_widget
        if widget is not None:
            widget.remove()
            self._thinking_widget = None

    def _scroll_bottom(self) -> None:
        self.query_one("#chat-view").scroll_end(animate=False)

    def _update_subtitle(self) -> None:
        self.sub_title = f"Turn {self.turn}  ·  /help for commands"

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_clear_chat(self) -> None:
        """Reset the entire session."""
        self.history = ""
        self.context = ""
        self.turn = 0
        self._thinking_widget = None
        chat = self.query_one("#chat-view")
        chat.remove_children()
        chat.mount(MarkdownWidget(WELCOME_MD, classes="welcome"))
        self._add_system("🗑️   Chat cleared — history, context and turn counter reset.")
        self.sub_title = "Type /help for commands"


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    TutorApp().run()
