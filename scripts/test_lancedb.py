
import requests
import json
import time

API_URL = "http://localhost:8005"


def wait_for_health() -> None:
    print("⏳ Waiting for API Health (and Lazy Load)...")
    for _ in range(12):  # Wait up to 60s
        try:
            resp = requests.get(f"{API_URL}/health", timeout=5)
            if resp.status_code == 200:
                print(f"✅ API Up: {resp.json()}")
                return
        except Exception:
            pass
        time.sleep(5)
    print("❌ API failed to come up.")
    exit(1)


def main() -> None:
    wait_for_health()

    print("\n💾 Testing LanceDB Storage...")
    doc = {
        "id": "doc_001",
        "text": "LanceDB is a serverless vector database that runs on your file system. It is great for local AI.",
        "metadata": {"source": "manual_test", "category": "tech"},
    }

    try:
        start = time.time()
        # Timeout 120s for first run (loading embedding model)
        resp = requests.post(f"{API_URL}/vector/store", json=doc, timeout=120)
        print(f"Store Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        print(f"⏱️ Time: {time.time() - start:.2f}s")
    except Exception as e:
        print(f"❌ Storage Failed: {e}")
        exit(1)

    print("\n🔍 Testing Semantic Search...")
    query = {
        "query": "local vector database for AI",
        "limit": 2,
    }

    try:
        start = time.time()
        resp = requests.post(f"{API_URL}/vector/search", json=query, timeout=30)
        print(f"Search Status: {resp.status_code}")
        results = resp.json().get("results", [])
        print(f"Found {len(results)} results:")
        for result in results:
            # Deserialize metadata if feasible or just print text
            print(f"   - [{result['id']}] {result['text']} (Meta: {result['metadata']})")
        print(f"⏱️ Time: {time.time() - start:.2f}s")
    except Exception as e:
        print(f"❌ Search Failed: {e}")


if __name__ == "__main__":
    main()
