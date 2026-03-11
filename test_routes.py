import requests

def test_routes():
    resps = {
        "finanzas": requests.get("http://localhost:8001/api/v1/finanzas/transactions"),
        "reparto": requests.get("http://localhost:8001/api/v1/reparto/stops"),
        "idiomas-ia": "frontend-only", 
        "programacion": "frontend-only",
        "system": requests.get("http://localhost:8001/api/v1/system/chips")
    }
    
    print("FINANZAS HTTP", resps["finanzas"].status_code)
    print("REPARTO HTTP", resps["reparto"].status_code)
    print("SYSTEM HTTP", resps["system"].status_code)
    
    chips = resps["system"].json()
    visible = [c.get("slug") for c in chips]
    print("VISIBLE CHIPS:", visible)
    
test_routes()
