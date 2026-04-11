import sys
import os
import requests
import time
import subprocess
import json
import threading
from contextlib import contextmanager

# Simple Mock Server for Stage B to simulate LM Studio/llama.cpp
from http.server import HTTPServer, BaseHTTPRequestHandler

class MockLMStudioHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": "[STAGE B MOCK] OmniWeb procesando tu solicitud de forma extendida y analítica."
                    }
                }
            ]
        }
        self.wfile.write(json.dumps(response_data).encode("utf-8"))
        
    def log_message(self, format, *args):
        pass # Suppress logs

def run_mock_server():
    server = HTTPServer(('127.0.0.1', 1234), MockLMStudioHandler)
    server.serve_forever()

def run_validation():
    print("--- STARTING STAGE B RUNTIME VALIDATION ---")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(".")
    
    import importlib
    chip_module = importlib.import_module("chips.chip-idiomas.core.engine.orchestrator")
    LanguageOrchestrator = getattr(chip_module, "LanguageOrchestrator")
    orchestrator = LanguageOrchestrator()
    
    print("\n--- TEST: STAGE A FULL FALLBACK (NO MOCK SERVER RUNNING - FIRST ATTEMPT) ---")
    start = time.time()
    # "qué es omniweb" maps to 'explanation'
    res_a = orchestrator.orchestrate("qué es omniweb", None, "es")
    latency1 = time.time() - start
    print(f"Latency: {latency1:.3f}s")
    print(f"Result (Explanation): {res_a}")
    
    print("\n--- TEST: STAGE A FULL FALLBACK (NO MOCK SERVER RUNNING - SECOND ATTEMPT) ---")
    start = time.time()
    res_a2 = orchestrator.orchestrate("resumen de omniweb", None, "es")
    latency2 = time.time() - start
    print(f"Latency: {latency2:.3f}s")
    print(f"Result (Summary): {res_a2}")
    
    if latency1 <= 3.0 and latency2 < 0.05:
        print("[PASS] Latency Shielding correctly cached the failure. First attempt timed out elegantly, second attempt proved immediate.")
    else:
        print(f"[FAIL] Latency shielding failed! L1: {latency1:.3f}s, L2: {latency2:.3f}s")
        
    print("\n--- SPINNING UP MOCK 'STAGE B' LM STUDIO SERVER ---")
    # Reset shield cache for test
    orchestrator.composer.tool_adapter._last_failure_time = 0
    
    mock_thread = threading.Thread(target=run_mock_server, daemon=True)
    mock_thread.start()
    time.sleep(1) # Let server start
    
    print("\n--- TEST: STAGE B ACTIVE ---")
    start = time.time()
    res_b = orchestrator.orchestrate("qué es omniweb", None, "es")
    latency = time.time() - start
    print(f"Latency: {latency:.3f}s")
    print(f"Result (Explanation): {res_b}")
    if "[STAGE B MOCK]" in res_b:
        print("[PASS] Stage B handles allowed intents correctly when available.")
    else:
        print("[FAIL] Stage B was available but did not handle the request.")
        
    print("\n--- TEST: NON-GATED INTENT (greetings bypass Stage B) ---")
    res_greet = orchestrator.orchestrate("hola", None, "es")
    print(f"Result (Greeting): {res_greet}")
    if "[STAGE B MOCK]" not in res_greet and "Hola" in res_greet:
        print("[PASS] Non-gated intent safely bypassed Stage B and used Stage A.")
    else:
        print("[WARN/FAIL] Intent gating didn't work as expected.")
        
    print("\n--- TEST: LOCALHOST & HUD STABILITY ---")
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8008"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)
    try:
        res = requests.get("http://localhost:8008/api/v1/system/health")
        if res.status_code == 200:
            print("[PASS] Localhost API and router stable.")
        res_launcher = requests.get("http://localhost:8008/shell/?creator=true")
        if res_launcher.status_code == 200:
            print("[PASS] HUD / Launcher renders without regressions.")
    except Exception as e:
        print(f"[FAIL] Localhost tests failed: {e}")
    finally:
        process.terminate()
        process.wait()
        
    print("\n--- VALIDATION COMPLETE ---")

if __name__ == "__main__":
    import pathlib
    # Adjust pythonpath to find chips module correctly
    sys.path.append(os.path.abspath("."))
    run_validation()
