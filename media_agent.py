"""
Full Media Suite Agent v2 — Claude Opus + 8 Free Providers

The agent creates a COMPLETE social media package:
  Images  → Pollinations (free/no-key) → Together AI (free FLUX forever)
             → Google Gemini (500/day free) → Cloudflare (50/day free)
             → HuggingFace → fal.ai → NVIDIA NIM → Fireworks → DeepInfra
  Video   → Pollinations (free/no-key) → HuggingFace Wan2.2
             → Novita Kling (async, $0.50 credits) → MiniMax/Hailuo
             → fal.ai (CogVideoX, Kling, Wan)
  Animate → animate_image: bring a still image to life as a video clip
             fal.ai Kling i2v → fal.ai MiniMax i2v → Novita Kling i2v
  Copy    → Platform-native captions, hooks, CTAs
  Hashtags → 3-tier strategy (niche + mid + mega)
  Music   → Royalty-free recs with BPM + free sources
  Schedule → Peak times + 4-week campaign strategy
  Export  → Full JSON package + Markdown brief

Required:
  ANTHROPIC_API_KEY   → console.anthropic.com        (free $5 credit)

All others optional (agent auto-selects based on what's available):
  TOGETHER_API_KEY    → together.ai                   (FREE FLUX forever)
  GOOGLE_API_KEY      → aistudio.google.com           (500 images/day FREE)
  CF_API_TOKEN +
  CF_ACCOUNT_ID       → cloudflare.com                (~50 images/day FREE)
  HF_TOKEN            → huggingface.co/settings/tokens (free tier)
  FAL_KEY             → fal.ai                        ($20 signup credits)
  NVIDIA_API_KEY      → build.nvidia.com              (1,000 free credits)
  FIREWORKS_API_KEY   → fireworks.ai                  ($1 signup credits)
  DEEPINFRA_TOKEN     → deepinfra.com                 ($5 signup credits)
  NOVITA_API_KEY      → novita.ai                     ($0.50 + Kling video)
  MINIMAX_API_KEY     → minimax.io                    (MiniMax/Hailuo video)

Setup:
  pip install anthropic requests pillow together huggingface_hub

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
ANTHROPIC_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
TOGETHER_KEY   = os.environ.get("TOGETHER_API_KEY", "")
GOOGLE_KEY     = os.environ.get("GOOGLE_API_KEY", "")
CF_TOKEN       = os.environ.get("CF_API_TOKEN", "")
CF_ACCOUNT     = os.environ.get("CF_ACCOUNT_ID", "")
HF_TOKEN       = os.environ.get("HF_TOKEN", "") or os.environ.get("HF_API_KEY", "")
FAL_KEY        = os.environ.get("FAL_KEY", "")
NVIDIA_KEY     = os.environ.get("NVIDIA_API_KEY", "")
FIREWORKS_KEY  = os.environ.get("FIREWORKS_API_KEY", "")
DEEPINFRA_KEY  = os.environ.get("DEEPINFRA_TOKEN", "")
NOVITA_KEY     = os.environ.get("NOVITA_API_KEY", "")
MINIMAX_KEY    = os.environ.get("MINIMAX_API_KEY", "")

OUTPUT_DIR = Path("media_output")


# ── Save helper ────────────────────────────────────────────────────────────────

def _save(data: bytes, filename: str) -> str:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_bytes(data)
    return str(path)


# ── Image providers (in free-first order) ─────────────────────────────────────

def _img_pollinations(prompt: str, w: int, h: int, filename: str) -> dict:
    """Pollinations.ai — 100% free, no key needed."""
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width={w}&height={h}&nologo=true&model=flux"
    try:
        r = requests.get(url, timeout=90)
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            return {"success": True, "path": _save(r.content, filename), "provider": "Pollinations.ai (free/no-key)", "error": ""}
        return {"success": False, "path": "", "provider": "Pollinations", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "Pollinations", "error": str(e)}


def _img_together(prompt: str, w: int, h: int, filename: str) -> dict:
    """Together AI — permanently FREE FLUX.1-schnell-Free endpoint."""
    if not TOGETHER_KEY:
        return {"success": False, "path": "", "provider": "Together AI", "error": "TOGETHER_API_KEY not set (free at together.ai)"}
    try:
        from together import Together
        client = Together(api_key=TOGETHER_KEY)
        resp = client.images.generate(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-schnell-Free",
            width=min(w, 1440), height=min(h, 1440),
            steps=4, n=1,
        )
        item = resp.data[0]
        if hasattr(item, "b64_json") and item.b64_json:
            path = _save(base64.b64decode(item.b64_json), filename)
        elif hasattr(item, "url") and item.url:
            img_r = requests.get(item.url, timeout=60)
            path = _save(img_r.content, filename)
        else:
            return {"success": False, "path": "", "provider": "Together AI", "error": "No image data in response"}
        return {"success": True, "path": path, "provider": "Together AI FLUX (free)", "error": ""}
    except Exception as e:
        return {"success": False, "path": "", "provider": "Together AI", "error": str(e)}


def _img_google(prompt: str, filename: str) -> dict:
    """Google Gemini — 500 free images/day (free Google account key)."""
    if not GOOGLE_KEY:
        return {"success": False, "path": "", "provider": "Google Gemini", "error": "GOOGLE_API_KEY not set (free at aistudio.google.com)"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent?key={GOOGLE_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    try:
        r = requests.post(url, json=payload, timeout=60)
        if r.status_code == 200:
            parts = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
            for part in parts:
                if "inlineData" in part:
                    b64 = part["inlineData"]["data"]
                    return {"success": True, "path": _save(base64.b64decode(b64), filename), "provider": "Google Gemini (500/day free)", "error": ""}
        return {"success": False, "path": "", "provider": "Google Gemini", "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "Google Gemini", "error": str(e)}


def _img_cloudflare(prompt: str, filename: str) -> dict:
    """Cloudflare Workers AI — ~50 free images/day (10k neurons/day)."""
    if not CF_TOKEN or not CF_ACCOUNT:
        return {"success": False, "path": "", "provider": "Cloudflare", "error": "CF_API_TOKEN + CF_ACCOUNT_ID not set (free at cloudflare.com)"}
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {CF_TOKEN}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"prompt": prompt}, timeout=60)
        if r.status_code == 200:
            return {"success": True, "path": _save(r.content, filename), "provider": "Cloudflare Workers AI (free)", "error": ""}
        return {"success": False, "path": "", "provider": "Cloudflare", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "Cloudflare", "error": str(e)}


def _img_huggingface(prompt: str, w: int, h: int, filename: str) -> dict:
    """HuggingFace Inference API — free tier (rate-limited)."""
    if not HF_TOKEN:
        return {"success": False, "path": "", "provider": "HuggingFace", "error": "HF_TOKEN not set (free at huggingface.co/settings/tokens)"}
    url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt, "parameters": {"width": min(w, 1024), "height": min(h, 1024)}}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            return {"success": True, "path": _save(r.content, filename), "provider": "HuggingFace FLUX (free tier)", "error": ""}
        if r.status_code == 503:
            return {"success": False, "path": "", "provider": "HuggingFace", "error": "Model loading (cold start) — retry in 20s"}
        return {"success": False, "path": "", "provider": "HuggingFace", "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "HuggingFace", "error": str(e)}


def _img_fal(prompt: str, w: int, h: int, filename: str, quality: str) -> dict:
    """fal.ai — $20 signup credits, 1000+ models."""
    if not FAL_KEY:
        return {"success": False, "path": "", "provider": "fal.ai", "error": "FAL_KEY not set (free $20 at fal.ai)"}
    model = "fal-ai/flux/dev" if quality == "high" else "fal-ai/flux/schnell"
    url = f"https://fal.run/{model}"
    headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
    payload = {"prompt": prompt, "image_size": "square_hd" if w == h else "portrait_4_3", "num_inference_steps": 28 if quality == "high" else 4}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code == 200:
            images = r.json().get("images", [])
            if images:
                img_url = images[0].get("url", "")
                if img_url:
                    img_r = requests.get(img_url, timeout=60)
                    return {"success": True, "path": _save(img_r.content, filename), "provider": "fal.ai FLUX", "error": ""}
        return {"success": False, "path": "", "provider": "fal.ai", "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "fal.ai", "error": str(e)}


def _img_nvidia(prompt: str, w: int, h: int, filename: str, quality: str) -> dict:
    """NVIDIA NIM — 1,000 free credits from build.nvidia.com."""
    if not NVIDIA_KEY:
        return {"success": False, "path": "", "provider": "NVIDIA NIM", "error": "NVIDIA_API_KEY not set (free 1000 credits at build.nvidia.com)"}
    model = "flux.1-dev" if quality == "high" else "flux.1-schnell"
    url = f"https://ai.api.nvidia.com/v1/genai/black-forest-labs/{model}"
    headers = {"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json", "Accept": "application/json"}
    payload = {"prompt": prompt, "width": min(w, 1024), "height": min(h, 1024), "seed": 42}
    if quality == "high":
        payload.update({"num_inference_steps": 28, "guidance": 3.5})
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code == 200:
            b64 = r.json().get("artifacts", [{}])[0].get("base64", "")
            if b64:
                return {"success": True, "path": _save(base64.b64decode(b64), filename), "provider": "NVIDIA NIM FLUX", "error": ""}
        return {"success": False, "path": "", "provider": "NVIDIA NIM", "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "NVIDIA NIM", "error": str(e)}


def _img_fireworks(prompt: str, filename: str) -> dict:
    """Fireworks AI — $1 signup credits, FLUX schnell FP8."""
    if not FIREWORKS_KEY:
        return {"success": False, "path": "", "provider": "Fireworks AI", "error": "FIREWORKS_API_KEY not set ($1 free at fireworks.ai)"}
    url = "https://api.fireworks.ai/inference/v1/workflows/accounts/fireworks/models/flux-1-schnell-fp8/text_to_image"
    headers = {"Authorization": f"Bearer {FIREWORKS_KEY}", "Content-Type": "application/json", "Accept": "image/jpeg"}
    try:
        r = requests.post(url, headers=headers, json={"prompt": prompt}, timeout=60)
        if r.status_code == 200:
            return {"success": True, "path": _save(r.content, filename), "provider": "Fireworks AI FLUX (FP8)", "error": ""}
        return {"success": False, "path": "", "provider": "Fireworks AI", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "Fireworks AI", "error": str(e)}


def _img_deepinfra(prompt: str, filename: str) -> dict:
    """DeepInfra — $5 signup credits, FLUX family."""
    if not DEEPINFRA_KEY:
        return {"success": False, "path": "", "provider": "DeepInfra", "error": "DEEPINFRA_TOKEN not set ($5 free at deepinfra.com)"}
    try:
        from openai import OpenAI
        client = OpenAI(api_key=DEEPINFRA_KEY, base_url="https://api.deepinfra.com/v1/openai")
        resp = client.images.generate(model="black-forest-labs/FLUX-1-schnell", prompt=prompt, size="1024x1024", n=1)
        img_url = resp.data[0].url
        r = requests.get(img_url, timeout=60)
        return {"success": True, "path": _save(r.content, filename), "provider": "DeepInfra FLUX", "error": ""}
    except Exception as e:
        return {"success": False, "path": "", "provider": "DeepInfra", "error": str(e)}


# ── Video providers ────────────────────────────────────────────────────────────

def _video_pollinations(prompt: str, filename: str) -> dict:
    """Pollinations video — free, no key (Veo, Seedance, Wan models)."""
    url = f"https://video.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
    try:
        r = requests.get(url, timeout=180)
        if r.status_code == 200 and len(r.content) > 10000:
            return {"success": True, "path": _save(r.content, filename), "provider": "Pollinations Video (free/no-key)", "error": ""}
        return {"success": False, "path": "", "provider": "Pollinations Video", "error": f"HTTP {r.status_code} size={len(r.content)}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "Pollinations Video", "error": str(e)}


def _video_huggingface(prompt: str, filename: str) -> dict:
    """HuggingFace Wan2.2 text-to-video — free tier."""
    if not HF_TOKEN:
        return {"success": False, "path": "", "provider": "HuggingFace T2V", "error": "HF_TOKEN not set (free at huggingface.co/settings/tokens)"}
    url = "https://api-inference.huggingface.co/models/Wan-AI/Wan2.2-TI2V-5B"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        r = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=300)
        if r.status_code == 200 and len(r.content) > 50000:
            return {"success": True, "path": _save(r.content, filename), "provider": "HuggingFace Wan2.2 (free)", "error": ""}
        if r.status_code == 503:
            return {"success": False, "path": "", "provider": "HuggingFace T2V", "error": "Model loading — retry in 30s"}
        return {"success": False, "path": "", "provider": "HuggingFace T2V", "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "HuggingFace T2V", "error": str(e)}


def _video_fal(prompt: str, filename: str) -> dict:
    """fal.ai CogVideoX — $20 signup credits, 720p 6-second clips."""
    if not FAL_KEY:
        return {"success": False, "path": "", "provider": "fal.ai Video", "error": "FAL_KEY not set (free $20 at fal.ai)"}
    url = "https://fal.run/fal-ai/cogvideox-5b"
    headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
    payload = {"prompt": prompt, "num_inference_steps": 50}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=300)
        if r.status_code == 200:
            video_url = r.json().get("video", {}).get("url", "")
            if video_url:
                vr = requests.get(video_url, timeout=120)
                return {"success": True, "path": _save(vr.content, filename), "provider": "fal.ai CogVideoX", "error": ""}
        return {"success": False, "path": "", "provider": "fal.ai Video", "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "fal.ai Video", "error": str(e)}


def _video_novita(prompt: str, filename: str) -> dict:
    """Novita Kling text-to-video — async polling, $0.50 credits at novita.ai."""
    if not NOVITA_KEY:
        return {"success": False, "path": "", "provider": "Novita T2V", "error": "NOVITA_API_KEY not set (credits at novita.ai)"}
    headers = {"Authorization": f"Bearer {NOVITA_KEY}", "Content-Type": "application/json"}
    payload = {"model_name": "kling-v1-5", "prompt": prompt, "width": 768, "height": 1024, "duration": 5}
    try:
        r = requests.post(
            "https://api.novita.ai/v3/async/txt2video-kling-v3.0-std",
            headers=headers, json=payload, timeout=60,
        )
        if r.status_code != 200:
            return {"success": False, "path": "", "provider": "Novita T2V", "error": f"HTTP {r.status_code}: {r.text[:200]}"}
        task_id = r.json().get("task_id", "")
        if not task_id:
            return {"success": False, "path": "", "provider": "Novita T2V", "error": "No task_id returned"}
        # Poll up to 300s
        deadline = time.time() + 300
        while time.time() < deadline:
            time.sleep(10)
            pr = requests.get(
                f"https://api.novita.ai/v3/async/task-result?task_id={task_id}",
                headers=headers, timeout=30,
            )
            if pr.status_code != 200:
                continue
            data = pr.json()
            status = data.get("task", {}).get("status", "")
            if status == "TASK_STATUS_SUCCEED":
                video_url = data.get("task", {}).get("output", {}).get("video_url", "")
                if not video_url:
                    # Try alternate path
                    videos = data.get("videos", [])
                    video_url = videos[0].get("video_url", "") if videos else ""
                if video_url:
                    vr = requests.get(video_url, timeout=120)
                    return {"success": True, "path": _save(vr.content, filename), "provider": "Novita Kling T2V", "error": ""}
                return {"success": False, "path": "", "provider": "Novita T2V", "error": "Succeeded but no video_url in response"}
            if status in ("TASK_STATUS_FAILED", "TASK_STATUS_CANCELED"):
                return {"success": False, "path": "", "provider": "Novita T2V", "error": f"Task {status}"}
        return {"success": False, "path": "", "provider": "Novita T2V", "error": "Timed out after 300s"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "Novita T2V", "error": str(e)}


def _video_minimax(prompt: str, filename: str) -> dict:
    """MiniMax/Hailuo video-01 — poll until Success, then retrieve download URL."""
    if not MINIMAX_KEY:
        return {"success": False, "path": "", "provider": "MiniMax Video", "error": "MINIMAX_API_KEY not set (minimax.io)"}
    headers = {"Authorization": f"Bearer {MINIMAX_KEY}", "Content-Type": "application/json"}
    try:
        r = requests.post(
            "https://api.minimax.io/v1/video_generation",
            headers=headers, json={"model": "video-01", "prompt": prompt}, timeout=60,
        )
        if r.status_code != 200:
            return {"success": False, "path": "", "provider": "MiniMax Video", "error": f"HTTP {r.status_code}: {r.text[:200]}"}
        task_id = r.json().get("task_id", "")
        if not task_id:
            return {"success": False, "path": "", "provider": "MiniMax Video", "error": "No task_id returned"}
        # Poll up to 300s
        deadline = time.time() + 300
        while time.time() < deadline:
            time.sleep(10)
            pr = requests.get(
                f"https://api.minimax.io/v1/query/video_generation?task_id={task_id}",
                headers=headers, timeout=30,
            )
            if pr.status_code != 200:
                continue
            data = pr.json()
            status = data.get("status", "")
            if status == "Success":
                file_id = data.get("file_id", "")
                if not file_id:
                    return {"success": False, "path": "", "provider": "MiniMax Video", "error": "No file_id in success response"}
                fr = requests.get(
                    f"https://api.minimax.io/v1/files/retrieve?file_id={file_id}",
                    headers=headers, timeout=30,
                )
                if fr.status_code != 200:
                    return {"success": False, "path": "", "provider": "MiniMax Video", "error": f"File retrieve HTTP {fr.status_code}"}
                download_url = fr.json().get("file", {}).get("download_url", "")
                if download_url:
                    vr = requests.get(download_url, timeout=120)
                    return {"success": True, "path": _save(vr.content, filename), "provider": "MiniMax Hailuo Video", "error": ""}
                return {"success": False, "path": "", "provider": "MiniMax Video", "error": "No download_url in file response"}
            if status in ("Fail", "Failed"):
                return {"success": False, "path": "", "provider": "MiniMax Video", "error": f"Task failed: {data}"}
        return {"success": False, "path": "", "provider": "MiniMax Video", "error": "Timed out after 300s"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "MiniMax Video", "error": str(e)}


# ── Image-to-video helpers ─────────────────────────────────────────────────────

def _upload_to_fal(image_path: str) -> str:
    """Upload a local image to fal.ai CDN and return public URL."""
    with open(image_path, "rb") as f:
        data = f.read()
    ext = Path(image_path).suffix.lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": mime}
    r = requests.post("https://fal.run/files/upload", headers=headers, data=data, timeout=60)
    if r.status_code == 200:
        return r.json().get("url", "")
    return ""


def _i2v_fal_kling(img_url: str, motion_prompt: str, filename: str) -> dict:
    """fal.ai Kling v2.1 image-to-video."""
    if not FAL_KEY:
        return {"success": False, "path": "", "provider": "fal.ai Kling i2v", "error": "FAL_KEY not set"}
    headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
    payload = {"image_url": img_url, "prompt": motion_prompt}
    try:
        r = requests.post(
            "https://fal.run/fal-ai/kling-video/v2.1/master/image-to-video",
            headers=headers, json=payload, timeout=300,
        )
        if r.status_code == 200:
            video_url = r.json().get("video", {}).get("url", "")
            if video_url:
                vr = requests.get(video_url, timeout=120)
                return {"success": True, "path": _save(vr.content, filename), "provider": "fal.ai Kling i2v", "error": ""}
        return {"success": False, "path": "", "provider": "fal.ai Kling i2v", "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "fal.ai Kling i2v", "error": str(e)}


def _i2v_fal_minimax(img_url: str, motion_prompt: str, filename: str) -> dict:
    """fal.ai MiniMax Hailuo-02 image-to-video."""
    if not FAL_KEY:
        return {"success": False, "path": "", "provider": "fal.ai MiniMax i2v", "error": "FAL_KEY not set"}
    headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
    payload = {"image_url": img_url, "prompt": motion_prompt}
    try:
        r = requests.post(
            "https://fal.run/fal-ai/minimax/hailuo-02/standard/image-to-video",
            headers=headers, json=payload, timeout=300,
        )
        if r.status_code == 200:
            video_url = r.json().get("video", {}).get("url", "")
            if video_url:
                vr = requests.get(video_url, timeout=120)
                return {"success": True, "path": _save(vr.content, filename), "provider": "fal.ai MiniMax i2v", "error": ""}
        return {"success": False, "path": "", "provider": "fal.ai MiniMax i2v", "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "fal.ai MiniMax i2v", "error": str(e)}


def _i2v_novita_kling(img_url: str, motion_prompt: str, filename: str) -> dict:
    """Novita Kling image-to-video — async polling."""
    if not NOVITA_KEY:
        return {"success": False, "path": "", "provider": "Novita Kling i2v", "error": "NOVITA_API_KEY not set"}
    headers = {"Authorization": f"Bearer {NOVITA_KEY}", "Content-Type": "application/json"}
    payload = {"model_name": "kling-v1-5", "image_url": img_url, "prompt": motion_prompt, "duration": 5}
    try:
        r = requests.post(
            "https://api.novita.ai/v3/async/img2video-kling-v3.0-std",
            headers=headers, json=payload, timeout=60,
        )
        if r.status_code != 200:
            return {"success": False, "path": "", "provider": "Novita Kling i2v", "error": f"HTTP {r.status_code}: {r.text[:200]}"}
        task_id = r.json().get("task_id", "")
        if not task_id:
            return {"success": False, "path": "", "provider": "Novita Kling i2v", "error": "No task_id returned"}
        deadline = time.time() + 300
        delay = 10
        while time.time() < deadline:
            time.sleep(delay)
            pr = requests.get(
                f"https://api.novita.ai/v3/async/task-result?task_id={task_id}",
                headers=headers, timeout=30,
            )
            if pr.status_code != 200:
                delay = min(delay * 2, 30)
                continue
            data = pr.json()
            status = data.get("task", {}).get("status", "")
            if status == "TASK_STATUS_SUCCEED":
                videos = data.get("videos", [])
                video_url = videos[0].get("video_url", "") if videos else ""
                if not video_url:
                    video_url = data.get("task", {}).get("output", {}).get("video_url", "")
                if video_url:
                    vr = requests.get(video_url, timeout=120)
                    return {"success": True, "path": _save(vr.content, filename), "provider": "Novita Kling i2v", "error": ""}
                return {"success": False, "path": "", "provider": "Novita Kling i2v", "error": "Succeeded but no video_url"}
            if status in ("TASK_STATUS_FAILED", "TASK_STATUS_CANCELED"):
                return {"success": False, "path": "", "provider": "Novita Kling i2v", "error": f"Task {status}"}
            delay = min(delay * 1.5, 30)
        return {"success": False, "path": "", "provider": "Novita Kling i2v", "error": "Timed out after 300s"}
    except Exception as e:
        return {"success": False, "path": "", "provider": "Novita Kling i2v", "error": str(e)}


# ── Public tool functions ──────────────────────────────────────────────────────

def generate_image(
    prompt: str,
    filename: str,
    width: int = 1024,
    height: int = 1024,
    quality: str = "fast",
    provider: str = "auto",
) -> dict:
    """
    Generate an image using the best available free provider.

    provider='auto' tries in order:
      1. Pollinations.ai  (no key, always works)
      2. Together AI      (free FLUX forever — just needs free account key)
      3. Google Gemini    (500 free/day — needs free Google AI key)
      4. Cloudflare       (50 free/day — needs free Cloudflare key)
      5. HuggingFace      (free tier — needs free HF token)
      6. fal.ai           ($20 signup credits)
      7. NVIDIA NIM       (1,000 free credits)
      8. Fireworks AI     ($1 signup)
      9. DeepInfra        ($5 signup)

    provider can also be: 'pollinations', 'together', 'google', 'cloudflare',
                          'huggingface', 'fal', 'nvidia', 'fireworks', 'deepinfra'
    """
    order = ["pollinations", "together", "google", "cloudflare",
             "huggingface", "fal", "nvidia", "fireworks", "deepinfra"] if provider == "auto" else [provider]

    for p in order:
        if p == "pollinations":   result = _img_pollinations(prompt, width, height, filename)
        elif p == "together":     result = _img_together(prompt, width, height, filename)
        elif p == "google":       result = _img_google(prompt, filename)
        elif p == "cloudflare":   result = _img_cloudflare(prompt, filename)
        elif p == "huggingface":  result = _img_huggingface(prompt, width, height, filename)
        elif p == "fal":          result = _img_fal(prompt, width, height, filename, quality)
        elif p == "nvidia":       result = _img_nvidia(prompt, width, height, filename, quality)
        elif p == "fireworks":    result = _img_fireworks(prompt, filename)
        elif p == "deepinfra":    result = _img_deepinfra(prompt, filename)
        else: continue

        if result["success"]:
            return result
        print(f"    [{p}] failed: {result['error']}")

    return {"success": False, "path": "", "provider": "all", "error": "All image providers failed — check PROVIDERS.md for setup"}


def generate_video(
    prompt: str,
    filename: str,
    provider: str = "auto",
) -> dict:
    """
    Generate a short video clip from a text prompt.

    provider='auto' tries:
      1. Pollinations Video  (no key, free — Veo/Seedance/Wan)
      2. HuggingFace         (Wan2.2, free tier)
      3. Novita Kling        (async, $0.50 credits — novita.ai)
      4. MiniMax/Hailuo      (async, minimax.io)
      5. fal.ai              (CogVideoX, $20 signup credits)

    Tips for good video prompts:
    - Be specific about motion: "slow pan left", "zoom in", "flowing", "rippling"
    - Include camera direction: "drone shot descending", "handheld close-up"
    - Keep it 1-2 sentences focused on the visual action
    """
    order = ["pollinations", "huggingface", "novita", "minimax", "fal"] if provider == "auto" else [provider]

    for p in order:
        if p == "pollinations":   result = _video_pollinations(prompt, filename)
        elif p == "huggingface":  result = _video_huggingface(prompt, filename)
        elif p == "novita":       result = _video_novita(prompt, filename)
        elif p == "minimax":      result = _video_minimax(prompt, filename)
        elif p == "fal":          result = _video_fal(prompt, filename)
        else: continue

        if result["success"]:
            return result
        print(f"    [{p} video] failed: {result['error']}")

    return {
        "success": False, "path": "", "provider": "all",
        "error": "Video generation failed. For best results set HF_TOKEN (free) or FAL_KEY ($20 free credits).",
        "manual_option": "Visit arena.ai/video for 3 free generations/day using Veo 3, Sora 2, Kling.",
        "self_host": "Run Wan2.1 locally (Apache 2.0, free forever) — needs 24GB VRAM GPU."
    }


def animate_image(
    image_path: str,
    motion_prompt: str,
    filename: str,
    provider: str = "auto",
) -> dict:
    """
    Animate a still image into a short video clip.

    provider='auto' tries in order:
      1. fal.ai Kling i2v   (FAL_KEY, $20 signup credits)
      2. fal.ai MiniMax i2v (FAL_KEY, same credits)
      3. Novita Kling i2v   (NOVITA_API_KEY, $0.50 credits — async)

    image_path can be a local file path or a public URL.
    If local, the image is uploaded to fal.ai CDN automatically.
    """
    # Resolve image URL — upload local files to fal CDN first
    def _resolve_url(path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if FAL_KEY:
            uploaded = _upload_to_fal(path)
            if uploaded:
                return uploaded
        # Fallback: can't upload without FAL_KEY, return as-is and let provider fail gracefully
        return path

    order = ["fal_kling", "fal_minimax", "novita"] if provider == "auto" else [provider]

    for p in order:
        img_url = _resolve_url(image_path)
        if p == "fal_kling":
            result = _i2v_fal_kling(img_url, motion_prompt, filename)
        elif p == "fal_minimax":
            result = _i2v_fal_minimax(img_url, motion_prompt, filename)
        elif p == "novita":
            result = _i2v_novita_kling(img_url, motion_prompt, filename)
        else:
            continue

        if result["success"]:
            return result
        print(f"    [{p} i2v] failed: {result['error']}")

    return {
        "success": False, "path": "", "provider": "all",
        "error": "All image-to-video providers failed. Set FAL_KEY ($20 free) or NOVITA_API_KEY ($0.50 credits).",
    }


def write_social_copy(
    platform: str,
    visual_description: str,
    brand_voice: str,
    goal: str,
    include_hashtags: bool = True,
) -> dict:
    """Get platform rules + hashtag strategy for writing captions."""
    rules = {
        "instagram": [
            "First 125 chars must hook before 'more' cutoff — make every word count",
            "One sentence per line — line breaks are your best formatting tool",
            "End with a single CTA question to drive comments (comments = reach)",
            "Hashtags: 20-30 in 3 tiers — 30% niche (<10K), 50% mid (10K-500K), 20% mega (1M+)",
        ],
        "tiktok": [
            "First 2 seconds = hook: 'POV:', 'The day I...', 'No one talks about...'",
            "Lowercase, casual, conversational — sounds like a friend",
            "3-5 hashtags max — one niche, one broad, one trending sound",
            "Hook must match the first visual frame exactly",
        ],
        "facebook": [
            "Storytelling works — people read long form on Facebook",
            "Emotional narrative beats product features every time",
            "End with: 'Tag someone who needs to see this' for organic reach",
        ],
        "linkedin": [
            "Bold standalone first line as a hook statement",
            "Short paragraphs, white space — make it scannable",
            "Vulnerability + lesson = highest engagement",
            "3-5 hashtags, professional but human tone",
        ],
    }
    hashtag_strategy = {
        "formula": "30% niche (<10K posts) + 50% mid (10K-500K) + 20% mega (1M+)",
        "why": "Niche tags get discovered by right audience; mega tags give reach; mid balance both",
        "warning": "Never use same hashtag block on every post — platform flags as spam",
    }
    return {
        "platform": platform, "brand_voice": brand_voice, "goal": goal,
        "visual_described": visual_description,
        "platform_rules": rules.get(platform.lower(), rules["instagram"]),
        "hashtag_strategy": hashtag_strategy,
        "instruction": (
            f"Using the rules and brand voice above, write the ACTUAL {platform} post copy. "
            "Return a JSON object with keys: hook (first line, scroll-stopping), "
            "body (2-5 lines, storytelling, emotional), cta (one action, low friction), "
            f"hashtags (string, {'20-30 hashtags in 3 tiers' if include_hashtags else 'none'})."
        ),
    }


def recommend_music(mood: str, platform: str, genre_preference: str = "any") -> dict:
    """Get royalty-free music recs, BPM, and free sources for video content."""
    moods = {
        "energetic": {"bpm": "120-140", "genres": ["electronic", "hip-hop", "pop-punk"]},
        "warm":      {"bpm": "70-90",   "genres": ["acoustic", "folk", "lo-fi"]},
        "luxury":    {"bpm": "60-80",   "genres": ["cinematic", "jazz", "neo-classical"]},
        "playful":   {"bpm": "100-120", "genres": ["indie-pop", "ukulele", "reggae"]},
        "trust":     {"bpm": "70-85",   "genres": ["acoustic", "strings", "ambient"]},
        "urgency":   {"bpm": "130-160", "genres": ["electronic", "trap", "drum-heavy"]},
        "nostalgic": {"bpm": "80-100",  "genres": ["lo-fi", "vintage", "analog"]},
    }
    sources = {
        "Pixabay Music":          "pixabay.com/music — free, commercial use OK, no attribution",
        "YouTube Audio Library":  "studio.youtube.com/channel/music — free, most tracks no attribution",
        "Mixkit":                 "mixkit.co — free, no attribution needed",
        "Freesound":              "freesound.org — huge library, check individual CC licenses",
        "Bensound":               "bensound.com — free with attribution OR paid without",
        "Epidemic Sound trial":   "epidemicsound.com — 30-day free trial, full library",
    }
    return {
        "mood": mood, "platform": platform,
        "mood_profile": moods.get(mood.lower(), moods["warm"]),
        "free_sources": sources,
        "audio_tip": "Match edit cuts to BPM. On TikTok, use trending audio when possible — algorithm boosts it.",
        "volume_tip": "Music at 30-40% volume — voice/text is primary. Swell on transitions.",
    }


def create_posting_schedule(platforms: list, content_pieces: int, campaign_goal: str) -> dict:
    """Generate optimal posting schedule with peak times and 4-week strategy."""
    peak_times = {
        "instagram": {"best_days": ["Tue", "Wed", "Fri"], "best_times": ["7-9am", "11am-1pm", "6-8pm"], "frequency": "3-5x/week", "tip": "Reels get 2x reach — post ≥2 Reels/week"},
        "tiktok":    {"best_days": ["Tue", "Thu", "Fri"], "best_times": ["6-10am", "7-9pm"], "frequency": "1-3x/day for growth", "tip": "Post within 48hrs of a trending sound"},
        "facebook":  {"best_days": ["Wed", "Thu", "Fri"], "best_times": ["9-10am", "1-2pm", "4-5pm"], "frequency": "1x/day max"},
        "linkedin":  {"best_days": ["Tue", "Wed", "Thu"], "best_times": ["7-8am", "12pm", "5-6pm"], "frequency": "3-5x/week"},
    }
    return {
        "platforms": platforms, "content_pieces": content_pieces, "campaign_goal": campaign_goal,
        "peak_times": {p: peak_times.get(p.lower(), {}) for p in platforms},
        "4_week_strategy": {
            "week_1": "Brand story — 3 posts introducing who you are and why you exist",
            "week_2": "Social proof — real customers, testimonials, behind-the-scenes",
            "week_3": "Value content — tips, education, entertainment (zero selling)",
            "week_4": "Conversion push — offer, clear CTA, urgency or scarcity",
        },
        "golden_rule": "Consistency beats perfection. Post on schedule even if content isn't perfect.",
    }


def compile_media_package(
    brand_name: str, campaign_name: str, strategy: str,
    assets: list, copy_pieces: list, schedule: dict, music: list,
) -> dict:
    """Export complete package as JSON + Markdown brief."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    package = {
        "brand": brand_name, "campaign": campaign_name,
        "generated": datetime.now().isoformat(),
        "strategy": strategy, "assets": assets,
        "copy": copy_pieces, "schedule": schedule, "music": music,
    }
    json_path = OUTPUT_DIR / f"package_{ts}.json"
    json_path.write_text(json.dumps(package, indent=2), encoding="utf-8")

    md = [
        f"# {campaign_name}", f"**Brand:** {brand_name}  |  **Generated:** {datetime.now().strftime('%B %d, %Y')}",
        "", "## Strategy", strategy, "", "## Assets", "",
    ]
    for a in assets:
        md.append(f"- **{a.get('type','').upper()}** `{a.get('path','')}` — {a.get('purpose','')}")
        if a.get("prompt"):
            md.append(f"  > *{a['prompt'][:120]}...*")
    md += ["", "## Copy", ""]
    for c in copy_pieces:
        md += [f"### {c.get('platform','').title()}", f"**Hook:** {c.get('hook','')}",
               f"**Body:** {c.get('body','')}", f"**CTA:** {c.get('cta','')}", ""]
        if c.get("hashtags"):
            md.append(f"**Tags:** {c['hashtags']}\n")
    md += ["## Schedule", ""]
    for plat, times in schedule.get("peak_times", {}).items():
        if times:
            md.append(f"**{plat.title()}:** {', '.join(times.get('best_times',[]))} on {', '.join(times.get('best_days',[]))}")
    md += ["", "---", "*Generated by Full Media Suite Agent v2 — Claude Opus + 8 Free Providers*"]

    md_path = OUTPUT_DIR / f"brief_{ts}.md"
    md_path.write_text("\n".join(md), encoding="utf-8")

    return {"json_path": str(json_path), "markdown_path": str(md_path), "asset_count": len(assets), "copy_count": len(copy_pieces)}


# ── Tool schemas ───────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "generate_image",
        "description": (
            "Generate a professional image. Auto mode tries 9 providers in free-first order: "
            "Pollinations (no key) → Together AI (free FLUX forever) → Google Gemini (500/day free) "
            "→ Cloudflare (50/day free) → HuggingFace → fal.ai → NVIDIA → Fireworks → DeepInfra. "
            "Write detailed photography-grade prompts (50-200 words) for best results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt":   {"type": "string", "description": "Detailed image prompt: subject, lighting, camera/lens, mood, color palette, composition, style reference"},
                "filename": {"type": "string", "description": "Output filename e.g. hero_01.jpg, slide_02_contrast.jpg"},
                "width":    {"type": "integer", "default": 1024, "description": "Width in pixels (256-1440). Instagram square=1024, portrait=768, story=576"},
                "height":   {"type": "integer", "default": 1024, "description": "Height in pixels. Story/Reel/TikTok use 1024, square use 1024x1024"},
                "quality":  {"type": "string", "enum": ["fast", "high"], "default": "fast", "description": "fast=schnell (4 steps), high=dev model (28 steps, more photorealistic)"},
                "provider": {"type": "string", "enum": ["auto", "pollinations", "together", "google", "cloudflare", "huggingface", "fal", "nvidia", "fireworks", "deepinfra"], "default": "auto"},
            },
            "required": ["prompt", "filename"],
        },
    },
    {
        "name": "generate_video",
        "description": (
            "Generate a short video clip (2-6 seconds). Free options: "
            "Pollinations (no key, Veo/Seedance/Wan models) and HuggingFace (Wan2.2, free tier). "
            "fal.ai option uses $20 signup credits for CogVideoX (720p, 6 seconds). "
            "Write motion-focused prompts: describe what moves, camera direction, speed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt":   {"type": "string", "description": "Motion-focused video prompt. Include: what moves, camera direction, speed, mood. E.g. 'slow cinematic pan across a farmers market at golden hour, warm bokeh, shallow depth of field'"},
                "filename": {"type": "string", "description": "Output filename e.g. reel_intro.mp4"},
                "provider": {"type": "string", "enum": ["auto", "pollinations", "huggingface", "novita", "minimax", "fal"], "default": "auto"},
            },
            "required": ["prompt", "filename"],
        },
    },
    {
        "name": "animate_image",
        "description": (
            "Animate a still image into a short video clip. Takes a generated image and brings it to life "
            "with motion. Use this after generating a hero image to create a Reel/TikTok version. "
            "Provider auto order: fal.ai Kling → fal.ai MiniMax → Novita Kling."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path":    {"type": "string", "description": "Local path to the image file (e.g. media_output/hero_01.jpg) or a public URL"},
                "motion_prompt": {"type": "string", "description": "Describe the motion: what moves, how, camera direction. E.g. 'gentle breeze moves through the market stalls, slow pan left, warm golden light'"},
                "filename":      {"type": "string", "description": "Output video filename e.g. hero_animated.mp4"},
                "provider":      {"type": "string", "enum": ["auto", "fal_kling", "fal_minimax", "novita"], "default": "auto"},
            },
            "required": ["image_path", "motion_prompt", "filename"],
        },
    },
    {
        "name": "write_social_copy",
        "description": "Get platform rules + hashtag strategy, then write the actual post copy. Call once per platform.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform":           {"type": "string", "enum": ["instagram", "tiktok", "facebook", "linkedin"]},
                "visual_description": {"type": "string"},
                "brand_voice":        {"type": "string", "description": "e.g. 'warm and authentic', 'bold and provocative', 'educational but playful'"},
                "goal":               {"type": "string", "description": "awareness | trust | sales | engagement"},
                "include_hashtags":   {"type": "boolean", "default": True},
            },
            "required": ["platform", "visual_description", "brand_voice", "goal"],
        },
    },
    {
        "name": "recommend_music",
        "description": "Get royalty-free music recs with BPM, genre, and free download sources for video content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mood":     {"type": "string", "description": "warm | energetic | luxury | playful | trust | urgency | nostalgic"},
                "platform": {"type": "string"},
            },
            "required": ["mood", "platform"],
        },
    },
    {
        "name": "create_posting_schedule",
        "description": "Generate optimal posting schedule: peak times per platform + 4-week warm-up campaign strategy.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platforms":      {"type": "array", "items": {"type": "string"}},
                "content_pieces": {"type": "integer"},
                "campaign_goal":  {"type": "string"},
            },
            "required": ["platforms", "content_pieces", "campaign_goal"],
        },
    },
    {
        "name": "compile_media_package",
        "description": "Export complete media package (JSON + Markdown brief). Call LAST after everything is generated.",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_name":    {"type": "string"},
                "campaign_name": {"type": "string"},
                "strategy":      {"type": "string"},
                "assets": {
                    "type": "array",
                    "items": {"type": "object", "properties": {
                        "type": {"type": "string"}, "path": {"type": "string"},
                        "purpose": {"type": "string"}, "prompt": {"type": "string"},
                    }},
                },
                "copy_pieces": {
                    "type": "array",
                    "items": {"type": "object", "properties": {
                        "platform": {"type": "string"}, "hook": {"type": "string"},
                        "body": {"type": "string"}, "cta": {"type": "string"},
                        "hashtags": {"type": "string"},
                    }},
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
        print(f"\n  [IMAGE] {inputs.get('filename')} — trying providers in free-first order...")
        result = generate_image(**inputs)
        if result["success"]:
            print(f"         ✓ Saved: {result['path']}  [{result['provider']}]")
        else:
            print(f"         ✗ All providers failed: {result['error']}")
        return json.dumps(result)
    elif name == "generate_video":
        print(f"\n  [VIDEO] {inputs.get('filename')}...")
        result = generate_video(**inputs)
        if result["success"]:
            print(f"         ✓ Saved: {result['path']}  [{result['provider']}]")
        else:
            print(f"         ✗ Video failed: {result.get('manual_option','')}")
        return json.dumps(result)
    elif name == "animate_image":
        print(f"\n  [ANIMATE] {inputs.get('image_path')} → {inputs.get('filename')}...")
        result = animate_image(**inputs)
        if result["success"]:
            print(f"            ✓ Saved: {result['path']}  [{result['provider']}]")
        else:
            print(f"            ✗ Animation failed: {result['error']}")
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
        print(f"           JSON:  {result['json_path']}")
        print(f"           Brief: {result['markdown_path']}")
        return json.dumps(result)
    return json.dumps({"error": f"Unknown tool: {name}"})


# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM = """You are a world-class creative director, brand strategist, and social media specialist.

Your job: deliver a COMPLETE, production-ready media package every single time.

For every brief you MUST produce all of the following:
1. Images — platform-optimized, professional prompts, use generate_image
2. At least one video — use generate_video (try even if uncertain, Pollinations is free)
3. Animate hero image — ALWAYS call animate_image on the hero/main image after generating it.
   A still image + its animated version = double the content from one prompt (still for feed, video for Reels/TikTok).
4. Written copy — platform-native for each requested platform, use write_social_copy
5. Music recommendation — mood + BPM + free sources, use recommend_music
6. Posting schedule — best times per platform + 4-week strategy, use create_posting_schedule
7. Package export — everything compiled, use compile_media_package LAST

Image prompt standards (non-negotiable):
- 50-200 words per prompt
- Always include: subject, lighting (golden hour / softbox / rim light etc), camera/lens (Canon 5D, 85mm f/1.4 etc), mood, color palette, composition technique, style reference (editorial/cinematic/documentary/commercial)
- Never write generic prompts — be specific to the brand, product, and emotion

Platform dimensions (use these exactly):
- Instagram square: 1024×1024
- Instagram portrait: 768×1024
- Instagram story/Reel: 576×1024
- TikTok: 576×1024
- Facebook: 1024×512

Copy standards:
- Write the ACTUAL copy (hook, body, CTA, hashtags) — do not just describe what to write
- Platform-native tone: TikTok ≠ LinkedIn ≠ Instagram
- Hashtags: 3 tiers (niche/mid/mega), platform-correct count

Think like a $500/hour creative director who delivers results, not just assets.
Over-deliver on every brief."""


# ── Agent loop ─────────────────────────────────────────────────────────────────

def run_agent(brief: str):
    if not ANTHROPIC_KEY or not ANTHROPIC_KEY.startswith("sk-ant-"):
        print("\nERROR: ANTHROPIC_API_KEY not set.")
        print("  Get free $5 credit at console.anthropic.com")
        print("  export ANTHROPIC_API_KEY=sk-ant-xxxx\n")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    print(f"\n{'='*68}")
    print("  Full Media Suite Agent v2")
    print("  Claude Opus 4.8 + 8 Free Image Providers + 3 Video Providers")
    print(f"{'='*68}")

    # Show which providers are active
    active = ["Pollinations.ai (images + video — always active, no key needed)"]
    if TOGETHER_KEY:  active.append("Together AI (free FLUX forever)")
    if GOOGLE_KEY:    active.append("Google Gemini (500 images/day free)")
    if CF_TOKEN:      active.append("Cloudflare Workers AI (~50 images/day free)")
    if HF_TOKEN:      active.append("HuggingFace (images + Wan2.2 video, free tier)")
    if FAL_KEY:       active.append("fal.ai (images + video, $20 credits)")
    if NVIDIA_KEY:    active.append("NVIDIA NIM FLUX (1,000 credits)")
    if FIREWORKS_KEY: active.append("Fireworks AI ($1 credits)")
    if DEEPINFRA_KEY: active.append("DeepInfra ($5 credits)")

    print(f"\nActive providers ({len(active)}):")
    for a in active: print(f"  ✓ {a}")

    inactive = []
    if not TOGETHER_KEY:  inactive.append("TOGETHER_API_KEY  → together.ai  (free FLUX forever)")
    if not GOOGLE_KEY:    inactive.append("GOOGLE_API_KEY    → aistudio.google.com  (500 images/day)")
    if not CF_TOKEN:      inactive.append("CF_API_TOKEN + CF_ACCOUNT_ID  → cloudflare.com  (50 images/day)")
    if not HF_TOKEN:      inactive.append("HF_TOKEN          → huggingface.co/settings/tokens  (video too)")
    if not FAL_KEY:       inactive.append("FAL_KEY           → fal.ai  ($20 credits)")
    if inactive:
        print(f"\nUnlock more providers (set these env vars):")
        for i in inactive[:3]: print(f"  ○ {i}")

    print(f"\nBrief: {brief}\n{'─'*68}\n")

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

    print(f"\n{'='*68}")
    print(f"  Done! Everything saved to  media_output/")
    print(f"  See PROVIDERS.md for how to unlock more free providers.")
    print(f"{'='*68}\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    run_agent(" ".join(sys.argv[1:]))


if __name__ == "__main__":
    main()
