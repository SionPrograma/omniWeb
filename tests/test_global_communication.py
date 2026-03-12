import pytest
from backend.core.global_communication.session_manager import session_manager, Participant, LanguageCode
from backend.core.global_communication.translation_stream_engine import translation_stream_engine
from backend.core.global_communication.spatial_bubble_engine import spatial_bubble_engine
from backend.core.permissions import set_chip_context

@pytest.fixture(autouse=True)
def core_context():
    with set_chip_context("core"):
        yield

@pytest.mark.asyncio
async def test_session_lifecycle():
    creator = Participant(user_id="alice", name="Alice", native_language=LanguageCode.ENGLISH, listening_language=LanguageCode.ENGLISH)
    session = session_manager.create_session("Test Call", creator)
    
    assert session.title == "Test Call"
    assert "alice" in session.participants
    
    bob = Participant(user_id="bob", name="Bob", native_language=LanguageCode.SPANISH, listening_language=LanguageCode.SPANISH)
    session_manager.join_session(session.id, bob)
    assert len(session_manager.sessions[session.id].participants) == 2
    
    session_manager.leave_session(session.id, "alice")
    session_manager.leave_session(session.id, "bob")
    assert session_manager.sessions[session.id].status == "closed"

@pytest.mark.asyncio
async def test_multi_target_translation_stream():
    # Setup session with 3 users (ES, AR, EN)
    u1 = Participant(user_id="p1", name="P1", native_language=LanguageCode.SPANISH, listening_language=LanguageCode.SPANISH)
    u2 = Participant(user_id="p2", name="P2", native_language=LanguageCode.ARABIC, listening_language=LanguageCode.ARABIC)
    u3 = Participant(user_id="p3", name="P3", native_language=LanguageCode.ENGLISH, listening_language=LanguageCode.ENGLISH)
    
    session = session_manager.create_session("Stream Test", u1)
    session_manager.join_session(session.id, u2)
    session_manager.join_session(session.id, u3)
    
    from backend.core.language_bridge.conversation_bridge import conversation_bridge, BridgeUserConfig
    await conversation_bridge.set_user_config("p2", BridgeUserConfig(user_id="p2", preferred_listening_language=LanguageCode.ARABIC))
    await conversation_bridge.set_user_config("p3", BridgeUserConfig(user_id="p3", preferred_listening_language=LanguageCode.ENGLISH))

    # User 1 speaks Spanish
    results = await translation_stream_engine.distribute_translation(session, "p1", "Hola")
    
    assert "p2" in results
    assert "p3" in results
    assert results["p2"]["translated_text"] == "salaam" # Simulated Arabic
    assert results["p3"]["translated_text"] == "hello"  # Simulated English

def test_spatial_bubble_generation():
    p = Participant(user_id="p1", name="Carlos", native_language=LanguageCode.SPANISH, listening_language=LanguageCode.SPANISH)
    bubble = spatial_bubble_engine.generate_bubble(p, "Salaam", "🇲🇦")
    
    assert bubble.speaker_id == "p1"
    assert bubble.content == "Salaam"
    assert bubble.language_flag == "🇲🇦"
    assert "x" in bubble.position
