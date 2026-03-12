import logging
import asyncio
from typing import Dict, Any, List
from .language_bridge_models import Speaker, BridgeUserConfig, LanguageCode, TranslatedSegment, VoiceStyle
from .speech_capture import speech_capture
from .translation_engine import translation_engine
from .voice_adapter import voice_adapter
from .subtitle_engine import subtitle_engine
from .pronunciation_helper import pronunciation_helper
from .speaker_indicator import speaker_indicator

logger = logging.getLogger(__name__)

class ConversationBridge:
    """The central orchestrator for real-time multilingual translation sessions."""
    
    def __init__(self):
        self.active_speakers: List[Speaker] = []
        self.user_configs: Dict[str, BridgeUserConfig] = {}

    async def register_speaker(self, name: str, lang: LanguageCode) -> Speaker:
        speaker = Speaker(name=name, native_language=lang)
        self.active_speakers.append(speaker)
        logger.info(f"Language Bridge: Registered speaker {name} ({lang.value})")
        return speaker

    async def set_user_config(self, user_id: str, config: BridgeUserConfig):
        self.user_configs[user_id] = config
        logger.info(f"Language Bridge: Updated config for user {user_id}")

    async def process_utterance(self, speaker: Speaker, text: str, recipient_user_id: str) -> Dict[str, Any]:
        """Runs the full bridge pipeline for a single spoken sentence."""
        
        # 1. Capture/Transcribe
        segment = await speech_capture.capture_segment(speaker, text)
        
        # 2. Translate for the recipient
        config = self.user_configs.get(recipient_user_id)
        target_lang = config.preferred_listening_language if config else LanguageCode.ENGLISH
        
        translated = await translation_engine.translate(segment, target_lang)
        
        # 3. Add Pronunciation Guide if requested
        if config and config.show_pronunciation:
            translated.pronunciation_guide = pronunciation_helper.get_guide(
                translated.translated_text, target_lang
            )

        # 4. Prepare UI data
        ui_payload = {
            "speaker_info": speaker_indicator.get_indicator_data(speaker),
            "subtitles": subtitle_engine.generate_display_data(translated, config or BridgeUserConfig(user_id=recipient_user_id, preferred_listening_language=target_lang)),
            "voice_params": await voice_adapter.generate_speech_metadata(translated, config.voice_adaptation_style if config else VoiceStyle.FRIENDLY),
            "translated_text": translated.translated_text,
            "pronunciation": translated.pronunciation_guide
        }
        
        return ui_payload

conversation_bridge = ConversationBridge()
