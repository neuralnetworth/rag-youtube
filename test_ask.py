#!/usr/bin/env python3
import requests

url = "http://localhost:5555/ask?question=What%20is%20gamma%20in%20options%20trading?"
try:
    response = requests.get(url, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")