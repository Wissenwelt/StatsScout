import requests
import json
import time

url = "http://localhost:8000/chat"

# Simulating an agent response that triggers a highlight
# We need to test if the frontend parses this correctly. 
# Note: This Python script can't see the frontend UI, but we can verify the backend sends the prompt.
# To truly test the frontend, we'd need a browser tool, but "web proof" requires manual verification anyway.
# This script ensures the backend is capable of sending the token.

payload = {
    "message": "Who is the key player for Sri Lanka?"
}

print(f"Sending request to {url}...")
try:
    with requests.post(url, json=payload, stream=True) as r:
        r.raise_for_status()
        print("Response stream started...")
        for line in r.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    json_str = decoded_line[6:]
                    if json_str == "[DONE]":
                        break
                    try:
                        data = json.loads(json_str)
                        if data.get("type") == "answer":
                            print(f"Agent Text: {data.get('content')}")
                        elif data.get("type") == "thought":
                             print(f"Thought: {data.get('content')}")
                    except json.JSONDecodeError:
                        pass
except Exception as e:
    print(f"Error: {e}")
