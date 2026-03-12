import pytest
from backend.core.knowledge_os.workspace_manager import workspace_manager, InteractionMode
from backend.core.permissions import set_chip_context

@pytest.fixture(autouse=True)
def core_context():
    with set_chip_context("core"):
        yield

def test_workspace_mode_switch():
    workspace_manager.switch_mode(InteractionMode.SPATIAL)
    assert workspace_manager.state.current_mode == InteractionMode.SPATIAL

def test_tool_mounting():
    workspace_manager.mount_tool("test_chip_123")
    assert "test_chip_123" in workspace_manager.state.active_tools
    workspace_manager.unmount_tool("test_chip_123")
    assert "test_chip_123" not in workspace_manager.state.active_tools
