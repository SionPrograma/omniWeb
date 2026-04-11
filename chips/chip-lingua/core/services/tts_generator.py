import subprocess
import json
import sys
import os
import re
import logging
import time
import asyncio
from pathlib import Path
from ..models.lingua_config import settings
try:
    from backend.core.ai_host.forge import forge_ledger, OutcomeStatus, CapabilityClass
    FORGE_AVAILABLE = True
except ImportError:
    FORGE_AVAILABLE = False

logger = logging.getLogger(__name__)

class TTSGenerator:
    """
    TTS Bridge V1.5 - Decoupled Synthesis Service.
    Orchestrates the out-of-process TTS Worker for isolation and stability.
    Uses native logic for text normalization and subprocess for heavy synthesis.
    """
    def __init__(self):
        self.worker_script = Path(__file__).parent.parent / "tts_worker.py"

    def _normalize_text(self, text: str) -> str:
        """
        Transforms markdown and technical patterns into natural human speech.
        """
        if not text: return ""
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text) 
        text = re.sub(r'__([^_]+)__', r'\1', text)     
        text = re.sub(r'`([^`]+)`', r'\1', text)       
        text = re.sub(r'#+\s+', '', text)              
        text = re.sub(r'[-*]\s+', ' ', text)           
        text = text.replace('_', ' ')
        text = text.replace('*', '')  
        text = re.sub(r'\s+', ' ', text) 
        return text.strip()

    def _resolve_provider(self) -> str:
        if not FORGE_AVAILABLE: return "gtts_google"
        try:
             res = forge_ledger.get_active_provider_sync("synthesis")
             return res if res else "gtts_google"
        except:
             return "gtts_google"

    def generate(self, text: str, output_path: Path, job_id: str, speaker_wav: Path = None, language: str = "en"):
        """
        Synthesizes audio by delegating to the isolated TTS worker.
        """
        if not settings.TTS_ENABLED:
            logger.info("TTS Generation is disabled in config.")
            return None
            
        norm_text = self._normalize_text(text)
        if not norm_text:
            return None

        # Resolve active provider via Forge (Block 82)
        active_provider = self._resolve_provider()

        # Build command for isolated worker
        cmd = [
            sys.executable,
            str(self.worker_script),
            norm_text,
            language,
            str(output_path),
            "--provider", active_provider
        ]
        
        try:
            logger.info(f"TTS Bridge V1.5: Launching worker for '{norm_text[:20]}...'")
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60) # 60s timeout
            latency_ms = int((time.time() - start_time) * 1000)
            
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown worker error"
                logger.error(f"TTS Worker Failed: {error_msg}")
                self._fire_and_forget_forge({"metadata": {"mode": "FAIL", "error": error_msg}}, latency_ms)
                return None
            
            # Read metadata from worker
            try:
                data = json.loads(result.stdout)
                mode = data.get("metadata", {}).get("mode", "UNKNOWN")
                logger.info(f"TTS Success. Mode: {mode}")
                self._fire_and_forget_forge(data, latency_ms)
                return output_path if output_path.exists() else None
            except json.JSONDecodeError:
                logger.error("Invalid TTS worker output format")
                self._fire_and_forget_forge({"metadata": {"mode": "FAIL", "error": "JSON error"}}, latency_ms)
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("TTS Worker Timeout (60s limit reached)")
            self._fire_and_forget_forge({"metadata": {"mode": "TIMEOUT"}}, 60000)
            return None
        except Exception as e:
            logger.error(f"TTS Bridge Exception: {str(e)}")
            self._fire_and_forget_forge({"metadata": {"mode": "FAIL", "error": str(e)}}, 0)
            return None

    def _fire_and_forget_forge(self, result: dict, latency: int):
        """Helper to fire async telemetry from sync context."""
        if not FORGE_AVAILABLE: return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._report_forge(result, latency))
        except:
            pass

    async def _report_forge(self, result: dict, latency: int):
        """Standardized reporting for synthesis."""
        mode = result.get("metadata", {}).get("mode", "UNKNOWN")
        provider = result.get("metadata", {}).get("provider_used") or "gtts_google"
        status = OutcomeStatus.FAIL
        quality = 0.0
        
        if mode == "REAL_REMOTE":
            status = OutcomeStatus.SUCCESS
            quality = 1.0
        elif mode == "FALLBACK":
            status = OutcomeStatus.PARTIAL
            quality = 0.5
            
        await forge_ledger.log_telemetry({
            "provider_id": provider,
            "capability_class": CapabilityClass.SYNTHESIS.value,
            "task_context": f"mode:{mode}",
            "outcome_status": status.value,
            "quality_score": quality,
            "latency_ms": latency,
            "notes": result.get("metadata", {}).get("error")
        })

    def _cleanup_memory(self):
        # Memory cleanup not needed as worker is out-of-process.
        pass
