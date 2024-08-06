import flet as ft
from flet import (
    Page, UserControl, GridView, Stack, Container, Column, Row,
    Text, TextField, IconButton, ElevatedButton, Dropdown, Tab, Tabs,
    Card, ListView, colors, icons, FontWeight, dropdown
)
import openai
import os
import json
import asyncio
from typing import List, Dict, Any

# Constants
SYSTEM_USER = "System"
AI_USER = "AI"
HUMAN_USER = "You"
DEFAULT_PADDING = 10
DEFAULT_BORDER_RADIUS = 10
DEFAULT_FONT_SIZE = 16
SMALL_FONT_SIZE = 14
EXTRA_SMALL_FONT_SIZE = 12
LARGE_FONT_SIZE = 20
GRID_RUNS_COUNT = 5
GRID_MAX_EXTENT = 150
GRID_CHILD_ASPECT_RATIO = 1
GRID_SPACING = 5
DROPDOWN_WIDTH = 200
CHAT_TAB_TEXT = "Chat"
AGENTS_TAB_TEXT = "Agents"
SELECT_AGENT_TEXT = "Select Agent"
WRITE_MESSAGE_HINT = "Write a message..."
CLOSE_BUTTON_TEXT = "Close"
SYSTEM_PROMPT_TEXT = "System Prompt:"
TOOLS_TEXT = "Tools:"
FUNCTION_TEXT = "Function:"

# Model
class Message:
    def __init__(self, user_name: str, text: str, is_user: bool):
        self.user_name = user_name
        self.text = text
        self.is_user = is_user

    def __str__(self):
        return f"{self.user_name}: {self.text}"

class Tool:
    def __init__(self, name: str, description: str, function: callable):
        self.name = name
        self.description = description
        self.function = function

class Agent:
    def __init__(self, name: str, description: str, prompt: str, tools: List[Tool]):
        self.name = name
        self.description = description
        self.prompt = prompt
        self.tools = tools

class AgentManager:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.agents: Dict[str, Agent] = {}
        self.load_agents()

    def load_agents(self):
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        for agent_config in config['agents']:
            tools = [Tool(t['name'], t['description'], eval(t['function'])) for t in agent_config['tools']]
            agent = Agent(agent_config['name'], agent_config['description'], agent_config['prompt'], tools)
            self.agents[agent.name] = agent

    def get_agent(self, name: str) -> Agent:
        return self.agents.get(name)

    def list_agents(self) -> List[str]:
        return list(self.agents.keys())

# View
class AgentCard(UserControl):
    def __init__(self, agent: Agent, on_click):
        super().__init__()
        self.agent = agent
        self.on_click = on_click

    def build(self):
        return Card(
            content=Container(
                content=Column([
                    Text(self.agent.name, weight=FontWeight.BOLD, size=DEFAULT_FONT_SIZE),
                    Text(self.agent.description, size=SMALL_FONT_SIZE),
                    Text(f"Tools: {len(self.agent.tools)}", size=EXTRA_SMALL_FONT_SIZE),
                ]),
                padding=DEFAULT_PADDING,
            ),
            on_click=lambda _: self.on_click(self.agent),
        )

class AgentModal(UserControl):
    def __init__(self, agent: Agent, on_close):
        super().__init__()
        self.agent = agent
        self.on_close = on_close

    def build(self):
        tool_cards = [self.create_tool_card(tool) for tool in self.agent.tools]
        
        return Container(
            content=Column([
                Text(self.agent.name, weight=FontWeight.BOLD, size=LARGE_FONT_SIZE),
                Text(self.agent.description, size=DEFAULT_FONT_SIZE),
                Text(SYSTEM_PROMPT_TEXT, weight=FontWeight.BOLD),
                TextField(value=self.agent.prompt, multiline=True, min_lines=3, max_lines=5, read_only=True),
                Text(TOOLS_TEXT, weight=FontWeight.BOLD),
                Column(tool_cards),
                ElevatedButton(CLOSE_BUTTON_TEXT, on_click=self.on_close),
            ]),
            padding=DEFAULT_PADDING * 2,
            bgcolor=colors.WHITE,
            border_radius=DEFAULT_BORDER_RADIUS,
        )

    def create_tool_card(self, tool: Tool):
        return Card(
            content=Container(
                content=Column([
                    Text(tool.name, weight=FontWeight.BOLD),
                    Text(tool.description),
                    Text(FUNCTION_TEXT, weight=FontWeight.BOLD),
                    TextField(value=tool.function.__name__, read_only=True),
                ]),
                padding=DEFAULT_PADDING,
            ),
        )

class AgentGallery(UserControl):
    def __init__(self, agent_manager: AgentManager):
        super().__init__()
        self.agent_manager = agent_manager
        self.modal_visible = False
        self.selected_agent = None

    def build(self):
        self.agent_cards = [AgentCard(agent, self.open_agent_modal) for agent in self.agent_manager.agents.values()]
        self.agent_grid = GridView(
            runs_count=GRID_RUNS_COUNT,
            max_extent=GRID_MAX_EXTENT,
            child_aspect_ratio=GRID_CHILD_ASPECT_RATIO,
            spacing=GRID_SPACING,
            run_spacing=GRID_SPACING,
            controls=self.agent_cards,
        )
        
        self.modal = Container(visible=False)
        
        return Stack([
            self.agent_grid,
            self.modal,
        ])

    def open_agent_modal(self, agent: Agent):
        self.selected_agent = agent
        self.modal.content = AgentModal(agent, self.close_agent_modal)
        self.modal.visible = True
        self.update()

    def close_agent_modal(self, _):
        self.modal.visible = False
        self.update()

# Controller
class ChatApp(UserControl):
    def __init__(self, agent_manager: AgentManager):
        super().__init__()
        self.agent_manager = agent_manager
        self.current_agent = None
        self.chat_view = ListView(expand=True, spacing=DEFAULT_PADDING, auto_scroll=True)
        self.new_message = TextField(hint_text=WRITE_MESSAGE_HINT, expand=True, on_submit=self.send_message)
        self.send_button = IconButton(icon=icons.SEND_ROUNDED, on_click=self.send_message)
        self.agent_dropdown = Dropdown(
            options=[dropdown.Option(agent) for agent in self.agent_manager.list_agents()],
            width=DROPDOWN_WIDTH,
            label=SELECT_AGENT_TEXT,
            on_change=self.change_agent
        )
        self.agent_gallery = AgentGallery(agent_manager)

    def build(self):
        return Column([
            Tabs(
                selected_index=0,
                tabs=[
                    Tab(
                        text=CHAT_TAB_TEXT,
                        content=Column([
                            Row([self.agent_dropdown]),
                            Container(content=self.chat_view, expand=True),
                            Row([self.new_message, self.send_button]),
                        ])
                    ),
                    Tab(
                        text=AGENTS_TAB_TEXT,
                        content=self.agent_gallery
                    ),
                ],
                expand=1
            ),
        ])

    def change_agent(self, e):
        self.current_agent = self.agent_manager.get_agent(self.agent_dropdown.value)
        self.add_message(Message(SYSTEM_USER, f"Switched to agent: {self.current_agent.name}", False))

    def send_message(self, e):
        if self.new_message.value and self.current_agent:
            self.add_message(Message(HUMAN_USER, self.new_message.value, True))
            self.new_message.value = ""
            self.new_message.focus()
            self.update()
            asyncio.create_task(self.get_ai_response())
        elif not self.current_agent:
            self.add_message(Message(SYSTEM_USER, "Please select an agent first.", False))

    def add_message(self, message: Message):
        self.chat_view.controls.append(self.render_message(message))
        self.chat_view.update()

    def render_message(self, message: Message):
        return Container(
            content=Column([
                Text(message.user_name, weight=FontWeight.BOLD),
                Text(message.text),
            ]),
            bgcolor=colors.BLUE_GREY_100 if message.is_user else colors.GREY_100,
            border_radius=DEFAULT_BORDER_RADIUS,
            padding=DEFAULT_PADDING,
            width=float("inf"),
        )

    async def get_ai_response(self):
        try:
            messages = [
                {"role": "system", "content": self.current_agent.prompt},
                {"role": "user", "content": self.chat_view.controls[-1].content.controls[1].value},
            ]
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=messages,
                functions=[{"name": tool.name, "description": tool.description} for tool in self.current_agent.tools],
                function_call="auto"
            )
            
            ai_message = response['choices'][0]['message']
            if 'function_call' in ai_message:
                function_name = ai_message['function_call']['name']
                function_args = json.loads(ai_message['function_call']['arguments'])
                tool = next(tool for tool in self.current_agent.tools if tool.name == function_name)
                result = tool.function(**function_args)
                self.add_message(Message(AI_USER, f"Called function {function_name}. Result: {result}", False))
            else:
                self.add_message(Message(AI_USER, ai_message['content'], False))
        except Exception as e:
            self.add_message(Message(SYSTEM_USER, f"Error: {str(e)}", False))

def main(page: Page):
    page.title = "AI Chat App with Dynamic Agents"
    page.theme_mode = ft.ThemeMode.LIGHT
    agent_manager = AgentManager("agents_config.json")
    chat_app = ChatApp(agent_manager)
    page.add(chat_app)

if __name__ == "__main__":
    openai.api_key = os.getenv("OPENAI_API_KEY", "lm-studio")
    openai.base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    ft.app(target=main)