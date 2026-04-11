import subprocess
import json
import sys
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

class Translator:
    """
    Transl Bridge V1.4 - Decoupled Translation Service.
    Orchestrates the out-of-process Transl Worker for isolation and auditability.
    Ensures 'main.py' runtime stays clean of heavy translation libraries.
    """
    def __init__(self):
        self.worker_script = Path(__file__).parent.parent / "transl_worker.py"

    def _resolve_provider(self) -> str:
        if not FORGE_AVAILABLE: return "deep_translator_google"
        try:
             res = forge_ledger.get_active_provider_sync("translation")
             return res if res else "deep_translator_google"
        except:
             return "deep_translator_google"

    def translate(self, text: str, target_lang: str) -> dict:
        """
        Executes the out-of-process Transl Worker for a single translation.
        """
        if not text or not text.strip():
            return {"text": text, "metadata": {"mode": "PASS_THROUGH", "status": "success"}}
            
        start_time = time.time()
        active_provider = self._resolve_provider()
        cmd = [
            sys.executable,
            str(self.worker_script),
            text,
            target_lang,
            "--provider", active_provider
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            latency_ms = int((time.time() - start_time) * 1000)
            
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown worker error"
                logger.error(f"Transl Worker Failed: {error_msg}")
                res = self._fallback_result(text, target_lang, f"Worker Error: {error_msg}")
                self._fire_and_forget_forge(res, latency_ms)
                return res
            
            try:
                data = json.loads(result.stdout)
                self._fire_and_forget_forge(data, latency_ms)
                return data
            except json.JSONDecodeError:
                res = self._fallback_result(text, target_lang, "Invalid worker output format")
                self._fire_and_forget_forge(res, latency_ms)
                return res
                
        except Exception as e:
            logger.error(f"Transl Bridge Exception: {str(e)}")
            res = self._fallback_result(text, target_lang, f"Bridge Exception: {str(e)}")
            self._fire_and_forget_forge(res, 0)
            return res

    def translate_batch(self, texts: list, target_lang: str) -> list:
        """Translates a batch of strings in a single subprocess call."""
        if not texts:
            return []
        
        start_time = time.time()
        active_provider = self._resolve_provider()
        cmd = [
            sys.executable,
            str(self.worker_script),
            json.dumps(texts),
            target_lang,
            "--provider", active_provider
        ]
        
        try:
            logger.info(f"Transl Bridge: Executing Batch Translation (Len: {len(texts)}) via {active_provider}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            latency_ms = int((time.time() - start_time) * 1000)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                translated = data.get("translations") or texts
                
                # Report batch telemetry
                if FORGE_AVAILABLE:
                    telemetry = {
                        "provider_id": active_provider,
                        "capability_class": CapabilityClass.TRANSLATION.value,
                        "task_context": f"batch_size:{len(texts)}",
                        "outcome_status": OutcomeStatus.SUCCESS.value,
                        "quality_score": 1.0,
                        "latency_ms": latency_ms
                    }
                    asyncio.create_task(forge_ledger.log_telemetry(telemetry))
                
                return translated
            else:
                 logger.error(f"Batch Transl Error: {result.stderr}")
                 return [self.translate(t, target_lang).get("text", t) for t in texts]
        except Exception as e:
            logger.error(f"Batch Transl Failure: {e}")
            return [self.translate(t, target_lang).get("text", t) for t in texts]

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
        """Standardized reporting for translation."""
        mode = result.get("metadata", {}).get("mode", "UNKNOWN")
        provider = result.get("metadata", {}).get("provider_used") or "deep_translator_google"
        status = OutcomeStatus.FAIL
        quality = 0.0
        
        if mode == "REAL_REMOTE":
            status = OutcomeStatus.SUCCESS
            quality = 1.0
        elif mode == "FALLBACK" or mode == "PASS_THROUGH":
            status = OutcomeStatus.PARTIAL
            quality = 0.5
            
        await forge_ledger.log_telemetry({
            "provider_id": provider,
            "capability_class": CapabilityClass.TRANSLATION.value,
            "task_context": f"mode:{mode}",
            "outcome_status": status.value,
            "quality_score": quality,
            "latency_ms": latency,
            "notes": result.get("metadata", {}).get("error")
        })

    def _fallback_result(self, text: str, target_lang: str, reason: str) -> dict:
        """Standard fallback structure for failed translations."""
        return {
            "text": f"[TRANSL_ERR] {text}",
            "metadata": {
                "worker": "Transl-Bridge-V1.4",
                "status": "failed",
                "error": reason,
                "target_lang": target_lang,
                "mode": "FALLBACK"
            }
        }
