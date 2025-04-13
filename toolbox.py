#!/usr/bin/env python3
import uuid
import logging
from pathlib import Path
from typing import Dict, List
import yaml
import requests
from datetime import datetime
from unittest.mock import MagicMock

from config import Config

logger = logging.getLogger(__name__)

class Toolbox:
    """Collection of utility functions and tools for Agents."""

    def __init__(self):
        """Initialize the toolbox with required settings."""
        self.base_url = "http://localhost:11434/api"
        self.model = Config.MODEL_CONFIG.get("model", "mistral")
        if Config.is_test_environment():
            self.client = MagicMock()
        self.model_config = Config.get_model_config()

    def write_markdown(self, file_path: Path, content: str) -> None:
        """Write content to a markdown file."""
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            logger.debug(f"Wrote content to {file_path}")
        except Exception as e:
            logger.error(f"Error writing to {file_path}: {str(e)}")
            raise

    def append_chapter(self, text: str) -> str:
        """Create a new chapter file and append text to it."""
        save_path = Path(Config.SAVES_DIR)
        chapters = sorted(save_path.glob(f"{Config.CHAPTER_PREFIX}*.md"))
        next_num = len(chapters) + 1

        chapter_path = save_path / f"{Config.CHAPTER_PREFIX}{next_num}{Config.CHAPTER_EXT}"
        self.write_markdown(chapter_path, text)
        return str(chapter_path)

    def update_links_index(self, from_file: Path, links: List[Dict]) -> None:
        """Update the links index with new relationships."""
        links_file = Config.get_links_path(from_file.parent.name)
        try:
            if links_file.exists():
                with open(links_file) as f:
                    existing_links = yaml.safe_load(f) or {}
            else:
                existing_links = {}

            existing_links[str(from_file)] = links

            with open(links_file, 'w') as f:
                yaml.safe_dump(existing_links, f)

            logger.debug(f"Updated links index for {from_file}")
        except Exception as e:
            logger.error(f"Error updating links index: {str(e)}")
            raise

    def generate_uuid(self) -> str:
        """Generate a unique identifier."""
        return str(uuid.uuid4())

    def check_ollama_status(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/version")
            return response.status_code == 200
        except:
            return False

    def list_available_models(self) -> List[str]:
        """Get list of available Ollama models."""
        try:
            response = requests.get(f"{self.base_url}/tags")
            if response.status_code == 200:
                return [model["name"] for model in response.json()["models"]]
            return []
        except:
            return []

    def pull_model(self, model_name: str) -> bool:
        """Pull a new model from Ollama."""
        try:
            response = requests.post(
                f"{self.base_url}/pull",
                json={"name": model_name}
            )
            return response.status_code == 200
        except:
            return False

    def invoke_llm(self, prompt: str, **kwargs) -> str:
        """Send a prompt to Ollama and return the response."""
        try:
            # Merge default config with any overrides
            config = self.model_config.copy()
            config.update(kwargs)

            if Config.is_test_environment():
                return self._mock_llm_response(prompt)

            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": config.get("temperature", 0.7),
                        "top_p": config.get("top_p", 0.9),
                    }
                }
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                raise Exception(f"Ollama API error: {response.text}")

        except Exception as e:
            logger.error(f"Error invoking Ollama: {str(e)}")
            raise

    def _mock_llm_response(self, prompt: str) -> str:
        """Return mock responses for testing."""
        return f"Mock response for prompt: {prompt[:50]}..."

    def get_story_prompt(self, current_text: str, choice: str) -> str:
        """Generate a story continuation prompt."""
        return f"Continue the story based on:\n{current_text}\nChosen action: {choice}"

    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    def get_choices_prompt(self, current_text: str, world_state: Dict) -> str:
        """Generate a prompt for choice generation."""
        return f"Generate choices based on:\n{current_text}\nWorld state: {world_state}"

    def parse_choices(self, response: str) -> List[str]:
        """Parse choices from LLM response."""
        choices = [c.strip() for c in response.split('\n') if c.strip()]
        return choices[:Config.MAX_CHOICES]

    def read_markdown(self, file_path: str) -> str:
        """Read content from markdown file."""
        with open(file_path) as f:
            return f.read()

    def get_links_prompt(self, content: str) -> str:
        """Generate prompt for link analysis."""
        return f"Analyze narrative links in:\n{content}"

    def parse_links(self, response: str) -> List[str]:
        """Parse narrative links from LLM response."""
        return [link.strip() for link in response.split('\n') if link.strip()]

    def get_lore_prompt(self, topic: str, context: Dict) -> str:
        """Generate prompt for lore generation."""
        return f"Generate lore about {topic} in context:\n{context}"

    def format_lore(self, response: str) -> str:
        """Format lore response."""
        return response.strip()

if __name__ == "__main__":
    # Simple test of toolbox functionality
    toolbox = Toolbox()
    test_path = Path("test.md")
    toolbox.write_markdown(test_path, "# Test Content")
    print(f"Test file created: {test_path.exists()}")
    test_path.unlink()  # Cleanup
