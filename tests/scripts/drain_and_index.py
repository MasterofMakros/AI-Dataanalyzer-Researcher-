import redis
import requests
import json
import os
import time
import sys

# Configuration (Container Internal)
REDIS_HOST = os.getenv("REDIS_HOST", "conductor-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "change_me_in_prod")
# conductor-api service name in docker-compose
API_URL = "http://conductor-api:8000/index/documents" 

STREAM = "enrich:ner"
GROUP = "manual_indexer"
CONSUMER = "script-1"

def main():
    print(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}...")
    try:
        r = redis.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            password=REDIS_PASSWORD, 
            decode_responses=True
        )
        r.ping()
        print("Connected to Redis.")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        sys.exit(1)

    # Create consumer group
    try:
        r.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        print(f"Created consumer group '{GROUP}'.")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"Consumer group '{GROUP}' already exists.")
        else:
            raise e

    processed_count = 0
    
    print(f"Starting processing loop for stream '{STREAM}'...")
    while True:
        try:
            # Read batch of 50
            entries = r.xreadgroup(GROUP, CONSUMER, {STREAM: ">"}, count=50, block=2000)
            
            if not entries:
                print("No new messages. Waiting...", end="\r")
                time.sleep(1)
                continue

            for stream, messages in entries:
                docs_to_index = []
                msg_ids = []
                
                print(f"\nReceived {len(messages)} messages.")
                
                for msg_id, data in messages:
                    msg_ids.append(msg_id)
                    if "data" in data:
                        try:
                            # The 'data' field might be a JSON string or dict depending on producer
                            payload = data["data"]
                            if isinstance(payload, str):
                                payload = json.loads(payload)
                            
                            # Ensure ID for search index
                            if "id" not in payload:
                                payload["id"] = msg_id.replace("-", "")
                                
                            docs_to_index.append(payload)
                        except Exception as e:
                            print(f"Error parsing message {msg_id}: {e}")

                if docs_to_index:
                    try:
                        print(f"Indexing {len(docs_to_index)} documents to {API_URL}...")
                        resp = requests.post(API_URL, json={"documents": docs_to_index}, timeout=30)
                        
                        if resp.status_code in (200, 202):
                            r.xack(STREAM, GROUP, *msg_ids)
                            processed_count += len(docs_to_index)
                            print(f"Success! Total indexed: {processed_count}")
                        else:
                            print(f"API Error {resp.status_code}: {resp.text}")
                    except Exception as e:
                        print(f"API Request Failed: {e}")
        
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
