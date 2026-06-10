"""
video_agent.py — AI video generation agent powered by Claude Opus 4.8.

Usage:
    python video_agent.py "A cinematic shot of a sunset over mountains"
    python video_agent.py "Animate this photo" --image path/to/image.jpg
"""

import anthropic
import requests
import base64
import json
import os
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config / env
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("video_output")
OUTPUT_DIR.mkdir(exist_ok=True)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
HF_TOKEN          = os.environ.get("HF_TOKEN", "")
FAL_KEY           = os.environ.get("FAL_KEY", "")
NOVITA_API_KEY    = os.environ.get("NOVITA_API_KEY", "")
MINIMAX_API_KEY   = os.environ.get("MINIMAX_API_KEY", "")
LUMAAI_API_KEY    = os.environ.get("LUMAAI_API_KEY", "")

# ---------------------------------------------------------------------------
# Aspect-ratio helpers
# ---------------------------------------------------------------------------

ASPECT_RATIOS = {
    "9:16": {"width": 576,  "height": 1024},
    "16:9": {"width": 1024, "height": 576},
    "1:1":  {"width": 768,  "height": 768},
}

PLATFORM_TO_RATIO = {
    "tiktok":    "9:16",
    "reel":      "9:16",
    "story":     "9:16",
    "instagram": "9:16",
    "youtube":   "16:9",
    "landscape": "16:9",
    "square":    "1:1",
}

def _resolve_ratio(aspect_ratio: str) -> dict:
    ratio = PLATFORM_TO_RATIO.get(aspect_ratio.lower(), aspect_ratio)
    return ASPECT_RATIOS.get(ratio, ASPECT_RATIOS["16:9"])

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert AI video director with deep cinematic knowledge.
You help users create stunning video content by orchestrating multiple AI video generation providers.

Your expertise includes:
- Crafting evocative, detailed video prompts with lighting, camera movement, mood, and style descriptors
- Choosing the right aspect ratio for each platform (9:16 for TikTok/Reels, 16:9 for YouTube, 1:1 for square)
- Writing cohesive multi-scene storyboards and scripts
- Packaging deliverables with metadata and creative notes

When given a brief, think about the full cinematic vision: composition, color grading, pacing, and atmosphere.
Always enhance user prompts with professional cinematography language before generating videos.

Use the tools available to generate videos, animate images, write scripts, and compile packages.
Try to fulfill the user's request as completely as possible, using multiple tools if needed."""

# ---------------------------------------------------------------------------
# Async polling helper
# ---------------------------------------------------------------------------

def _poll_async(
    poll_url: str,
    headers: dict,
    task_id: str,
    task_id_key: str = "task_id",
    result_key: str = "videos",
    status_key: str = "status",
    success_statuses: Optional[list] = None,
    failed_statuses: Optional[list] = None,
    max_wait: int = 300,
) -> Optional[dict]:
    """Poll an async endpoint until the task completes or times out.

    Returns the final response dict on success, or None on failure/timeout.
    """
    if success_statuses is None:
        success_statuses = ["succeed", "success", "completed", "Success", "Succeeded"]
    if failed_statuses is None:
        failed_statuses = ["failed", "error", "Failed", "Error", "cancelled"]

    deadline = time.time() + max_wait
    wait = 5
    params = {task_id_key: task_id}

    while time.time() < deadline:
        try:
            resp = requests.get(poll_url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            print(f"[poll] request error: {exc}", flush=True)
            time.sleep(wait)
            wait = min(wait + 5, 15)
            continue

        status = data.get(status_key, "")
        print(f"[poll] status={status}", flush=True)

        if status in success_statuses:
            return data
        if status in failed_statuses:
            print(f"[poll] task failed: {data}", flush=True)
            return None

        time.sleep(wait)
        wait = min(wait + 5, 15)

    print("[poll] timed out", flush=True)
    return None

# ---------------------------------------------------------------------------
# Utility: download a video URL to disk
# ---------------------------------------------------------------------------

def _download_video(url: str, filepath: Path) -> bool:
    try:
        r = requests.get(url, timeout=120, stream=True)
        r.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        return True
    except Exception as exc:
        print(f"[download] error: {exc}", flush=True)
        return False

# ---------------------------------------------------------------------------
# Utility: encode local image as base64 data URL
# ---------------------------------------------------------------------------

def _encode_image(image_path: str) -> str:
    path = Path(image_path)
    ext = path.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp", "gif": "image/gif"}.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"

# ---------------------------------------------------------------------------
# fal.ai generic runner (uses requests directly, NOT fal_client)
# ---------------------------------------------------------------------------

def _fal_run(model: str, payload: dict, filename: str, provider_name: str) -> dict:
    if not FAL_KEY:
        return {"success": False, "error": "FAL_KEY not set"}

    url = f"https://fal.run/{model}"
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    # Extract video URL from various response shapes
    video_url = None
    if "video" in data:
        v = data["video"]
        video_url = v.get("url") if isinstance(v, dict) else v
    elif "videos" in data and data["videos"]:
        v = data["videos"][0]
        video_url = v.get("url") if isinstance(v, dict) else v
    elif "output" in data:
        out = data["output"]
        if isinstance(out, list) and out:
            video_url = out[0]
        elif isinstance(out, str):
            video_url = out

    if not video_url:
        return {"success": False, "error": f"No video URL in response: {data}"}

    filepath = OUTPUT_DIR / filename
    if not _download_video(video_url, filepath):
        return {"success": False, "error": "Download failed"}

    return {
        "success": True,
        "provider": provider_name,
        "file": str(filepath),
        "url": video_url,
    }

# ---------------------------------------------------------------------------
# Text-to-video providers
# ---------------------------------------------------------------------------

def provider_pollinations(prompt: str, filename: str, width: int, height: int) -> dict:
    """Pollinations.ai — free, no key required."""
    try:
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&model=video"
        resp = requests.get(url, timeout=120)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("video"):
            filepath = OUTPUT_DIR / filename
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return {"success": True, "provider": "pollinations", "file": str(filepath)}
        return {"success": False, "error": f"Unexpected response: {resp.status_code}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def provider_huggingface_wan(prompt: str, filename: str, width: int, height: int) -> dict:
    """HuggingFace Wan2.2 text-to-video via Inference API."""
    if not HF_TOKEN:
        return {"success": False, "error": "HF_TOKEN not set"}

    model = "Wan-AI/Wan2.2-T2V-14B"
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "inputs": prompt,
        "parameters": {"width": width, "height": height, "num_frames": 49},
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=300)
        resp.raise_for_status()
        if resp.headers.get("content-type", "").startswith("video"):
            filepath = OUTPUT_DIR / filename
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return {"success": True, "provider": "huggingface_wan", "file": str(filepath)}
        return {"success": False, "error": f"Unexpected content-type: {resp.headers.get('content-type')}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def provider_fal_cogvideox(prompt: str, filename: str, width: int, height: int) -> dict:
    """fal.ai CogVideoX text-to-video."""
    payload = {
        "prompt": prompt,
        "video_size": {"width": width, "height": height},
        "num_inference_steps": 50,
    }
    return _fal_run("fal-ai/cogvideox-5b", payload, filename, "fal_cogvideox")


def provider_fal_wan_t2v(prompt: str, filename: str, width: int, height: int) -> dict:
    """fal.ai Wan text-to-video."""
    payload = {
        "prompt": prompt,
        "video_size": {"width": width, "height": height},
    }
    return _fal_run("fal-ai/wan-t2v", payload, filename, "fal_wan_t2v")


def provider_novita_kling_t2v(prompt: str, filename: str, width: int, height: int) -> dict:
    """Novita AI Kling 3.0 text-to-video (async)."""
    if not NOVITA_API_KEY:
        return {"success": False, "error": "NOVITA_API_KEY not set"}

    submit_url = "https://api.novita.ai/v3/async/txt2video-kling-v3.0-std"
    poll_url   = "https://api.novita.ai/v3/async/task-result"
    headers = {
        "Authorization": f"Bearer {NOVITA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "duration": 5,
    }

    try:
        resp = requests.post(submit_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        task_id = resp.json().get("task_id")
        if not task_id:
            return {"success": False, "error": f"No task_id in response: {resp.text}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    print(f"[novita_kling] task_id={task_id}", flush=True)
    result = _poll_async(
        poll_url=poll_url,
        headers=headers,
        task_id=task_id,
        task_id_key="task_id",
        result_key="videos",
        status_key="status",
        success_statuses=["TASK_STATUS_SUCCEED", "succeed"],
        failed_statuses=["TASK_STATUS_FAILED", "failed"],
        max_wait=300,
    )

    if not result:
        return {"success": False, "error": "Task failed or timed out"}

    videos = result.get("videos") or result.get("result", {}).get("videos", [])
    if not videos:
        return {"success": False, "error": f"No videos in result: {result}"}

    video_url = videos[0].get("url") if isinstance(videos[0], dict) else videos[0]
    filepath = OUTPUT_DIR / filename
    if not _download_video(video_url, filepath):
        return {"success": False, "error": "Download failed"}

    return {"success": True, "provider": "novita_kling", "file": str(filepath), "url": video_url}


def provider_minimax_t2v(prompt: str, filename: str, width: int, height: int) -> dict:
    """MiniMax/Hailuo text-to-video (async)."""
    if not MINIMAX_API_KEY:
        return {"success": False, "error": "MINIMAX_API_KEY not set"}

    submit_url = "https://api.minimax.io/v1/video_generation"
    poll_url   = "https://api.minimax.io/v1/query/video_generation"
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": "video-01", "prompt": prompt}

    try:
        resp = requests.post(submit_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        task_id = resp.json().get("task_id")
        if not task_id:
            return {"success": False, "error": f"No task_id: {resp.text}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    print(f"[minimax] task_id={task_id}", flush=True)
    result = _poll_async(
        poll_url=poll_url,
        headers=headers,
        task_id=task_id,
        task_id_key="task_id",
        result_key="file_id",
        status_key="status",
        success_statuses=["Success"],
        failed_statuses=["Failed", "Error"],
        max_wait=300,
    )

    if not result:
        return {"success": False, "error": "Task failed or timed out"}

    file_id = result.get("file_id")
    if not file_id:
        return {"success": False, "error": f"No file_id in result: {result}"}

    # Download via files API
    download_url = f"https://api.minimax.io/v1/files/retrieve?file_id={file_id}"
    try:
        dr = requests.get(download_url, headers=headers, timeout=60)
        dr.raise_for_status()
        # Response may be JSON with a download URL or raw bytes
        ct = dr.headers.get("content-type", "")
        if "application/json" in ct:
            ddata = dr.json()
            video_url = ddata.get("download_url") or ddata.get("url")
            if not video_url:
                return {"success": False, "error": f"No download URL: {ddata}"}
            filepath = OUTPUT_DIR / filename
            if not _download_video(video_url, filepath):
                return {"success": False, "error": "Download failed"}
        else:
            filepath = OUTPUT_DIR / filename
            with open(filepath, "wb") as f:
                for chunk in dr.iter_content(65536):
                    f.write(chunk)
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    return {"success": True, "provider": "minimax", "file": str(filepath)}

# ---------------------------------------------------------------------------
# Image-to-video providers
# ---------------------------------------------------------------------------

def provider_fal_kling_i2v(image_path: str, prompt: str, filename: str) -> dict:
    """fal.ai Kling image-to-video."""
    data_url = _encode_image(image_path)
    payload = {
        "image_url": data_url,
        "prompt": prompt,
        "duration": "5",
    }
    return _fal_run("fal-ai/kling-video/v1.5/standard/image-to-video", payload, filename, "fal_kling_i2v")


def provider_fal_minimax_i2v(image_path: str, prompt: str, filename: str) -> dict:
    """fal.ai MiniMax image-to-video."""
    data_url = _encode_image(image_path)
    payload = {
        "image_url": data_url,
        "prompt": prompt,
    }
    return _fal_run("fal-ai/minimax/video-01/image-to-video", payload, filename, "fal_minimax_i2v")


def provider_luma_i2v(image_path: str, prompt: str, filename: str) -> dict:
    """Luma Dream Machine image-to-video via lumaai SDK."""
    if not LUMAAI_API_KEY:
        return {"success": False, "error": "LUMAAI_API_KEY not set"}

    try:
        from lumaai import LumaAI
    except ImportError:
        return {"success": False, "error": "lumaai package not installed (pip install lumaai)"}

    data_url = _encode_image(image_path)
    client = LumaAI(auth_token=LUMAAI_API_KEY)

    try:
        generation = client.generations.create(
            prompt=prompt,
            keyframes={"frame0": {"type": "image", "url": data_url}},
        )
        # Poll until complete
        deadline = time.time() + 300
        while time.time() < deadline:
            gen = client.generations.get(id=generation.id)
            state = gen.state
            print(f"[luma] state={state}", flush=True)
            if state == "completed":
                video_url = gen.assets.video
                filepath = OUTPUT_DIR / filename
                if _download_video(video_url, filepath):
                    return {"success": True, "provider": "luma", "file": str(filepath), "url": video_url}
                return {"success": False, "error": "Download failed"}
            if state in ("failed", "error"):
                return {"success": False, "error": f"Luma generation failed: {gen}"}
            time.sleep(10)
        return {"success": False, "error": "Luma timed out"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def provider_novita_kling_i2v(image_path: str, prompt: str, filename: str) -> dict:
    """Novita AI Kling image-to-video (async)."""
    if not NOVITA_API_KEY:
        return {"success": False, "error": "NOVITA_API_KEY not set"}

    data_url = _encode_image(image_path)
    submit_url = "https://api.novita.ai/v3/async/img2video-kling-v3.0-std"
    poll_url   = "https://api.novita.ai/v3/async/task-result"
    headers = {
        "Authorization": f"Bearer {NOVITA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "image": data_url,
        "prompt": prompt,
        "duration": 5,
    }

    try:
        resp = requests.post(submit_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        task_id = resp.json().get("task_id")
        if not task_id:
            return {"success": False, "error": f"No task_id: {resp.text}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    print(f"[novita_kling_i2v] task_id={task_id}", flush=True)
    result = _poll_async(
        poll_url=poll_url,
        headers=headers,
        task_id=task_id,
        task_id_key="task_id",
        result_key="videos",
        status_key="status",
        success_statuses=["TASK_STATUS_SUCCEED", "succeed"],
        failed_statuses=["TASK_STATUS_FAILED", "failed"],
        max_wait=300,
    )

    if not result:
        return {"success": False, "error": "Task failed or timed out"}

    videos = result.get("videos") or result.get("result", {}).get("videos", [])
    if not videos:
        return {"success": False, "error": f"No videos in result: {result}"}

    video_url = videos[0].get("url") if isinstance(videos[0], dict) else videos[0]
    filepath = OUTPUT_DIR / filename
    if not _download_video(video_url, filepath):
        return {"success": False, "error": "Download failed"}

    return {"success": True, "provider": "novita_kling_i2v", "file": str(filepath), "url": video_url}

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def tool_generate_video(
    prompt: str,
    aspect_ratio: str = "16:9",
    duration: int = 5,
    style: str = "",
) -> dict:
    """Generate a text-to-video using the best available provider."""
    dims = _resolve_ratio(aspect_ratio)
    width, height = dims["width"], dims["height"]

    enhanced = prompt
    if style:
        enhanced = f"{prompt}, {style}"

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"video_{ts}.mp4"

    providers = [
        ("pollinations",    lambda: provider_pollinations(enhanced, filename, width, height)),
        ("huggingface_wan", lambda: provider_huggingface_wan(enhanced, filename, width, height)),
        ("fal_cogvideox",   lambda: provider_fal_cogvideox(enhanced, filename, width, height)),
        ("fal_wan_t2v",     lambda: provider_fal_wan_t2v(enhanced, filename, width, height)),
        ("novita_kling",    lambda: provider_novita_kling_t2v(enhanced, filename, width, height)),
        ("minimax",         lambda: provider_minimax_t2v(enhanced, filename, width, height)),
    ]

    for name, fn in providers:
        print(f"[generate_video] trying {name}...", flush=True)
        result = fn()
        if result.get("success"):
            print(f"[generate_video] success with {name}", flush=True)
            result["prompt"] = enhanced
            result["aspect_ratio"] = aspect_ratio
            result["dimensions"] = f"{width}x{height}"
            return result
        print(f"[generate_video] {name} failed: {result.get('error')}", flush=True)

    return {"success": False, "error": "All providers failed"}


def tool_animate_image(
    image_path: str,
    prompt: str,
    motion_style: str = "",
) -> dict:
    """Animate a static image into a video."""
    if not Path(image_path).exists():
        return {"success": False, "error": f"Image not found: {image_path}"}

    enhanced = prompt
    if motion_style:
        enhanced = f"{prompt}, {motion_style}"

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"animated_{ts}.mp4"

    providers = [
        ("fal_kling_i2v",   lambda: provider_fal_kling_i2v(image_path, enhanced, filename)),
        ("fal_minimax_i2v", lambda: provider_fal_minimax_i2v(image_path, enhanced, filename)),
        ("luma",            lambda: provider_luma_i2v(image_path, enhanced, filename)),
        ("novita_kling_i2v",lambda: provider_novita_kling_i2v(image_path, enhanced, filename)),
    ]

    for name, fn in providers:
        print(f"[animate_image] trying {name}...", flush=True)
        result = fn()
        if result.get("success"):
            print(f"[animate_image] success with {name}", flush=True)
            result["source_image"] = image_path
            result["prompt"] = enhanced
            return result
        print(f"[animate_image] {name} failed: {result.get('error')}", flush=True)

    return {"success": False, "error": "All i2v providers failed"}


def tool_generate_storyboard(
    concept: str,
    num_scenes: int = 5,
    target_platform: str = "youtube",
) -> dict:
    """Generate a detailed storyboard for a video concept."""
    aspect_ratio = PLATFORM_TO_RATIO.get(target_platform.lower(), "16:9")
    dims = _resolve_ratio(aspect_ratio)

    scenes = []
    # Build a basic storyboard structure — Claude will fill in details via the conversation
    for i in range(1, num_scenes + 1):
        scenes.append({
            "scene": i,
            "description": f"[Scene {i} — to be detailed by director]",
            "duration_seconds": 5,
            "camera": "static",
            "lighting": "natural",
            "mood": "neutral",
            "prompt_suggestion": f"Scene {i} of: {concept}",
        })

    storyboard = {
        "success": True,
        "concept": concept,
        "num_scenes": num_scenes,
        "target_platform": target_platform,
        "aspect_ratio": aspect_ratio,
        "dimensions": f"{dims['width']}x{dims['height']}",
        "total_duration_seconds": num_scenes * 5,
        "scenes": scenes,
        "note": "Expand each scene prompt with cinematic detail before generating.",
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = OUTPUT_DIR / f"storyboard_{ts}.json"
    with open(outfile, "w") as f:
        json.dump(storyboard, f, indent=2)
    storyboard["file"] = str(outfile)
    return storyboard


def tool_write_video_script(
    concept: str,
    duration_seconds: int = 60,
    tone: str = "cinematic",
    include_voiceover: bool = True,
) -> dict:
    """Write a structured video script."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    script = {
        "success": True,
        "concept": concept,
        "duration_seconds": duration_seconds,
        "tone": tone,
        "include_voiceover": include_voiceover,
        "script_sections": [
            {
                "section": "hook",
                "duration": 5,
                "visual": f"Opening shot establishing {concept}",
                "voiceover": "[Hook line here]" if include_voiceover else None,
                "notes": "Grab attention immediately",
            },
            {
                "section": "main_content",
                "duration": duration_seconds - 15,
                "visual": f"Core visual storytelling for {concept}",
                "voiceover": "[Main narrative]" if include_voiceover else None,
                "notes": f"Tone: {tone}",
            },
            {
                "section": "outro",
                "duration": 10,
                "visual": "Call to action / fade out",
                "voiceover": "[Closing]" if include_voiceover else None,
                "notes": "Strong finish",
            },
        ],
        "tone": tone,
    }

    outfile = OUTPUT_DIR / f"script_{ts}.json"
    with open(outfile, "w") as f:
        json.dump(script, f, indent=2)
    script["file"] = str(outfile)
    return script


def tool_compile_video_package(
    project_name: str,
    video_files: list,
    script: Optional[dict] = None,
    storyboard: Optional[dict] = None,
    notes: str = "",
) -> dict:
    """Compile all video assets into a structured delivery package."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_dir = OUTPUT_DIR / f"package_{project_name}_{ts}"
    package_dir.mkdir(exist_ok=True)

    manifest = {
        "project": project_name,
        "created": ts,
        "video_files": video_files,
        "script": script,
        "storyboard": storyboard,
        "notes": notes,
        "package_dir": str(package_dir),
    }

    manifest_file = package_dir / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    # Write a human-readable summary
    summary_lines = [
        f"# Video Package: {project_name}",
        f"Created: {ts}",
        "",
        "## Video Files",
    ]
    for vf in video_files:
        summary_lines.append(f"- {vf}")
    if notes:
        summary_lines += ["", "## Notes", notes]

    summary_file = package_dir / "README.md"
    with open(summary_file, "w") as f:
        f.write("\n".join(summary_lines))

    return {
        "success": True,
        "package_dir": str(package_dir),
        "manifest": str(manifest_file),
        "summary": str(summary_file),
    }

# ---------------------------------------------------------------------------
# Tool schemas for Claude
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "generate_video",
        "description": (
            "Generate a text-to-video clip. Tries multiple providers in order "
            "(Pollinations → HuggingFace Wan → fal CogVideoX → fal Wan → Novita Kling → MiniMax). "
            "Returns the file path of the saved video."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Detailed cinematic video prompt with style, lighting, camera movement.",
                },
                "aspect_ratio": {
                    "type": "string",
                    "description": "Aspect ratio or platform name: '16:9', '9:16', '1:1', 'youtube', 'tiktok', 'instagram', etc.",
                    "default": "16:9",
                },
                "duration": {
                    "type": "integer",
                    "description": "Desired duration in seconds (provider-dependent).",
                    "default": 5,
                },
                "style": {
                    "type": "string",
                    "description": "Optional style suffix appended to the prompt (e.g. 'cinematic, 8K, golden hour').",
                    "default": "",
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "animate_image",
        "description": (
            "Animate a static image into a video clip using image-to-video AI. "
            "Tries: fal Kling i2v → fal MiniMax i2v → Luma Dream Machine → Novita Kling i2v."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Local filesystem path to the source image.",
                },
                "prompt": {
                    "type": "string",
                    "description": "Motion/animation description for how the image should come to life.",
                },
                "motion_style": {
                    "type": "string",
                    "description": "Optional motion style suffix (e.g. 'slow zoom in', 'parallax', 'camera pan left').",
                    "default": "",
                },
            },
            "required": ["image_path", "prompt"],
        },
    },
    {
        "name": "generate_storyboard",
        "description": "Generate a structured multi-scene storyboard for a video concept. Saves JSON to video_output/.",
        "input_schema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "High-level creative concept or brief for the video.",
                },
                "num_scenes": {
                    "type": "integer",
                    "description": "Number of scenes to plan.",
                    "default": 5,
                },
                "target_platform": {
                    "type": "string",
                    "description": "Target platform: 'youtube', 'tiktok', 'instagram', 'reel', 'story', etc.",
                    "default": "youtube",
                },
            },
            "required": ["concept"],
        },
    },
    {
        "name": "write_video_script",
        "description": "Write a structured video script with hook, main content, and outro sections. Saves JSON to video_output/.",
        "input_schema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "The video concept or topic.",
                },
                "duration_seconds": {
                    "type": "integer",
                    "description": "Total desired video duration in seconds.",
                    "default": 60,
                },
                "tone": {
                    "type": "string",
                    "description": "Tone/style: 'cinematic', 'documentary', 'energetic', 'calm', 'dramatic', etc.",
                    "default": "cinematic",
                },
                "include_voiceover": {
                    "type": "boolean",
                    "description": "Whether to include voiceover/narration lines.",
                    "default": True,
                },
            },
            "required": ["concept"],
        },
    },
    {
        "name": "compile_video_package",
        "description": "Compile all generated video files, scripts, and storyboards into a structured delivery package.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Name for the project/package.",
                },
                "video_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of video file paths to include.",
                },
                "script": {
                    "type": "object",
                    "description": "Script dict returned by write_video_script (optional).",
                },
                "storyboard": {
                    "type": "object",
                    "description": "Storyboard dict returned by generate_storyboard (optional).",
                },
                "notes": {
                    "type": "string",
                    "description": "Additional creative or delivery notes.",
                    "default": "",
                },
            },
            "required": ["project_name", "video_files"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

def dispatch_tool(name: str, inputs: dict) -> str:
    try:
        if name == "generate_video":
            result = tool_generate_video(**inputs)
        elif name == "animate_image":
            result = tool_animate_image(**inputs)
        elif name == "generate_storyboard":
            result = tool_generate_storyboard(**inputs)
        elif name == "write_video_script":
            result = tool_write_video_script(**inputs)
        elif name == "compile_video_package":
            result = tool_compile_video_package(**inputs)
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as exc:
        result = {"error": f"Tool execution error: {exc}"}

    return json.dumps(result)

# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def run_agent(user_request: str, image_path: Optional[str] = None) -> None:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build initial message
    if image_path:
        content = (
            f"{user_request}\n\n"
            f"Source image provided at: {image_path}\n"
            "Please start by animating this image using the animate_image tool."
        )
    else:
        content = user_request

    messages = [{"role": "user", "content": content}]

    print(f"\n[agent] Starting video generation agent...", flush=True)
    print(f"[agent] Request: {user_request}", flush=True)
    if image_path:
        print(f"[agent] Image: {image_path}", flush=True)
    print("=" * 60, flush=True)

    max_iterations = 20
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"\n[agent] Iteration {iteration}", flush=True)

        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Collect assistant message blocks
        assistant_content = []
        tool_calls = []

        for block in response.content:
            assistant_content.append(block)
            if block.type == "thinking":
                print(f"[agent] <thinking>...</thinking>", flush=True)
            elif block.type == "text":
                print(f"[agent] {block.text}", flush=True)
            elif block.type == "tool_use":
                tool_calls.append(block)
                print(f"[agent] → calling tool: {block.name}", flush=True)
                print(f"[agent]   inputs: {json.dumps(block.input, indent=2)}", flush=True)

        # Add assistant turn to messages
        messages.append({"role": "assistant", "content": assistant_content})

        # Check stop condition
        if response.stop_reason == "end_turn":
            print("\n[agent] Done.", flush=True)
            break

        if response.stop_reason != "tool_use" or not tool_calls:
            print(f"\n[agent] Stopping (stop_reason={response.stop_reason})", flush=True)
            break

        # Execute tool calls and build tool_result blocks
        tool_results = []
        for tc in tool_calls:
            print(f"[agent] Executing {tc.name}...", flush=True)
            result_str = dispatch_tool(tc.name, tc.input)
            result_data = json.loads(result_str)
            print(f"[agent] Result: {json.dumps(result_data, indent=2)}", flush=True)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": result_str,
            })

        messages.append({"role": "user", "content": tool_results})

    if iteration >= max_iterations:
        print(f"\n[agent] Reached max iterations ({max_iterations}).", flush=True)

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python video_agent.py \"brief\" [--image path/to/image.jpg]")
        sys.exit(1)

    image_path = None
    filtered = []
    i = 0
    while i < len(args):
        if args[i] == "--image" and i + 1 < len(args):
            image_path = args[i + 1]
            i += 2
        else:
            filtered.append(args[i])
            i += 1

    user_request = " ".join(filtered)

    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    run_agent(user_request, image_path=image_path)


if __name__ == "__main__":
    main()
