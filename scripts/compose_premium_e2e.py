#!/usr/bin/env python3
"""
Premium e2e film — visuals/audio/content aligned to the real demo.

- Official Omnigent UI screenshots (Databricks / omnigent.ai)
- Accurate Protein Lab session UI (matches product chrome)
- Real Boltz GLP-1 CIF (premium all-atom spin)
- Real metrics from our run
- Real agent YAML excerpt
- ElevenLabs VO v2 (Alice) frame-synced
- Soft burned captions for key claims

Output: outputs/omnigent_glp1_hormone_e2e_demo.mp4
        outputs/FINAL_omnigent_glp1_demo.mp4
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "premium-film"
FRAMES = OUT / "frames"
VO_DIR = ROOT / "outputs" / "vo_v2"
ASSETS = ROOT / "docs" / "assets"
UI = ASSETS / "omnigent-ui"
W, H, FPS = 1920, 1080, 24

# Brand
BG = (10, 12, 20)
WHITE = (248, 248, 252)
MUTED = (155, 162, 185)
PURPLE = (124, 92, 255)
TEAL = (0, 212, 170)
PINK = (236, 72, 153)
YELLOW = (251, 191, 36)
GREEN = (52, 211, 153)

SEQ = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
METRICS = {
    "structure_confidence": 0.834,
    "complex_plddt": 0.897,
    "ptm": 0.581,
}


def font(size: int, bold: bool = False):
    cands = []
    if bold:
        cands += [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
        ]
    cands += [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in cands:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def ffprobe_dur(path: Path) -> float:
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(path),
            ],
            text=True,
        ).strip()
    )


def rrect(d, box, r, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def glow_canvas() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    g = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(g)
    d.ellipse([W // 2 - 520, H // 2 - 300, W // 2 + 520, H // 2 + 340], fill=(42, 22, 78))
    g = g.filter(ImageFilter.GaussianBlur(95))
    return Image.blend(img, g, 0.55)


def fit_cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    iw, ih = im.size
    s = max(tw / iw, th / ih)
    nw, nh = int(iw * s), int(ih * s)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    l, t = (nw - tw) // 2, (nh - th) // 2
    return im.crop((l, t, l + tw, t + th))


def fit_contain(im: Image.Image, tw: int, th: int, bg=(8, 8, 12)) -> Image.Image:
    c = Image.new("RGB", (tw, th), bg)
    iw, ih = im.size
    s = min(tw / iw, th / ih)
    nw, nh = max(1, int(iw * s)), max(1, int(ih * s))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    c.paste(im, ((tw - nw) // 2, (th - nh) // 2))
    return c


def lower_third(img: Image.Image, line: str, right: str = "Omnigent · Databricks") -> Image.Image:
    out = img.copy()
    d = ImageDraw.Draw(out)
    d.rectangle([0, H - 96, W, H], fill=(6, 7, 12))
    d.rectangle([0, H - 98, W, H - 96], fill=PURPLE)
    d.text((48, H - 48), line, fill=WHITE, font=font(24, True), anchor="lm")
    d.text((W - 48, H - 48), right, fill=MUTED, font=font(15), anchor="rm")
    return out


def ken_burns(base: Image.Image, t: float, zoom0: float = 1.0, zoom1: float = 1.08) -> Image.Image:
    """t in [0,1] — subtle zoom/pan for stills."""
    z = zoom0 + (zoom1 - zoom0) * t
    iw, ih = base.size
    nw, nh = int(iw / z), int(ih / z)
    # slight pan right
    ox = int((iw - nw) * (0.3 + 0.4 * t))
    oy = int((ih - nh) * 0.35)
    crop = base.crop((ox, oy, ox + nw, oy + nh))
    return crop.resize((W, H), Image.Resampling.LANCZOS)


# --------------- scenes ---------------


def scene_title() -> Image.Image:
    img = glow_canvas()
    d = ImageDraw.Draw(img)
    rrect(d, [W // 2 - 220, 250, W // 2 + 220, 298], 18, (36, 28, 62), PURPLE, 2)
    d.text((W // 2, 274), "Omnigent on Databricks", fill=PURPLE, font=font(18, True), anchor="mm")
    d.text((W // 2, 400), "The 2-Minute Hormone", fill=WHITE, font=font(64, True), anchor="mm")
    d.text(
        (W // 2, 490),
        "GLP-1 · structure prediction · live agent session",
        fill=MUTED,
        font=font(26),
        anchor="mm",
    )
    d.rectangle([W // 2 - 70, 560, W // 2 + 70, 566], fill=PINK)
    d.text((W // 2, H - 100), "Protein Lab demo · Boltz · ElevenLabs", fill=(90, 95, 120), font=font(16), anchor="mm")
    return img


def scene_gut_clock(progress: float = 0.0) -> Image.Image:
    """Visual for 2-minute half-life."""
    img = glow_canvas()
    d = ImageDraw.Draw(img)
    d.text((120, 120), "Natural GLP-1", fill=WHITE, font=font(42, True))
    d.text((120, 190), "Released after meals · destroyed in ~1–2 minutes", fill=MUTED, font=font(24))

    # clock
    cx, cy, R = 1400, 520, 220
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=PURPLE, width=8)
    d.ellipse([cx - R + 20, cy - R + 20, cx + R - 20, cy + R - 20], outline=(40, 38, 60), width=2)
    # hand sweeps with progress (0..1 = full 2 min metaphor)
    ang = -math.pi / 2 + progress * 2 * math.pi
    d.line([cx, cy, cx + R * 0.75 * math.cos(ang), cy + R * 0.75 * math.sin(ang)], fill=PINK, width=8)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=PINK)
    d.text((cx, cy + R + 50), "~2 min half-life", fill=YELLOW, font=font(26, True), anchor="mm")

    # enzyme chip
    rrect(d, [120, 360, 700, 520], 16, (30, 28, 48), YELLOW, 2)
    d.text((160, 400), "DPP-4 enzyme", fill=YELLOW, font=font(26, True))
    d.text((160, 450), "Rapidly cleaves active GLP-1", fill=MUTED, font=font(20))

    rrect(d, [120, 560, 700, 720], 16, (30, 28, 48), TEAL, 2)
    d.text((160, 600), "Signal lost", fill=TEAL, font=font(26, True))
    d.text((160, 650), "Too short-lived as a drug", fill=MUTED, font=font(20))
    return img


def scene_sequence() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((80, 70), "GLP-1 (7–36) amide", fill=WHITE, font=font(40, True))
    d.text((80, 130), "Human sequence · 30 amino acids · incretin hormone", fill=MUTED, font=font(22))

    # sequence grid
    x0, y0 = 80, 240
    colors = [PURPLE, TEAL, PINK, YELLOW, (100, 180, 255), (180, 140, 255)]
    for i, aa in enumerate(SEQ):
        col = colors[i % len(colors)]
        row, col_i = divmod(i, 15)
        x = x0 + col_i * 118
        y = y0 + row * 140
        rrect(d, [x, y, x + 100, y + 100], 14, (26, 28, 44), col, 3)
        d.text((x + 50, y + 42), aa, fill=col, font=font(36, True), anchor="mm")
        d.text((x + 50, y + 78), str(i + 1), fill=(100, 105, 130), font=font(14), anchor="mm")

    # biology bullets
    bullets = [
        "↑ Insulin when glucose is high (glucose-dependent)",
        "↓ Glucagon  ·  ↓ appetite signals in the brain",
        "From proglucagon (UniProt P01275)",
    ]
    y = 560
    for b in bullets:
        d.text((80, y), "▸  " + b, fill=MUTED, font=font(22))
        y += 50
    d.text((80, H - 80), "Source sequence used for Boltz: prediction-input-glp1.json", fill=(90, 95, 120), font=font(16))
    return img


def scene_problem() -> Image.Image:
    img = glow_canvas()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 140), "Why natural GLP-1 failed as a drug", fill=WHITE, font=font(40, True), anchor="mm")

    boxes = [
        ("1", "Signal", "Binds GLP-1 receptor\n→ insulin & satiety", TEAL),
        ("2", "DPP-4", "Enzyme cuts peptide\nin ~1–2 minutes", YELLOW),
        ("3", "Fix", "Analogues resist cleavage\n& last for days", PURPLE),
    ]
    x = 120
    for num, title, body, col in boxes:
        rrect(d, [x, 280, x + 520, 720], 20, (24, 26, 42), col, 3)
        d.ellipse([x + 30, 320, x + 90, 380], fill=col)
        d.text((x + 60, 350), num, fill=BG, font=font(28, True), anchor="mm")
        d.text((x + 40, 420), title, fill=WHITE, font=font(32, True))
        for i, line in enumerate(body.split("\n")):
            d.text((x + 40, 490 + i * 40), line, fill=MUTED, font=font(22))
        x += 560
    d.text(
        (W // 2, H - 100),
        "Semaglutide-class drugs ≈ same fold idea · engineered half-life",
        fill=MUTED,
        font=font(20),
        anchor="mm",
    )
    return img


def scene_screenshot(path: Path, caption: str) -> Image.Image:
    stage = Image.new("RGB", (W, H), (6, 6, 10))
    raw = Image.open(path).convert("RGB")
    win = fit_contain(raw, 1700, 920, bg=(6, 6, 10))
    # shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([90, 50, 1830, 990], 20, fill=(0, 0, 0, 180))
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    stage = stage.convert("RGBA")
    stage = Image.alpha_composite(stage, sh).convert("RGB")
    stage.paste(win, ((W - 1700) // 2, 40))
    return lower_third(stage, caption)


def scene_yaml() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # window chrome like Omnigent product
    rrect(d, [60, 50, W - 60, H - 50], 16, (28, 26, 40), (60, 56, 84), 1)
    for i, c in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
        d.ellipse([90 + i * 30, 70, 108 + i * 30, 88], fill=c)
    d.text((W // 2, 80), "agents/protein-lab/config.yaml", fill=MUTED, font=font(16), anchor="mm")
    rrect(d, [W - 220, 62, W - 90, 98], 14, PINK)
    d.text((W - 155, 80), "↑ Share", fill=WHITE, font=font(14, True), anchor="mm")

    code = [
        ("spec_version: 1", MUTED),
        ("name: protein-lab", TEAL),
        ("", MUTED),
        ("executor:", WHITE),
        ("  type: omnigent", MUTED),
        ("  config:", MUTED),
        ("    harness: claude-sdk   # swap → codex | pi | grok", PURPLE),
        ("", MUTED),
        ("tools:", WHITE),
        ("  run_boltz_api_prediction:  # Boltz cloud", PINK),
        ("    type: function", MUTED),
        ("    callable: tools.protein_tools.run_boltz_api_prediction", MUTED),
        ("  render_structure:", PINK),
        ("    type: function", MUTED),
        ("  make_structure_movie:", PINK),
        ("    type: function", MUTED),
        ("", MUTED),
        ("policies:", WHITE),
        ("  max_tool_calls: { limit: 40 }", YELLOW),
    ]
    y = 140
    mono = font(22)
    for line, col in code:
        d.text((120, y), line, fill=col, font=mono)
        y += 36
    return lower_third(img, "Custom agent = YAML · tools + harness + policies stay portable")


def scene_metrics() -> Image.Image:
    img = glow_canvas()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 100), "Our live Boltz run", fill=WHITE, font=font(40, True), anchor="mm")
    d.text((W // 2, 160), "GLP-1 (7–36) · boltz-api structure-and-binding", fill=MUTED, font=font(20), anchor="mm")

    cards = [
        ("structure_confidence", f"{METRICS['structure_confidence']:.2f}", PURPLE),
        ("complex_plddt", f"{METRICS['complex_plddt']:.2f}", TEAL),
        ("ptm", f"{METRICS['ptm']:.2f}", PINK),
        ("residues", "30", YELLOW),
    ]
    x = 100
    for name, val, col in cards:
        rrect(d, [x, 280, x + 400, 560], 18, (26, 28, 46), col, 3)
        d.text((x + 30, 330), name, fill=MUTED, font=font(18))
        d.text((x + 30, 410), val, fill=col, font=font(64, True))
        x += 450

    d.text((W // 2, 680), "Artifact", fill=MUTED, font=font(18), anchor="mm")
    rrect(d, [280, 720, W - 280, 860], 14, (22, 24, 38), TEAL, 2)
    d.text(
        (W // 2, 790),
        "sab_pred_…_predicted.cif  ·  metrics.json  ·  glp1_premium_spin.mp4",
        fill=TEAL,
        font=font(22, True),
        anchor="mm",
    )
    return img


def scene_protein_lab_ui(struct: Optional[Image.Image], phase: str = "result") -> Image.Image:
    """
    Light Omnigent-accurate chrome (matches official carousel / Share pink).
    """
    # soft pink stage like real Omnigent marketing
    img = Image.new("RGB", (W, H), (250, 236, 242))
    d = ImageDraw.Draw(img)

    # floating window
    wx0, wy0, wx1, wy1 = 60, 40, W - 60, H - 40
    rrect(d, [wx0, wy0, wx1, wy1], 14, (255, 255, 255), (220, 210, 220), 1)

    # traffic lights
    for i, c in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
        d.ellipse([wx0 + 24 + i * 28, wy0 + 18, wx0 + 40 + i * 28, wy0 + 34], fill=c)
    d.text(((wx0 + wx1) // 2, wy0 + 26), "Protein Lab — GLP-1 · omnigent", fill=(120, 110, 130), font=font(15), anchor="mm")
    rrect(d, [wx1 - 150, wy0 + 12, wx1 - 30, wy0 + 42], 12, PINK)
    d.text((wx1 - 90, wy0 + 27), "↑ Share", fill=WHITE, font=font(13, True), anchor="mm")

    # layout
    mid = int(wx0 + (wx1 - wx0) * 0.62)
    # left chat
    rrect(d, [wx0 + 16, wy0 + 56, mid - 8, wy1 - 16], 10, (252, 250, 253))
    # right agents
    rrect(d, [mid + 8, wy0 + 56, wx1 - 16, wy1 - 16], 10, (248, 246, 250))

    # tabs
    tx = mid + 24
    for name, on in [("Files", False), ("Agents", True), ("Shells", False)]:
        if on:
            rrect(d, [tx, wy0 + 72, tx + 90, wy0 + 100], 8, (45, 90, 160))
            d.text((tx + 45, wy0 + 86), name, fill=WHITE, font=font(13, True), anchor="mm")
        else:
            d.text((tx + 45, wy0 + 86), name, fill=(140, 130, 150), font=font(13), anchor="mm")
        tx += 100

    # agents
    agents = [
        ("protein-lab", "claude-sdk · live", True, "GLP-1 session"),
        ("boltz-api", "tool · cloud", True, "prediction succeeded"),
        ("viz", "tool · render", True, "spin.mp4 ready"),
    ]
    ay = wy0 + 130
    for name, meta, on, st in agents:
        bg = (45, 90, 160) if on else (240, 238, 245)
        fg = WHITE if on else (40, 40, 50)
        rrect(d, [mid + 24, ay, wx1 - 36, ay + 78], 10, bg)
        d.ellipse([mid + 40, ay + 32, mid + 56, ay + 48], fill=GREEN)
        d.text((mid + 72, ay + 22), name, fill=fg, font=font(16, True))
        d.text((mid + 72, ay + 48), f"{meta} · {st}", fill=(200, 210, 230) if on else MUTED, font=font(13))
        ay += 92

    # policy
    rrect(d, [mid + 24, wy1 - 120, wx1 - 36, wy1 - 40], 10, (255, 250, 230), YELLOW, 2)
    d.text((mid + 40, wy1 - 100), "Policy · max_tool_calls 40", fill=(140, 100, 20), font=font(14, True))
    d.text((mid + 40, wy1 - 75), "Sandbox write: outputs/ · network: Boltz API", fill=(120, 110, 90), font=font(13))

    # chat content
    lx0 = wx0 + 36
    # user bubble
    ub = "Fold GLP-1 with Boltz and make a spin movie"
    rrect(d, [mid - 420, wy0 + 90, mid - 40, wy0 + 150], 16, (90, 70, 140))
    d.text((mid - 230, wy0 + 120), ub, fill=WHITE, font=font(15), anchor="mm")

    d.text((lx0, wy0 + 190), "Done. Live Boltz results:", fill=(30, 30, 40), font=font(17, True))
    d.text(
        (lx0, wy0 + 230),
        f"structure_confidence {METRICS['structure_confidence']:.2f}  ·  pLDDT {METRICS['complex_plddt']:.2f}",
        fill=(60, 60, 80),
        font=font(16),
    )

    # tool cards
    def tool(y, title, body, done=True):
        rrect(d, [lx0, y, mid - 40, y + 100], 12, (245, 243, 250), (220, 215, 230), 1)
        d.text((lx0 + 20, y + 18), title, fill=(30, 30, 45), font=font(16, True))
        d.text((mid - 60, y + 18), "✓ Done" if done else "● Running", fill=GREEN if done else PURPLE, font=font(14, True), anchor="ra")
        d.text((lx0 + 20, y + 50), body, fill=(110, 110, 130), font=font(14))
        rrect(d, [lx0 + 20, y + 78, mid - 60, y + 86], 4, (230, 228, 240))
        rrect(d, [lx0 + 20, y + 78, mid - 60, y + 86], 4, GREEN)

    tool(wy0 + 280, "run_boltz_api_prediction", "prediction-input-glp1.json → predicted.cif")
    tool(wy0 + 400, "make_structure_movie", "glp1_premium_spin.mp4 · 96 frames @ 24fps")

    if struct is not None:
        thumb = fit_cover(struct, mid - 80 - lx0, 200)
        rrect(d, [lx0, wy0 + 530, mid - 40, wy0 + 750], 12, (20, 22, 35), PURPLE, 2)
        img.paste(thumb, (lx0 + 10, wy0 + 540))
        d = ImageDraw.Draw(img)

    # composer
    rrect(d, [lx0, wy1 - 90, mid - 40, wy1 - 40], 20, (245, 243, 250), (220, 215, 230), 1)
    d.text((lx0 + 24, wy1 - 65), "Ask the agent anything…", fill=(150, 145, 160), font=font(14), anchor="lm")
    d.ellipse([mid - 80, wy1 - 82, mid - 54, wy1 - 56], fill=PURPLE)

    return lower_third(img, "Omnigent session UI · chat · tool cards · Agents · Share · policies")


def scene_structure_frame(spin_frame: Image.Image) -> Image.Image:
    base = fit_cover(spin_frame, W, H)
    return lower_third(base, "Boltz-predicted GLP-1 fold · N→C rainbow · heavy-atom sticks")


def scene_cta() -> Image.Image:
    img = glow_canvas()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 220), "Sequence → Structure → Story", fill=WHITE, font=font(46, True), anchor="mm")
    d.text((W // 2, 290), "Protein Lab on Omnigent by Databricks", fill=MUTED, font=font(24), anchor="mm")
    cmds = [
        "omni run ./agents/protein-lab",
        "python -m demo.run_boltz_e2e  # prediction-input-glp1.json",
        "open outputs/omnigent_glp1_hormone_e2e_demo.mp4",
    ]
    y = 400
    for c in cmds:
        rrect(d, [W // 2 - 520, y, W // 2 + 520, y + 78], 14, (28, 26, 46), PURPLE, 2)
        d.text((W // 2, y + 39), c, fill=TEAL, font=font(24, True), anchor="mm")
        y += 100
    d.text((W // 2, H - 100), "docs.databricks.com/aws/en/omnigent  ·  omnigent.ai", fill=(90, 95, 120), font=font(18), anchor="mm")
    return img


# --------------- audio / assemble ---------------


def ensure_vo() -> List[Path]:
    VO_DIR.mkdir(parents=True, exist_ok=True)
    script = json.loads((ROOT / "demo/vo_script_v2.json").read_text())
    key_path = ROOT / ".env"
    if not key_path.exists():
        key_path = Path.home() / "Developer/video-use/.env"
    key = key_path.read_text().split("ELEVENLABS_API_KEY=", 1)[1].strip().splitlines()[0]
    voice = script["voice_id"]
    model = script["model_id"]
    files = []
    for seg in script["segments"]:
        out = VO_DIR / f"{seg['id']}.mp3"
        files.append(out)
        if out.exists() and out.stat().st_size > 1000:
            print(f"  VO cache {seg['id']}")
            continue
        print(f"  TTS {seg['id']}…")
        body = json.dumps(
            {
                "text": seg["text"],
                "model_id": model,
                "voice_settings": {
                    "stability": 0.42,
                    "similarity_boost": 0.82,
                    "style": 0.28,
                    "use_speaker_boost": True,
                },
            }
        ).encode()
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
            data=body,
            headers={
                "xi-api-key": key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            out.write_bytes(resp.read())
        time.sleep(0.25)
    return files


def ensure_premium_spin() -> Path:
    still = ROOT / "outputs/glp1_premium/glp1_premium_still.png"
    frames = ROOT / "outputs/glp1_premium/frames"
    if not still.exists() or not frames.exists() or len(list(frames.glob("*.png"))) < 48:
        print("Rendering premium GLP-1 spin…")
        subprocess.run([sys.executable, str(ROOT / "scripts/render_glp1_premium.py")], check=True, cwd=str(ROOT))
    return ROOT / "outputs/glp1_premium"


def concat_audio(files: List[Path], gap: float = 0.18) -> Tuple[Path, List[float], float]:
    """Return (narration.mp3, per-segment durations including trailing gap, total)."""
    silence = OUT / "silence.mp3"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono",
            "-t",
            str(gap),
            "-q:a",
            "9",
            "-acodec",
            "libmp3lame",
            str(silence),
        ],
        check=True,
        capture_output=True,
    )
    durs = []
    lines = []
    total = 0.0
    for i, f in enumerate(files):
        d = ffprobe_dur(f)
        durs.append(d + (gap if i < len(files) - 1 else 0.0))
        total += durs[-1]
        lines.append(f"file '{f.resolve()}'")
        if i < len(files) - 1:
            lines.append(f"file '{silence.resolve()}'")
    list_path = OUT / "audio_list.txt"
    list_path.write_text("\n".join(lines) + "\n")
    audio = OUT / "narration.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", str(audio)],
        check=True,
        capture_output=True,
    )
    return audio, durs, ffprobe_dur(audio)


def hold(img: Image.Image, seconds: float) -> List[Image.Image]:
    n = max(1, int(round(seconds * FPS)))
    return [img.copy() for _ in range(n)]


def animate_still(builder: Callable[[], Image.Image], seconds: float, burns: bool = True) -> List[Image.Image]:
    n = max(1, int(round(seconds * FPS)))
    base = builder()
    if not burns:
        return [base.copy() for _ in range(n)]
    out = []
    for i in range(n):
        t = i / max(n - 1, 1)
        # apply ken burns on full frame slightly
        # only zoom canvas content
        z = 1.0 + 0.04 * t
        iw, ih = base.size
        nw, nh = int(iw / z), int(ih / z)
        ox = int((iw - nw) * 0.5 * t)
        oy = int((ih - nh) * 0.3)
        crop = base.crop((ox, oy, ox + nw, oy + nh)).resize((W, H), Image.Resampling.LANCZOS)
        out.append(crop)
    return out


def spin_frames(premium: Path, seconds: float) -> List[Image.Image]:
    files = sorted((premium / "frames").glob("frame_*.png"))
    n = max(1, int(round(seconds * FPS)))
    out = []
    for i in range(n):
        im = Image.open(files[i % len(files)]).convert("RGB")
        out.append(scene_structure_frame(im))
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir()

    print("=== 1) Premium structure ===")
    premium = ensure_premium_spin()
    struct_still = Image.open(premium / "glp1_premium_still.png").convert("RGB")

    print("=== 2) Voiceover ===")
    vo_files = ensure_vo()
    audio, seg_durs, audio_total = concat_audio(vo_files, gap=0.18)
    print("  segment durs:", [round(x, 2) for x in seg_durs], "total", round(audio_total, 2))

    # Official UI assets
    composition = UI / "composition-dark.png"
    control = UI / "control-dark.png"
    collab = UI / "collaboration-dark.png"
    carousel = sorted((UI / "carousel_frames").glob("f_*.png"))

    print("=== 3) Build timeline (9 VO chapters) ===")
    # Each chapter: carefully chosen correct visuals
    timeline: List[Image.Image] = []

    # 01 hook — title then clock
    d0 = seg_durs[0]
    timeline += animate_still(scene_title, d0 * 0.45)
    n_clock = max(1, int(round(d0 * 0.55 * FPS)))
    for i in range(n_clock):
        timeline.append(scene_gut_clock(progress=i / max(n_clock - 1, 1)))

    # 02 name — sequence
    timeline += animate_still(scene_sequence, seg_durs[1])

    # 03 problem
    timeline += animate_still(scene_problem, seg_durs[2])

    # 04 omnigent — real UI carousel + composition
    d4 = seg_durs[3]
    if carousel:
        # cycle carousel for first half
        half = d4 * 0.55
        n = max(1, int(round(half * FPS)))
        for i in range(n):
            cf = Image.open(carousel[i % len(carousel)]).convert("RGB")
            timeline.append(
                lower_third(
                    fit_cover(cf, W, H),
                    "Real Omnigent workspace UI on Databricks",
                )
            )
        if composition.exists():
            timeline += animate_still(
                lambda: scene_screenshot(composition, "Composition · multi-agent · Share · Agents panel"),
                d4 * 0.45,
                burns=False,
            )
        else:
            timeline += hold(scene_title(), d4 * 0.45)
    else:
        timeline += animate_still(lambda: scene_screenshot(composition, "Omnigent UI"), d4)

    # 05 agent — YAML
    timeline += animate_still(scene_yaml, seg_durs[4], burns=False)

    # 06 boltz — metrics + spin start
    d6 = seg_durs[5]
    timeline += animate_still(scene_metrics, d6 * 0.45)
    timeline += spin_frames(premium, d6 * 0.55)

    # 07 structure — full premium spin
    timeline += spin_frames(premium, seg_durs[6])

    # 08 ui — protein lab session + control policy screenshot
    d8 = seg_durs[7]
    timeline += animate_still(
        lambda: scene_protein_lab_ui(struct_still, "result"),
        d8 * 0.6,
        burns=False,
    )
    if control.exists():
        timeline += animate_still(
            lambda: scene_screenshot(control, "Control · contextual policies & approvals"),
            d8 * 0.4,
            burns=False,
        )
    else:
        timeline += hold(scene_protein_lab_ui(struct_still), d8 * 0.4)

    # 09 cta
    timeline += animate_still(scene_cta, seg_durs[8])

    # Pad/trim to audio length
    need = int(round(audio_total * FPS))
    if len(timeline) < need:
        timeline += [timeline[-1].copy() for _ in range(need - len(timeline))]
    elif len(timeline) > need:
        timeline = timeline[:need]

    print(f"=== 4) Write {len(timeline)} frames ({len(timeline)/FPS:.1f}s) ===")
    for i, fr in enumerate(timeline):
        fr.save(FRAMES / f"f_{i:05d}.png")
        if i % 200 == 0:
            print(f"  frame {i}/{len(timeline)}")

    silent = OUT / "video_silent.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(FRAMES / "f_%05d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "16",
            "-movflags",
            "+faststart",
            str(silent),
        ],
        check=True,
        capture_output=True,
    )

    final = ROOT / "outputs" / "omnigent_glp1_hormone_e2e_demo.mp4"
    # loudnorm audio for broadcast-ish levels
    audio_norm = OUT / "narration_loud.m4a"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(audio),
            "-af",
            "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(audio_norm),
        ],
        check=True,
        capture_output=True,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent),
            "-i",
            str(audio_norm),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(final),
        ],
        check=True,
        capture_output=True,
    )
    ship = ROOT / "outputs" / "FINAL_omnigent_glp1_demo.mp4"
    shutil.copy(final, ship)

    # poster
    mid = timeline[len(timeline) // 2]
    mid.save(ASSETS / "glp1_demo_poster.png")

    meta = {
        "final": str(final),
        "duration_s": ffprobe_dur(final),
        "metrics": METRICS,
        "sequence": SEQ,
        "voice": "Alice (ElevenLabs)",
        "structure": "outputs/glp1_premium/",
        "story": "GLP-1 2-minute hormone · accurate Omnigent UI · live Boltz metrics",
    }
    (ROOT / "outputs" / "glp1_e2e_session.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
