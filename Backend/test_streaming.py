import requests
import json
import sys

def test_streaming():
    url = "http://localhost:8000/chat"
    payload = {"message": "Has V. Kohli shown any weakness?"}
    headers = {"Content-Type": "application/json"}

    print(f"Connecting to {url}...")
    try:
        with requests.post(url, json=payload, headers=headers, stream=True) as response:
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(response.text)
                return

            print("--- Stream Started ---")
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        json_str = decoded_line[6:] # Remove "data: " prefix
                        try:
                            data = json.loads(json_str)
                            event_type = data.get("type", "unknown")
                            content = data.get("content", "")
                            print(f"[{event_type.upper()}] {content}")
                        except json.JSONDecodeError:
                            print(f"[RAW] {decoded_line}")
            print("--- Stream Ended ---")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_streaming()
