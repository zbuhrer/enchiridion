#!/usr/bin/env python3
import curses
import textwrap
from typing import List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Renderer:
    """Handles the display and user interface using curses."""

    def __init__(self, screen: curses.window):
        """Initialize the renderer with a curses screen."""
        self.screen = screen
        self.height, self.width = screen.getmaxyx()
        self.text_win = curses.newwin(self.height - 4, self.width, 0, 0)
        self.choice_win = curses.newwin(4, self.width, self.height - 4, 0)

    def clear(self) -> None:
        """Clear all windows."""
        self.screen.clear()
        self.text_win.clear()
        self.choice_win.clear()
        self.screen.refresh()

    def render_markdown(self, text: str) -> None:
        """Render markdown text in the text window."""
        try:
            # Wrap text to fit window width
            wrapped_lines = []
            for line in text.split('\n'):
                if line.strip():
                    wrapped = textwrap.wrap(line, self.width - 2)
                    wrapped_lines.extend(wrapped)
                else:
                    wrapped_lines.append('')

            # Display text
            for i, line in enumerate(wrapped_lines):
                if i < self.height - 4:  # Leave room for choices
                    self.text_win.addstr(i, 1, line)

            self.text_win.refresh()

        except Exception as e:
            logger.error(f"Error rendering markdown: {str(e)}", exc_info=True)

    def render_choices(self, choices: List[str]) -> str:
        """Display choices and handle selection."""
        try:
            current_choice = 0
            while True:
                # Display choices
                self.choice_win.clear()
                for i, choice in enumerate(choices):
                    if i < 4:  # Maximum 4 choices
                        prefix = '> ' if i == current_choice else '  '
                        attr = curses.A_REVERSE if i == current_choice else curses.A_NORMAL
                        self.choice_win.addstr(i, 1, f"{prefix}{choice}", attr)

                self.choice_win.refresh()

                # Handle input
                key = self.screen.getch()
                if key in [curses.KEY_UP, ord('k')]:
                    current_choice = (current_choice - 1) % len(choices)
                elif key in [curses.KEY_DOWN, ord('j')]:
                    current_choice = (current_choice + 1) % len(choices)
                elif key in [curses.KEY_ENTER, ord('\n'), ord(' ')]:
                    return choices[current_choice]

        except Exception as e:
            logger.error(f"Error rendering choices: {str(e)}", exc_info=True)
            return "quit"

    def show_ending(self) -> None:
        """Display the game ending sequence."""
        try:
            self.clear()
            msg = "The End"
            y = self.height // 2
            x = (self.width - len(msg)) // 2
            self.screen.addstr(y, x, msg, curses.A_BOLD)
            self.screen.refresh()
            self.screen.getch()

        except Exception as e:
            logger.error(f"Error showing ending: {str(e)}", exc_info=True)

    def show_error(self, message: str) -> None:
        """Display an error message."""
        try:
            self.clear()
            wrapped = textwrap.wrap(message, self.width - 4)
            for i, line in enumerate(wrapped):
                if i < self.height - 2:
                    self.screen.addstr(i + 1, 2, line, curses.color_pair(3))
            self.screen.refresh()
            self.screen.getch()

        except Exception as e:
            logger.error(f"Error showing error message: {str(e)}", exc_info=True)

    def get_dimensions(self) -> Tuple[int, int]:
        """Get current screen dimensions."""
        return self.height, self.width

    def resize(self) -> None:
        """Handle terminal resize events."""
        self.height, self.width = self.screen.getmaxyx()
        self.text_win.resize(self.height - 4, self.width)
        self.choice_win.mvwin(self.height - 4, 0)
        self.choice_win.resize(4, self.width)
        self.screen.clear()
        self.screen.refresh()
