#!/usr/bin/env python3
import uuid
from pathlib import Path
from typing import List, Optional
import logging

from agents import StoryAgent, LinkAgent, LoreAgent
from state import StateManager
from toolbox import Toolbox
from config import Config

logger = logging.getLogger(__name__)

class Game:
    """Core game logic and state management."""

    def __init__(self):
        self.uuid: str = ""
        self.toolbox = Toolbox()
        self.state = StateManager()

        # Initialize agents
        self.story_agent = StoryAgent(self.toolbox)
        self.link_agent = LinkAgent(self.toolbox)
        self.lore_agent = LoreAgent(self.toolbox)

        # Game state
        self.current_chapter: str = ""
        self.save_path: Optional[Path] = None

    def new(self) -> None:
        """Create a new game instance."""
        self.uuid = str(uuid.uuid4())
        self.save_path = Path(Config.SAVES_DIR) / self.uuid
        self.save_path.mkdir(parents=True, exist_ok=True)

        # Initialize new game state
        self.state.initialize_world_state(self.save_path)

        try:
            # Generate initial chapter
            initial_story = self.story_agent.call(
                current_text="",
                choice="begin"
            )

            # Create first chapter file and set current chapter
            self.current_chapter = self.toolbox.append_chapter(initial_story['text'])

            # Ensure the chapter file exists
            if not Path(self.current_chapter).exists():
                raise ValueError("Failed to create initial chapter file")

            # Save initial state
            self.save()

            logger.info(f"New game created with UUID: {self.uuid}")

        except Exception as e:
            logger.error(f"Error creating new game: {str(e)}")
            raise

    def load(self, save_uuid: Optional[str] = None) -> None:
        """Load an existing game state."""
        if save_uuid:
            self.uuid = save_uuid
        else:
            # Find most recent save if none specified
            saves_dir = Path(Config.SAVES_DIR)
            if not saves_dir.exists():
                raise FileNotFoundError("No saved games found")

            saves = sorted(saves_dir.glob("*"), key=lambda x: x.stat().st_mtime)
            if not saves:
                raise FileNotFoundError("No saved games found")

            self.uuid = saves[-1].name

        self.save_path = Path(Config.SAVES_DIR) / self.uuid

        # Load game state
        self.state.load_world_state(self.save_path)

        # Find current chapter
        chapters = sorted(self.save_path.glob(f"{Config.CHAPTER_PREFIX}*.md"))
        if not chapters:
            raise ValueError(f"No chapters found in save directory: {self.save_path}")

        self.current_chapter = str(chapters[-1])

        if not Path(self.current_chapter).exists():
            raise FileNotFoundError(f"Chapter file not found: {self.current_chapter}")

        logger.info(f"Loaded game with UUID: {self.uuid}")

    def save(self) -> None:
        """Save current game state."""
        if not self.save_path:
            raise ValueError("Game must be initialized or loaded before saving")

        self.state.save_world_state(self.save_path)
        logger.info(f"Game saved to {self.save_path}")

    def advance(self, choice: str) -> None:
        """Advance game state based on player choice."""
        try:
            # Get current story context
            current_text = self.get_current_text()

            # Generate next story segment
            story_result = self.story_agent.call(
                current_text=current_text,
                choice=choice
            )

            # Update world state based on choice
            self.state.apply_choice(choice)

            # Append new chapter
            self.current_chapter = self.toolbox.append_chapter(story_result['text'])

            # Update story links
            self.link_agent.call([self.current_chapter])

            # Auto-save if enabled
            if Config.AUTO_SAVE:
                self.save()

            logger.info(f"Advanced game state with choice: {choice}")

        except Exception as e:
            logger.error(f"Error advancing game state: {str(e)}", exc_info=True)
            raise

    def get_current_text(self) -> str:
        """Get the current chapter text."""
        if not self.current_chapter:
            return ""

        try:
            with open(self.current_chapter, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading current chapter: {str(e)}", exc_info=True)
            return ""

    def get_current_choices(self) -> List[str]:
        """Get available choices for the current game state."""
        current_text = self.get_current_text()
        world_state = self.state.get_world_state()

        # Generate choices based on current context
        try:
            choices = self.story_agent.get_choices(current_text, world_state)
            choices.append("quit")  # Always add quit option
            return choices
        except Exception as e:
            logger.error(f"Error getting choices: {str(e)}", exc_info=True)
            return ["quit"]

    def is_finished(self) -> bool:
        """Check if the game has reached an ending."""
        return self.state.is_end_state()

    def get_lore(self, topic: str) -> str:
        """Get lore information about a specific topic."""
        try:
            return self.lore_agent.call(
                lore_id=topic,
                context=self.state.get_world_state()
            )
        except Exception as e:
            logger.error(f"Error retrieving lore: {str(e)}", exc_info=True)
            return ""
