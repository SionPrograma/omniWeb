import subprocess
import json
import os
import sys
import asyncio
from pathlib import Path
import logging
import time
from ..models.lingua_config import settings
try:
    from backend.core.ai_host.forge import forge_ledger, OutcomeStatus, CapabilityClass
    FORGE_AVAILABLE = True
except ImportError:
    FORGE_AVAILABLE = False

logger = logging.getLogger(__name__)

class Transcriber:
    """
    Vox Bridge V1.2 - Provisioning-Aware Bridge.
    Orchestrates the out-of-process Vox Worker and reports real-time provisioning state.
    """
    def __init__(self):
        self.worker_script = Path(__file__).parent.parent / "vox_worker.py"

    async def transcribe_async(self, audio_path: Path) -> dict:
        """
        Executes the out-of-process Vox Worker asynchronously (non-blocking).
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found at {audio_path}")
            
        job_id = audio_path.stem
        output_json = settings.TEMP_DIR / f"{job_id}_vox_result.json"
        
        # Resolve active provider via Forge (Block 81)
        active_model = settings.WHISPER_MODEL
        if FORGE_AVAILABLE:
            from backend.core.ai_host.forge.config_manager import forge_config_manager
            active_model = await forge_config_manager.get_provider("transcription", settings.WHISPER_MODEL)
            
        # Build command
        cmd = [
            sys.executable,
            str(self.worker_script),
            str(audio_path),
            str(output_json),
            active_model
        ]
        
        try:
            logger.info(f"Vox Bridge V1.2: Launching async worker for {audio_path.name}")
            start_time = time.time()
            
            # Using asyncio.create_subprocess_exec for true event-loop friendliness
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion (limited timeout to prevent hang)
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600) # 10 mins
            latency_ms = int((time.time() - start_time) * 1000)
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip() or "Unknown worker error"
                logger.error(f"Vox Worker Failed: {error_msg}")
                res = self._fallback_result(audio_path, f"Worker Error: {error_msg}")
                await self._report_forge(res, latency_ms)
                return res
            
            # Read back standard result
            if output_json.exists():
                with open(output_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                await self._report_forge(data, latency_ms, provider_id=active_model)
                return data
            else:
                res = self._fallback_result(audio_path, "Output JSON missing")
                await self._report_forge(res, latency_ms, provider_id=active_model)
                return res
                
        except asyncio.TimeoutError:
            logger.error("Vox Worker Timeout (10 min limit reached)")
            res = self._fallback_result(audio_path, "Transcription Timeout")
            await self._report_forge(res, 600000) # 10 mins
            return res
        except Exception as e:
            logger.error(f"Vox Bridge Exception: {str(e)}")
            res = self._fallback_result(audio_path, f"Bridge Exception: {str(e)}")
            await self._report_forge(res, 0)
            return res
        finally:
            if output_json.exists():
                try: os.remove(output_json)
                except: pass

    async def _report_forge(self, result: dict, latency: int, provider_id: str = None):
        """Standardized reporting to Intelligence Forge."""
        if not FORGE_AVAILABLE: return
        
        mode = result.get("metadata", {}).get("mode", "UNKNOWN")
        status = OutcomeStatus.FAIL
        quality = 0.0
        
        if mode == "REAL_ML":
            status = OutcomeStatus.SUCCESS
            quality = 1.0
        elif mode == "MOCK_FALLBACK":
            status = OutcomeStatus.PARTIAL
            quality = 0.5
            
        final_pid = provider_id or settings.WHISPER_MODEL
        await forge_ledger.log_telemetry({
            "provider_id": f"whisper_{final_pid}_local",
            "capability_class": CapabilityClass.TRANSCRIPTION.value,
            "task_context": f"mode:{mode}",
            "outcome_status": status.value,
            "quality_score": quality,
            "latency_ms": latency,
            "notes": result.get("metadata", {}).get("error") or result.get("metadata", {}).get("warning")
        })

    def transcribe(self, audio_path: Path) -> dict:
        """Synchronous wrapper for legacy/thread compatibility."""
        return asyncio.run(self.transcribe_async(audio_path))

    async def warmup_async(self) -> dict:
        """
        Triggers an isolated pre-load of the ML model into the system cache.
        Helps mitigate first-request cold-start latency.
        """
        cmd = [
            sys.executable,
            str(self.worker_script),
            "WARMUP_ONLY",
            str(settings.TEMP_DIR / "warmup.json"),
            settings.WHISPER_MODEL
        ]
        try:
            logger.info("Vox Bridge: Triggering ML Warmup...")
            process = await asyncio.create_subprocess_exec(*cmd)
            await asyncio.wait_for(process.wait(), timeout=120)
            return {"status": "warmup_completed"}
        except Exception as e:
            logger.warning(f"Vox Bridge Warmup failed/timed out: {e}")
            return {"status": "warmup_failed", "reason": str(e)}

    def _fallback_result(self, audio_path: Path, error_reason: str) -> dict:
        """Standard fallback structure for failed transcriptions."""
        return {
            "text": f"[VOX_FAIL] {error_reason}",
            "segments": [],
            "metadata": {
                "worker": "Vox-Bridge-V1.2",
                "status": "failed",
                "error": error_reason,
                "input": audio_path.name,
                "mode": "ERROR_REJECTION"
            }
        }

    def _cleanup_memory(self):
        pass
