# NVIDIA NIM Free Image & Video Generator

Generate images and videos for **free** using NVIDIA's NIM API (no credit card needed).

- **Image generation** — FLUX.1-schnell (fastest, high quality)
- **Video generation** — Stable Video Diffusion (animates any image into a short video)

---

## Setup (5 minutes)

### 1. Get a free API key
1. Go to **[build.nvidia.com](https://build.nvidia.com)**
2. Sign up for a free NVIDIA Developer account
3. Click any model → **"Get API Key"**
4. Copy your key (starts with `nvapi-`)

> Free tier: **1,000 credits** on signup, no credit card required.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your API key
```bash
export NVIDIA_API_KEY=nvapi-xxxx
```

---

## Usage

### Generate an image
```bash
python generate.py image "a futuristic city at night, neon lights, cinematic"
# Saves: output_image.jpg
```

### Animate an image into a video
```bash
python generate.py video output_image.jpg
# Saves: output_video.mp4  (~25 frames, 576x1024)
```

### Generate image + animate it in one command
```bash
python generate.py both "a golden retriever running on a beach at sunset"
# Saves: output_image.jpg + output_video.mp4
```

---

## Free Models Used

| Task | Model | Credits per call |
|------|-------|-----------------|
| Image | FLUX.1-schnell | ~1 credit |
| Video | Stable Video Diffusion | ~5 credits |

With 1,000 free credits you get roughly:
- ~500 images, OR
- ~200 image+video pairs

---

## Tips

- For **more motion** in videos: edit `motion_bucket_id` (1–255, default 127)
- For **different image sizes**: pass `width`/`height` (must be multiples of 8, max 1024)
- For **higher quality images** (slower): use `flux.1-dev` — change the model URL in `generate.py` and set `steps=20`
