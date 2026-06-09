"""
NVIDIA NIM Free API — Image Generator
Uses free credits from build.nvidia.com (no credit card required).

Usage:
  py generate.py "a futuristic city at night"
  py generate.py "a golden retriever on a beach" my_dog.jpg
"""

import os
import sys
import base64
import requests

API_KEY = os.environ.get("NVIDIA_API_KEY", "")
BASE_URL = "https://ai.api.nvidia.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def check_api_key():
    if not API_KEY or not API_KEY.startswith("nvapi-"):
        print("ERROR: Set your NVIDIA API key first:")
        print('  $env:NVIDIA_API_KEY="nvapi-xxxx"')
        print("  Get one free at https://build.nvidia.com")
        sys.exit(1)


def generate_image(prompt: str, output_path: str = "output_image.jpg") -> str:
    print(f"Generating image: {prompt!r}")
    url = f"{BASE_URL}/genai/black-forest-labs/flux.1-schnell"
    payload = {
        "prompt": prompt,
        "width": 1024,
        "height": 1024,
        "seed": 0,
    }
    response = requests.post(url, headers=HEADERS, json=payload, timeout=120)
    if response.status_code != 200:
        print(f"ERROR {response.status_code}: {response.text}")
        sys.exit(1)
    data = response.json()
    artifacts = data.get("artifacts", [])
    if not artifacts:
        print("ERROR: No image in response:", data)
        sys.exit(1)
    img_bytes = base64.b64decode(artifacts[0]["base64"])
    with open(output_path, "wb") as f:
        f.write(img_bytes)
    print(f"Done! Image saved: {output_path}")
    return output_path


def main():
    check_api_key()
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    prompt = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "output_image.jpg"
    generate_image(prompt, output)


if __name__ == "__main__":
    main()
