#!/usr/bin/env python3
"""
Product demo: Omnigent by Databricks · Protein Lab

Builds a 1920×1080 launch film that shows the *product UI* — not just
structure spins:

  1. Brand title (Databricks · Omnigent)
  2. Official Omnigent workspace carousel (docs.databricks.com)
  3. Composition / Control / Collaboration pillars (omnigent.ai screenshots)
  4. Animated Protein Lab session UI (chat + tool cards + Agents panel)
  5. Live Boltz metrics + structure viewer pane
  6. Spin movie inset
  7. CTA: omni run ./agents/protein-lab

Output:
  outputs/omnigent_databricks_protein_lab_ui_demo.mp4
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets" / "omnigent-ui"
OUT = ROOT / "outputs" / "omnigent-ui-demo"
FRAMES = OUT / "frames"
W, H = 1920, 1080
FPS = 24

# Omnigent-ish dark UI palette (from product screenshots)
BG = (12, 12, 18)
PANEL = (28, 26, 40)
PANEL2 = (36, 34, 52)
CHAT_BG = (22, 20, 34)
ACCENT = (236, 72, 153)  # pink Share button
PURPLE = (124, 92, 255)
TEAL = (0, 212, 170)
WHITE = (240, 240, 245)
MUTED = (150, 148, 170)
GREEN = (52, 211, 153)
YELLOW = (251, 191, 36)
CARD = (40, 38, 58)
BORDER = (60, 56, 84)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    cands = [
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", True),
        ("/System/Library/Fonts/Supplemental/Arial.ttf", False),
        ("/System/Library/Fonts/Helvetica.ttc", False),
        ("/Library/Fonts/SF-Pro-Display-Bold.otf", True),
        ("/System/Library/Fonts/SFNS.ttf", False),
    ]
    for path, is_bold in cands:
        if bold and not is_bold and "Bold" not in path:
            continue
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def rrect(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def fit_cover(img: Image.Image, tw: int, th: int) -> Image.Image:
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def fit_contain(img: Image.Image, tw: int, th: int, bg=(0, 0, 0)) -> Image.Image:
    canvas = Image.new("RGB", (tw, th), bg)
    iw, ih = img.size
    scale = min(tw / iw, th / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas.paste(img, ((tw - nw) // 2, (th - nh) // 2))
    return canvas


def load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def new_canvas(color=BG) -> Image.Image:
    return Image.new("RGB", (W, H), color)


def title_card(subtitle: str, badge: str = "Omnigent on Databricks") -> Image.Image:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # soft purple glow
    glow = Image.new("RGB", (W, H), BG)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W // 2 - 420, H // 2 - 220, W // 2 + 420, H // 2 + 280], fill=(40, 20, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img = Image.blend(img, glow, 0.55)
    d = ImageDraw.Draw(img)

    # badge
    bw, bh = 360, 40
    bx, by = (W - bw) // 2, H // 2 - 160
    rrect(d, [bx, by, bx + bw, by + bh], 20, fill=(40, 30, 70), outline=PURPLE, width=2)
    d.text((W // 2, by + bh // 2), badge, fill=PURPLE, font=font(18, True), anchor="mm")

    d.text((W // 2, H // 2 - 40), "Protein Lab", fill=WHITE, font=font(72, True), anchor="mm")
    d.text((W // 2, H // 2 + 40), subtitle, fill=MUTED, font=font(28), anchor="mm")
    d.text(
        (W // 2, H - 80),
        "docs.databricks.com/aws/en/omnigent  ·  omnigent.ai",
        fill=(90, 88, 110),
        font=font(18),
        anchor="mm",
    )
    # accent bar
    d.rectangle([W // 2 - 80, H // 2 + 90, W // 2 + 80, H // 2 + 96], fill=ACCENT)
    return img


def caption_bar(img: Image.Image, text: str) -> Image.Image:
    """Bottom caption strip for product beats."""
    out = img.copy()
    d = ImageDraw.Draw(out)
    d.rectangle([0, H - 88, W, H], fill=(8, 8, 14))
    d.rectangle([0, H - 90, W, H - 88], fill=PURPLE)
    d.text((48, H - 44), text, fill=WHITE, font=font(26, True), anchor="lm")
    d.text((W - 48, H - 44), "Omnigent · Databricks", fill=MUTED, font=font(18), anchor="rm")
    return out


def screenshot_slide(path: Path, caption: str) -> Image.Image:
    raw = load_rgb(path)
    # window on dark stage
    stage = new_canvas((6, 6, 10))
    # soft shadow
    window = fit_contain(raw, 1680, 920, bg=(6, 6, 10))
    # drop shadow
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([100, 60, 1820, 1000], radius=18, fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    stage = stage.convert("RGBA")
    stage = Image.alpha_composite(stage, shadow)
    stage = stage.convert("RGB")
    # paste window with slight inset
    stage.paste(window, ((W - 1680) // 2, 50))
    return caption_bar(stage, caption)


def draw_window_chrome(d: ImageDraw.ImageDraw, title: str):
    # macOS-like chrome matching Omnigent product shots
    rrect(d, [40, 40, W - 40, H - 40], 16, fill=PANEL, outline=BORDER, width=1)
    # traffic lights
    for i, c in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
        d.ellipse([64 + i * 28, 58, 80 + i * 28, 74], fill=c)
    d.text((W // 2, 66), title, fill=MUTED, font=font(16), anchor="mm")
    # Share button
    rrect(d, [W - 200, 52, W - 70, 84], 14, fill=ACCENT)
    d.text((W - 135, 68), "↑  Share", fill=WHITE, font=font(15, True), anchor="mm")


def protein_lab_session(
    phase: str,
    structure_img: Optional[Image.Image] = None,
) -> Image.Image:
    """
    High-fidelity Omnigent-style web UI for Protein Lab.

    phase:
      empty | prompt | tools | result | share
    """
    img = new_canvas((8, 8, 12))
    d = ImageDraw.Draw(img)
    draw_window_chrome(d, "Protein Lab — protein-folding-fun · omnigent")

    # Layout: chat (left 58%) | right panel (files/agents)
    left = [56, 100, int(W * 0.58), H - 56]
    right = [int(W * 0.58) + 12, 100, W - 56, H - 56]

    rrect(d, left, 12, fill=CHAT_BG)
    rrect(d, right, 12, fill=PANEL2)

    # Right tabs
    rx0, ry0, rx1, ry1 = right
    tabs = [("Files", False), ("Agents", True), ("Shells", False)]
    tx = rx0 + 16
    for name, active in tabs:
        tw = 90
        if active:
            rrect(d, [tx, ry0 + 14, tx + tw, ry0 + 44], 8, fill=(50, 80, 140))
            d.text((tx + tw // 2, ry0 + 29), name, fill=WHITE, font=font(14, True), anchor="mm")
        else:
            d.text((tx + tw // 2, ry0 + 29), name, fill=MUTED, font=font(14), anchor="mm")
        tx += tw + 8

    # Agents list
    agents = [
        ("protein-lab", "claude-sdk · live", True, "Folding peptide + aspirin…"),
        ("boltz-runner", "tool · boltz-api", phase in ("tools", "result", "share"), "prediction succeeded"),
        ("viz", "tool · matplotlib", phase in ("result", "share"), "spin.mp4 ready"),
    ]
    ay = ry0 + 64
    for name, meta, active, status in agents:
        bg = (45, 70, 120) if active else (32, 30, 48)
        rrect(d, [rx0 + 12, ay, rx1 - 12, ay + 72], 10, fill=bg)
        d.ellipse([rx0 + 28, ay + 28, rx0 + 44, ay + 44], fill=GREEN if active else MUTED)
        d.text((rx0 + 56, ay + 22), name, fill=WHITE, font=font(16, True), anchor="lm")
        d.text((rx0 + 56, ay + 46), f"{meta}  ·  {status}", fill=MUTED, font=font(13), anchor="lm")
        ay += 84

    # Policy chip
    rrect(d, [rx0 + 12, ry1 - 90, rx1 - 12, ry1 - 20], 10, fill=(50, 40, 30), outline=YELLOW, width=1)
    d.text((rx0 + 28, ry1 - 70), "Policy · max_tool_calls 40", fill=YELLOW, font=font(14, True), anchor="lm")
    d.text((rx0 + 28, ry1 - 48), "Sandbox · write outputs/ · network for Boltz", fill=MUTED, font=font(13), anchor="lm")

    # Chat column
    lx0, ly0, lx1, ly1 = left
    cy = ly0 + 28

    def bubble_user(text: str):
        nonlocal cy
        # right-aligned pill
        pad = 16
        f = font(18)
        # rough width
        max_w = int((lx1 - lx0) * 0.72)
        # wrap
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if f.getlength(test) > max_w - 40:
                lines.append(cur)
                cur = w
            else:
                cur = test
        if cur:
            lines.append(cur)
        th = 20 * len(lines) + pad * 2
        tw = min(max_w, int(max(f.getlength(l) for l in lines) + 40))
        bx1 = lx1 - 24
        bx0 = bx1 - tw
        rrect(d, [bx0, cy, bx1, cy + th], 18, fill=(70, 60, 110))
        for i, line in enumerate(lines):
            d.text((bx0 + 20, cy + pad + i * 20), line, fill=WHITE, font=f)
        cy += th + 18

    def bubble_agent(text: str):
        nonlocal cy
        f = font(17)
        max_w = int((lx1 - lx0) * 0.85)
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if f.getlength(test) > max_w - 32:
                lines.append(cur)
                cur = w
            else:
                cur = test
        if cur:
            lines.append(cur)
        for i, line in enumerate(lines):
            d.text((lx0 + 28, cy + i * 24), line, fill=WHITE, font=f)
        cy += 24 * len(lines) + 14

    def tool_card(title: str, body: str, status: str = "running"):
        nonlocal cy
        color = GREEN if status == "done" else (PURPLE if status == "running" else YELLOW)
        label = {"done": "✓ Done", "running": "● Running", "ask": "? Approval"}.get(status, status)
        rrect(d, [lx0 + 20, cy, lx1 - 20, cy + 110], 12, fill=CARD, outline=BORDER, width=1)
        d.text((lx0 + 40, cy + 18), title, fill=WHITE, font=font(16, True))
        d.text((lx1 - 40, cy + 18), label, fill=color, font=font(14, True), anchor="ra")
        d.text((lx0 + 40, cy + 48), body, fill=MUTED, font=font(14))
        # progress bar
        rrect(d, [lx0 + 40, cy + 80, lx1 - 40, cy + 90], 4, fill=(30, 28, 45))
        prog = 1.0 if status == "done" else (0.55 if status == "running" else 0.15)
        rrect(
            d,
            [lx0 + 40, cy + 80, lx0 + 40 + int((lx1 - lx0 - 80) * prog), cy + 90],
            4,
            fill=color,
        )
        cy += 124

    # Session content by phase
    if phase == "empty":
        d.text(
            ((lx0 + lx1) // 2, (ly0 + ly1) // 2 - 20),
            "protein-lab",
            fill=WHITE,
            font=font(36, True),
            anchor="mm",
        )
        d.text(
            ((lx0 + lx1) // 2, (ly0 + ly1) // 2 + 30),
            "Custom Omnigent agent · harness: claude-sdk · tools: Boltz + viz",
            fill=MUTED,
            font=font(16),
            anchor="mm",
        )
    elif phase == "prompt":
        bubble_user("Fold peptide + aspirin with Boltz and make a spin movie")
        bubble_agent("On it — I'll use run_boltz_api_prediction, then render + movie tools.")
    elif phase == "tools":
        bubble_user("Fold peptide + aspirin with Boltz and make a spin movie")
        bubble_agent("Calling tools through Omnigent…")
        tool_card(
            "run_boltz_api_prediction",
            "input: prediction-input.json  ·  engine: boltz-api cloud",
            "done",
        )
        tool_card(
            "render_structure",
            "CIF → hero PNG  ·  chains A (peptide) + B (aspirin)",
            "running",
        )
        tool_card(
            "make_structure_movie",
            "72 frames @ 24fps  →  boltz-aspirin-peptide_spin.mp4",
            "running",
        )
    elif phase in ("result", "share"):
        bubble_user("Fold peptide + aspirin with Boltz and make a spin movie")
        bubble_agent(
            "Done. Boltz structure_confidence 0.75 · complex_plddt 0.84 · "
            "movie ready in outputs/."
        )
        tool_card("run_boltz_api_prediction", "sab_pred_…_predicted.cif", "done")
        tool_card("make_structure_movie", "boltz-aspirin-peptide_spin.mp4", "done")

        # structure preview card
        if structure_img is not None:
            rrect(d, [lx0 + 20, cy, lx1 - 20, cy + 220], 12, fill=(16, 14, 28), outline=PURPLE, width=1)
            thumb = fit_cover(structure_img.convert("RGB"), (lx1 - lx0) - 60, 180)
            img.paste(thumb, (lx0 + 30, cy + 20))
            # rebind draw after paste
            d = ImageDraw.Draw(img)
            cy += 236

        if phase == "share":
            # share toast
            rrect(d, [lx0 + 40, ly1 - 120, lx1 - 40, ly1 - 50], 12, fill=(60, 30, 70), outline=ACCENT, width=2)
            d.text(
                ((lx0 + lx1) // 2, ly1 - 85),
                "Session shared · teammates can watch tools stream live",
                fill=WHITE,
                font=font(16, True),
                anchor="mm",
            )

    # Composer
    rrect(d, [lx0 + 16, ly1 - 70, lx1 - 16, ly1 - 20], 22, fill=(32, 30, 48), outline=BORDER, width=1)
    d.text((lx0 + 40, ly1 - 45), "Ask the agent anything…", fill=MUTED, font=font(15), anchor="lm")
    d.ellipse([lx1 - 56, ly1 - 62, lx1 - 32, ly1 - 28], fill=PURPLE)
    d.text((lx1 - 44, ly1 - 45), "↑", fill=WHITE, font=font(16, True), anchor="mm")

    # bottom mode switch
    d.text((W // 2 - 40, H - 28), "Chat", fill=WHITE, font=font(13, True), anchor="mm")
    d.text((W // 2 + 40, H - 28), "Terminal", fill=MUTED, font=font(13), anchor="mm")

    return img


def yaml_slide() -> Image.Image:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    draw_window_chrome(d, "agents/protein-lab/config.yaml")
    code = '''spec_version: 1
name: protein-lab
description: Structural biology lab on Omnigent

executor:
  type: omnigent
  config:
    harness: claude-sdk   # swap → codex | pi | grok

tools:
  run_boltz_api_prediction:
    type: function
    callable: tools.protein_tools.run_boltz_api_prediction
  render_structure:
    type: function
    callable: tools.protein_tools.render_structure
  make_structure_movie:
    type: function
    callable: tools.protein_tools.make_structure_movie

policies:
  max_tool_calls:
    handler: omnigent.policies.builtins.safety.max_tool_calls_per_session
    factory_params: { limit: 40 }'''
    rrect(d, [80, 110, W - 80, H - 80], 14, fill=(18, 16, 28), outline=BORDER, width=1)
    mono = font(20)
    y = 140
    for line in code.splitlines():
        # simple syntax coloring
        col = WHITE
        if line.strip().startswith("#") or "swap" in line:
            col = MUTED
        elif line.rstrip().endswith(":") and not line.strip().startswith("-"):
            col = TEAL
        elif "claude-sdk" in line or "codex" in line or "harness" in line:
            col = PURPLE
        elif "run_boltz" in line or "render_" in line or "make_structure" in line:
            col = ACCENT
        d.text((120, y), line, fill=col, font=mono)
        y += 28
    return caption_bar(img, "Custom agent = short YAML · tools + harness + policies")


def architecture_slide() -> Image.Image:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 80), "How Omnigent sits above agents", fill=WHITE, font=font(36, True), anchor="mm")
    d.text(
        (W // 2, 130),
        "Meta-harness on Databricks · AI Gateway · Sandbox · Shareable sessions",
        fill=MUTED,
        font=font(20),
        anchor="mm",
    )

    layers = [
        ("Interfaces", "Web UI  ·  Desktop  ·  Mobile  ·  Terminal  ·  API", ACCENT),
        ("Omnigent server", "Policies · history · collab · Unity AI Gateway", PURPLE),
        ("Runner + Sandbox", "Databricks Sandbox · OS isolation · credentials broker", TEAL),
        ("Harnesses", "claude-sdk · codex · pi · grok · your YAML agents", YELLOW),
        ("Tools", "Boltz API · UniProt · render · spin movie", GREEN),
    ]
    y = 200
    for title, body, color in layers:
        rrect(d, [220, y, W - 220, y + 100], 16, fill=PANEL, outline=color, width=2)
        d.rectangle([220, y, 240, y + 100], fill=color)
        d.text((280, y + 32), title, fill=WHITE, font=font(24, True))
        d.text((280, y + 68), body, fill=MUTED, font=font(18))
        y += 120
    return img


def metrics_slide(structure: Optional[Image.Image]) -> Image.Image:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.text((80, 60), "Boltz results in the Omnigent session", fill=WHITE, font=font(34, True))
    d.text((80, 110), "Live cloud prediction · confidence streamed back as tool output", fill=MUTED, font=font(18))

    metrics = [
        ("structure_confidence", "0.75", PURPLE),
        ("complex_plddt", "0.84", TEAL),
        ("ptm", "0.64", ACCENT),
        ("iptm", "0.39", YELLOW),
    ]
    x = 80
    for name, val, color in metrics:
        rrect(d, [x, 180, x + 400, 320], 16, fill=PANEL, outline=color, width=2)
        d.text((x + 30, 210), name, fill=MUTED, font=font(16))
        d.text((x + 30, 250), val, fill=color, font=font(48, True))
        x += 440

    if structure is not None:
        thumb = fit_cover(structure, 900, 480)
        rrect(d, [80, 380, 1000, 900], 16, fill=(10, 10, 16), outline=BORDER, width=1)
        img.paste(thumb, (90, 400))
        d = ImageDraw.Draw(img)

    rrect(d, [1040, 380, W - 80, 900], 16, fill=PANEL)
    d.text((1080, 420), "Artifacts", fill=WHITE, font=font(22, True))
    arts = [
        "outputs/.../predicted.cif",
        "outputs/.../metrics.json",
        "boltz-aspirin-peptide_still.png",
        "boltz-aspirin-peptide_spin.mp4",
        "omnigent_protein_lab_launch.mp4",
    ]
    y = 480
    for a in arts:
        d.text((1080, y), "▸  " + a, fill=TEAL, font=font(18))
        y += 48
    return img


def cta_slide() -> Image.Image:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    glow = Image.new("RGB", (W, H), BG)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W // 2 - 500, H // 2 - 200, W // 2 + 500, H // 2 + 300], fill=(50, 20, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.blend(img, glow, 0.5)
    d = ImageDraw.Draw(img)

    d.text((W // 2, 280), "Try it on Databricks Omnigent", fill=WHITE, font=font(44, True), anchor="mm")
    cmds = [
        "omni run ./agents/protein-lab",
        "python -m demo.run_boltz_e2e",
        "open outputs/omnigent_protein_lab_launch.mp4",
    ]
    y = 400
    for c in cmds:
        rrect(d, [W // 2 - 420, y, W // 2 + 420, y + 70], 12, fill=PANEL, outline=PURPLE, width=2)
        d.text((W // 2, y + 35), c, fill=TEAL, font=font(24, True), anchor="mm")
        y += 100
    d.text(
        (W // 2, H - 100),
        "docs.databricks.com/aws/en/omnigent  ·  omnigent.ai",
        fill=MUTED,
        font=font(18),
        anchor="mm",
    )
    return img


def hold(frames: List[Image.Image], img: Image.Image, seconds: float):
    n = max(1, int(seconds * FPS))
    for _ in range(n):
        frames.append(img.copy())


def crossfade(frames: List[Image.Image], a: Image.Image, b: Image.Image, seconds: float = 0.4):
    n = max(1, int(seconds * FPS))
    for i in range(n):
        t = (i + 1) / n
        frames.append(Image.blend(a, b, t))


def write_video(frames: List[Image.Image], path: Path):
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir(parents=True)
    for i, fr in enumerate(frames):
        fr.save(FRAMES / f"f_{i:05d}.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
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
        "17",
        "-movflags",
        "+faststart",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"wrote {path} ({len(frames)} frames, {len(frames)/FPS:.1f}s)")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    frames: List[Image.Image] = []

    structure = None
    for p in [
        ROOT / "outputs/boltz-aspirin-peptide/boltz-aspirin-peptide_still.png",
        ROOT / "outputs/boltz-aspirin-peptide/boltz-aspirin-peptide_hero.png",
        ROOT / "outputs/ubiquitin/ubiquitin_still.png",
    ]:
        if p.exists():
            structure = load_rgb(p)
            break

    # 1. Brand
    t1 = title_card("How protein structure demos run in the Omnigent UI")
    hold(frames, t1, 2.5)

    # 2. Official carousel frames (real Databricks Omnigent UI)
    carousel_dir = ASSETS / "carousel_frames"
    if carousel_dir.exists():
        cf = sorted(carousel_dir.glob("f_*.png"))
        # hold each carousel frame ~0.5s, with caption
        for i, fp in enumerate(cf):
            slide = fit_cover(load_rgb(fp), W, H)
            slide = caption_bar(
                slide,
                "Omnigent workspace UI on Databricks  ·  live agent sessions",
            )
            hold(frames, slide, 0.55 if i > 2 else 0.7)

    # 3. Product pillars from official screenshots
    for path, cap in [
        (ASSETS / "composition-dark.png", "Composition — multi-agent sessions, Share, Agents panel"),
        (ASSETS / "control-dark.png", "Control — contextual policies & approval cards"),
        (ASSETS / "collaboration-dark.png", "Collaboration — share live sessions with your team"),
    ]:
        if path.exists():
            s = screenshot_slide(path, cap)
            hold(frames, s, 2.8)

    # 4. Architecture
    arch = architecture_slide()
    hold(frames, arch, 3.2)

    # 5. YAML agent
    yml = yaml_slide()
    hold(frames, yml, 3.5)

    # 6. Protein Lab UI walkthrough
    phases = [
        ("empty", 1.8, "Start: omni run ./agents/protein-lab"),
        ("prompt", 2.2, "User prompt in the Omnigent chat"),
        ("tools", 3.2, "Tool cards stream — Boltz + render + movie"),
        ("result", 3.0, "Results + structure preview in-session"),
        ("share", 2.5, "Share the live session with a teammate"),
    ]
    prev = None
    for phase, secs, cap in phases:
        ui = protein_lab_session(phase, structure_img=structure)
        ui = caption_bar(ui, cap)
        if prev is not None:
            crossfade(frames, prev, ui, 0.35)
        hold(frames, ui, secs)
        prev = ui

    # 7. Metrics + structure
    met = metrics_slide(structure)
    hold(frames, met, 3.5)

    # 8. Inset structure spin frames if available
    spin_frames_dir = ROOT / "outputs/boltz-aspirin-peptide/frames"
    if spin_frames_dir.exists():
        spin_list = sorted(spin_frames_dir.glob("frame_*.png"))[::2]  # every other
        for fp in spin_list[:36]:
            base = protein_lab_session("result", structure_img=load_rgb(fp))
            base = caption_bar(base, "Structure movie renders into the agent workspace")
            frames.append(base)

    # 9. CTA
    cta = cta_slide()
    if prev is not None:
        crossfade(frames, frames[-1], cta, 0.4)
    hold(frames, cta, 3.5)

    out_path = ROOT / "outputs" / "omnigent_databricks_protein_lab_ui_demo.mp4"
    write_video(frames, out_path)

    # also write a poster frame
    poster = frames[len(frames) // 3]
    poster_path = ROOT / "docs" / "assets" / "omnigent_ui_demo_poster.png"
    poster.save(poster_path)
    print(f"poster → {poster_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
