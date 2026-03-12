import pytest
from backend.core.multi_ai_interface.agent_manager import agent_manager
from backend.core.web_window_engine.web_window_controller import web_window_controller
from backend.core.permissions import set_chip_context

@pytest.fixture(autouse=True)
def core_context():
    with set_chip_context("core"):
        yield

def test_agent_invitation():
    agent = agent_manager.invite_agent("coder")
    assert agent is not None
    assert agent.name == "DevAI"
    assert agent.id in agent_manager.active_agents

def test_web_window_creation():
    win = web_window_controller.create_window("https://youtube.com", "YouTube")
    assert win.url == "https://youtube.com"
    assert win.title == "YouTube"
    assert win.id in web_window_controller.windows

def test_interface_config():
    web_window_controller.update_config(brightness=0.5)
    assert web_window_controller.config.brightness == 0.5
