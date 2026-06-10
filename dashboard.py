"""
AI Media Suite — Interactive Dashboard
Run this to control all agents from one place.

  python dashboard.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.text import Text
    from rich.rule import Rule
    from rich import box
    RICH = True
except ImportError:
    RICH = False

# ── Keys read from env ────────────────────────────────────────────────────────
KEYS = {
    "ANTHROPIC_API_KEY":  {"label": "Anthropic (Claude brain)",    "url": "console.anthropic.com",           "free": "Free $5 credit",       "required": True},
    "TOGETHER_API_KEY":   {"label": "Together AI (free FLUX ∞)",   "url": "together.ai",                     "free": "FREE forever",         "required": False},
    "GOOGLE_API_KEY":     {"label": "Google Gemini (images)",       "url": "aistudio.google.com",             "free": "500 img/day FREE",     "required": False},
    "CF_API_TOKEN":       {"label": "Cloudflare Workers AI",        "url": "cloudflare.com",                  "free": "~50 img/day FREE",     "required": False},
    "HF_TOKEN":           {"label": "HuggingFace (img + video)",    "url": "huggingface.co/settings/tokens",  "free": "Free tier",            "required": False},
    "FAL_KEY":            {"label": "fal.ai (img + video)",         "url": "fal.ai",                          "free": "$20 signup",           "required": False},
    "NVIDIA_API_KEY":     {"label": "NVIDIA NIM (FLUX)",            "url": "build.nvidia.com",                "free": "1,000 free credits",   "required": False},
    "FIREWORKS_API_KEY":  {"label": "Fireworks AI (FLUX FP8)",      "url": "fireworks.ai",                    "free": "$1 signup",            "required": False},
    "DEEPINFRA_TOKEN":    {"label": "DeepInfra (FLUX family)",      "url": "deepinfra.com",                   "free": "$5 signup",            "required": False},
    "NOVITA_API_KEY":     {"label": "Novita AI (Kling video)",      "url": "novita.ai",                       "free": "$0.50 + video",        "required": False},
    "MINIMAX_API_KEY":    {"label": "MiniMax / Hailuo (video)",     "url": "platform.minimax.io",             "free": "Trial credits",        "required": False},
    "LUMAAI_API_KEY":     {"label": "Luma Dream Machine (video)",   "url": "lumalabs.ai",                     "free": "Paid only",            "required": False},
}

OUTPUT_DIRS = ["media_output", "video_output", "agent_output"]

console = Console() if RICH else None


# ── Helpers ───────────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def _print(msg, style=""):
    if RICH:
        console.print(msg, style=style)
    else:
        print(msg)


def _input(prompt):
    if RICH:
        return Prompt.ask(prompt)
    return input(f"{prompt}: ")


def _confirm(prompt):
    if RICH:
        return Confirm.ask(prompt)
    return input(f"{prompt} [y/N]: ").strip().lower() == "y"


def banner():
    if RICH:
        console.print()
        console.print(Panel.fit(
            "[bold cyan]AI Media Suite[/bold cyan]\n"
            "[dim]Claude Opus 4.8 · 9 Image Providers · 6 Video Providers[/dim]\n"
            "[dim]Images · Videos · Captions · Hashtags · Music · Schedule[/dim]",
            border_style="cyan",
            padding=(1, 4),
        ))
        console.print()
    else:
        print("\n" + "="*60)
        print("  AI Media Suite Dashboard")
        print("  Claude Opus + 9 Image + 6 Video Providers")
        print("="*60 + "\n")


# ── Provider status ────────────────────────────────────────────────────────────

def show_provider_status():
    active_img = 0
    active_vid = 0
    missing_required = []

    if RICH:
        table = Table(title="Provider Status", box=box.ROUNDED, border_style="cyan", show_lines=False)
        table.add_column("Provider", style="white", min_width=28)
        table.add_column("Type", style="dim", min_width=8)
        table.add_column("Status", min_width=10)
        table.add_column("Free Tier", style="dim")
        table.add_column("Get Key", style="dim blue")
    else:
        rows = []

    img_providers = ["ANTHROPIC_API_KEY", "TOGETHER_API_KEY", "GOOGLE_API_KEY",
                     "CF_API_TOKEN", "HF_TOKEN", "FAL_KEY", "NVIDIA_API_KEY",
                     "FIREWORKS_API_KEY", "DEEPINFRA_TOKEN"]
    vid_providers  = ["HF_TOKEN", "FAL_KEY", "NOVITA_API_KEY", "MINIMAX_API_KEY", "LUMAAI_API_KEY"]

    for key, info in KEYS.items():
        val = os.environ.get(key, "")
        is_set = bool(val)
        is_img = key in img_providers
        is_vid = key in vid_providers
        ptype  = "img+vid" if (is_img and is_vid) else ("video" if is_vid else "image")

        if is_set:
            status = "[green]✓ ACTIVE[/green]" if RICH else "✓ ACTIVE"
            if is_img: active_img += 1
            if is_vid: active_vid += 1
        elif info["required"]:
            status = "[bold red]✗ REQUIRED[/bold red]" if RICH else "✗ REQUIRED"
            missing_required.append(key)
        else:
            status = "[yellow]○ NO KEY[/yellow]" if RICH else "○ NO KEY"

        if RICH:
            table.add_row(info["label"], ptype, status, info["free"], info["url"])
        else:
            rows.append((info["label"], ptype, "ACTIVE" if is_set else "NO KEY", info["free"]))

    if RICH:
        console.print(table)
        console.print()
        console.print(f"  Image providers active: [cyan]{active_img}[/cyan]  |  Video providers active: [cyan]{active_vid}[/cyan]")
        if missing_required:
            console.print(f"  [bold red]Missing required key: ANTHROPIC_API_KEY[/bold red] — get free $5 at [blue]console.anthropic.com[/blue]")
        else:
            console.print(f"  [green]✓ Ready to generate[/green]  (Pollinations always works — no key needed for images)")
        console.print()
    else:
        for r in rows:
            print(f"  {r[1]:8} {r[2]:10} {r[0]}")
        print(f"\n  Active image providers: {active_img}")
        print(f"  Active video providers: {active_vid}\n")

    return len(missing_required) == 0


# ── Output files viewer ────────────────────────────────────────────────────────

def show_outputs():
    files = []
    for d in OUTPUT_DIRS:
        p = Path(d)
        if p.exists():
            for f in sorted(p.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                files.append(f)

    if not files:
        _print("  No output files yet. Run an agent to generate content.", "dim")
        return

    if RICH:
        table = Table(box=box.SIMPLE, show_header=True, border_style="dim")
        table.add_column("#",        style="dim",   width=4)
        table.add_column("File",     style="white", min_width=35)
        table.add_column("Type",     style="cyan",  width=8)
        table.add_column("Size",     style="dim",   width=10)
        table.add_column("Created",  style="dim",   width=16)
        for i, f in enumerate(files, 1):
            size = f.stat().st_size
            size_str = f"{size/1024:.0f} KB" if size > 1024 else f"{size} B"
            ts = datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d %H:%M")
            ext = f.suffix.lower().lstrip(".")
            table.add_row(str(i), str(f), ext, size_str, ts)
        console.print(table)
    else:
        for i, f in enumerate(files, 1):
            print(f"  {i:2}. {f}")


# ── Run agent ─────────────────────────────────────────────────────────────────

def run_agent(script: str, args: list):
    cmd = [sys.executable, script] + args
    _print(f"\n  Running: [cyan]{' '.join(cmd)}[/cyan]\n" if RICH else f"\n  Running: {' '.join(cmd)}\n")

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            print(line, end="", flush=True)
        proc.wait()
        return proc.returncode == 0
    except KeyboardInterrupt:
        proc.terminate()
        _print("\n  [yellow]Interrupted.[/yellow]" if RICH else "\n  Interrupted.")
        return False
    except Exception as e:
        _print(f"  [red]Error: {e}[/red]" if RICH else f"  Error: {e}")
        return False


# ── Setup guide ───────────────────────────────────────────────────────────────

def show_setup_guide():
    if RICH:
        console.print(Panel(
            "[bold]Step 1 — Required (Claude brain)[/bold]\n"
            "  • Go to [blue]console.anthropic.com[/blue]\n"
            "  • Sign up → get free $5 credit (no credit card)\n"
            "  • Copy your key → [cyan]set ANTHROPIC_API_KEY=sk-ant-xxx[/cyan]\n\n"

            "[bold]Step 2 — Free FLUX images forever[/bold]\n"
            "  • Go to [blue]together.ai[/blue]\n"
            "  • Sign up free → API → copy key\n"
            "  • [cyan]set TOGETHER_API_KEY=xxx[/cyan]\n"
            "  • Result: unlimited FLUX.1-schnell images at $0.00/image\n\n"

            "[bold]Step 3 — 500 free images/day (Google)[/bold]\n"
            "  • Go to [blue]aistudio.google.com[/blue]\n"
            "  • Sign in with Google → Get API key → copy\n"
            "  • [cyan]set GOOGLE_API_KEY=xxx[/cyan]\n\n"

            "[bold]Step 4 — Free image + video (HuggingFace)[/bold]\n"
            "  • Go to [blue]huggingface.co/settings/tokens[/blue]\n"
            "  • Create token → copy\n"
            "  • [cyan]set HF_TOKEN=hf_xxx[/cyan]\n"
            "  • Unlocks: FLUX images + Wan2.2 video generation\n\n"

            "[bold]Step 5 — $20 credits for premium video (fal.ai)[/bold]\n"
            "  • Go to [blue]fal.ai[/blue] → sign up with business email\n"
            "  • API keys → copy\n"
            "  • [cyan]set FAL_KEY=xxx[/cyan]\n"
            "  • Unlocks: Kling video, CogVideoX, Wan, MiniMax i2v\n\n"

            "[bold]Step 6 — Kling video (Novita AI)[/bold]\n"
            "  • Go to [blue]novita.ai[/blue] → sign up → $0.50 free credits\n"
            "  • [cyan]set NOVITA_API_KEY=xxx[/cyan]\n"
            "  • Unlocks: Kling 3.0 text-to-video + image-to-video\n\n"

            "[bold]Windows (set in PowerShell):[/bold]\n"
            "  [cyan]$env:ANTHROPIC_API_KEY='sk-ant-xxx'[/cyan]\n"
            "  [cyan]$env:TOGETHER_API_KEY='xxx'[/cyan]\n\n"

            "[bold]Mac/Linux:[/bold]\n"
            "  [cyan]export ANTHROPIC_API_KEY=sk-ant-xxx[/cyan]\n"
            "  [cyan]export TOGETHER_API_KEY=xxx[/cyan]",
            title="Setup Guide",
            border_style="green",
            padding=(1, 2),
        ))
    else:
        print("\nSETUP GUIDE")
        print("-" * 40)
        print("1. ANTHROPIC_API_KEY → console.anthropic.com (free $5)")
        print("2. TOGETHER_API_KEY  → together.ai (free FLUX forever)")
        print("3. GOOGLE_API_KEY    → aistudio.google.com (500/day free)")
        print("4. HF_TOKEN          → huggingface.co/settings/tokens")
        print("5. FAL_KEY           → fal.ai ($20 signup)")
        print("6. NOVITA_API_KEY    → novita.ai ($0.50 + Kling video)")
        print()


# ── Cheat sheet ───────────────────────────────────────────────────────────────

def show_cheatsheet():
    if RICH:
        console.print(Panel(
            "[bold cyan]media_agent.py[/bold cyan] — Full campaign: images + video + captions + hashtags + music + schedule\n"
            "  [cyan]python media_agent.py \"your brief here\"[/cyan]\n\n"

            "[bold cyan]video_agent.py[/bold cyan] — Dedicated video: T2V, I2V, storyboard, shot script\n"
            "  [cyan]python video_agent.py \"30s TikTok reel for luxury brand\"[/cyan]\n"
            "  [cyan]python video_agent.py \"animate this\" --image photo.jpg[/cyan]\n\n"

            "[bold cyan]agent.py[/bold cyan] — Simple image-only agent with brand strategy\n"
            "  [cyan]python agent.py \"3 Instagram posts for handmade soap brand\"[/cyan]\n\n"

            "[bold cyan]providers_check.py[/bold cyan] — Test all providers, show what's working\n"
            "  [cyan]python providers_check.py[/cyan]\n\n"

            "[bold cyan]generate.py[/bold cyan] — Quick single image (no AI brain)\n"
            "  [cyan]python generate.py image \"a futuristic city at night\"[/cyan]\n\n"

            "[bold]Output folders:[/bold]\n"
            "  media_output/   → media_agent.py results\n"
            "  video_output/   → video_agent.py results\n"
            "  agent_output/   → agent.py results\n\n"

            "[bold]Brief tips for best results:[/bold]\n"
            "  • Include platform: \"for Instagram\" / \"for TikTok\"\n"
            "  • Include tone: \"luxury\" / \"raw/authentic\" / \"playful\"\n"
            "  • Include goal: \"trust\" / \"sales\" / \"brand awareness\"\n"
            "  • Be specific: product, audience, key message",
            title="Quick Reference",
            border_style="blue",
            padding=(1, 2),
        ))
    else:
        print("\nQUICK REFERENCE")
        print("  python media_agent.py \"brief\" — full campaign")
        print("  python video_agent.py \"brief\"  — video only")
        print("  python providers_check.py       — check providers")
        print()


# ── Main menu ─────────────────────────────────────────────────────────────────

def main_menu():
    while True:
        clear()
        banner()
        ready = show_provider_status()

        if RICH:
            console.print(Rule(style="dim"))
            console.print()
            options = [
                ("[1]", "Run Media Agent",    "Full campaign: images + video + captions + hashtags + schedule"),
                ("[2]", "Run Video Agent",     "Dedicated video: T2V, I2V, storyboard, animated clips"),
                ("[3]", "Quick Image",         "Single image from a prompt (fast, no AI brain)"),
                ("[4]", "Check Providers",     "Test all 16 providers, see what's working"),
                ("[5]", "View Output Files",   "Browse all generated images and videos"),
                ("[6]", "Setup Guide",         "Step-by-step: which keys to get and where"),
                ("[7]", "Quick Reference",     "All commands and brief-writing tips"),
                ("[0]", "Exit",                ""),
            ]
            for num, name, desc in options:
                if desc:
                    console.print(f"  [bold cyan]{num}[/bold cyan]  [white]{name:<22}[/white] [dim]{desc}[/dim]")
                else:
                    console.print(f"  [bold cyan]{num}[/bold cyan]  [white]{name}[/white]")
            console.print()
        else:
            print("  [1] Run Media Agent")
            print("  [2] Run Video Agent")
            print("  [3] Quick Image")
            print("  [4] Check Providers")
            print("  [5] View Output Files")
            print("  [6] Setup Guide")
            print("  [7] Quick Reference")
            print("  [0] Exit\n")

        choice = _input("[bold cyan]Choose[/bold cyan]" if RICH else "Choose").strip()

        if choice == "1":
            clear()
            banner()
            if not ready:
                _print("  [red]ANTHROPIC_API_KEY is required. Run option [6] for setup guide.[/red]" if RICH else "  ANTHROPIC_API_KEY required. See option 6.")
                _input("Press Enter to continue")
                continue
            brief = _input("[cyan]Your brief[/cyan]" if RICH else "Your brief")
            if brief.strip():
                run_agent("media_agent.py", [brief])
            _input("\n  [dim]Press Enter to return to menu[/dim]" if RICH else "\nPress Enter to continue")

        elif choice == "2":
            clear()
            banner()
            if not ready:
                _print("  [red]ANTHROPIC_API_KEY is required.[/red]" if RICH else "  ANTHROPIC_API_KEY required.")
                _input("Press Enter to continue")
                continue
            brief = _input("[cyan]Video brief[/cyan]" if RICH else "Video brief")
            if brief.strip():
                use_image = _confirm("Animate a specific image?")
                if use_image:
                    img = _input("Image path")
                    run_agent("video_agent.py", [brief, "--image", img])
                else:
                    run_agent("video_agent.py", [brief])
            _input("\n  [dim]Press Enter to return to menu[/dim]" if RICH else "\nPress Enter to continue")

        elif choice == "3":
            clear()
            banner()
            prompt = _input("[cyan]Image prompt[/cyan]" if RICH else "Image prompt")
            if prompt.strip():
                run_agent("generate.py", ["image", prompt])
            _input("\n  [dim]Press Enter to return to menu[/dim]" if RICH else "\nPress Enter to continue")

        elif choice == "4":
            clear()
            banner()
            run_agent("providers_check.py", [])
            _input("\n  [dim]Press Enter to return to menu[/dim]" if RICH else "\nPress Enter to continue")

        elif choice == "5":
            clear()
            banner()
            _print("  [bold]Generated files:[/bold]\n" if RICH else "\nGenerated files:")
            show_outputs()
            _input("\n  [dim]Press Enter to return to menu[/dim]" if RICH else "\nPress Enter to continue")

        elif choice == "6":
            clear()
            banner()
            show_setup_guide()
            _input("\n  [dim]Press Enter to return to menu[/dim]" if RICH else "\nPress Enter to continue")

        elif choice == "7":
            clear()
            banner()
            show_cheatsheet()
            _input("\n  [dim]Press Enter to return to menu[/dim]" if RICH else "\nPress Enter to continue")

        elif choice == "0":
            _print("\n  [dim]Goodbye.[/dim]\n" if RICH else "\nGoodbye.\n")
            break

        else:
            _print("  [yellow]Invalid choice.[/yellow]" if RICH else "  Invalid choice.")
            time.sleep(0.8)


if __name__ == "__main__":
    # Install rich if missing
    try:
        import rich
    except ImportError:
        print("Installing rich for better UI...")
        subprocess.run([sys.executable, "-m", "pip", "install", "rich", "-q"])
        print("Done. Restarting...\n")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    main_menu()
