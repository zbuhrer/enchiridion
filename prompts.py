#!/usr/bin/env python3
from typing import Dict, Optional
import yaml
from pathlib import Path

class PromptManager:
    """Manages prompt templates and system messages for agents."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize the prompt manager."""
        self.templates_dir = templates_dir
        self._load_templates()

    def _load_templates(self) -> None:
        """Load prompt templates from files."""
        self.templates = {
            'story': {
                'system': """You are a narrative co-creator tasked with generating interactive
                story segments. Focus on rich descriptions, meaningful choices, and maintaining
                narrative consistency.""",
                'chapter': """Based on the current text and chosen action '{choice}',
                continue the story with a new chapter that flows naturally and presents
                meaningful consequences for the player's choice."""
            },
            'lore': {
                'system': """You are a lorekeeper responsible for maintaining and expanding
                the game's mythology and background information. Ensure consistency and depth
                in all lore entries.""",
                'query': """Provide detailed information about {topic} within the context
                of the current world state. Include relevant connections and implications."""
            },
            'link': {
                'system': """You analyze story text to identify and track important narrative
                elements, themes, and connections between different story segments.""",
                'analyze': """Analyze the provided text and identify key elements that should
                be tracked for continuity and referenced in future story segments."""
            }
        }

    def get_story_prompt(self, context: Dict) -> str:
        """Generate a story continuation prompt."""
        template = self.templates['story']['chapter']
        return template.format(**context)

    def get_lore_prompt(self, topic: str) -> str:
        """Generate a lore query prompt."""
        template = self.templates['lore']['query']
        return template.format(topic=topic)

    def get_link_prompt(self) -> str:
        """Generate a link analysis prompt."""
        return self.templates['link']['analyze']

    def system_message(self, role: str) -> str:
        """Get the system message for a specific agent role."""
        return self.templates[role]['system']

    def save_templates(self) -> None:
        """Save current templates to files."""
        if self.templates_dir:
            with open(self.templates_dir / 'templates.yaml', 'w') as f:
                yaml.safe_dump(self.templates, f)

    def load_custom_templates(self, path: Path) -> None:
        """Load custom templates from a YAML file."""
        with open(path, 'r') as f:
            custom_templates = yaml.safe_load(f)
            self.templates.update(custom_templates)

    def get_completion_params(self, role: str) -> Dict:
        """Get role-specific completion parameters."""
        params = {
            'story': {'temperature': 0.7, 'max_tokens': 2000},
            'lore': {'temperature': 0.5, 'max_tokens': 1000},
            'link': {'temperature': 0.3, 'max_tokens': 500}
        }
        return params.get(role, {'temperature': 0.7, 'max_tokens': 1000})
