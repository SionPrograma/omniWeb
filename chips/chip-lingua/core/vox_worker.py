import sys
import json
import os
import time
from pathlib import Path

def run_transcription(audio_path, output_json, model_name="base"):
    """
    Vox Worker V1.2 - Hardened Isolated Transcription.
    Detects provisioning and reports mode.
    """
    result = {
        "text": "",
        "segments": [],
        "metadata": {
            "worker": "Vox-Worker-V1.2",
            "model": model_name,
            "status": "pending",
            "timestamp": time.time(),
            "mode": "UNKNOWN"
        }
    }

    try:
        # 0. Warmup Protection (Phase 76)
        if audio_path == "WARMUP_ONLY":
            try:
                import whisper
                import torch
                whisper.load_model(model_name, device="cpu" if not torch.cuda.is_available() else "cuda")
                result["metadata"]["mode"] = "WARMUP_SUCCESS"
                result["metadata"]["status"] = "success"
                with open(output_json, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                return True
            except Exception as e:
                print(f"Warmup Failed: {e}", file=sys.stderr)
                return False

        # 1. Dependency Check (Provisioning Detection)
        has_whisper = False
        try:
            import whisper
            import torch
            has_whisper = True
        except ImportError:
            has_whisper = False

        # 2. Execution Logic
        if has_whisper:
            import torch
            device = "cpu" if not torch.cuda.is_available() else "cuda"
            try:
                model = whisper.load_model(model_name, device=device)
                transcription = model.transcribe(str(audio_path), verbose=False)
                result["text"] = transcription.get("text", "")
                result["segments"] = transcription.get("segments", [])
                result["metadata"]["mode"] = "REAL_ML"
                result["metadata"]["status"] = "success"
                result["metadata"]["device"] = device
            except Exception as ml_e:
                result["metadata"]["mode"] = "REAL_ML_FAIL"
                result["metadata"]["error"] = str(ml_e)
                raise ml_e
        else:
            # Fallback for Missing ML Stack
            result["text"] = f"[VOX_MOCK] {os.path.basename(audio_path)} - Transcription Mocked (V1.2)"
            result["segments"] = [{"start": 0, "end": 2, "text": result["text"]}]
            result["metadata"]["mode"] = "MOCK_FALLBACK"
            result["metadata"]["status"] = "success"
            result["metadata"]["warning"] = "Whisper stack not provisioned."

        # 3. Finalize
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Vox Worker Final Failure: {str(e)}", file=sys.stderr)
        # Even on failure, try to save a machine-readable failure object if possible
        try:
            result["metadata"]["status"] = "failed"
            result["metadata"]["error"] = str(e)
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        except:
            pass
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python vox_worker.py <input_audio> <output_json> [model_name]")
        sys.exit(1)
        
    audio_file = sys.argv[1]
    output_file = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "base"
    
    success = run_transcription(audio_file, output_file, model)
    sys.exit(0 if success else 1)
