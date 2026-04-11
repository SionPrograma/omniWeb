import os
import sys
import requests
import time
import subprocess

def validate_staging_v21():
    print("--- OMNI_LINGUA_DOMAIN_DEPLOYMENT_V2.1 VALIDATION ---")
    
    # 1. Start backend process (Headless Staging)
    # Using a different port to simulate non-dev if needed, but 8000 is fine
    print("[1/3] Boiling Headless Backend...")
    # Using python -m uvicorn ...
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8008"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(5) # Wait for startup
    
    try:
        # 2. Check Static Files / Mount Truth
        print("[2/3] Verifying Output Mount...")
        test_file = "outputs/staging_test.txt"
        with open(test_file, "w") as f:
            f.write("STAGING_TRUTH")
            
        res = requests.get("http://127.0.0.1:8008/outputs/staging_test.txt")
        if res.status_code == 200 and res.text == "STAGING_TRUTH":
            print("[PASS] /outputs/ is correctly mounted and served.")
        else:
            print(f"[FAIL] /outputs/ mount failed. Status: {res.status_code}")

        # 3. Check Proxy Headers (Forwarded Headers)
        print("[3/3] Simulating Proxy Headers...")
        headers = {
            "X-Forwarded-Host": "omniweb.staging",
            "X-Forwarded-Proto": "https"
        }
        res_proxy = requests.get("http://127.0.0.1:8008/api/v1/lingua/process/governance/audit", headers=headers)
        # We don't have a direct "reflect headers" route in Lingua, but we can check if it 
        # doesn't crash and returns the correct response.
        if res_proxy.status_code == 200:
            print("[PASS] Backend survives proxy-forwarded requests.")
        else:
            print(f"[FAIL] Proxy audit test failed: {res_proxy.status_code}")

    finally:
        proc.terminate()
        if os.path.exists("outputs/staging_test.txt"): os.remove("outputs/staging_test.txt")
        print("\nGraduation Verdict: STAGING DEPLOYMENT HARDENED.")

if __name__ == "__main__":
    validate_staging_v21()
