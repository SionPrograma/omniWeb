import pytest
from backend.core.user_onboarding.onboarding_manager import onboarding_manager
from backend.core.language_bridge.language_bridge_models import LanguageCode

@pytest.mark.asyncio
async def test_language_detection_spanish():
    res = await onboarding_manager.process_initial_greeting("user_es", "Hola, me gustaría empezar un proyecto")
    assert res["detected_language"] == LanguageCode.SPANISH
    assert "Bienvenido" in res["greeting"]

@pytest.mark.asyncio
async def test_language_detection_english():
    res = await onboarding_manager.process_initial_greeting("user_en", "Hello, I want to create a research project about AI")
    assert res["detected_language"] == LanguageCode.ENGLISH
    assert "Welcome" in res["greeting"]

@pytest.mark.asyncio
async def test_language_detection_german():
    res = await onboarding_manager.process_initial_greeting("user_de", "Hallo, ich bin neu hier")
    assert res["detected_language"] == LanguageCode.GERMAN
    assert "Willkommen" in res["greeting"]
