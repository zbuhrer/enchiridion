#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Configuration settings for the Enchiridion game."""

    # Base paths
    BASE_DIR = Path(__file__).parent.resolve()
    SAVES_DIR = BASE_DIR / "saves"
    TEMPLATES_DIR = BASE_DIR / "templates"

    # Ensure required directories exist
    SAVES_DIR.mkdir(exist_ok=True)
    TEMPLATES_DIR.mkdir(exist_ok=True)

    # File extensions and patterns
    CHAPTER_PREFIX = "chapter_"
    CHAPTER_EXT = ".md"
    WORLD_STATE_FILE = "world.yaml"
    LINKS_FILE = "links.yaml"

    # Model settings
    MODEL_CONFIG: Dict[str, Any] = {
        "model": "qwen2.5",  # Default model
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 2048  # Maximum tokens per request
    }

    # Game settings
    MAX_CHOICES = 4  # Maximum number of choices to present
    MAX_CHAPTERS = 50  # Maximum number of chapters before forced ending
    AUTO_SAVE = True  # Whether to auto-save after each choice

    # Display settings
    MARKDOWN_WIDTH = 80  # Maximum width for markdown text
    CHOICE_PREFIX = "> "  # Prefix for choice options

    # Debug settings
    DEBUG = os.getenv("ENCHIRIDION_DEBUG", "0") == "1"
    TEST_MODE = os.getenv("ENCHIRIDION_TEST", "0") == "1"

    @classmethod
    def get_chapter_path(cls, save_uuid: str, chapter_num: int) -> Path:
        """Get the path for a specific chapter file."""
        return cls.SAVES_DIR / save_uuid / f"{cls.CHAPTER_PREFIX}{chapter_num}{cls.CHAPTER_EXT}"

    @classmethod
    def get_world_state_path(cls, save_uuid: str) -> Path:
        """Get the path for the world state file."""
        return cls.SAVES_DIR / save_uuid / cls.WORLD_STATE_FILE

    @classmethod
    def get_links_path(cls, save_uuid: str) -> Path:
        """Get the path for the links file."""
        return cls.SAVES_DIR / save_uuid / cls.LINKS_FILE

    @classmethod
    def get_model_config(cls, override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get model configuration with optional overrides."""
        config = cls.MODEL_CONFIG.copy()
        if override:
            config.update(override)
        return config

    @classmethod
    def validate_paths(cls) -> bool:
        """Validate that all required paths exist."""
        required_paths = [
            cls.BASE_DIR,
            cls.SAVES_DIR,
            cls.TEMPLATES_DIR
        ]
        return all(path.exists() for path in required_paths)

    @classmethod
    def is_test_environment(cls) -> bool:
        """Check if running in test environment."""
        return cls.TEST_MODE

    @classmethod
    def get_debug_info(cls) -> Dict[str, Any]:
        """Get debug information about current configuration."""
        return {
            "base_dir": str(cls.BASE_DIR),
            "saves_dir": str(cls.SAVES_DIR),
            "templates_dir": str(cls.TEMPLATES_DIR),
            "debug_mode": cls.DEBUG,
            "test_mode": cls.TEST_MODE,
            "model": cls.MODEL_CONFIG["model"],
            "auto_save": cls.AUTO_SAVE
        }

if __name__ == "__main__":
    # Simple test to verify configuration
    print("Configuration test:")
    print(f"Base directory: {Config.BASE_DIR}")
    print(f"Saves directory: {Config.SAVES_DIR}")
    print(f"Templates directory: {Config.TEMPLATES_DIR}")
    print(f"Paths valid: {Config.validate_paths()}")
    print(f"Debug info: {Config.get_debug_info()}")
