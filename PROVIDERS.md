# AI Image & Video Generation — Free Provider Knowledge Base
*Deep-researched June 2026. Update this file whenever providers change their terms.*

---

## TL;DR — Best Free Options Right Now

| Priority | Provider | What's Free | Key Required? | Images | Video |
|---|---|---|---|---|---|
| 1 | **Pollinations.ai** | Unlimited (rate-limited) | **No** | FLUX, Wan, GPT-Image | Veo, Seedance, Wan |
| 2 | **Together AI** | FLUX.1-schnell FREE endpoint forever | Yes (free account) | FLUX family | No |
| 3 | **Google Gemini** | 500 images/day | Yes (free, no CC) | Gemini Flash Image | No |
| 4 | **Cloudflare Workers AI** | ~20-50 images/day | Yes (free account) | SDXL, DreamShaper | No |
| 5 | **HuggingFace** | Free tier (rate-limited) | Yes (free) | FLUX, thousands | Wan2.2 (limited) |
| 6 | **fal.ai** | $20 signup credits | Yes (free signup) | FLUX, SD3.5, Kling | Wan, CogVideoX, Kling, Veo3 |
| 7 | **DeepInfra** | $5 signup credits | Yes (CC likely) | FLUX family | No |
| 8 | **Replicate** | Small trial runs | Yes (free) | FLUX, SDXL | AnimateDiff, Wan2.2 |
| 9 | **Fireworks AI** | $1 signup credits | Yes (free) | FLUX schnell/dev FP8 | No |
| 10 | **Novita AI** | $0.50 signup credits | Yes (free) | FLUX, SDXL, 200+ | Kling 3.0, SVD |
| 11 | **NVIDIA NIM** | 1,000 credits signup | Yes (free) | FLUX.1-schnell/dev | Deprecated |
| 12 | **Stability AI** | 25 credits (~8 images) | Yes (free) | SD Core, SD 3.5 | SVD (limited) |
| 13 | **Segmind** | **None** (min $10 deposit) | Yes + CC | FLUX family, SDXL | Seedance 2.0 |

---

## Detailed Provider Reference

---

### 1. Pollinations.ai ⭐ (Zero Setup — Use This First)

**Why it's special:** No API key, no signup, no credit card. Just call the URL.

**Base URL:** `https://gen.pollinations.ai`

**Image endpoints:**
```
GET  https://image.pollinations.ai/prompt/{url-encoded-prompt}?width=1024&height=1024&model=flux&nologo=true
POST https://gen.pollinations.ai/v1/images/generations   (OpenAI-compatible)
```

**Video endpoints:**
```
GET  https://video.pollinations.ai/prompt/{url-encoded-prompt}
POST https://gen.pollinations.ai/v1/videos/generations
```

**Image models (free):** `flux`, `wan-image`, `wan-image-pro`, `seedream`, `seedream-pro`, `gptimage`, `gpt-image-2`, `kontext`, `nanobanana`, `qwen-image`, `grok-imagine`, `seedream5`, `nova-canvas`

**Video models (free):** `veo`, `seedance`, `seedance-pro`, `wan`, `nova-reel`

**Authentication:** None for basic use. Optional: `Authorization: Bearer sk_xxx` for higher limits.

**Rate limits:** Anonymous use is rate-limited (HTTP 429 + Retry-After). Use a free account key for higher throughput.

**Python usage:**
```python
import requests, urllib.parse
prompt = "aerial view of farmers market at golden hour"
url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&model=flux&nologo=true"
img_bytes = requests.get(url, timeout=90).content

video_url = f"https://video.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
video_bytes = requests.get(video_url, timeout=120).content
```

**Caveats:** Rate limits hit under heavy use. Video quality varies. Best for prototyping and lighter production use.

---

### 2. Together AI ⭐ (Free FLUX Forever)

**Why it's special:** Permanently free FLUX.1-schnell endpoint — $0.00 per image.

**Free tier:** $25 signup credits + `FLUX.1-schnell-Free` model is permanently $0.00/image.

**Base URL:** `https://api.together.xyz/v1`

**Image endpoint:** `POST /images/generations`

**Free model:** `black-forest-labs/FLUX.1-schnell-Free` — costs $0.00

**Paid models (use signup credits):** FLUX.1-dev, FLUX.1-pro, FLUX1.1-pro, FLUX.1-Kontext-dev

**Auth:** `Authorization: Bearer $TOGETHER_API_KEY` (free account at together.ai)

**Python SDK:** `pip install together`
```python
from together import Together
client = Together()  # reads TOGETHER_API_KEY env var
response = client.images.generate(
    prompt="a market stall at golden hour",
    model="black-forest-labs/FLUX.1-schnell-Free",
    n=1,
)
# response.data[0].b64_json or response.data[0].url
```

**No video generation** on Together AI.

---

### 3. Google Gemini Image API (500 Free Images/Day)

**Free tier:** 500 images/day on Gemini 2.5 Flash Image model — no credit card needed.

**Get API key:** https://aistudio.google.com (free Google account)

**Base URL:** `https://generativelanguage.googleapis.com/v1beta`

**Python SDK:** `pip install google-generativeai`
```python
import google.generativeai as genai
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")
response = model.generate_content(
    ["Generate an image of: " + prompt],
    generation_config={"response_modalities": ["IMAGE", "TEXT"]}
)
```

**Output:** 1024×1024, JPEG. Rate limit: ~2 images/min on free tier.

---

### 4. Cloudflare Workers AI (~20-50 Free Images/Day)

**Free tier:** 10,000 Neurons/day (resets 00:00 UTC). Images cost ~200-500 neurons each.

**Get account:** Free at cloudflare.com (no credit card for free tier).

**Base URL:** `https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/`

**Image models:** `@cf/stabilityai/stable-diffusion-xl-base-1.0`, `@cf/lykon/dreamshaper-8`, `@cf/bytedance/stable-diffusion-xl-lightning`

**Auth:** `Authorization: Bearer $CF_API_TOKEN`

**Python usage:**
```python
import requests
url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
response = requests.post(url, headers=headers, json={"prompt": prompt})
img_bytes = response.content  # returns raw PNG
```

---

### 5. HuggingFace Inference API (Free Tier)

**Free tier:** Free serverless inference (rate-limited, no published limits). PRO = $9/month for higher limits + 2M Inference Provider credits.

**Get token:** https://huggingface.co/settings/tokens (free account)

**Base URL:** `https://api-inference.huggingface.co/models/`

**Good free image models:** `black-forest-labs/FLUX.1-schnell`, `black-forest-labs/FLUX.1-dev`

**Video:** `Wan-AI/Wan2.2-TI2V-5B` via Inference Providers

**Auth:** `Authorization: Bearer $HF_TOKEN`

**Python SDK:** `pip install huggingface_hub`
```python
from huggingface_hub import InferenceClient
client = InferenceClient(api_key=os.environ["HF_TOKEN"])
image = client.text_to_image(prompt, model="black-forest-labs/FLUX.1-schnell")
image.save("output.jpg")
# Video:
video = client.text_to_video(prompt, model="Wan-AI/Wan2.2-TI2V-5B")
```

---

### 6. fal.ai ($20 Signup Credits)

**Free tier:** $20 one-time signup credits (business email required, ~30-90 day expiry).

**Why it's powerful:** 1,000+ models including Veo 3.1, Sora 2, Kling 3.0, Wan, CogVideoX.

**Base URL:** `https://fal.run/`

**Auth:** `Authorization: Key $FAL_KEY`

**Python SDK:** `pip install fal-client`
```python
import fal_client
result = fal_client.run(
    "fal-ai/flux/schnell",
    arguments={"prompt": prompt, "image_size": "square_hd"}
)
# result["images"][0]["url"]

# Video (image-to-video):
result = fal_client.run(
    "fal-ai/kling-video/v2.1/master/image-to-video",
    arguments={"image_url": img_url, "prompt": motion_prompt}
)
```

**Key video models via fal.ai:** `fal-ai/cogvideox-5b`, `fal-ai/kling-video/v2.1/master/text-to-video`, `fal-ai/minimax/hailuo-02/standard/image-to-video`, `fal-ai/pika/v2.2/image-to-video`

---

### 7. DeepInfra ($5 Signup Credits)

**Free tier:** $5 signup credits (credit card may be required for verification).

**Base URL:** `https://api.deepinfra.com/v1/openai` (OpenAI-compatible)

**Image models:** FLUX.1-schnell, FLUX.1-dev, FLUX-pro, FLUX-1.1-pro, FLUX.1-Kontext-dev

**Auth:** `Authorization: Bearer $DEEPINFRA_TOKEN`

**Python:** Uses `openai` SDK with custom base_url
```python
from openai import OpenAI
client = OpenAI(api_key=os.environ["DEEPINFRA_TOKEN"], base_url="https://api.deepinfra.com/v1/openai")
response = client.images.generate(model="black-forest-labs/FLUX-1-schnell", prompt=prompt, size="1024x1024")
```

---

### 8. Replicate (Small Free Trial)

**Free tier:** Small number of free predictions on new account. No ongoing free quota.

**Base URL:** `https://api.replicate.com/v1`

**Auth:** `Authorization: Bearer $REPLICATE_API_TOKEN`

**Python SDK:** `pip install replicate`
```python
import replicate
output = replicate.run("black-forest-labs/flux-schnell", input={"prompt": prompt})
# output is a list of file URLs
```

**Video:** `lucataco/animate-diff` (~$0.07/run), Wan 2.2, community models.

**MCP server (OFFICIAL):** `mcp.replicate.com` — add to Claude Code environment settings.

---

### 9. Fireworks AI ($1 Signup Credits)

**Free tier:** $1 signup credits (~714 images at schnell pricing).

**Base URL:** `https://api.fireworks.ai/inference/v1`

**Image endpoint:** `POST /workflows/accounts/fireworks/models/flux-1-schnell-fp8/text_to_image`

**Auth:** `Authorization: Bearer $FIREWORKS_API_KEY` + `Accept: image/jpeg`

**Python SDK:** `pip install fireworks-ai`

---

### 10. Novita AI ($0.50 Signup Credits + Video)

**Free tier:** $0.50 signup credits. Notable for having Kling 3.0 video API.

**Base URL:** `https://api.novita.ai/v3`

**Image endpoint (async):** `POST /async/txt2img`
**Video endpoint (async):** `POST /async/txt2video-kling-v3.0-std`

**Auth:** `Authorization: Bearer $NOVITA_API_KEY`

**Note:** Official Python SDK archived May 2026. Use OpenAI-compatible endpoint or direct requests.

---

### 11. NVIDIA NIM (1,000 Free Credits)

**Free tier:** 1,000 credits on signup at build.nvidia.com (no credit card).

**Base URL:** `https://ai.api.nvidia.com/v1`

**Image endpoint:** `POST /genai/black-forest-labs/flux.1-schnell`

**Auth:** `Authorization: Bearer $NVIDIA_API_KEY`

**Note:** Cloud environments block outbound calls to NVIDIA. Run locally.

---

### 12. Stability AI (25 Free Credits ≈ 8 Images)

**Free tier:** 25 credits on signup ($0.25 value). Essentially just a trial.

**Base URL:** `https://api.stability.ai`

**Key endpoints:** `/v2beta/stable-image/generate/core`, `/v2beta/stable-image/generate/sd3`

**Auth:** `Authorization: Bearer $STABILITY_API_KEY`

---

## MCP Servers for Claude Code

Add these to your environment at code.claude.com → Environment Settings → MCP Servers:

| Provider | Type | How to Add | Capabilities |
|---|---|---|---|
| **Replicate** | **OFFICIAL** | Remote: `https://mcp.replicate.com` | Images + video, 50,000+ models |
| **HuggingFace** | **OFFICIAL** | Remote: `https://huggingface.co/mcp` | FLUX images, Gradio Spaces, video via Spaces |
| **MiniMax/Hailuo** | **OFFICIAL** | `uvx minimax-mcp` | Video gen, TTS, image gen |
| **fal.ai** | Community | `uvx fal-ai-mcp-server` | 600+ models, image + video |
| **Kling AI** | Community | `npx mcp-kling` | Text/image-to-video, 13 tools |
| **Luma AI** | Community | `pip install mcp-luma` | Dream Machine video + image |
| **Stability AI** | Community | `npx mcp-server-stability-ai` | SD 3.5, search/replace, upscale |

---

## Video Generation — Best Free Options

### Via API (no consumer login needed):
1. **Pollinations.ai** — `GET https://video.pollinations.ai/prompt/{prompt}` — completely free, no key
2. **HuggingFace** — Wan2.2 via Inference Providers (free tier, limited)
3. **fal.ai** — CogVideoX, Wan, Kling ($20 signup credits)
4. **MiniMax/Hailuo** — 200 one-time trial credits via official API

### Via consumer apps (manual download only, no programmatic API):
1. **Arena.ai** — 3 free generations/day across Veo 3, Sora 2, Kling, etc.
2. **Kling AI** — 66 credits/day (consumer app only, not API)
3. **Luma Dream Machine** — ~80 credits/day (consumer app only)
4. **Pika Labs** — 80 credits/month (consumer app only)

---

## Open Source Models (Self-Host = Free Forever)

| Model | Type | License | Min VRAM | HuggingFace |
|---|---|---|---|---|
| FLUX.1-schnell | Image | Apache 2.0 | 8GB | black-forest-labs/FLUX.1-schnell |
| FLUX.1-dev | Image | FLUX non-commercial | 16GB | black-forest-labs/FLUX.1-dev |
| Wan2.1 / Wan2.2 | Video | Apache 2.0 | 24GB (14B) | Wan-Video/Wan2.1 |
| CogVideoX-5B | Video | Apache 2.0 | 16GB | THUDM/CogVideoX-5b |
| AnimateDiff | Video | Apache 2.0 | 8GB | guoyww/animatediff |
| Stable Video Diffusion | Video | Non-commercial | 16GB | stabilityai/stable-video-diffusion-img2vid |

---

## Required Environment Variables (set in your shell)

```bash
# Zero setup (no key needed):
# Pollinations.ai just works

# Free accounts (no credit card):
export TOGETHER_API_KEY=...        # together.ai — free FLUX forever
export HF_TOKEN=...                # huggingface.co/settings/tokens
export GOOGLE_API_KEY=...          # aistudio.google.com — 500 img/day free
export CF_API_TOKEN=...            # cloudflare.com — free account

# Signup credits:
export FAL_KEY=...                 # fal.ai — $20 on signup
export DEEPINFRA_TOKEN=...         # deepinfra.com — $5 on signup
export REPLICATE_API_TOKEN=...     # replicate.com — small free trial
export FIREWORKS_API_KEY=...       # fireworks.ai — $1 on signup
export NOVITA_API_KEY=...          # novita.ai — $0.50 on signup
export NVIDIA_API_KEY=...          # build.nvidia.com — 1,000 free credits
export STABILITY_API_KEY=...       # platform.stability.ai — 25 free credits

# Video-specific:
export LUMAAI_API_KEY=...          # lumalabs.ai — paid only
export KLING_ACCESS_KEY=...        # klingai.com — paid only
export KLING_SECRET_KEY=...        # klingai.com — paid only
export MINIMAX_API_KEY=...         # platform.minimax.io — trial credits

# For Claude Opus brain:
export ANTHROPIC_API_KEY=...       # console.anthropic.com — $5 free credit
```

---

*Last updated: June 2026 — Sources: fal.ai docs, together.ai blog, HF docs, Pollinations GitHub, MCP server repos, multiple verified aggregators. See agent research in session history for full sourcing.*
