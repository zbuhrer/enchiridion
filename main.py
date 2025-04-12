#!/usr/bin/env python3
import curses
import sys
import logging

from typing import Optional
from game import Game
from renderer import Renderer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='enchiridion.log'
)
logger = logging.getLogger(__name__)

def setup_curses() -> tuple[curses.window, Renderer]:
    """Initialize curses and return the main screen and renderer."""
    screen = curses.initscr()
    curses.noecho()
    curses.cbreak()
    screen.keypad(True)
    curses.start_color()
    curses.use_default_colors()

    # Initialize color pairs
    curses.init_pair(1, curses.COLOR_GREEN, -1)  # Choices
    curses.init_pair(2, curses.COLOR_YELLOW, -1) # Highlights
    curses.init_pair(3, curses.COLOR_RED, -1)    # Errors/Warnings

    return screen, Renderer(screen)

def cleanup_curses(screen: Optional[curses.window] = None) -> None:
    """Restore terminal to original state."""
    if screen:
        screen.keypad(False)
    curses.echo()
    curses.nocbreak()
    curses.endwin()

def main() -> None:
    """Main entry point for the Enchiridion game."""
    screen = None
    try:
        # Initialize curses and renderer
        screen, renderer = setup_curses()

        # Load or create new game
        game = Game()
        if len(sys.argv) > 1 and sys.argv[1] == '--load':
            game.load()
        else:
            game.new()

        # Main game loop
        while True:
            # Render current state
            renderer.clear()
            current_text = game.get_current_text()
            choices = game.get_current_choices()

            renderer.render_markdown(current_text)
            selected_choice = renderer.render_choices(choices)

            if selected_choice.lower() == 'quit':
                break

            # Advance game state based on choice
            game.advance(selected_choice)
            game.save()  # Auto-save after each choice

            # Check for game end condition
            if game.is_finished():
                renderer.show_ending()
                break

    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    finally:
        # Clean up and exit
        cleanup_curses(screen)
        sys.exit(0)

if __name__ == "__main__":
    main()
