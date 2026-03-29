import requests
import sys

def check_url(url):
    try:
        print(f"Checking {url}...")
        r = requests.get(url, timeout=5)
        print(f"Status: {r.status_code}")
        print(f"Length: {len(r.text)}")
        if r.status_code == 200:
            print("Successfully reached.")
            return True
        else:
            print(f"Error: {r.status_code}")
            return False
    except Exception as e:
        print(f"Failed: {e}")
        return False

# Since I am on the same machine, I can try localhost and the LAN IP
# First, let's find the LAN IP
import socket
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
print(f"Detected IP: {ip_address}")

base_url = f"http://{ip_address}:8000"

results = []
results.append(check_url(f"{base_url}/"))
results.append(check_url(f"{base_url}/shell/index.html"))
results.append(check_url(f"{base_url}/dashboard"))

if all(results):
    print("\nAll local LAN-simulated checks PASSED.")
else:
    print("\nSome checks FAILED.")
