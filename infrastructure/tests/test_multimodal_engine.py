import pytest
import asyncio
from backend.core.multimodal.multimodal_router import multimodal_router, MultimodalInput
from backend.core.ai_host.command_router import ai_command_router
from backend.core.permissions import set_chip_context

@pytest.fixture
def multimodal_input():
    return MultimodalInput(
        modality="text",
        raw_data="status"
    )

@pytest.mark.asyncio
async def test_multimodal_routing_text():
    inp = MultimodalInput(modality="text", raw_data="Hola sistema")
    command = await multimodal_router.handle_input(inp)
    assert command == "Hola sistema"

@pytest.mark.asyncio
async def test_multimodal_routing_voice_simulation():
    # In simulation, 'raw_data' as string is accepted as recognized text
    inp = MultimodalInput(modality="voice", raw_data="abrir finanzas")
    command = await multimodal_router.handle_input(inp)
    assert command == "abrir finanzas"

@pytest.mark.asyncio
async def test_ai_host_multimodal_integration():
    with set_chip_context("core"):
        # Send a voice command to AI Host
        # "explora motor" should return a visual table
        response = await ai_command_router.route("explora motor", modality="voice")
        
        assert response.intent == "graph_explore"
        assert "visual" in response.payload
        assert response.payload["visual"]["type"] == "table"
        assert response.payload["visual"]["title"] == "Relaciones de motor"

@pytest.mark.asyncio
async def test_visual_response_generation():
    from backend.core.multimodal.visual_response import VisualResponseEngine
    chart = VisualResponseEngine.create_chart("Test Chart", ["A", "B"], [10, 20])
    assert chart["type"] == "chart_bar"
    assert chart["data"]["values"] == [10, 20]

if __name__ == "__main__":
    # Manual run
    async def run():
        print("Running multimodal tests...")
        await test_multimodal_routing_text()
        print("PASS: test_multimodal_routing_text")
        await test_multimodal_routing_voice_simulation()
        print("PASS: test_multimodal_routing_voice_simulation")
        await test_ai_host_multimodal_integration()
        print("PASS: test_ai_host_multimodal_integration")
        await test_visual_response_generation()
        print("PASS: test_visual_response_generation")
    
    asyncio.run(run())
