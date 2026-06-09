"""
Instagram Carousel Generator — Branding Post
Generates all 6 slides for: PEOPLE BUY FROM BRANDS THEY TRUST

Usage:
  py carousel.py

Saves: slide_1.jpg through slide_6.jpg
"""

import os
import sys
import base64
import time
import requests

API_KEY = os.environ.get("NVIDIA_API_KEY", "")
BASE_URL = "https://ai.api.nvidia.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

SLIDES = [
    {
        "file": "slide_1.jpg",
        "prompt": (
            "Aerial overhead cinematic photograph of a vibrant, warm, colourful African market street, "
            "many market stalls below, one stall highlighted with a glowing thin gold circle ring around it, "
            "golden hour sunlight, rich warm tones, documentary style, high detail, photorealistic, "
            "shot on Sony A7R, shallow depth of field, Instagram square format"
        ),
    },
    {
        "file": "slide_2.jpg",
        "prompt": (
            "Eye-level street photography at an African market stall, plain generic stall with no branding, "
            "dull colours, customers walking past without stopping, ignoring the stall, "
            "warm natural light, candid documentary style, photorealistic, cinematic, "
            "busy market background blurred, authentic African people"
        ),
    },
    {
        "file": "slide_3.jpg",
        "prompt": (
            "Eye-level street photography at a beautifully branded African market stall, "
            "clean elegant signage, warm cohesive colours, small crowd of customers stopping and engaging, "
            "smiling vendor, golden hour warm light, cinematic documentary style, photorealistic, "
            "authentic Mauritius or African market atmosphere, vibrant but professional"
        ),
    },
    {
        "file": "slide_4.jpg",
        "prompt": (
            "Close-up photograph of two identical products placed side by side on a wooden surface, "
            "one product has plain generic no-brand packaging, the other has clean premium elegant branding, "
            "a human hand reaching decisively for the branded product, "
            "warm studio lighting, shallow depth of field, photorealistic, commercial photography style"
        ),
    },
    {
        "file": "slide_5.jpg",
        "prompt": (
            "Evening twilight street photography at an African market, two stalls side by side, "
            "left stall is generic with no branding — completely empty, no customers, dim light, "
            "right stall has clean branding — still busy with customers, warm glowing lights, "
            "cinematic atmosphere, photorealistic, documentary style, golden and warm tones"
        ),
    },
    {
        "file": "slide_6.jpg",
        "prompt": (
            "Minimalist flat lay graphic design, pure black background, "
            "elegant white bold typography centered: 'WHAT DOES YOUR BRAND SAY ABOUT YOU?', "
            "below in smaller gold text: 'DM BRAND', "
            "clean luxury branding aesthetic, high contrast, Instagram CTA slide, "
            "professional graphic design, no clutter"
        ),
    },
]


def generate_image(prompt: str, output_path: str) -> str:
    url = f"{BASE_URL}/genai/black-forest-labs/flux.1-schnell"
    payload = {"prompt": prompt, "width": 1024, "height": 1024, "seed": 42}
    response = requests.post(url, headers=HEADERS, json=payload, timeout=120)
    if response.status_code != 200:
        print(f"  ERROR {response.status_code}: {response.text}")
        return None
    artifacts = response.json().get("artifacts", [])
    if not artifacts:
        print("  ERROR: No image in response")
        return None
    img_bytes = base64.b64decode(artifacts[0]["base64"])
    with open(output_path, "wb") as f:
        f.write(img_bytes)
    return output_path


def main():
    if not API_KEY or not API_KEY.startswith("nvapi-"):
        print("ERROR: Set your API key first:")
        print('  $env:NVIDIA_API_KEY="nvapi-xxxx"')
        sys.exit(1)

    print("Generating 6 Instagram carousel slides...\n")
    success = 0
    for i, slide in enumerate(SLIDES, 1):
        print(f"[{i}/6] {slide['file']} ...")
        result = generate_image(slide["prompt"], slide["file"])
        if result:
            print(f"  Saved: {slide['file']}")
            success += 1
        else:
            print(f"  Failed: {slide['file']}")
        if i < len(SLIDES):
            time.sleep(1)

    print(f"\nDone! {success}/6 slides saved in C:\\Users\\SA Resilience\\")
    print("Files: slide_1.jpg to slide_6.jpg")


if __name__ == "__main__":
    main()
