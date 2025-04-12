#!/usr/bin/env python3
import yaml
from pathlib import Path
from typing import Dict, Any
import logging
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)

class StateManager:
    """Manages game world state and story progression."""

    def __init__(self):
        self.world_state: Dict[str, Any] = {
            'player': {},
            'world': {},
            'story': {
                'chapters': 0,
                'choices': [],
                'endings_seen': set(),
            },
            'meta': {
                'created': '',
                'last_saved': '',
                'version': '1.0'
            }
        }

    def initialize_world_state(self, save_path: Path) -> None:
        """Initialize a new world state."""
        self.world_state['meta']['created'] = datetime.now().isoformat()
        self.world_state['meta']['last_saved'] = datetime.now().isoformat()
        self.save_world_state(save_path)

    def load_world_state(self, save_path: Path) -> None:
        """Load world state from YAML file."""
        world_state_path = Config.get_world_state_path(save_path.name)
        try:
            with open(world_state_path, 'r') as f:
                loaded_state = yaml.safe_load(f)
                if loaded_state:
                    self.world_state = loaded_state
                    logger.info(f"Loaded world state from {world_state_path}")
        except FileNotFoundError:
            logger.warning(f"No world state found at {world_state_path}, using default")
        except Exception as e:
            logger.error(f"Error loading world state: {str(e)}", exc_info=True)
            raise

    def save_world_state(self, save_path: Path) -> None:
        """Save current world state to YAML file."""
        if isinstance(save_path, str):
            save_path = Path(save_path)

        if Config.is_test_environment():
            save_dir = save_path
        else:
            save_dir = Config.SAVES_DIR / save_path.name

        save_dir.mkdir(parents=True, exist_ok=True)
        world_state_path = save_dir / Config.WORLD_STATE_FILE

        try:
            self.world_state['meta']['last_saved'] = datetime.now().isoformat()
            with open(world_state_path, 'w') as f:
                yaml.safe_dump(self.world_state, f)
            logger.info(f"Saved world state to {world_state_path}")
        except Exception as e:
            logger.error(f"Error saving world state: {str(e)}", exc_info=True)
            raise

    def get_world_state(self) -> Dict[str, Any]:
        """Get current world state."""
        return self.world_state.copy()

    def update_world_state(self, changes: Dict[str, Any]) -> None:
        """Update world state with new values."""
        def deep_update(target: Dict, source: Dict) -> None:
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_update(target[key], value)
                else:
                    target[key] = value

        deep_update(self.world_state, changes)
        logger.debug(f"Updated world state with changes: {changes}")

    def apply_choice(self, choice: str) -> None:
        """Apply the effects of a player choice to the world state."""
        self.world_state['story']['choices'].append(choice)
        self.world_state['story']['chapters'] += 1
        logger.debug(f"Applied choice: {choice}")

    def is_end_state(self) -> bool:
        """Check if the current state is an ending."""
        # Check various end conditions
        if self.world_state['story']['chapters'] >= Config.MAX_CHAPTERS:
            return True

        # Add other ending conditions here
        return False

    def record_ending(self, ending_id: str) -> None:
        """Record that a specific ending has been seen."""
        self.world_state['story']['endings_seen'].add(ending_id)

    def get_choices_history(self) -> list:
        """Get the history of choices made."""
        return self.world_state['story']['choices'].copy()

    def get_chapter_count(self) -> int:
        """Get the current chapter count."""
        return self.world_state['story']['chapters']

    def get_meta_info(self) -> Dict[str, str]:
        """Get meta information about the current game state."""
        return self.world_state['meta'].copy()
