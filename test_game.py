#!/usr/bin/env python3
import pytest
from pathlib import Path
import shutil
import tempfile
from unittest.mock import Mock, patch, MagicMock

from main import Game
from config import Config
from state import StateManager
from toolbox import Toolbox
from agents import StoryAgent, LinkAgent, LoreAgent
from renderer import Renderer
from task_queue import TaskQueue, TaskStatus

# Test fixtures
@pytest.fixture
def mock_curses():
    """Mock curses functionality globally."""
    curses_mock = MagicMock()
    curses_mock.LINES = 24
    curses_mock.COLS = 80
    curses_mock.COLOR_GREEN = 2
    curses_mock.COLOR_BLACK = 0
    curses_mock.COLOR_YELLOW = 3
    curses_mock.COLOR_CYAN = 6
    curses_mock.A_NORMAL = 0
    curses_mock.A_BOLD = 1
    curses_mock.A_REVERSE = 2

    window_mock = MagicMock()
    window_mock.getmaxyx.return_value = (24, 80)
    window_mock.addstr = MagicMock()
    window_mock.refresh = MagicMock()
    window_mock.clear = MagicMock()
    window_mock.keypad = MagicMock()
    window_mock.getch = MagicMock(return_value=ord('\n'))

    curses_mock.initscr.return_value = window_mock
    curses_mock.newwin.return_value = window_mock
    curses_mock.color_pair.return_value = 0
    curses_mock.init_pair = MagicMock()
    curses_mock.start_color = MagicMock()
    curses_mock.use_default_colors = MagicMock()
    curses_mock.noecho = MagicMock()
    curses_mock.cbreak = MagicMock()

    with patch.dict('sys.modules', {'curses': curses_mock}):
        yield curses_mock

@pytest.fixture
def mock_screen(mock_curses):
    """Mock curses screen for testing."""
    return mock_curses.initscr()

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

@pytest.fixture
def game():
    """Create a game instance for testing."""
    return Game()

@pytest.fixture
def state_manager():
    """Create a state manager instance."""
    return StateManager()

@pytest.fixture
def toolbox():
    """Create a toolbox instance."""
    return Toolbox()

# Config Tests
def test_config_paths():
    """Test config path resolution."""
    assert Config.BASE_DIR.exists()
    assert Config.SAVES_DIR.exists()
    assert Config.TEMPLATES_DIR.exists()

def test_config_model_settings():
    """Test model configuration."""
    config = Config.get_model_config()
    assert 'model' in config
    assert 'temperature' in config
    assert 'max_tokens' in config

# State Tests
def test_state_initialization(state_manager, temp_dir):
    """Test state manager initialization."""
    state_manager.initialize_world_state(temp_dir)
    assert state_manager.world_state['meta']['version'] == '1.0'
    assert 'player' in state_manager.world_state
    assert 'world' in state_manager.world_state

def test_state_save_load(state_manager, temp_dir):
    """Test saving and loading state."""
    state_manager.initialize_world_state(temp_dir)
    state_manager.update_world_state({'test': 'value'})
    state_manager.save_world_state(temp_dir)

    new_state = StateManager()
    new_state.load_world_state(temp_dir)
    assert new_state.world_state['test'] == 'value'

# Toolbox Tests
def test_toolbox_file_operations(toolbox, temp_dir):
    """Test file operations in toolbox."""
    test_file = temp_dir / "test.md"
    test_content = "# Test Content"

    toolbox.write_markdown(test_file, test_content)
    assert test_file.exists()
    assert test_file.read_text() == test_content

def test_toolbox_uuid_generation(toolbox):
    """Test UUID generation."""
    uuid1 = toolbox.generate_uuid()
    uuid2 = toolbox.generate_uuid()
    assert uuid1 != uuid2
    assert len(uuid1) == 36  # Standard UUID length

def test_toolbox_llm_invocation(toolbox):
    """Test LLM invocation."""
    expected_response = "Mock response for test"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": expected_response}

    with patch('requests.post', return_value=mock_response):
        response = toolbox.invoke_llm("Test prompt")
        assert response == expected_response

# Agent Tests
def test_story_agent(toolbox):
    """Test story agent functionality."""
    agent = StoryAgent(toolbox)
    with patch.object(toolbox, 'invoke_llm', return_value="Test story"):
        result = agent.call("current text", "test choice")
        assert 'text' in result
        assert 'metadata' in result

def test_link_agent(toolbox):
    """Test link agent functionality."""
    agent = LinkAgent(toolbox)
    with patch.object(toolbox, 'invoke_llm', return_value="Test links"):
        result = agent.call(["test.md"])
        assert isinstance(result, dict)

def test_lore_agent(toolbox):
    """Test lore agent functionality."""
    agent = LoreAgent(toolbox)
    with patch.object(toolbox, 'invoke_llm', return_value="Test lore"):
        result = agent.call("test_topic", {})
        assert isinstance(result, str)

# Renderer Tests
def test_renderer_initialization(mock_screen):
    """Test renderer initialization."""
    renderer = Renderer(mock_screen)
    height, width = renderer.get_dimensions()
    assert height == 24
    assert width == 80

def test_renderer_markdown(mock_screen):
    """Test markdown rendering."""
    renderer = Renderer(mock_screen)
    test_text = "# Test Header\nTest content"

    # Mock the text window
    mock_text_win = MagicMock()
    renderer.text_win = mock_text_win

    renderer.render_markdown(test_text)
    assert mock_text_win.addstr.call_count > 0, "Text was not rendered"

# Task Queue Tests
def test_task_queue():
    """Test task queue operations."""
    queue = TaskQueue()
    mock_agent = Mock()
    mock_agent.call.return_value = {"result": "success"}

    result = queue.enqueue(mock_agent, "test_task", {"param": "value"})
    assert result.status == TaskStatus.PENDING

    # Test async execution
    import asyncio
    asyncio.run(queue.run_all())

    # Add retries to wait for result
    max_retries = 5
    task_result = None
    for _ in range(max_retries):
        task_result = queue.get_result(result.task_id)
        if task_result is not None:
            break
        asyncio.run(asyncio.sleep(0.1))

    assert task_result is not None
    assert task_result.status == TaskStatus.COMPLETED

# Game Integration Tests
def test_game_initialization(game, temp_dir):
    """Test game initialization."""
    with patch.object(Config, 'SAVES_DIR', temp_dir):
        # Setup mock story response
        mock_story = {'text': 'Initial chapter', 'metadata': {}}

        # Create necessary directories
        save_dir = temp_dir / "test-uuid"
        save_dir.mkdir(parents=True, exist_ok=True)

        # Create chapter file first
        chapter_path = save_dir / "chapter_1.md"
        chapter_path.write_text('Initial chapter')

        # Patch story agent and toolbox
        with patch.object(game.story_agent, 'call', return_value=mock_story), \
             patch.object(game.toolbox, 'append_chapter', return_value=str(chapter_path)), \
             patch.object(game, 'uuid', "test-uuid"):

            # Initialize new game
            game.new()
            assert game.uuid != ""
            assert game.save_path.exists()
            assert game.current_chapter == str(chapter_path)
            assert Path(game.current_chapter).exists()

def test_game_save_load(game, temp_dir):
    """Test game save/load functionality."""
    with patch.object(Config, 'SAVES_DIR', temp_dir):
        # Setup mock story response
        mock_story = {'text': 'Initial chapter', 'metadata': {}}

        # Create necessary directories
        save_dir = temp_dir / "test-uuid"
        save_dir.mkdir(parents=True, exist_ok=True)

        # Create chapter file first
        chapter_path = save_dir / "chapter_1.md"
        chapter_path.write_text('Initial chapter')

        # Patch story agent and toolbox
        with patch.object(game.story_agent, 'call', return_value=mock_story), \
             patch.object(game.toolbox, 'append_chapter', return_value=str(chapter_path)), \
             patch.object(game, 'uuid', "test-uuid"):

            # Initialize new game
            game.new()
            game.save()

            # Test loading
            new_game = Game()
            new_game.load("test-uuid")

            assert new_game.uuid == "test-uuid"
            assert new_game.current_chapter == str(chapter_path)
            assert Path(new_game.current_chapter).exists()

def test_game_advance(game):
    """Test game state advancement."""
    with patch.object(game.story_agent, 'call') as mock_story:
        mock_story.return_value = {'text': 'New chapter', 'metadata': {}}
        game.new()
        game.advance("test choice")
        assert game.current_chapter != ""

# Run all tests
if __name__ == "__main__":
    pytest.main([__file__])
