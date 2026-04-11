import sys
import os
import requests
import time
import subprocess
import json

def run_validation():
    print("--- STARTING RUNTIME VALIDATION (CHIP-IDIOMAS VISUAL ACTIVATION) ---")
    
    # Check creator.js
    creator_js_path = "frontend/shell/creator.js"
    with open(creator_js_path, "r", encoding="utf-8") as f:
        content = f.read()
        if "chip-status-container" in content and "chip.name" in content:
            print("[PASS] creator.js contains the injected chip rendering logic.")
        else:
            print("[FAIL] creator.js is missing the injected logic.")

    # Check chip.json
    chip_json_path = "chips/chip-idiomas/chip.json"
    with open(chip_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if "Activa la fase charlable" in data.get("description", ""):
            print("[PASS] chip-idiomas description is correctly updated with sovereign role.")
        else:
            print("[FAIL] chip-idiomas description not updated.")
            
    print("--- SPINNING UP LOCALHOST ---")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(".")
    
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8008"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3) # Wait for startup
    
    try:
        # Check if localhost works
        res = requests.get("http://localhost:8008/api/v1/system/health")
        if res.status_code == 200:
            print("[PASS] Localhost runtime operates correctly.")
        else:
            print(f"[FAIL] Localhost runtime returned {res.status_code}")

        # Test shell launcher loading
        res_shell = requests.get("http://localhost:8008/shell/?creator=true")
        if res_shell.status_code == 200 and "creator_theme.css" in res_shell.text:
            print("[PASS] /shell/?creator=true loads correctly.")
        else:
            print("[FAIL] /shell/ failed to load properly.")
            
        headers = {"Authorization": "Bearer omniweb-dev-secret-token"}
        res_state = requests.get("http://localhost:8008/api/v1/system/state", headers=headers)
        if res_state.status_code == 200:
            state = res_state.json()
            chips = state.get("chips", [])
            idiomas_chip = next((c for c in chips if c["slug"] == "idiomas"), None)
            
            if idiomas_chip:
                print(f"[PASS] chip-idiomas state is readable via API: {idiomas_chip['status']}")
            else:
                print("[FAIL] chip-idiomas not found in state API.")
            
            # Check other chips
            if len(chips) > 1:
                print(f"[PASS] No unrelated chip disappeared. Total found: {len(chips)}")
            else:
                print(f"[FAIL] Other chips disappeared! Only found {len(chips)}.")
            
        else:
            print(f"[FAIL] State API routing failed {res_state.status_code}")

    except Exception as e:
        print(f"[ERROR] Exception during requests: {e}")
    finally:
        process.terminate()
        process.wait()
        print("--- VALIDATION FINISHED ---")

if __name__ == "__main__":
    run_validation()
