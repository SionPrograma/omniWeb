import pytest
from backend.core.language_bridge.conversation_bridge import conversation_bridge
from backend.core.language_bridge.language_bridge_models import LanguageCode, BridgeUserConfig, VoiceStyle
from backend.core.permissions import set_chip_context

@pytest.fixture(autouse=True)
def core_context():
    with set_chip_context("core"):
        yield

@pytest.mark.asyncio
async def test_language_bridge_translation():
    # Setup recipient config
    user_id = "test_user"
    config = BridgeUserConfig(
        user_id=user_id,
        preferred_listening_language=LanguageCode.ARABIC,
        show_pronunciation=True
    )
    await conversation_bridge.set_user_config(user_id, config)
    
    # Simulate speaker
    speaker = await conversation_bridge.register_speaker("Carlos", LanguageCode.SPANISH)
    
    # Process utterance
    payload = await conversation_bridge.process_utterance(speaker, "Gracias", user_id)
    
    assert payload["translated_text"] == "shukran"
    assert payload["subtitles"]["visible"] is True
    assert payload["pronunciation"] == "shok-ran"

@pytest.mark.asyncio
async def test_voice_adaptation_styles():
    speaker = await conversation_bridge.register_speaker("Alice", LanguageCode.ENGLISH)
    
    # Friendly vs Energetic
    user_id = "listener"
    
    # 1. Friendly
    config_f = BridgeUserConfig(user_id=user_id, preferred_listening_language=LanguageCode.SPANISH, voice_adaptation_style=VoiceStyle.FRIENDLY)
    await conversation_bridge.set_user_config(user_id, config_f)
    payload_f = await conversation_bridge.process_utterance(speaker, "Hello", user_id)
    
    # 2. Energetic
    config_e = BridgeUserConfig(user_id=user_id, preferred_listening_language=LanguageCode.SPANISH, voice_adaptation_style=VoiceStyle.ENERGETIC)
    await conversation_bridge.set_user_config(user_id, config_e)
    payload_e = await conversation_bridge.process_utterance(speaker, "Hello", user_id)
    
    assert payload_e["voice_params"]["speed"] > payload_f["voice_params"]["speed"]
