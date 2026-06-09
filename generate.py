"""
NVIDIA NIM Free API — Image & Video Generator
Uses free credits from build.nvidia.com (no credit card required).

Usage:
  py generate.py image "a futuristic city at night"
  py generate.py video path/to/input.jpg
  py generate.py both "a golden retriever on a beach"
"""

import os
import sys
import base64
import time
import requests
from pathlib import Path

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
    print(f"Image saved: {output_path}")
    return output_path


def generate_video(image_path: str, output_path: str = "output_video.mp4") -> str:
    print(f"Generating video from: {image_path}")
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    ext = Path(image_path).suffix.lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    url = f"{BASE_URL}/genai/stabilityai/stable-video-diffusion"
    payload = {
        "image": f"data:{mime};base64,{img_b64}",
        "seed": 0,
    }
    response = requests.post(url, headers=HEADERS, json=payload, timeout=120)
    if response.status_code == 202:
        request_id = response.headers.get("NVCF-REQID") or response.json().get("requestId")
        print(f"  Job queued (id={request_id}), polling...")
        video_bytes = _poll_for_video(request_id)
    elif response.status_code == 200:
        data = response.json()
        artifacts = data.get("artifacts", [])
        if not artifacts:
            print("ERROR: No video in response:", data)
            sys.exit(1)
        video_bytes = base64.b64decode(artifacts[0]["base64"])
    else:
        print(f"ERROR {response.status_code}: {response.text}")
        sys.exit(1)
    with open(output_path, "wb") as f:
        f.write(video_bytes)
    print(f"Video saved: {output_path}")
    return output_path


def _poll_for_video(request_id: str, max_wait: int = 300) -> bytes:
    poll_url = f"{BASE_URL}/genai/stabilityai/stable-video-diffusion"
    poll_headers = {**HEADERS, "NVCF-POLL-SECONDS": "15", "NVCF-REQID": request_id}
    waited = 0
    interval = 5
    while waited < max_wait:
        time.sleep(interval)
        waited += interval
        resp = requests.get(poll_url, headers=poll_headers, timeout=60)
        if resp.status_code == 202:
            pct = resp.headers.get("NVCF-PERCENT-COMPLETE", "?")
            print(f"  ...{pct}% complete ({waited}s elapsed)")
            interval = min(interval + 5, 20)
            continue
        if resp.status_code == 200:
            data = resp.json()
            artifacts = data.get("artifacts", [])
            if not artifacts:
                print("ERROR: No video in poll response:", data)
                sys.exit(1)
            return base64.b64decode(artifacts[0]["base64"])
        print(f"  Poll error {resp.status_code}: {resp.text}")
        sys.exit(1)
    print("ERROR: Timed out waiting for video.")
    sys.exit(1)


def main():
    check_api_key()
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(0)
    mode = sys.argv[1].lower()
    arg = sys.argv[2]
    if mode == "image":
        generate_image(arg)
    elif mode == "video":
        if not os.path.exists(arg):
            print(f"ERROR: File not found: {arg}")
            sys.exit(1)
        generate_video(arg)
    elif mode == "both":
        img_path = generate_image(arg, output_path="output_image.jpg")
        generate_video(img_path, output_path="output_video.mp4")
        print("\nDone! Files: output_image.jpg  output_video.mp4")
    else:
        print(f"Unknown mode: {mode!r}. Use: image | video | both")
        sys.exit(1)


if __name__ == "__main__":
    main()
