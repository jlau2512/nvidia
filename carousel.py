"""
Instagram Carousel Generator — Branding Post (HIGH QUALITY)
Uses FLUX.1-dev for photorealistic results.

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
            "Aerial drone photograph looking straight down at a vibrant crowded African outdoor market street, "
            "dozens of colorful market stalls with fabric canopies in orange, red, yellow, green, "
            "one stall in the center highlighted with a thin glowing gold circle around it, "
            "people walking between stalls, golden hour afternoon sunlight casting long shadows, "
            "ultra-realistic DSLR photography, shot from 40 meters height, Canon EOS R5, "
            "85mm lens, cinematic color grade, rich warm tones, photorealistic 8K"
        ),
    },
    {
        "file": "slide_2.jpg",
        "prompt": (
            "Eye-level street photography at a plain generic market stall in a busy African outdoor market, "
            "stall has no branding, no signage, dull brown wooden table, messy display of products, "
            "people in the busy market walking past completely ignoring the stall, vendor looks bored, "
            "motion blur on passing people, shallow depth of field, 35mm f1.8 lens, "
            "natural warm afternoon light, ultra-realistic documentary photography, "
            "authentic African market atmosphere, photorealistic, high detail skin texture"
        ),
    },
    {
        "file": "slide_3.jpg",
        "prompt": (
            "Eye-level street photography at a beautifully branded premium market stall in an African market, "
            "clean professional logo signage, elegant color-coordinated display, neat product arrangement, "
            "a small crowd of 3-4 customers stopping, leaning in, smiling, engaging with the vendor, "
            "vendor is confident and welcoming, golden hour warm sunlight, "
            "shallow depth of field background bokeh, 35mm f1.8 documentary photography, "
            "ultra-realistic photorealistic 8K, authentic African people, warm vibrant tones"
        ),
    },
    {
        "file": "slide_4.jpg",
        "prompt": (
            "Close-up commercial product photography, two identical bottles of hot sauce side by side "
            "on a dark wooden surface, left bottle has plain white generic label with no design, "
            "right bottle has premium elegant branded label with clean typography and logo, "
            "a dark-skinned human hand reaching from the right side decisively grabbing the branded bottle, "
            "dramatic studio lighting with soft shadows, shallow depth of field, "
            "ultra-realistic commercial photography, 100mm macro lens, photorealistic 8K, "
            "warm amber tones, cinematic"
        ),
    },
    {
        "file": "slide_5.jpg",
        "prompt": (
            "Evening twilight street photography at an African outdoor market, two adjacent market stalls, "
            "left stall: plain unbranded, completely empty with no customers, dim lighting, vendor sitting alone, "
            "right stall: clean branded signage with warm glowing string lights, 4-5 customers browsing, "
            "lively and busy, golden warm glow, blue evening sky in background, "
            "35mm lens, ultra-realistic documentary photography, photorealistic 8K, "
            "cinematic color grade, high detail"
        ),
    },
    {
        "file": "slide_6.jpg",
        "prompt": (
            "Minimalist luxury graphic design poster, pure deep black background, "
            "large bold white sans-serif typography in the center reading: WHAT DOES YOUR BRAND SAY ABOUT YOU, "
            "below it smaller elegant gold metallic text: DM BRAND, "
            "very subtle gold thin horizontal line separating the two texts, "
            "perfect symmetry, high-end fashion magazine aesthetic, "
            "ultra clean, no clutter, dramatic lighting on text, photorealistic render, 8K"
        ),
    },
]


def generate_image(prompt: str, output_path: str) -> bool:
    # FLUX.1-dev: higher quality, more realistic than schnell
    url = f"{BASE_URL}/genai/black-forest-labs/flux.1-dev"
    payload = {
        "prompt": prompt,
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 28,
        "guidance": 3.5,
        "seed": 42,
    }
    response = requests.post(url, headers=HEADERS, json=payload, timeout=180)

    if response.status_code != 200:
        # Fallback to schnell if dev is not available
        print(f"  dev model error ({response.status_code}), trying schnell fallback...")
        url = f"{BASE_URL}/genai/black-forest-labs/flux.1-schnell"
        payload = {"prompt": prompt, "width": 1024, "height": 1024, "seed": 42}
        response = requests.post(url, headers=HEADERS, json=payload, timeout=120)
        if response.status_code != 200:
            print(f"  ERROR {response.status_code}: {response.text}")
            return False

    artifacts = response.json().get("artifacts", [])
    if not artifacts:
        print("  ERROR: No image in response")
        return False

    img_bytes = base64.b64decode(artifacts[0]["base64"])
    with open(output_path, "wb") as f:
        f.write(img_bytes)
    return True


def main():
    if not API_KEY or not API_KEY.startswith("nvapi-"):
        print("ERROR: Set your API key first:")
        print('  $env:NVIDIA_API_KEY="nvapi-xxxx"')
        sys.exit(1)

    print("Generating 6 high-quality Instagram carousel slides (FLUX.1-dev)...")
    print("Each slide takes ~20-30 seconds. Please wait...\n")

    success = 0
    for i, slide in enumerate(SLIDES, 1):
        print(f"[{i}/6] Generating {slide['file']} ...")
        ok = generate_image(slide["prompt"], slide["file"])
        if ok:
            print(f"  Saved: {slide['file']}")
            success += 1
        else:
            print(f"  Failed: {slide['file']}")
        if i < len(SLIDES):
            time.sleep(2)

    print(f"\nDone! {success}/6 slides saved.")
    print("Open File Explorer > C:\\Users\\SA Resilience\\ to view your images.")


if __name__ == "__main__":
    main()
