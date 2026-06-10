#!/usr/bin/env python3
"""
Provider Health Check and Status Tool
Tests every AI image/video provider and shows which ones work,
which need keys, and which are failing.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

import requests

TIMEOUT = 7  # seconds per request

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


@dataclass
class ProviderResult:
    name: str
    type: str  # "image" or "video"
    status: str  # "active", "no_key", "error"
    status_code: Optional[int]
    free_tier: str
    note: str
    get_key_url: str = ""


def check_pollinations_image() -> ProviderResult:
    url = "https://image.pollinations.ai/prompt/test?width=64&height=64&nologo=true"
    try:
        r = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code == 200:
            return ProviderResult(
                name="Pollinations.ai",
                type="image",
                status="active",
                status_code=200,
                free_tier="Yes (unlimited)",
                note="No key needed",
            )
        return ProviderResult(
            name="Pollinations.ai",
            type="image",
            status="error",
            status_code=r.status_code,
            free_tier="Yes (unlimited)",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="Pollinations.ai",
            type="image",
            status="error",
            status_code=None,
            free_tier="Yes (unlimited)",
            note=f"Connection error: {type(e).__name__}",
        )


def check_together_ai() -> ProviderResult:
    key = os.environ.get("TOGETHER_API_KEY", "")
    if not key:
        return ProviderResult(
            name="Together AI",
            type="image",
            status="no_key",
            status_code=None,
            free_tier="$25 credit",
            note="Set TOGETHER_API_KEY",
            get_key_url="https://api.together.xyz/settings/api-keys",
        )
    try:
        r = requests.get(
            "https://api.together.xyz/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return ProviderResult(
                name="Together AI",
                type="image",
                status="active",
                status_code=200,
                free_tier="$25 credit",
                note="Key valid",
            )
        return ProviderResult(
            name="Together AI",
            type="image",
            status="error",
            status_code=r.status_code,
            free_tier="$25 credit",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="Together AI",
            type="image",
            status="error",
            status_code=None,
            free_tier="$25 credit",
            note=f"Connection error: {type(e).__name__}",
        )


def check_google_gemini() -> ProviderResult:
    key = os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        return ProviderResult(
            name="Google Gemini",
            type="image",
            status="no_key",
            status_code=None,
            free_tier="Yes (generous)",
            note="Set GOOGLE_API_KEY",
            get_key_url="https://aistudio.google.com/app/apikey",
        )
    try:
        r = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return ProviderResult(
                name="Google Gemini",
                type="image",
                status="active",
                status_code=200,
                free_tier="Yes (generous)",
                note="Key valid",
            )
        return ProviderResult(
            name="Google Gemini",
            type="image",
            status="error",
            status_code=r.status_code,
            free_tier="Yes (generous)",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="Google Gemini",
            type="image",
            status="error",
            status_code=None,
            free_tier="Yes (generous)",
            note=f"Connection error: {type(e).__name__}",
        )


def check_cloudflare() -> ProviderResult:
    token = os.environ.get("CF_API_TOKEN", "")
    account_id = os.environ.get("CF_ACCOUNT_ID", "")
    if not token or not account_id:
        missing = []
        if not token:
            missing.append("CF_API_TOKEN")
        if not account_id:
            missing.append("CF_ACCOUNT_ID")
        return ProviderResult(
            name="Cloudflare Workers AI",
            type="image",
            status="no_key",
            status_code=None,
            free_tier="Yes (10k/day)",
            note=f"Set {', '.join(missing)}",
            get_key_url="https://dash.cloudflare.com/profile/api-tokens",
        )
    try:
        r = requests.get(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/models/search",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return ProviderResult(
                name="Cloudflare Workers AI",
                type="image",
                status="active",
                status_code=200,
                free_tier="Yes (10k/day)",
                note="Keys valid",
            )
        return ProviderResult(
            name="Cloudflare Workers AI",
            type="image",
            status="error",
            status_code=r.status_code,
            free_tier="Yes (10k/day)",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="Cloudflare Workers AI",
            type="image",
            status="error",
            status_code=None,
            free_tier="Yes (10k/day)",
            note=f"Connection error: {type(e).__name__}",
        )


def check_huggingface() -> ProviderResult:
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        return ProviderResult(
            name="HuggingFace",
            type="image",
            status="no_key",
            status_code=None,
            free_tier="Yes (limited)",
            note="Set HF_TOKEN",
            get_key_url="https://huggingface.co/settings/tokens",
        )
    try:
        r = requests.get(
            "https://huggingface.co/api/whoami",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            data = r.json()
            username = data.get("name", "unknown")
            return ProviderResult(
                name="HuggingFace",
                type="image",
                status="active",
                status_code=200,
                free_tier="Yes (limited)",
                note=f"User: {username}",
            )
        return ProviderResult(
            name="HuggingFace",
            type="image",
            status="error",
            status_code=r.status_code,
            free_tier="Yes (limited)",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="HuggingFace",
            type="image",
            status="error",
            status_code=None,
            free_tier="Yes (limited)",
            note=f"Connection error: {type(e).__name__}",
        )


def check_fal_ai() -> ProviderResult:
    key = os.environ.get("FAL_KEY", "")
    if not key:
        return ProviderResult(
            name="fal.ai",
            type="image",
            status="no_key",
            status_code=None,
            free_tier="$10 credit",
            note="Set FAL_KEY",
            get_key_url="https://fal.ai/dashboard/keys",
        )
    try:
        r = requests.get(
            "https://fal.run/health",
            headers={"Authorization": f"Key {key}"},
            timeout=TIMEOUT,
        )
        if r.status_code in (200, 404):
            # 404 is OK — endpoint exists, auth passed
            return ProviderResult(
                name="fal.ai",
                type="image",
                status="active",
                status_code=r.status_code,
                free_tier="$10 credit",
                note="Key valid",
            )
        if r.status_code == 401:
            return ProviderResult(
                name="fal.ai",
                type="image",
                status="error",
                status_code=401,
                free_tier="$10 credit",
                note="Invalid key (401)",
            )
        return ProviderResult(
            name="fal.ai",
            type="image",
            status="active",
            status_code=r.status_code,
            free_tier="$10 credit",
            note="Key valid (API reachable)",
        )
    except Exception as e:
        return ProviderResult(
            name="fal.ai",
            type="image",
            status="error",
            status_code=None,
            free_tier="$10 credit",
            note=f"Connection error: {type(e).__name__}",
        )


def check_nvidia_nim() -> ProviderResult:
    key = os.environ.get("NVIDIA_API_KEY", "")
    if not key:
        return ProviderResult(
            name="NVIDIA NIM",
            type="image",
            status="no_key",
            status_code=None,
            free_tier="1000 credits",
            note="Set NVIDIA_API_KEY",
            get_key_url="https://build.nvidia.com/",
        )
    try:
        r = requests.get(
            "https://api.nvidia.com/credits/v1/balance",
            headers={"Authorization": f"Bearer {key}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            try:
                data = r.json()
                balance = data.get("balance", "unknown")
                return ProviderResult(
                    name="NVIDIA NIM",
                    type="image",
                    status="active",
                    status_code=200,
                    free_tier="1000 credits",
                    note=f"Balance: {balance}",
                )
            except Exception:
                return ProviderResult(
                    name="NVIDIA NIM",
                    type="image",
                    status="active",
                    status_code=200,
                    free_tier="1000 credits",
                    note="Key valid",
                )
        return ProviderResult(
            name="NVIDIA NIM",
            type="image",
            status="error",
            status_code=r.status_code,
            free_tier="1000 credits",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="NVIDIA NIM",
            type="image",
            status="error",
            status_code=None,
            free_tier="1000 credits",
            note=f"Connection error: {type(e).__name__}",
        )


def check_fireworks() -> ProviderResult:
    key = os.environ.get("FIREWORKS_API_KEY", "")
    if not key:
        return ProviderResult(
            name="Fireworks AI",
            type="image",
            status="no_key",
            status_code=None,
            free_tier="$1 credit",
            note="Set FIREWORKS_API_KEY",
            get_key_url="https://fireworks.ai/account/api-keys",
        )
    try:
        r = requests.get(
            "https://api.fireworks.ai/inference/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return ProviderResult(
                name="Fireworks AI",
                type="image",
                status="active",
                status_code=200,
                free_tier="$1 credit",
                note="Key valid",
            )
        return ProviderResult(
            name="Fireworks AI",
            type="image",
            status="error",
            status_code=r.status_code,
            free_tier="$1 credit",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="Fireworks AI",
            type="image",
            status="error",
            status_code=None,
            free_tier="$1 credit",
            note=f"Connection error: {type(e).__name__}",
        )


def check_deepinfra() -> ProviderResult:
    token = os.environ.get("DEEPINFRA_TOKEN", "")
    if not token:
        return ProviderResult(
            name="DeepInfra",
            type="image",
            status="no_key",
            status_code=None,
            free_tier="$1.80 credit",
            note="Set DEEPINFRA_TOKEN",
            get_key_url="https://deepinfra.com/dash/api_keys",
        )
    try:
        r = requests.get(
            "https://api.deepinfra.com/v1/openai/models",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return ProviderResult(
                name="DeepInfra",
                type="image",
                status="active",
                status_code=200,
                free_tier="$1.80 credit",
                note="Key valid",
            )
        return ProviderResult(
            name="DeepInfra",
            type="image",
            status="error",
            status_code=r.status_code,
            free_tier="$1.80 credit",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="DeepInfra",
            type="image",
            status="error",
            status_code=None,
            free_tier="$1.80 credit",
            note=f"Connection error: {type(e).__name__}",
        )


def check_novita() -> ProviderResult:
    key = os.environ.get("NOVITA_API_KEY", "")
    if not key:
        return ProviderResult(
            name="Novita AI",
            type="image",
            status="no_key",
            status_code=None,
            free_tier="$0.50 credit",
            note="Set NOVITA_API_KEY",
            get_key_url="https://novita.ai/settings/key-management",
        )
    try:
        r = requests.get(
            "https://api.novita.ai/v3/model",
            headers={"Authorization": f"Bearer {key}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return ProviderResult(
                name="Novita AI",
                type="image",
                status="active",
                status_code=200,
                free_tier="$0.50 credit",
                note="Key valid",
            )
        return ProviderResult(
            name="Novita AI",
            type="image",
            status="error",
            status_code=r.status_code,
            free_tier="$0.50 credit",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="Novita AI",
            type="image",
            status="error",
            status_code=None,
            free_tier="$0.50 credit",
            note=f"Connection error: {type(e).__name__}",
        )


def check_stability() -> ProviderResult:
    key = os.environ.get("STABILITY_API_KEY", "")
    if not key:
        return ProviderResult(
            name="Stability AI",
            type="image",
            status="no_key",
            status_code=None,
            free_tier="25 credits",
            note="Set STABILITY_API_KEY",
            get_key_url="https://platform.stability.ai/account/keys",
        )
    try:
        r = requests.get(
            "https://api.stability.ai/v1/user/balance",
            headers={"Authorization": f"Bearer {key}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            try:
                data = r.json()
                credits = data.get("credits", "unknown")
                note = (
                    f"Credits: {credits:.1f}"
                    if isinstance(credits, float)
                    else f"Credits: {credits}"
                )
                return ProviderResult(
                    name="Stability AI",
                    type="image",
                    status="active",
                    status_code=200,
                    free_tier="25 credits",
                    note=note,
                )
            except Exception:
                return ProviderResult(
                    name="Stability AI",
                    type="image",
                    status="active",
                    status_code=200,
                    free_tier="25 credits",
                    note="Key valid",
                )
        return ProviderResult(
            name="Stability AI",
            type="image",
            status="error",
            status_code=r.status_code,
            free_tier="25 credits",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="Stability AI",
            type="image",
            status="error",
            status_code=None,
            free_tier="25 credits",
            note=f"Connection error: {type(e).__name__}",
        )


def check_pollinations_video() -> ProviderResult:
    url = "https://video.pollinations.ai/prompt/test"
    try:
        r = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        # Any non-5xx response means the endpoint is reachable
        if r.status_code < 500:
            return ProviderResult(
                name="Pollinations Video",
                type="video",
                status="active",
                status_code=r.status_code,
                free_tier="Yes (unlimited)",
                note="No key needed",
            )
        return ProviderResult(
            name="Pollinations Video",
            type="video",
            status="error",
            status_code=r.status_code,
            free_tier="Yes (unlimited)",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="Pollinations Video",
            type="video",
            status="error",
            status_code=None,
            free_tier="Yes (unlimited)",
            note=f"Connection error: {type(e).__name__}",
        )


def check_huggingface_wan() -> ProviderResult:
    """HuggingFace Wan2.2 — reuses the same HF_TOKEN check."""
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        return ProviderResult(
            name="HuggingFace Wan2.2",
            type="video",
            status="no_key",
            status_code=None,
            free_tier="Yes (limited)",
            note="Set HF_TOKEN",
            get_key_url="https://huggingface.co/settings/tokens",
        )
    try:
        r = requests.get(
            "https://huggingface.co/api/whoami",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return ProviderResult(
                name="HuggingFace Wan2.2",
                type="video",
                status="active",
                status_code=200,
                free_tier="Yes (limited)",
                note="Token valid (shared with HF image)",
            )
        return ProviderResult(
            name="HuggingFace Wan2.2",
            type="video",
            status="error",
            status_code=r.status_code,
            free_tier="Yes (limited)",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="HuggingFace Wan2.2",
            type="video",
            status="error",
            status_code=None,
            free_tier="Yes (limited)",
            note=f"Connection error: {type(e).__name__}",
        )


def check_fal_video() -> ProviderResult:
    """fal.ai video — reuses FAL_KEY check."""
    key = os.environ.get("FAL_KEY", "")
    if not key:
        return ProviderResult(
            name="fal.ai Video",
            type="video",
            status="no_key",
            status_code=None,
            free_tier="$10 credit",
            note="Set FAL_KEY",
            get_key_url="https://fal.ai/dashboard/keys",
        )
    try:
        r = requests.get(
            "https://fal.run/health",
            headers={"Authorization": f"Key {key}"},
            timeout=TIMEOUT,
        )
        if r.status_code in (200, 404):
            return ProviderResult(
                name="fal.ai Video",
                type="video",
                status="active",
                status_code=r.status_code,
                free_tier="$10 credit",
                note="Key valid (shared with fal.ai image)",
            )
        if r.status_code == 401:
            return ProviderResult(
                name="fal.ai Video",
                type="video",
                status="error",
                status_code=401,
                free_tier="$10 credit",
                note="Invalid key (401)",
            )
        return ProviderResult(
            name="fal.ai Video",
            type="video",
            status="active",
            status_code=r.status_code,
            free_tier="$10 credit",
            note="Key valid (API reachable)",
        )
    except Exception as e:
        return ProviderResult(
            name="fal.ai Video",
            type="video",
            status="error",
            status_code=None,
            free_tier="$10 credit",
            note=f"Connection error: {type(e).__name__}",
        )


def check_minimax() -> ProviderResult:
    key = os.environ.get("MINIMAX_API_KEY", "")
    if not key:
        return ProviderResult(
            name="MiniMax/Hailuo",
            type="video",
            status="no_key",
            status_code=None,
            free_tier="Limited free",
            note="Set MINIMAX_API_KEY",
            get_key_url="https://platform.minimaxi.com/user-center/basic-information/interface-key",
        )
    try:
        r = requests.get(
            "https://api.minimax.io/v1/me",
            headers={"Authorization": f"Bearer {key}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return ProviderResult(
                name="MiniMax/Hailuo",
                type="video",
                status="active",
                status_code=200,
                free_tier="Limited free",
                note="Key valid",
            )
        return ProviderResult(
            name="MiniMax/Hailuo",
            type="video",
            status="error",
            status_code=r.status_code,
            free_tier="Limited free",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="MiniMax/Hailuo",
            type="video",
            status="error",
            status_code=None,
            free_tier="Limited free",
            note=f"Connection error: {type(e).__name__}",
        )


def check_luma() -> ProviderResult:
    key = os.environ.get("LUMAAI_API_KEY", "")
    if not key:
        return ProviderResult(
            name="Luma AI",
            type="video",
            status="no_key",
            status_code=None,
            free_tier="30 free credits",
            note="Set LUMAAI_API_KEY",
            get_key_url="https://lumalabs.ai/dream-machine/api/keys",
        )
    try:
        r = requests.get(
            "https://api.lumalabs.ai/dream-machine/v1/generations",
            headers={"Authorization": f"Bearer {key}"},
            timeout=TIMEOUT,
        )
        if r.status_code in (200, 204):
            return ProviderResult(
                name="Luma AI",
                type="video",
                status="active",
                status_code=r.status_code,
                free_tier="30 free credits",
                note="Key valid",
            )
        return ProviderResult(
            name="Luma AI",
            type="video",
            status="error",
            status_code=r.status_code,
            free_tier="30 free credits",
            note=f"HTTP {r.status_code}",
        )
    except Exception as e:
        return ProviderResult(
            name="Luma AI",
            type="video",
            status="error",
            status_code=None,
            free_tier="30 free credits",
            note=f"Connection error: {type(e).__name__}",
        )


# All check functions in order
ALL_CHECKS = [
    # Image providers
    check_pollinations_image,
    check_together_ai,
    check_google_gemini,
    check_cloudflare,
    check_huggingface,
    check_fal_ai,
    check_nvidia_nim,
    check_fireworks,
    check_deepinfra,
    check_novita,
    check_stability,
    # Video providers
    check_pollinations_video,
    check_huggingface_wan,
    check_fal_video,
    check_minimax,
    check_luma,
]


def status_icon(status: str) -> str:
    if status == "active":
        return f"{GREEN}✓ ACTIVE{RESET}"
    elif status == "no_key":
        return f"{YELLOW}○ NO KEY{RESET}"
    else:
        return f"{RED}✗ ERROR {RESET}"


def print_table(results: list) -> None:
    col_provider = 24
    col_type = 7
    col_status = 8
    col_free = 14
    col_note = 40

    top = (
        f"┌{'─' * (col_provider + 2)}┬{'─' * (col_type + 2)}"
        f"┬{'─' * (col_status + 2)}┬{'─' * (col_free + 2)}"
        f"┬{'─' * (col_note + 2)}┐"
    )
    divider = (
        f"├{'─' * (col_provider + 2)}┼{'─' * (col_type + 2)}"
        f"┼{'─' * (col_status + 2)}┼{'─' * (col_free + 2)}"
        f"┼{'─' * (col_note + 2)}┤"
    )
    section_div = (
        f"├{'═' * (col_provider + 2)}╪{'═' * (col_type + 2)}"
        f"╪{'═' * (col_status + 2)}╪{'═' * (col_free + 2)}"
        f"╪{'═' * (col_note + 2)}┤"
    )
    bottom = (
        f"└{'─' * (col_provider + 2)}┴{'─' * (col_type + 2)}"
        f"┴{'─' * (col_status + 2)}┴{'─' * (col_free + 2)}"
        f"┴{'─' * (col_note + 2)}┘"
    )

    def section_header_row(title: str) -> str:
        total_inner = col_provider + col_type + col_status + col_free + col_note + 4 * 3
        content = f" {BOLD}{CYAN}{title}{RESET}"
        # Pad with spaces to fill the row (color codes don't count for width)
        pad = total_inner - len(title) - 1
        return f"│{content}{' ' * pad}│"

    def data_row(r: ProviderResult) -> str:
        icon = status_icon(r.status)
        note = r.note
        if r.status == "no_key" and r.get_key_url:
            note = f"{r.note} — {r.get_key_url}"
        # Truncate to col_note chars for display
        if len(note) > col_note:
            note = note[: col_note - 1] + "…"

        # Color the note
        if r.status == "active":
            colored_note = f"{GREEN}{note:<{col_note}}{RESET}"
        elif r.status == "no_key":
            colored_note = f"{YELLOW}{note:<{col_note}}{RESET}"
        else:
            colored_note = f"{RED}{note:<{col_note}}{RESET}"

        type_label = r.type.upper()
        # icon already has embedded color + RESET; pad to fixed width (no color in padding)
        icon_pad = " " * (col_status - 8)  # 8 = len("✓ ACTIVE") etc.

        return (
            f"│ {r.name:<{col_provider}} │ {type_label:<{col_type}} "
            f"│ {icon}{icon_pad} │ {r.free_tier:<{col_free}} "
            f"│ {colored_note} │"
        )

    image_results = [r for r in results if r.type == "image"]
    video_results = [r for r in results if r.type == "video"]

    print(top)
    # Image section
    print(section_header_row("IMAGE PROVIDERS"))
    print(section_div)
    for i, r in enumerate(image_results):
        print(data_row(r))
        if i < len(image_results) - 1:
            print(divider)
    # Video section
    print(section_div)
    print(section_header_row("VIDEO PROVIDERS"))
    print(section_div)
    for i, r in enumerate(video_results):
        print(data_row(r))
        if i < len(video_results) - 1:
            print(divider)
    print(bottom)


def print_summary(results: list) -> None:
    image_active = [r for r in results if r.type == "image" and r.status == "active"]
    image_no_key = [r for r in results if r.type == "image" and r.status == "no_key"]
    image_error = [r for r in results if r.type == "image" and r.status == "error"]

    video_active = [r for r in results if r.type == "video" and r.status == "active"]
    video_no_key = [r for r in results if r.type == "video" and r.status == "no_key"]
    video_error = [r for r in results if r.type == "video" and r.status == "error"]

    image_total = len([r for r in results if r.type == "image"])
    video_total = len([r for r in results if r.type == "video"])

    print()
    print(f"{BOLD}{'─' * 60}{RESET}")
    print(f"{BOLD}  SUMMARY{RESET}")
    print(f"{'─' * 60}")
    print(
        f"  {CYAN}Image providers:{RESET}  "
        f"{GREEN}{len(image_active)} active{RESET} / "
        f"{YELLOW}{len(image_no_key)} no key{RESET} / "
        f"{RED}{len(image_error)} error{RESET} "
        f"{DIM}(of {image_total} total){RESET}"
    )
    print(
        f"  {CYAN}Video providers:{RESET}  "
        f"{GREEN}{len(video_active)} active{RESET} / "
        f"{YELLOW}{len(video_no_key)} no key{RESET} / "
        f"{RED}{len(video_error)} error{RESET} "
        f"{DIM}(of {video_total} total){RESET}"
    )
    print()

    total_active = len(image_active) + len(video_active)
    if total_active == 0:
        print(f"  {RED}Not ready to generate — no active providers found.{RESET}")
    elif total_active < 3:
        print(
            f"  {YELLOW}Partially ready — {total_active} provider(s) active. "
            f"Add more API keys for full coverage.{RESET}"
        )
    else:
        print(
            f"  {GREEN}Ready to generate! "
            f"{total_active} provider(s) active across image + video.{RESET}"
        )

    if image_active:
        names = ", ".join(r.name for r in image_active)
        print(f"\n  {GREEN}Active image:{RESET} {names}")
    if video_active:
        names = ", ".join(r.name for r in video_active)
        print(f"  {GREEN}Active video:{RESET} {names}")

    missing_keys = []
    for r in results:
        if r.status == "no_key":
            env_hint = r.note.replace("Set ", "").strip()
            missing_keys.append(env_hint)
    if missing_keys:
        print(f"\n  {DIM}Missing keys: {', '.join(missing_keys)}{RESET}")

    print(f"{'─' * 60}")


def main() -> None:
    print()
    print(f"{BOLD}{CYAN}  AI Provider Health Check{RESET}")
    print(f"  {DIM}Running {len(ALL_CHECKS)} checks in parallel...{RESET}")
    print()

    start = time.time()
    results_map: dict = {}

    with ThreadPoolExecutor(max_workers=len(ALL_CHECKS)) as executor:
        future_to_name = {executor.submit(fn): fn.__name__ for fn in ALL_CHECKS}
        for future in as_completed(future_to_name):
            fn_name = future_to_name[future]
            try:
                result = future.result()
                results_map[fn_name] = result
            except Exception as e:
                results_map[fn_name] = ProviderResult(
                    name=fn_name,
                    type="unknown",
                    status="error",
                    status_code=None,
                    free_tier="",
                    note=f"Unexpected error: {e}",
                )

    elapsed = time.time() - start

    # Preserve original declaration order
    results = [
        results_map[fn.__name__]
        for fn in ALL_CHECKS
        if fn.__name__ in results_map
    ]

    print_table(results)
    print_summary(results)
    print(f"\n  {DIM}Completed in {elapsed:.1f}s{RESET}\n")


if __name__ == "__main__":
    main()
