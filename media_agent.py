"""
Full Media Suite Agent — Claude Opus + Multi-Provider AI

The agent creates a COMPLETE social media package:
  - Images (3 free providers: Pollinations, NVIDIA NIM, HuggingFace)
  - Videos (text-to-video + image-to-video via HuggingFace)
  - Platform-optimized captions with storytelling hooks
  - Hashtag strategy (niche + broad + trending mix)
  - Music/audio mood recommendations
  - Posting schedule with timing strategy
  - Full exportable JSON + Markdown package

Required API keys (all free):
  ANTHROPIC_API_KEY   → console.anthropic.com  (free $5 credit)
  NVIDIA_API_KEY      → build.nvidia.com        (free 1,000 credits)
  HF_API_KEY          → huggingface.co/settings/tokens  (free)

Pollinations.ai requires NO key at all — zero setup.

Setup:
  pip install anthropic requests pillow

Usage:
  python media_agent.py "launch campaign for handmade honey brand, Instagram + TikTok"
  python media_agent.py "3 carousel slides for market stall trust post"
  python media_agent.py "viral reel concept for a luxury sneaker drop"
"""

import os
import sys
import json
import base64
import time
import textwrap
import requests
import urllib.parse
from pathlib import Path
from datetime import datetime

import anthropic

# ── Keys ──────────────────────────────────────────────────────────────────────
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
NVIDIA_KEY    = os.environ.get("NVIDIA_API_KEY", "")
HF_KEY        = os.environ.get("HF_API_KEY", "")          # optional but unlocks video

OUTPUT_DIR = Path("media_output")

# ── Image providers ────────────────────────────────────────────────────────────

def _img_pollinations(prompt: str, width: int, height: int, filename: str) -> dict:
    """
    Pollinations.ai — 100% free, no API key, returns image via URL.
    Best for: quick drafts, organic/natural styles, landscapes.
    """
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&model=flux"
    try:
        resp = requests.get(url, timeout=90)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            path = _save_raw(resp.content, filename)
            return {"success": True, "path": path, "provider": "Pollinations.ai (free)", "error": ""}
        return {"success": False, "path": "", "provider": "Pollinations.ai", "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "Pollinations.ai", "error": str(e)}


def _img_nvidia(prompt: str, width: int, height: int, filename: str, quality: str) -> dict:
    """NVIDIA NIM FLUX — free credits, high quality."""
    if not NVIDIA_KEY:
        return {"success": False, "path": "", "provider": "NVIDIA NIM", "error": "NVIDIA_API_KEY not set"}
    model = "flux.1-dev" if quality == "high" else "flux.1-schnell"
    url   = f"https://ai.api.nvidia.com/v1/genai/black-forest-labs/{model}"
    headers = {
        "Authorization": f"Bearer {NVIDIA_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"prompt": prompt, "width": min(width, 1024), "height": min(height, 1024), "seed": 42}
    if quality == "high":
        payload.update({"num_inference_steps": 28, "guidance": 3.5})
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code == 200:
            b64 = resp.json().get("artifacts", [{}])[0].get("base64", "")
            if b64:
                path = _save_raw(base64.b64decode(b64), filename)
                return {"success": True, "path": path, "provider": "NVIDIA NIM FLUX", "error": ""}
        return {"success": False, "path": "", "provider": "NVIDIA NIM", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "NVIDIA NIM", "error": str(e)}


def _img_huggingface(prompt: str, width: int, height: int, filename: str) -> dict:
    """HuggingFace Inference API — free tier, FLUX.1-schnell model."""
    if not HF_KEY:
        return {"success": False, "path": "", "provider": "HuggingFace", "error": "HF_API_KEY not set"}
    url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {"width": min(width, 1024), "height": min(height, 1024)},
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            path = _save_raw(resp.content, filename)
            return {"success": True, "path": path, "provider": "HuggingFace FLUX", "error": ""}
        return {"success": False, "path": "", "provider": "HuggingFace", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "HuggingFace", "error": str(e)}


# ── Video providers ────────────────────────────────────────────────────────────

def _video_huggingface_t2v(prompt: str, filename: str) -> dict:
    """
    HuggingFace text-to-video — free tier.
    Uses damo-vilab/text-to-video-ms-1.7b (short clips ~2s, 256x256).
    """
    if not HF_KEY:
        return {"success": False, "path": "", "provider": "HuggingFace T2V", "error": "HF_API_KEY not set — get free at huggingface.co/settings/tokens"}
    url = "https://api-inference.huggingface.co/models/damo-vilab/text-to-video-ms-1.7b"
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    payload = {"inputs": prompt}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=180)
        if resp.status_code == 200:
            ct = resp.headers.get("content-type", "")
            if "video" in ct or "octet" in ct or len(resp.content) > 50000:
                path = _save_raw(resp.content, filename.replace(".mp4", ".mp4"))
                return {"success": True, "path": path, "provider": "HuggingFace Text-to-Video", "error": ""}
        if resp.status_code == 503:
            return {"success": False, "path": "", "provider": "HuggingFace T2V", "error": "Model loading (cold start) — try again in 20 seconds"}
        return {"success": False, "path": "", "provider": "HuggingFace T2V", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "HuggingFace T2V", "error": str(e)}


def _video_pollinations(prompt: str, filename: str) -> dict:
    """Pollinations video (experimental, no key needed)."""
    encoded = urllib.parse.quote(prompt)
    url = f"https://video.pollinations.ai/prompt/{encoded}"
    try:
        resp = requests.get(url, timeout=120)
        if resp.status_code == 200 and len(resp.content) > 10000:
            path = _save_raw(resp.content, filename)
            return {"success": True, "path": path, "provider": "Pollinations Video (free)", "error": ""}
        return {"success": False, "path": "", "provider": "Pollinations Video", "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "Pollinations Video", "error": str(e)}


# ── Save helper ────────────────────────────────────────────────────────────────

def _save_raw(data: bytes, filename: str) -> str:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_bytes(data)
    return str(path)


# ── Tool implementations ───────────────────────────────────────────────────────

def generate_image(
    prompt: str,
    filename: str,
    width: int = 1024,
    height: int = 1024,
    quality: str = "fast",
    provider: str = "auto",
) -> dict:
    """
    Generate an image. Provider priority:
    - 'auto': tries Pollinations first (no key needed), then NVIDIA, then HuggingFace
    - 'pollinations': always use Pollinations (free, no key)
    - 'nvidia': NVIDIA NIM FLUX (requires NVIDIA_API_KEY)
    - 'huggingface': HuggingFace FLUX (requires HF_API_KEY)
    """
    providers_to_try = []
    if provider == "auto":
        providers_to_try = ["pollinations", "nvidia", "huggingface"]
    else:
        providers_to_try = [provider]

    for p in providers_to_try:
        if p == "pollinations":
            result = _img_pollinations(prompt, width, height, filename)
        elif p == "nvidia":
            result = _img_nvidia(prompt, width, height, filename, quality)
        elif p == "huggingface":
            result = _img_huggingface(prompt, width, height, filename)
        else:
            continue

        if result["success"]:
            return result
        print(f"    [{p}] failed: {result['error']}")

    return {"success": False, "path": "", "provider": "all", "error": "All image providers failed"}


def generate_video(
    prompt: str,
    filename: str,
    provider: str = "auto",
) -> dict:
    """
    Generate a short video clip from a text prompt.
    provider='auto' tries Pollinations then HuggingFace.
    Short clips (2-4 seconds), good for Reels/TikTok B-roll.
    """
    providers_to_try = []
    if provider == "auto":
        providers_to_try = ["pollinations", "huggingface"]
    else:
        providers_to_try = [provider]

    for p in providers_to_try:
        if p == "huggingface":
            result = _video_huggingface_t2v(prompt, filename)
        elif p == "pollinations":
            result = _video_pollinations(prompt, filename)
        else:
            continue

        if result["success"]:
            return result
        print(f"    [{p} video] failed: {result['error']}")

    return {
        "success": False, "path": "", "provider": "all",
        "error": "Video generation unavailable. Set HF_API_KEY (free at huggingface.co/settings/tokens) to enable.",
        "fallback_advice": "Generate a still image and use CapCut/Canva to animate it into a Reel."
    }


def write_social_copy(
    platform: str,
    visual_description: str,
    brand_voice: str,
    goal: str,
    include_hashtags: bool = True,
) -> dict:
    """
    Write platform-optimized caption, hook line, CTA, and hashtag strategy.
    Returns structured copy ready to paste into any scheduling tool.
    """
    hooks = {
        "instagram": [
            "Start with a bold statement or provocative question",
            "Use line breaks aggressively — every sentence on its own line",
            "First 125 characters must hook before the 'more' cutoff",
            "End with a single clear CTA question to drive comments",
        ],
        "tiktok": [
            "First 2 seconds = hook ('POV:', 'the day I...', 'No one talks about...')",
            "Conversational, lowercase, casual",
            "3-5 hashtags max — one niche, one broad, one trending",
        ],
        "facebook": [
            "Longer storytelling works — people read on Facebook",
            "Emotional narrative > product features",
            "End with share prompt: 'Tag someone who needs to see this'",
        ],
        "linkedin": [
            "Bold first line that stands alone as a statement",
            "Short paragraphs, lots of white space",
            "Professional but human — vulnerability + lesson",
        ],
    }

    hashtag_strategy = {
        "formula": "20% mega (1M+ posts) + 50% mid (10K-500K) + 30% niche (under 10K)",
        "why": "Niche tags get you discovered by the right audience, mega tags give reach, mid tags balance both",
        "avoid": "Do not use the same hashtag block on every post — Instagram flags it as spam",
        "count": {
            "instagram": "20-30 hashtags in first comment or caption",
            "tiktok": "3-5 hashtags max in caption",
            "facebook": "2-3 hashtags",
            "linkedin": "3-5 hashtags",
        },
    }

    return {
        "platform": platform,
        "visual_description": visual_description,
        "brand_voice": brand_voice,
        "goal": goal,
        "platform_rules": hooks.get(platform.lower(), hooks["instagram"]),
        "hashtag_strategy": hashtag_strategy,
        "instruction": (
            f"Write a complete {platform} post. Include: "
            "1) Hook (first line that stops the scroll), "
            "2) Body copy (3-5 lines, storytelling, emotional), "
            "3) CTA (one action, low friction), "
            f"4) {'20-30 relevant hashtags in 3 tiers' if include_hashtags else 'No hashtags'}. "
            "Match the brand voice exactly. Output structured JSON with keys: hook, body, cta, hashtags."
        ),
    }


def recommend_music(
    mood: str,
    platform: str,
    genre_preference: str = "any",
) -> dict:
    """
    Recommend royalty-free music tracks and audio strategy for video content.
    Returns track suggestions, where to find them, and audio psychology tips.
    """
    free_music_sources = {
        "youtube_audio_library": "studio.youtube.com/channel/music — free, no attribution required for most tracks",
        "pixabay_music":         "pixabay.com/music — free download, commercial use allowed",
        "freesound":             "freesound.org — huge library, check individual licenses",
        "bensound":              "bensound.com — free with attribution",
        "mixkit":                "mixkit.co — free, no attribution needed",
        "soundstripe_free":      "soundstripe.com — limited free tier",
        "epidemicsound_trial":   "epidemicsound.com — 30-day free trial (full library)",
        "artlist_trial":         "artlist.io — 7-day free trial",
    }

    mood_map = {
        "energetic":    {"bpm": "120-140", "genres": ["electronic", "hip-hop", "pop-punk"], "feel": "Drive, excitement, action"},
        "warm":         {"bpm": "70-90",   "genres": ["acoustic", "folk", "lo-fi"],         "feel": "Trust, comfort, home"},
        "luxury":       {"bpm": "60-80",   "genres": ["cinematic", "jazz", "neo-classical"], "feel": "Aspiration, exclusivity"},
        "playful":      {"bpm": "100-120", "genres": ["indie-pop", "ukulele", "reggae"],    "feel": "Joy, fun, lightness"},
        "trust":        {"bpm": "70-85",   "genres": ["acoustic", "strings", "ambient"],   "feel": "Reliability, authenticity"},
        "urgency":      {"bpm": "130-160", "genres": ["electronic", "trap", "drum-heavy"], "feel": "FOMO, act now, limited"},
        "nostalgic":    {"bpm": "80-100",  "genres": ["lo-fi", "vintage", "analog"],       "feel": "Memory, emotion, longing"},
    }

    tiktok_audio_tips = [
        "Use trending audio when possible — TikTok pushes content using popular sounds",
        "Original audio can become your brand signature if it goes viral",
        "First 2 seconds of audio must match the visual hook exactly",
        "Music volume should be 30-40% — voice or text is primary",
    ]

    return {
        "mood": mood,
        "platform": platform,
        "mood_profile": mood_map.get(mood.lower(), mood_map["warm"]),
        "free_sources": free_music_sources,
        "tiktok_tips": tiktok_audio_tips if platform.lower() == "tiktok" else [],
        "audio_tip": "Match BPM to editing rhythm — cut on the beat for maximum engagement",
    }


def create_posting_schedule(
    platforms: list,
    content_pieces: int,
    campaign_goal: str,
) -> dict:
    """
    Generate an optimal posting schedule based on platform algorithms and peak times.
    """
    peak_times = {
        "instagram": {
            "best_days":  ["Tuesday", "Wednesday", "Friday"],
            "best_times": ["7-9am", "11am-1pm", "6-8pm"],
            "timezone":   "Your local audience timezone",
            "frequency":  "3-5x per week for growth, 1x per day max for most brands",
            "reels_tip":  "Reels get 2x more reach — post at least 2 Reels per week",
        },
        "tiktok": {
            "best_days":  ["Tuesday", "Thursday", "Friday"],
            "best_times": ["6-10am", "7-9pm"],
            "timezone":   "Your audience's timezone (check TikTok Analytics)",
            "frequency":  "1-3x per day for algorithm growth",
            "trend_tip":  "Post within 48 hours of a trending sound for maximum boost",
        },
        "facebook": {
            "best_days":  ["Wednesday", "Thursday", "Friday"],
            "best_times": ["9-10am", "1-2pm", "4-5pm"],
            "frequency":  "1x per day max",
        },
        "linkedin": {
            "best_days":  ["Tuesday", "Wednesday", "Thursday"],
            "best_times": ["7-8am", "12pm", "5-6pm"],
            "frequency":  "3-5x per week",
        },
    }

    warmup_strategy = {
        "week_1": "Establish visual identity — 3 posts introducing brand story",
        "week_2": "Social proof — show real customers, testimonials, behind-the-scenes",
        "week_3": "Value content — tips, education, entertainment (no selling)",
        "week_4": "Conversion push — offer, CTA, urgency",
    }

    return {
        "platforms":       platforms,
        "content_pieces":  content_pieces,
        "campaign_goal":   campaign_goal,
        "peak_times":      {p: peak_times.get(p.lower(), {}) for p in platforms},
        "4_week_strategy": warmup_strategy,
        "golden_rule":     "Consistency beats perfection. Post on schedule even if content isn't perfect.",
    }


def compile_media_package(
    brand_name: str,
    campaign_name: str,
    strategy: str,
    assets: list,
    copy_pieces: list,
    schedule: dict,
    music: list,
) -> dict:
    """
    Export the complete media package as JSON + Markdown.
    assets: [{"type": "image/video", "path": str, "purpose": str, "prompt": str}]
    copy_pieces: [{"platform": str, "hook": str, "body": str, "cta": str, "hashtags": list}]
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    package = {
        "brand":     brand_name,
        "campaign":  campaign_name,
        "generated": datetime.now().isoformat(),
        "strategy":  strategy,
        "assets":    assets,
        "copy":      copy_pieces,
        "schedule":  schedule,
        "music":     music,
    }

    json_path = OUTPUT_DIR / f"package_{timestamp}.json"
    json_path.write_text(json.dumps(package, indent=2), encoding="utf-8")

    # Markdown brief
    md_lines = [
        f"# {campaign_name}",
        f"**Brand:** {brand_name}  |  **Generated:** {datetime.now().strftime('%B %d, %Y')}",
        "",
        "## Creative Strategy",
        strategy,
        "",
        "## Assets",
    ]
    for a in assets:
        md_lines.append(f"- **{a.get('type','').upper()}** — `{a.get('path','')}`")
        md_lines.append(f"  > {a.get('purpose','')}")
        if a.get("prompt"):
            md_lines.append(f"  > Prompt: *{a['prompt'][:120]}...*")
    md_lines += ["", "## Copy", ""]
    for c in copy_pieces:
        md_lines.append(f"### {c.get('platform','').title()}")
        md_lines.append(f"**Hook:** {c.get('hook','')}")
        md_lines.append(f"**Body:** {c.get('body','')}")
        md_lines.append(f"**CTA:** {c.get('cta','')}")
        if c.get("hashtags"):
            tags = c["hashtags"] if isinstance(c["hashtags"], str) else " ".join(c["hashtags"])
            md_lines.append(f"**Hashtags:** {tags}")
        md_lines.append("")
    md_lines += ["## Posting Schedule", ""]
    for platform, times in schedule.get("peak_times", {}).items():
        if times:
            md_lines.append(f"**{platform.title()}:** {', '.join(times.get('best_times', []))} on {', '.join(times.get('best_days', []))}")
    md_lines += ["", "## Music Recommendations", ""]
    for m in music:
        md_lines.append(f"- **{m.get('mood','').title()} mood** — {m.get('profile', {}).get('genres', [''])[0]} @ {m.get('profile', {}).get('bpm','?')} BPM")
    md_lines += ["", "---", "*Generated by Full Media Suite Agent — Claude Opus + NVIDIA NIM + Pollinations + HuggingFace*"]

    md_path = OUTPUT_DIR / f"brief_{timestamp}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    return {
        "json_path":     str(json_path),
        "markdown_path": str(md_path),
        "asset_count":   len(assets),
        "copy_count":    len(copy_pieces),
    }


# ── Tool schemas ───────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "generate_image",
        "description": (
            "Generate a professional image. Write a detailed photography-grade prompt. "
            "provider='auto' tries Pollinations (free/no key) → NVIDIA → HuggingFace. "
            "Use quality='high' for hero images, 'fast' for drafts or multiple assets."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt":   {"type": "string", "description": "Detailed image prompt with lighting, composition, style, mood, colors (50-200 words)"},
                "filename": {"type": "string", "description": "Output filename e.g. hero_01.jpg, carousel_slide_02.jpg"},
                "width":    {"type": "integer", "default": 1024},
                "height":   {"type": "integer", "default": 1024},
                "quality":  {"type": "string", "enum": ["fast", "high"], "default": "fast"},
                "provider": {"type": "string", "enum": ["auto", "pollinations", "nvidia", "huggingface"], "default": "auto"},
            },
            "required": ["prompt", "filename"],
        },
    },
    {
        "name": "generate_video",
        "description": (
            "Generate a short video clip (2-4 seconds) from a text prompt. "
            "Great for TikTok/Reels B-roll, product reveals, ambient loops. "
            "Requires HF_API_KEY for HuggingFace or uses Pollinations (no key). "
            "Video is short — use it as a loop or intro."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt":   {"type": "string", "description": "Video scene description — what should happen, camera motion, mood"},
                "filename": {"type": "string", "description": "Output filename e.g. reel_intro.mp4"},
                "provider": {"type": "string", "enum": ["auto", "pollinations", "huggingface"], "default": "auto"},
            },
            "required": ["prompt", "filename"],
        },
    },
    {
        "name": "write_social_copy",
        "description": (
            "Get a structured brief and platform rules for writing captions. "
            "Call this before writing copy for each platform — it gives you the formula, "
            "hashtag strategy, and hook rules. Then YOU write the actual copy and include "
            "it in the final package."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "platform":            {"type": "string", "enum": ["instagram", "tiktok", "facebook", "linkedin"]},
                "visual_description":  {"type": "string", "description": "What the image/video shows"},
                "brand_voice":         {"type": "string", "description": "Brand tone e.g. 'warm and authentic', 'bold and provocative'"},
                "goal":                {"type": "string", "description": "Post goal: awareness, trust, sales, engagement"},
                "include_hashtags":    {"type": "boolean", "default": True},
            },
            "required": ["platform", "visual_description", "brand_voice", "goal"],
        },
    },
    {
        "name": "recommend_music",
        "description": "Get royalty-free music recommendations, free sources, and audio strategy for video content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mood":              {"type": "string", "description": "e.g. warm, energetic, luxury, playful, trust, urgency, nostalgic"},
                "platform":          {"type": "string", "description": "instagram, tiktok, facebook, youtube"},
                "genre_preference":  {"type": "string", "default": "any"},
            },
            "required": ["mood", "platform"],
        },
    },
    {
        "name": "create_posting_schedule",
        "description": "Generate an optimal posting schedule with peak times, frequency, and 4-week warm-up strategy.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platforms":       {"type": "array", "items": {"type": "string"}, "description": "List of platforms e.g. ['instagram', 'tiktok']"},
                "content_pieces":  {"type": "integer", "description": "Total number of content pieces created"},
                "campaign_goal":   {"type": "string", "description": "Overall campaign goal"},
            },
            "required": ["platforms", "content_pieces", "campaign_goal"],
        },
    },
    {
        "name": "compile_media_package",
        "description": (
            "Export the complete media package to JSON and Markdown. "
            "Call this LAST after all images, videos, copy, schedule, and music are ready. "
            "Include ALL assets and ALL copy pieces."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_name":    {"type": "string"},
                "campaign_name": {"type": "string"},
                "strategy":      {"type": "string", "description": "Full creative strategy and rationale"},
                "assets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type":    {"type": "string", "enum": ["image", "video"]},
                            "path":    {"type": "string"},
                            "purpose": {"type": "string"},
                            "prompt":  {"type": "string"},
                        },
                    },
                },
                "copy_pieces": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "platform": {"type": "string"},
                            "hook":     {"type": "string"},
                            "body":     {"type": "string"},
                            "cta":      {"type": "string"},
                            "hashtags": {"type": "string"},
                        },
                    },
                },
                "schedule": {"type": "object"},
                "music":    {"type": "array", "items": {"type": "object"}},
            },
            "required": ["brand_name", "campaign_name", "strategy", "assets", "copy_pieces", "schedule", "music"],
        },
    },
]


# ── Tool dispatcher ────────────────────────────────────────────────────────────

def dispatch(name: str, inputs: dict) -> str:
    if name == "generate_image":
        print(f"\n  [IMAGE] {inputs.get('filename')} — {inputs.get('provider','auto')}...")
        result = generate_image(**inputs)
        if result["success"]:
            print(f"         Saved: {result['path']} via {result['provider']}")
        else:
            print(f"         FAILED: {result['error']}")
        return json.dumps(result)

    elif name == "generate_video":
        print(f"\n  [VIDEO] {inputs.get('filename')}...")
        result = generate_video(**inputs)
        if result["success"]:
            print(f"         Saved: {result['path']} via {result['provider']}")
        else:
            print(f"         FAILED: {result['error']}")
        return json.dumps(result)

    elif name == "write_social_copy":
        result = write_social_copy(**inputs)
        return json.dumps(result)

    elif name == "recommend_music":
        result = recommend_music(**inputs)
        return json.dumps(result)

    elif name == "create_posting_schedule":
        result = create_posting_schedule(**inputs)
        return json.dumps(result)

    elif name == "compile_media_package":
        print("\n  [PACKAGE] Compiling final media package...")
        result = compile_media_package(**inputs)
        print(f"           JSON:     {result['json_path']}")
        print(f"           Brief:    {result['markdown_path']}")
        return json.dumps(result)

    return json.dumps({"error": f"Unknown tool: {name}"})


# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM = """You are a world-class creative director, brand strategist, and social media specialist.

Your job is to deliver a COMPLETE, production-ready media package — not just images.

For every brief you receive, you MUST produce:
1. Visual assets (images and/or videos) — platform-optimized dimensions, professional prompts
2. Written copy for each platform — hook, body, CTA, hashtags
3. Music recommendation — specific mood, genre, BPM, free sources
4. Posting schedule — best times, days, frequency, 4-week strategy
5. Complete package export — everything compiled into JSON + Markdown

Creative standards:
- Image prompts must be 50-200 words. Include: subject, lighting, camera/lens, mood, color palette, composition technique, style reference (editorial/cinematic/documentary/etc)
- Captions must be platform-native — TikTok reads different from LinkedIn
- Every piece of content must serve the campaign goal
- Think in systems: each asset should work standalone AND as part of a sequence

Platform dimensions:
- Instagram square: 1080x1080 (use 1024x1024)
- Instagram portrait: 1080x1350 (use 768x1024)
- Instagram story/reel: 1080x1920 (use 576x1024)
- TikTok: 1080x1920 (use 576x1024)
- Facebook post: 1200x630 (use 1024x512)

You have access to THREE free image providers (auto mode tries them in order):
1. Pollinations.ai — no API key, works always
2. NVIDIA NIM FLUX — high quality, needs NVIDIA_API_KEY
3. HuggingFace — needs HF_API_KEY

And video generation:
1. Pollinations Video — no key needed
2. HuggingFace text-to-video — needs HF_API_KEY

Always deliver more than expected. A brief for "3 Instagram posts" should still include captions, hashtags, music, and schedule."""


# ── Agent loop ─────────────────────────────────────────────────────────────────

def run_agent(brief: str):
    if not ANTHROPIC_KEY or not ANTHROPIC_KEY.startswith("sk-ant-"):
        print("\nERROR: Set your Anthropic API key:")
        print("  export ANTHROPIC_API_KEY=sk-ant-xxxx")
        print("  Get free credits at console.anthropic.com\n")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    print(f"\n{'='*65}")
    print("  Full Media Suite Agent")
    print("  Claude Opus 4.8 + Pollinations + NVIDIA NIM + HuggingFace")
    print(f"{'='*65}")

    available = []
    available.append("Pollinations.ai (images — always available)")
    if NVIDIA_KEY:   available.append("NVIDIA NIM FLUX (images)")
    if HF_KEY:       available.append("HuggingFace (images + video)")
    print("\nActive providers:")
    for a in available:
        print(f"  ✓ {a}")
    if not HF_KEY:
        print("  ○ Video: set HF_API_KEY for video generation (free at huggingface.co)")

    print(f"\nBrief: {brief}\n")
    print("Working...\n")

    messages = [{"role": "user", "content": brief}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(textwrap.fill(block.text, width=72, subsequent_indent="  "))

        if response.stop_reason == "end_turn":
            break
        if response.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                out = dispatch(block.name, block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": out})
        messages.append({"role": "user", "content": results})

    print(f"\n{'='*65}")
    print(f"  Done! Everything saved to  media_output/")
    print(f"{'='*65}\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    brief = " ".join(sys.argv[1:])
    run_agent(brief)


if __name__ == "__main__":
    main()
