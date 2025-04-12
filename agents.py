#!/usr/bin/env python3
from typing import Dict, List, Any
import logging
from abc import ABC, abstractmethod

from toolbox import Toolbox
from config import Config

logger = logging.getLogger(__name__)

class Agent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, toolbox: Toolbox):
        self.tools = toolbox

    @abstractmethod
    def call(self, *args, **kwargs) -> Any:
        """Execute the agent's primary function."""
        pass

class StoryAgent(Agent):
    """Agent responsible for generating story content and choices."""

    def call(self, current_text: str, choice: str) -> Dict[str, Any]:
        """Generate next story segment based on current text and choice."""
        try:
            # Get story generation prompt
            prompt = self.tools.get_story_prompt(
                current_text=current_text,
                choice=choice
            )

            # Generate story content
            response = self.tools.invoke_llm(prompt)

            return {
                'text': response,
                'metadata': {
                    'choice': choice,
                    'timestamp': self.tools.get_timestamp()
                }
            }

        except Exception as e:
            logger.error(f"StoryAgent error: {str(e)}", exc_info=True)
            raise

    def get_choices(self, current_text: str, world_state: Dict) -> List[str]:
        """Generate available choices based on current context."""
        try:
            prompt = self.tools.get_choices_prompt(
                current_text=current_text,
                world_state=world_state
            )

            response = self.tools.invoke_llm(prompt)
            choices = self.tools.parse_choices(response)

            return choices[:Config.MAX_CHOICES]  # Limit number of choices

        except Exception as e:
            logger.error(f"Error generating choices: {str(e)}", exc_info=True)
            return ["Continue..."]  # Fallback choice

class LinkAgent(Agent):
    """Agent responsible for managing narrative links and connections."""

    def call(self, md_files: List[str]) -> Dict[str, List[str]]:
        """Analyze and update story links between markdown files."""
        try:
            links = {}
            for file_path in md_files:
                content = self.tools.read_markdown(file_path)
                prompt = self.tools.get_links_prompt(content)

                response = self.tools.invoke_llm(prompt)
                file_links = self.tools.parse_links(response)

                links[file_path] = file_links

            return links

        except Exception as e:
            logger.error(f"LinkAgent error: {str(e)}", exc_info=True)
            return {}

class LoreAgent(Agent):
    """Agent responsible for generating and maintaining world lore."""

    def call(self, lore_id: str, context: Dict) -> str:
        """Generate or retrieve lore about a specific topic."""
        try:
            prompt = self.tools.get_lore_prompt(
                topic=lore_id,
                context=context
            )

            response = self.tools.invoke_llm(prompt)
            return self.tools.format_lore(response)

        except Exception as e:
            logger.error(f"LoreAgent error: {str(e)}", exc_info=True)
            return f"No lore available for {lore_id}"
