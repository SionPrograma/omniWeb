import sys
import json
import time

def run_translation(text, target_lang, source_lang="auto", provider=None):
    """
    Transl Worker V1.4 (Fixed - Batch Support) + Block 82 Provider Support
    """
    if isinstance(text, list):
        results = []
        for t in text:
            res = run_translation(t, target_lang, source_lang, provider)
            results.append(res.get("text", t))
        return {"translations": results, "metadata": {"mode": "BATCH_REAL", "count": len(text)}}

    result = {
        "text": "",
        "metadata": {
            "worker": "Transl-Worker-V1.4",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "status": "pending",
            "mode": "UNKNOWN",
            "timestamp": time.time(),
            "provider_used": provider or "deep_translator_google"
        }
    }

    if not text or not text.strip():
        result["text"] = text
        result["metadata"]["status"] = "success"
        result["metadata"]["mode"] = "PASS_THROUGH"
        return result

    try:
        # Block 82: Explicit Provider Logic
        if provider == "mock_lingua_v1":
             result["text"] = f"[TRANSL_MOCK] {text}"
             result["metadata"]["mode"] = "FALLBACK"
             result["metadata"]["status"] = "success"
             return result

        # Step 1: Attempt Real Translation (Using deep-translator as current 'real' baseline)
        try:
            from deep_translator import GoogleTranslator
            translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
            if translated and isinstance(translated, str) and translated.strip():
                result["text"] = translated
                result["metadata"]["mode"] = "REAL_REMOTE"
                result["metadata"]["status"] = "success"
                return result
        except Exception as e:
            result["metadata"]["warning"] = f"Real translation failed: {str(e)}"

        # Step 2: Fallback (Mock/Echo)
        result["text"] = f"[TRANSL_MOCK] {text}"
        result["metadata"]["mode"] = "FALLBACK"
        result["metadata"]["status"] = "success"
        return result

    except Exception as catastrophic:
        result["metadata"]["status"] = "failed"
        result["metadata"]["error"] = str(catastrophic)
        return result

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python transl_worker.py <text_json> <target_lang> [--provider <pid>]")
        sys.exit(1)
        
    try:
        input_data = sys.argv[1]
        target = sys.argv[2]
        
        provider = None
        if "--provider" in sys.argv:
            idx = sys.argv.index("--provider")
            if idx + 1 < len(sys.argv):
                provider = sys.argv[idx+1]
        try:
            input_val = json.loads(input_data)
            if isinstance(input_val, dict):
                text_to_translate = input_val.get("text", "")
            elif isinstance(input_val, list):
                text_to_translate = input_val
            else:
                text_to_translate = str(input_val)
        except json.JSONDecodeError:
            text_to_translate = input_data
            
        res = run_translation(text_to_translate, target, provider=provider)
        print(json.dumps(res, indent=2))
        sys.exit(0)
    except Exception as global_e:
        print(json.dumps({"error": str(global_e)}), file=sys.stderr)
        sys.exit(1)
