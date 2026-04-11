import sys
import json
import time
import os
from pathlib import Path

def run_tts(text, target_lang, output_path, provider=None):
    """
    TTS Worker V1.5 - Isolated Synthesis Engine + Block 82 Provider Support
    """
    result = {
        "audio_path": str(output_path),
        "metadata": {
            "worker": "TTS-Worker-V1.5",
            "text_len": len(text),
            "target_lang": target_lang,
            "status": "pending",
            "mode": "UNKNOWN",
            "timestamp": time.time(),
            "provider_used": provider or "gtts_google"
        }
    }

    if not text or not text.strip():
        result["metadata"]["status"] = "failed"
        result["metadata"]["error"] = "Empty text"
        return result

    try:
        # Step 1: Attempt Real Synthesis (Using gTTS as current 'real' baseline if possible)
        # Note: gTTS doesn't need heavy ML libs, but needs internet.
        if provider != "bip_fallback_local":
            try:
                from gtts import gTTS
                tts = gTTS(text=text, lang=target_lang)
                tts.save(str(output_path))
                if output_path.exists():
                    result["metadata"]["mode"] = "REAL_REMOTE"
                    result["metadata"]["status"] = "success"
                    return result
            except ImportError:
                pass # gTTS not installed
            except Exception as e:
                result["metadata"]["warning"] = f"Real synthesis failed: {str(e)}"

        # Step 2: Fallback (Generate Mock/Bip Audio)
        # We'll use a 1s silent/bip wav if we can't synthesize
        result["metadata"]["warning"] = "Real TTS engine not provisioned. Using bip fallback."
        
        # Generation of a dummy wav for pilot validation
        # (Assuming ffmpeg is still present from V1.3 validation)
        import subprocess
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=0.5',
            '-acodec', 'pcm_s16le', str(output_path), '-y'
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            if output_path.exists():
                result["metadata"]["mode"] = "FALLBACK"
                result["metadata"]["status"] = "success"
                return result
        except:
             result["metadata"]["error"] = "Fallback audio generation failed"
             result["metadata"]["status"] = "failed"
             return result

    except Exception as catastrophic:
        result["metadata"]["status"] = "failed"
        result["metadata"]["error"] = str(catastrophic)
        return result

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python tts_worker.py <text> <target_lang> <output_path>")
        sys.exit(1)
        
    try:
        text_input = sys.argv[1]
        lang = sys.argv[2]
        out = Path(sys.argv[3])
        
        provider = None
        if "--provider" in sys.argv:
            pidx = sys.argv.index("--provider")
            if pidx + 1 < len(sys.argv):
                provider = sys.argv[pidx+1]
        
        res = run_tts(text_input, lang, out, provider=provider)
        print(json.dumps(res, indent=2))
        sys.exit(0)
    except Exception as global_e:
        print(json.dumps({"error": str(global_e)}), file=sys.stderr)
        sys.exit(1)
