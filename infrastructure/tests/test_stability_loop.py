import pytest
import asyncio
from backend.core.stability_loop.loop_controller import loop_controller
from backend.core.stability_loop.loop_models import LoopStep

def test_successful_loop():
    async def run():
        async def success_action():
            return {"status": "success"}
        
        state, result = await loop_controller.execute_task(
            "test_task",
            {"data": "test"},
            success_action
        )
        
        assert state.current_step == LoopStep.COMPLETE
        assert result["status"] == "success"
        assert state.cycle_count == 1
    import asyncio
    asyncio.run(run())

def test_repair_cycle():
    async def run():
        async def raising_action():
            raise Exception("Temporary error")
            
        state, result = await loop_controller.execute_task(
            "test_fail",
            {},
            raising_action
        )
        
        assert state.current_step == LoopStep.FAILED
        assert "Temporary error" in state.errors
    import asyncio
    asyncio.run(run())

def test_max_cycles_exceeded():
    async def run():
        from backend.core.stability_loop.stability_checker import stability_checker
        import unittest.mock as mock
        
        async def dummy_action():
            return "ok"
            
        # Mock stability_checker to always return False (unstable)
        with mock.patch("backend.core.stability_loop.stability_checker.stability_checker.check_all", 
                        new_callable=mock.AsyncMock) as mocked_check:
            mocked_check.return_value = {"is_stable": False, "details": {"all": False}}
            
            state, result = await loop_controller.execute_task(
                "unstable_task",
                {},
                dummy_action
            )
            
            assert state.cycle_count == state.max_cycles
            assert state.current_step == LoopStep.ROLLBACK
    import asyncio
    asyncio.run(run())
