"""
AI Creative Agent — Powered by Claude Opus + NVIDIA NIM

The agent understands context, design, marketing trends, and brand strategy.
It analyzes your brief, researches what's trending, crafts professional prompts,
and generates images using NVIDIA's free FLUX.1 API.

Setup:
  1. pip install anthropic requests pillow
  2. export ANTHROPIC_API_KEY=sk-ant-xxxx        (get at console.anthropic.com)
  3. export NVIDIA_API_KEY=nvapi-xxxx             (get free at build.nvidia.com)

Usage:
  python agent.py "create 3 Instagram posts for a luxury streetwear brand"
  python agent.py "design a product ad for handmade soap targeting Gen Z"
  python agent.py "make a carousel about trust and community for a market stall brand"

The agent will:
  - Analyze your brief for tone, audience, platform, and goals
  - Research current design and marketing trends for your niche
  - Generate professional, platform-optimized image prompts
  - Create the images and save them locally
  - Give you a creative brief explaining each image's strategy
"""

import os
import sys
import base64
import json
import time
import textwrap
import requests
import anthropic
from pathlib import Path
from datetime import datetime

# ── Keys ──────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
NVIDIA_API_KEY    = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL   = "https://ai.api.nvidia.com/v1"

OUTPUT_DIR = Path("agent_output")


# ── Helpers ───────────────────────────────────────────────────────────────────

def check_keys():
    missing = []
    if not ANTHROPIC_API_KEY or not ANTHROPIC_API_KEY.startswith("sk-ant-"):
        missing.append("ANTHROPIC_API_KEY  →  get free at console.anthropic.com")
    if not NVIDIA_API_KEY or not NVIDIA_API_KEY.startswith("nvapi-"):
        missing.append("NVIDIA_API_KEY     →  get free at build.nvidia.com (1,000 credits)")
    if missing:
        print("\nMissing API keys — set these environment variables:")
        for m in missing:
            print(f"  export {m}")
        sys.exit(1)


def _nvidia_headers():
    return {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _save_image(b64_data: str, filename: str) -> str:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_bytes(base64.b64decode(b64_data))
    return str(path)


# ── Tool implementations (called by the agent) ────────────────────────────────

def generate_image(
    prompt: str,
    filename: str = "",
    width: int = 1024,
    height: int = 1024,
    quality: str = "fast",
) -> dict:
    """
    Generate an image via NVIDIA NIM FLUX API.
    quality='fast' uses flux.1-schnell (~1 credit).
    quality='high' uses flux.1-dev (~4 credits, more photorealistic).
    Returns {"success": bool, "path": str, "error": str}.
    """
    model = "flux.1-dev" if quality == "high" else "flux.1-schnell"
    url   = f"{NVIDIA_BASE_URL}/genai/black-forest-labs/{model}"

    payload = {
        "prompt": prompt,
        "width":  min(max(width, 256), 1024),
        "height": min(max(height, 256), 1024),
        "seed":   42,
    }
    if quality == "high":
        payload["num_inference_steps"] = 28
        payload["guidance"] = 3.5

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"image_{timestamp}.jpg"

    try:
        resp = requests.post(url, headers=_nvidia_headers(), json=payload, timeout=120)
        if resp.status_code != 200:
            # fallback to schnell
            if quality == "high":
                payload.pop("num_inference_steps", None)
                payload.pop("guidance", None)
                url = f"{NVIDIA_BASE_URL}/genai/black-forest-labs/flux.1-schnell"
                resp = requests.post(url, headers=_nvidia_headers(), json=payload, timeout=120)
            if resp.status_code != 200:
                return {"success": False, "path": "", "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}

        artifacts = resp.json().get("artifacts", [])
        if not artifacts:
            return {"success": False, "path": "", "error": "No image in response"}

        path = _save_image(artifacts[0]["base64"], filename)
        return {"success": True, "path": path, "error": ""}

    except Exception as e:
        return {"success": False, "path": "", "error": str(e)}


def get_design_trends(niche: str, platform: str = "Instagram") -> dict:
    """
    Return current design and marketing trend data for a niche/platform.
    This is curated knowledge — no live web call needed.
    """
    # Comprehensive trend database — the agent uses this to ground its creative decisions
    trends_db = {
        "general": {
            "2024_2025_visual_trends": [
                "Hyper-realistic CGI product shots with soft studio lighting",
                "Raw, documentary-style photography — imperfect, candid, authentic",
                "Brutalist typography: oversized, clashing, high contrast",
                "Chromatic aberration and analog film grain for nostalgia",
                "Negative space with bold color-blocked backgrounds",
                "Pastel-to-neon gradient duotone overlays",
                "3D clay render aesthetics (soft shadows, matte surfaces)",
                "Dark academia and cottagecore natural texture palettes",
            ],
            "color_palettes": {
                "luxury":    ["#1a1a2e", "#e8d5b7", "#c9a84c", "#f5f0e8"],
                "fresh":     ["#e8f5e9", "#a5d6a7", "#2e7d32", "#ffffff"],
                "bold":      ["#ff4444", "#1a1a1a", "#f5f5f5", "#ffd700"],
                "earthy":    ["#8d6e63", "#d7ccc8", "#4e342e", "#ffccbc"],
                "tech":      ["#0d0d0d", "#00e5ff", "#7c4dff", "#ffffff"],
            },
            "composition_rules": [
                "Rule of thirds for product placement",
                "Leading lines drawing eye to hero element",
                "Frame-within-frame (arches, windows, foliage)",
                "Flat lay from directly above for food/product",
                "Low angle hero shot for power/aspiration",
            ],
        },
        "instagram": {
            "carousel_best_practices": [
                "Slide 1: Bold hook — must stop the scroll in 0.5 seconds",
                "Slide 2-5: Value delivery — each slide = one clear insight",
                "Slide 6: Strong CTA with friction-free next step",
                "Consistent color palette across all slides",
                "Typography large enough to read without clicking",
                "Swipe-teaser on right edge of each slide",
            ],
            "story_trends": [
                "Full-bleed immersive visuals with minimal text",
                "Before/after split-screen transformations",
                "Countdown timers and interactive polls",
            ],
        },
        "market_stall": {
            "trust_signals": [
                "Show the maker's hands or face — human connection",
                "Display origin/provenance clearly (farm name, region)",
                "Abundance display: overflowing baskets signal freshness",
                "Natural materials in display (wood, linen, terracotta)",
                "Morning light photography signals freshness",
                "Chalkboard pricing suggests artisanal authenticity",
            ],
            "branding_advice": [
                "Warm, earthy color palette evokes nature and trust",
                "Hand-lettered style fonts feel personal, not corporate",
                "Show customers interacting with products",
                "Use seasons/weather as backdrop for freshness narrative",
            ],
        },
        "streetwear": {
            "visual_identity": [
                "High contrast black/white with one accent color",
                "Urban decay backgrounds: brick, concrete, graffiti",
                "Motion blur on edges for energy",
                "Layering and texture in garment close-ups",
                "Portrait mode with shallow depth of field on details",
            ],
        },
        "food_beverage": {
            "photography_style": [
                "Steam/smoke for hot drinks — motion adds life",
                "Overhead flat lay with intentional 'messy' staging",
                "Dark moody backgrounds for premium positioning",
                "Bright airy whites for health/wellness positioning",
                "Macro lens on texture — seeds, crystals, drips",
            ],
        },
    }

    result = {
        "niche":    niche,
        "platform": platform,
        "general_trends":   trends_db["general"],
        "platform_tips":    trends_db.get(platform.lower(), {}),
        "niche_insights":   trends_db.get(niche.lower().replace(" ", "_"), {}),
        "prompt_enhancers": [
            "shot on Hasselblad medium format, ultra sharp",
            "golden hour lighting, warm bokeh",
            "editorial photography, Vogue aesthetic",
            "85mm f/1.4 portrait lens",
            "studio lighting with softbox and reflector",
            "cinematic color grading, film look",
            "hyperrealistic, 8K, photorealistic",
            "award-winning commercial photography",
        ],
    }
    return result


def analyze_brief(brief: str) -> dict:
    """
    Extract structured creative direction from a user brief.
    Returns audience, platform, tone, goals, number of images needed.
    """
    # The agent (Claude) handles this natively — this tool is a passthrough
    # that returns the brief structured, letting Claude do the analysis
    return {
        "raw_brief": brief,
        "instruction": (
            "Analyze this brief deeply. Identify: target audience demographics, "
            "platform (Instagram/Facebook/TikTok/Print/etc), visual tone "
            "(luxury/raw/playful/minimal/bold), primary goal (awareness/trust/sales/engagement), "
            "number of images to generate, and any brand constraints."
        ),
    }


def create_creative_report(
    brief: str,
    strategy: str,
    images: list,
) -> dict:
    """
    Compile the final creative package report.
    images: list of {"filename": str, "prompt": str, "purpose": str}
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = OUTPUT_DIR / f"creative_brief_{timestamp}.md"

    lines = [
        "# Creative Brief & Image Report",
        f"\n**Generated:** {datetime.now().strftime('%B %d, %Y %H:%M')}",
        f"\n## Original Brief\n{brief}",
        f"\n## Creative Strategy\n{strategy}",
        "\n## Generated Images\n",
    ]
    for i, img in enumerate(images, 1):
        lines.append(f"### Image {i}: {img.get('filename', 'unknown')}")
        lines.append(f"**Purpose:** {img.get('purpose', '')}")
        lines.append(f"**Prompt used:**\n> {img.get('prompt', '')}\n")

    lines.append("\n---\n*Generated by AI Creative Agent — Claude Opus + NVIDIA NIM FLUX*")
    report_path.write_text("\n".join(lines), encoding="utf-8")

    return {"report_path": str(report_path), "image_count": len(images)}


# ── Tool schema definitions ────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "analyze_brief",
        "description": (
            "Extract structured creative direction from a user brief. "
            "Call this FIRST before doing anything else."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brief": {"type": "string", "description": "The user's creative brief or request"},
            },
            "required": ["brief"],
        },
    },
    {
        "name": "get_design_trends",
        "description": (
            "Get current design, visual, and marketing trends for a specific niche and platform. "
            "Use this to ground your creative decisions in what's working right now."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "niche":    {"type": "string", "description": "The industry or niche (e.g. market_stall, streetwear, food_beverage, beauty, fitness)"},
                "platform": {"type": "string", "description": "Target platform (Instagram, Facebook, TikTok, Print, YouTube)", "default": "Instagram"},
            },
            "required": ["niche"],
        },
    },
    {
        "name": "generate_image",
        "description": (
            "Generate a high-quality image using NVIDIA NIM FLUX AI. "
            "Write a detailed, professional prompt. Include: subject, style, lighting, camera, mood, colors, composition. "
            "The more specific and visual the prompt, the better the result."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt":   {"type": "string", "description": "Detailed image generation prompt (50-150 words for best results)"},
                "filename": {"type": "string", "description": "Output filename (e.g. slide_01_hook.jpg)"},
                "width":    {"type": "integer", "description": "Image width in pixels (256-1024, multiple of 8)", "default": 1024},
                "height":   {"type": "integer", "description": "Image height in pixels (256-1024, multiple of 8)", "default": 1024},
                "quality":  {"type": "string", "enum": ["fast", "high"], "description": "fast=schnell (~1 credit), high=dev model (~4 credits, more photorealistic)", "default": "fast"},
            },
            "required": ["prompt", "filename"],
        },
    },
    {
        "name": "create_creative_report",
        "description": "Compile the final creative brief and strategy report. Call this at the end after all images are generated.",
        "input_schema": {
            "type": "object",
            "properties": {
                "brief":    {"type": "string", "description": "Original user brief"},
                "strategy": {"type": "string", "description": "Your full creative strategy and rationale"},
                "images":   {
                    "type": "array",
                    "description": "List of generated images",
                    "items": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "prompt":   {"type": "string"},
                            "purpose":  {"type": "string"},
                        },
                    },
                },
            },
            "required": ["brief", "strategy", "images"],
        },
    },
]


# ── Tool dispatcher ────────────────────────────────────────────────────────────

def dispatch_tool(name: str, inputs: dict) -> str:
    if name == "analyze_brief":
        result = analyze_brief(**inputs)
    elif name == "get_design_trends":
        result = get_design_trends(**inputs)
    elif name == "generate_image":
        print(f"\n  Generating: {inputs.get('filename', 'image')}...")
        result = generate_image(**inputs)
        if result["success"]:
            print(f"  Saved: {result['path']}")
        else:
            print(f"  Error: {result['error']}")
    elif name == "create_creative_report":
        result = create_creative_report(**inputs)
        print(f"\n  Report saved: {result['report_path']}")
    else:
        result = {"error": f"Unknown tool: {name}"}

    return json.dumps(result)


# ── The Agent loop ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a world-class creative director and AI image generation specialist.

Your expertise spans:
- Brand strategy and positioning
- Visual design (composition, color theory, typography)
- Marketing psychology and conversion-focused creative
- Platform-specific best practices (Instagram, Facebook, TikTok, print)
- Current design trends across fashion, food, lifestyle, luxury, and street culture
- Professional photography aesthetics and prompting for AI image generators

When given a creative brief, you:
1. ALWAYS start by calling analyze_brief to deeply understand the ask
2. Call get_design_trends to ground your creative in what's working NOW
3. Develop a clear creative strategy (audience insight, visual language, emotional hook)
4. Write detailed, professional image prompts — be specific about lighting, composition, camera, mood
5. Generate the images using generate_image
6. End with create_creative_report to deliver a full creative package

For image prompts, use professional photography language:
- Specify camera/lens (e.g., "Canon 5D Mark IV, 50mm f/1.2, shallow DOF")
- Specify lighting (e.g., "golden hour backlight, rim lighting, soft diffused fill")
- Specify style (e.g., "editorial, commercial photography, award-winning, Vogue aesthetic")
- Include mood/emotion (e.g., "warm, aspirational, authentic, trustworthy")
- Include color palette direction
- Include composition guidance (e.g., "rule of thirds, leading lines, negative space")

You deliver commercially viable, trend-aware, audience-appropriate creative — not generic AI art.
Think like a $500/hour creative director who bills results, not hours."""


def run_agent(brief: str):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print(f"\n{'='*60}")
    print("  AI Creative Agent — Claude Opus + NVIDIA NIM FLUX")
    print(f"{'='*60}")
    print(f"\nBrief: {brief}\n")
    print("Thinking...")

    messages = [{"role": "user", "content": brief}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Collect any text output from this turn
        for block in response.content:
            if hasattr(block, "text") and block.text:
                wrapped = textwrap.fill(block.text, width=70, subsequent_indent="  ")
                print(f"\n{wrapped}")

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason != "tool_use":
            print(f"\nUnexpected stop reason: {response.stop_reason}")
            break

        # Execute all requested tools
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                print(f"\n[Tool] {block.name}({', '.join(f'{k}={repr(v)[:40]}' for k, v in block.input.items())})")
                result = dispatch_tool(block.name, block.input)
                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": block.id,
                    "content":     result,
                })

        messages.append({"role": "user", "content": tool_results})

    print(f"\n{'='*60}")
    print(f"  Done! Check the '{OUTPUT_DIR}/' folder for your images.")
    print(f"{'='*60}\n")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    check_keys()

    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExample:")
        print('  python agent.py "create 3 Instagram posts for a luxury streetwear brand"\n')
        sys.exit(0)

    brief = " ".join(sys.argv[1:])
    run_agent(brief)


if __name__ == "__main__":
    main()
