import pytest
from backend.core.supercommand.supercommand_parser import supercommand_parser
from backend.core.supercommand.superprompt_builder import superprompt_builder
from backend.core.supercommand.supercommand_models import TaskCategory

def test_parser_optimization():
    intent = supercommand_parser.parse("optimize semantic search engine")
    assert intent is not None
    assert intent.category == TaskCategory.OPTIMIZATION
    assert "semantic search engine" in intent.target

def test_parser_learning():
    intent = supercommand_parser.parse("teach me quantum physics")
    assert intent is not None
    assert intent.category == TaskCategory.LEARNING
    assert "quantum physics" in intent.target

def test_prompt_builder():
    intent = supercommand_parser.parse("optimize database")
    prompt = superprompt_builder.build_prompt(intent)
    assert prompt.category == TaskCategory.OPTIMIZATION
    assert len(prompt.steps) >= 3
    assert prompt.steps[0].name == "Audit Subsystem"

@pytest.mark.asyncio
async def test_loop_execution_stub():
    # Since it depends on loop_controller which needs a running app or heavy mocks
    # we just test the logic exists
    from backend.core.supercommand.loop_executor import loop_executor
    assert loop_executor is not None
    # execution test would be too complex for a unit test without full integration
