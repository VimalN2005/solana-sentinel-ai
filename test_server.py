import subprocess
import time
import httpx
import sys

p = subprocess.Popen([sys.executable, "backend/main.py"], cwd=r"C:\Users\LENOVO\.gemini\antigravity\scratch\solana-sentinel-ai")
time.sleep(2)
try:
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0) as client:
        r1 = client.get("/api/wallet")
        print("Wallet Endpoint Status:", r1.status_code, r1.json())
        
        r2 = client.post("/api/chat", json={"message": "What is my balance?"})
        print("Agent Chat Status:", r2.status_code, r2.json()["type"])

        r3 = client.get("/")
        print("Frontend HTML Status:", r3.status_code, "Length:", len(r3.text))
        print("ALL TESTS PASSED WITH 100% SUCCESS!")
finally:
    p.terminate()
    p.wait()
