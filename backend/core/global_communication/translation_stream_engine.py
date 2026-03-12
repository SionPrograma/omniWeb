import logging
from typing import Dict, Any
from backend.core.language_bridge.conversation_bridge import conversation_bridge, Speaker
from .communication_models import CommunicationSession, Participant

logger = logging.getLogger(__name__)

class TranslationStreamEngine:
    """Manages multi-target real-time translation for a live session."""
    
    async def distribute_translation(self, session: CommunicationSession, sender_id: str, text: str) -> Dict[str, Any]:
        """Translates and routes a single utterance to all session participants."""
        sender = session.participants.get(sender_id)
        if not sender: return {}

        results = {}
        speaker_obj = Speaker(name=sender.name, native_language=sender.native_language)
        
        for p_id, participant in session.participants.items():
            if p_id == sender_id: continue # Don't translate for the sender
            
            # Use the Language Bridge to process the translation for this specific participant
            translation_payload = await conversation_bridge.process_utterance(
                speaker_obj, 
                text, 
                p_id
            )
            results[p_id] = translation_payload
            
        logger.info(f"TranslationStream: Distributed '{text[:20]}...' to {len(results)} participants.")
        return results

translation_stream_engine = TranslationStreamEngine()
