"""
Instagram Poster — "The Fisherman With No Bait"
SA Resilience | Social Media Marketing Campaign
4:5 ratio (1080x1350px equivalent) — Static Post

Concept: Golden hour Mauritius dock, fisherman casting with no bait.
Fish visible below surface, completely ignoring the bare hook.

Usage:
  py poster_fisherman.py
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

POSTER = {
    "file": "poster_fisherman.jpg",
    "prompt": (
        "Cinematic golden hour photography, a lone fisherman sitting at the very end of a weathered wooden dock pier "
        "extending into a stunning Mauritius tropical lagoon, turquoise crystal-clear water, "
        "the fisherman casts his fishing line with intense focus and full effort, "
        "slightly below the water surface a school of large tropical fish are clearly visible swimming just out of reach, "
        "the fishing hook is completely bare — no bait, just a plain bare hook sinking through the pristine water, "
        "the fish swim casually past ignoring the hook entirely, "
        "the fisherman stares ahead unaware, "
        "warm amber and gold tones from sunset light reflecting on the water, "
        "dramatic cinematic depth of field, foreground dock planks sharp, distant island silhouette in soft bokeh, "
        "ultra-realistic DSLR photography, Canon EOS R5, 35mm f/2.0 lens, "
        "portrait orientation 4:5, photorealistic 8K, editorial documentary style, "
        "golden hour rim light on fisherman silhouette, rich cinematic color grade, "
        "poetic melancholy mood, beautifully composed rule-of-thirds"
    ),
}


def generate_image(prompt: str, output_path: str) -> bool:
    print(f"Generating poster: {output_path}")
    print("Using FLUX.1-dev (high quality, ~30s)...\n")

    url = f"{BASE_URL}/genai/black-forest-labs/flux.1-dev"
    payload = {
        "prompt": prompt,
        "width": 832,   # 4:5 portrait ratio supported by FLUX
        "height": 1024,
        "num_inference_steps": 30,
        "guidance": 4.0,
        "seed": 77,
    }
    response = requests.post(url, headers=HEADERS, json=payload, timeout=180)

    if response.status_code != 200:
        print(f"dev model error ({response.status_code}), trying schnell fallback...")
        url = f"{BASE_URL}/genai/black-forest-labs/flux.1-schnell"
        payload = {"prompt": prompt, "width": 832, "height": 1024, "seed": 77}
        response = requests.post(url, headers=HEADERS, json=payload, timeout=120)
        if response.status_code != 200:
            print(f"ERROR {response.status_code}: {response.text}")
            return False

    artifacts = response.json().get("artifacts", [])
    if not artifacts:
        print("ERROR: No image in response:", response.json())
        return False

    img_bytes = base64.b64decode(artifacts[0]["base64"])
    with open(output_path, "wb") as f:
        f.write(img_bytes)
    return True


def main():
    if not API_KEY or not API_KEY.startswith("nvapi-"):
        print("ERROR: Set your NVIDIA API key first:")
        print('  $env:NVIDIA_API_KEY="nvapi-xxxx"')
        print("  Get a free key at https://build.nvidia.com")
        sys.exit(1)

    print("=" * 55)
    print("  SA Resilience — Instagram Poster Generator")
    print("  'The Fisherman With No Bait'")
    print("=" * 55)
    print()

    ok = generate_image(POSTER["prompt"], POSTER["file"])

    if ok:
        print(f"\nPoster saved: {POSTER['file']}")
        print("\nCaption ready to copy:")
        print("-" * 55)
        print("POSTING EVERY DAY AND GETTING ZERO RESULTS?")
        print("HERE IS EXACTLY WHY.\n")
        print("The #1 mistake businesses make on social media:")
        print("They confuse activity with strategy.\n")
        print("Posting ≠ Marketing.\n")
        print("Real social media marketing means:")
        print("→ Content built around what your audience needs to hear")
        print("→ Visuals that stop the scroll")
        print("→ Captions that move people to act")
        print("→ Data that shows what's actually generating leads\n")
        print("If your social media isn't generating inquiries,")
        print("it's not a platform problem. It's a strategy problem.\n")
        print("SA Resilience creates and manages content that's")
        print("tied to your business goals.\n")
        print("What does your social media currently do for your business? 👇")
        print("-" * 55)
        print("\nHashtags: #SocialMediaMarketing #ContentStrategy")
        print("#DigitalMarketing #Mauritius #MarketingTips")
    else:
        print("\nFailed to generate poster.")
        sys.exit(1)


if __name__ == "__main__":
    main()
