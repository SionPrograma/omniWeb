import pytest
from backend.core.antimodal.antimodal_controller import antimodal_controller
from backend.core.antimodal.antimodal_models import AntimodalMode
from backend.core.antimodal.compact_response import response_generator

def test_mode_switching():
    antimodal_controller.set_mode(AntimodalMode.SILENT)
    assert antimodal_controller.get_current_mode() == AntimodalMode.SILENT
    
    antimodal_controller.set_mode(AntimodalMode.STANDARD)
    assert antimodal_controller.get_current_mode() == AntimodalMode.STANDARD

def test_compact_response():
    resp = "Este es un mensaje muy largo que debería ser resumido en modo compacto para evitar distracciones innecesarias. El sistema está funcionando bien. Todo está bajo control."
    
    # Standard mode: No change
    res_std = antimodal_controller.process_ai_response(resp)
    assert res_std == resp
    
    # Compact mode
    antimodal_controller.set_mode(AntimodalMode.COMPACT)
    res_comp = antimodal_controller.process_ai_response(resp)
    assert len(res_comp) < len(resp)
    
    # Summary only mode
    antimodal_controller.set_mode(AntimodalMode.SUMMARY_ONLY)
    res_summ = antimodal_controller.process_ai_response(resp)
    assert len(res_summ) < len(resp)
    
    antimodal_controller.set_mode(AntimodalMode.STANDARD)

def test_silent_ui_filtering():
    elements = [
        {"type": "full-panel", "name": "Stats"},
        {"type": "toast", "name": "Success"},
        {"type": "modal-rich-voice", "name": "Voice Assistant"}
    ]
    
    antimodal_controller.set_mode(AntimodalMode.STANDARD)
    filtered_std = antimodal_controller.filter_ui_feedback(elements)
    assert len(filtered_std) == 3
    
    antimodal_controller.set_mode(AntimodalMode.SILENT)
    filtered_silent = antimodal_controller.filter_ui_feedback(elements)
    # full-panel and modal-rich-voice should be filtered out
    assert len(filtered_silent) == 1
    assert filtered_silent[0]["type"] == "toast"
    
    antimodal_controller.set_mode(AntimodalMode.STANDARD)

def test_background_task_safety():
    import asyncio
    from backend.core.antimodal.background_orchestrator import background_orchestrator
    
    async def dummy_task():
        return "done"
        
    async def run_safety_test():
        antimodal_controller.set_mode(AntimodalMode.BACKGROUND)
        
        # Destructive task should be blocked in background mode
        result = await background_orchestrator.execute_in_background("delete_files", dummy_task(), is_destructive=True)
        assert "BLOCKED" in result
        
        # Safe task should be enqueued
        result = await background_orchestrator.execute_in_background("sync_stats", dummy_task(), is_destructive=False)
        assert "ENQUEUED" in result
        
        antimodal_controller.set_mode(AntimodalMode.STANDARD)
        
    asyncio.run(run_safety_test())
