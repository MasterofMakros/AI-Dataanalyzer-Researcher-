
import requests
import json

API_URL = "http://localhost:8005"

print("🔍 Checking API Health...")
try:
    resp = requests.get(f"{API_URL}/health", timeout=5)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
except Exception as e:
    print(f"❌ Health Check Failed: {e}")
    exit(1)

print("\n🛡️ Testing PII Detection (GLiNER)...")
payload = {
    "text": "Mitarbeiter Stefan Müller hat die IBAN DE45 1234 5678 verloren.",
    "labels": ["person", "iban"]
}
try:
    resp = requests.post(f"{API_URL}/process/pii", json=payload, timeout=120)
    print(f"Status: {resp.status_code}")
    print(f"Entities: {resp.json()}")
except Exception as e:
    print(f"❌ PII Detection Failed: {e}")

print("\n🧠 Testing Deep Ingest (Docling) - Skipped (Requires PDF upload)")
