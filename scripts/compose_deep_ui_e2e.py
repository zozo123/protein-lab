#!/usr/bin/env python3
"""
Deep visual + text e2e short:
  gut/GLP-1 world → REAL Omnigent-by-Databricks UI (heavy) → Boltz proof → fold.

Emphasizes product UI screenshots from docs.databricks.com / omnigent.ai
composited over gut-science backdrop. Deeper copy, still tight (~30–40s).
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
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "deep-ui-e2e"
FRAMES = OUT / "frames"
VO = ROOT / "outputs" / "vo_deep"
UI = ROOT / "docs" / "assets" / "omnigent-ui"
PREMIUM = ROOT / "outputs" / "glp1_premium"
W, H, FPS = 1920, 1080, 24

BG = (6, 10, 16)
WHITE = (248, 248, 252)
MUTED = (165, 175, 190)
TEAL = (0, 210, 165)
PURPLE = (140, 110, 255)
PINK = (236, 72, 153)  # Omnigent Share pink
GUT = (28, 70, 55)

SEQ = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
CONF, PLDDT, PTM = 0.83, 0.90, 0.58


def font(size: int, bold: bool = False):
    paths = (
        [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
        ]
        if bold
        else [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    )
    for p in paths:
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


def gut_world(dim: float = 0.0) -> Image.Image:
    """Deeper gut / incretin atmosphere."""
    img = Image.new("RGB", (W, H), BG)
    layer = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(layer)
    for cx, cy, r, col in [
        (300, 850, 550, (32, 85, 62)),
        (1600, 200, 480, (55, 30, 90)),
        (900, 1000, 520, (25, 65, 50)),
        (500, 300, 280, (40, 50, 90)),
        (1400, 800, 350, (70, 35, 70)),
    ]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    layer = layer.filter(ImageFilter.GaussianBlur(70))
    img = Image.blend(img, layer, 0.6)

    d = ImageDraw.Draw(img)
    # villi ridge
    for i in range(22):
        x = 20 + i * 95
        h = 70 + (i * 17 % 90)
        d.ellipse([x, H - 30 - h, x + 85, H + 50], fill=(22, 55, 40), outline=(45, 100, 72), width=2)
    # circulating peptide glyphs
    for i, aa in enumerate(SEQ):
        ang = i / 30 * math.pi * 2
        x = int(W * 0.5 + 420 * math.cos(ang * 0.7 + 0.4))
        y = int(280 + 90 * math.sin(ang * 1.3))
        d.ellipse([x, y, x + 28, y + 28], fill=(35, 30, 60), outline=PURPLE, width=1)
        d.text((x + 14, y + 14), aa, fill=MUTED, font=font(11, True), anchor="mm")

    if dim > 0:
        img = Image.blend(img, Image.new("RGB", (W, H), BG), dim)
    return img


def fit_cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    return ImageOps.fit(im.convert("RGB"), (tw, th), method=Image.Resampling.LANCZOS)


def fit_contain(im: Image.Image, tw: int, th: int, bg=BG) -> Image.Image:
    c = Image.new("RGB", (tw, th), bg)
    im = im.convert("RGB")
    im.thumbnail((tw, th), Image.Resampling.LANCZOS)
    c.paste(im, ((tw - im.width) // 2, (th - im.height) // 2))
    return c


def glass_panel(base: Image.Image, box, alpha: int = 200) -> Image.Image:
    out = base.convert("RGBA")
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle(box, 18, fill=(8, 12, 20, alpha))
    return Image.alpha_composite(out, panel).convert("RGB")


def badge(d: ImageDraw.ImageDraw, x: int, y: int, text: str, fill=PINK):
    tw = int(font(14, True).getlength(text) + 28)
    d.rounded_rectangle([x, y, x + tw, y + 32], 10, fill=fill)
    d.text((x + tw // 2, y + 16), text, fill=WHITE, font=font(14, True), anchor="mm")


def scene_gut_deep() -> Image.Image:
    img = gut_world(0.1)
    d = ImageDraw.Draw(img)
    img = glass_panel(img, [60, 80, 1100, 720], 215)
    d = ImageDraw.Draw(img)
    d.text((100, 120), "INTESTINAL L-CELLS", fill=TEAL, font=font(16, True))
    d.text((100, 170), "GLP-1 (7–36)", fill=WHITE, font=font(56, True))
    d.text((100, 250), "glucagon-like peptide-1  ·  incretin hormone", fill=MUTED, font=font(22))

    facts = [
        ("30", "amino acids"),
        ("~2 min", "plasma half-life"),
        ("DPP-4", "clears the peptide"),
        ("P01275", "UniProt proglucagon"),
    ]
    x = 100
    for a, b in facts:
        d.rounded_rectangle([x, 340, x + 220, 480], 12, fill=(16, 22, 30), outline=(50, 80, 70), width=2)
        d.text((x + 110, 390), a, fill=TEAL, font=font(28, True), anchor="mm")
        d.text((x + 110, 440), b, fill=MUTED, font=font(16), anchor="mm")
        x += 240

    d.text((100, 540), SEQ, fill=PURPLE, font=font(20, True))
    d.text((100, 600), "Raises insulin when glucose is high. Lowers appetite signaling.", fill=MUTED, font=font(20))
    d.text((100, 650), "Stabilized analogs → modern metabolic medicines.", fill=MUTED, font=font(20))

    # right callout
    d.rounded_rectangle([1180, 120, W - 60, 700], 16, fill=(14, 18, 28), outline=PINK, width=2)
    d.text((1220, 170), "WHY IT MATTERS", fill=PINK, font=font(16, True))
    for i, line in enumerate(
        [
            "Short half-life made the",
            "native peptide hard to use",
            "as a drug.",
            "",
            "Structure + chemistry",
            "extended the same signal",
            "from minutes to days.",
        ]
    ):
        d.text((1220, 230 + i * 42), line, fill=MUTED if line else MUTED, font=font(22))
    return img


def scene_ui_hero(path: Path, title: str, bullets: List[str], tag: str) -> Image.Image:
    """Giant real Omnigent UI on gut world."""
    base = gut_world(0.45)
    raw = Image.open(path).convert("RGB")
    # large product window
    win = fit_contain(raw, 1520, 860, bg=(8, 8, 12))
    # drop shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([160, 70, 1760, 980], 20, fill=(0, 0, 0, 160))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    base = Image.alpha_composite(base.convert("RGBA"), sh).convert("RGB")
    base.paste(win, ((W - 1520) // 2, 90))

    d = ImageDraw.Draw(base)
    # top product bar
    d.rectangle([0, 0, W, 70], fill=(8, 10, 16))
    badge(d, 40, 18, "OMNIGENT ON DATABRICKS", PINK)
    d.text((320, 35), title, fill=WHITE, font=font(22, True), anchor="lm")
    d.text((W - 40, 35), tag, fill=TEAL, font=font(16, True), anchor="rm")

    # bottom deep captions
    d.rectangle([0, H - 100, W, H], fill=(6, 8, 12))
    d.line([0, H - 100, W, H - 100], fill=PINK, width=3)
    x = 40
    for b in bullets:
        d.text((x, H - 50), "·  " + b, fill=MUTED, font=font(18), anchor="lm")
        x += int(font(18).getlength("·  " + b) + 36)
    return base


def scene_ui_triptych() -> Image.Image:
    """Three official UI shots: composition / control / collab."""
    base = gut_world(0.5)
    d = ImageDraw.Draw(base)
    d.text((W // 2, 50), "Omnigent by Databricks — product surface", fill=WHITE, font=font(28, True), anchor="mm")

    shots = [
        (UI / "composition-dark.png", "Composition", "multi-agent · Share · Agents"),
        (UI / "control-dark.png", "Control", "policies · approvals"),
        (UI / "collaboration-dark.png", "Collaboration", "live session · comments"),
    ]
    x = 50
    for path, title, sub in shots:
        if not path.exists():
            continue
        thumb = fit_cover(Image.open(path), 580, 720)
        # frame
        d.rounded_rectangle([x - 6, 100, x + 586, 900], 14, outline=PURPLE, width=2)
        base.paste(thumb, (x, 110))
        d = ImageDraw.Draw(base)
        d.rectangle([x, 840, x + 580, 900], fill=(10, 12, 18))
        d.text((x + 20, 855), title, fill=PINK, font=font(20, True))
        d.text((x + 20, 880), sub, fill=MUTED, font=font(15))
        x += 620
    return base


def scene_carousel_hold(path: Path, caption: str) -> Image.Image:
    base = gut_world(0.4)
    win = fit_contain(Image.open(path).convert("RGB"), 1600, 900, bg=(10, 10, 14))
    base.paste(win, ((W - 1600) // 2, 50))
    d = ImageDraw.Draw(base)
    d.rectangle([0, 0, W, 56], fill=(8, 10, 16))
    badge(d, 36, 12, "LIVE WORKSPACE UI", PINK)
    d.text((280, 28), "docs.databricks.com/aws/en/omnigent", fill=MUTED, font=font(16), anchor="lm")
    d.rectangle([0, H - 80, W, H], fill=(6, 8, 12))
    d.text((48, H - 40), caption, fill=WHITE, font=font(22, True), anchor="lm")
    d.text((W - 48, H - 40), "Omnigent · Databricks", fill=TEAL, font=font(16), anchor="rm")
    return base


def scene_stack() -> Image.Image:
    base = gut_world(0.35)
    base = glass_panel(base, [50, 60, W - 50, H - 60], 220)
    d = ImageDraw.Draw(base)

    d.text((100, 100), "PROTEIN LAB  →  BOLTZ", fill=WHITE, font=font(36, True))
    d.text((100, 160), "Custom Omnigent agent  ·  live cloud prediction", fill=MUTED, font=font(22))

    # yaml column
    d.rounded_rectangle([100, 230, 900, 920], 14, fill=(12, 16, 26), outline=PURPLE, width=2)
    d.text((130, 260), "agents/protein-lab/config.yaml", fill=PURPLE, font=font(16, True))
    yaml_lines = [
        ("name: protein-lab", TEAL),
        ("executor:", MUTED),
        ("  harness: claude-sdk", PURPLE),
        ("  # swap: codex | pi | grok", MUTED),
        ("tools:", WHITE),
        ("  run_boltz_api_prediction", PINK),
        ("  render_structure", PINK),
        ("  make_structure_movie", PINK),
        ("policies:", WHITE),
        ("  max_tool_calls: 40", TEAL),
        ("os_env:", MUTED),
        ("  sandbox: write outputs/", MUTED),
        ("  allow_network: true", MUTED),
    ]
    y = 310
    for line, col in yaml_lines:
        d.text((140, y), line, fill=col, font=font(24, True if "harness" in line or line.startswith("name") else False))
        y += 42

    # metrics column
    d.rounded_rectangle([960, 230, W - 100, 920], 14, fill=(12, 16, 26), outline=TEAL, width=2)
    d.text((1000, 270), "LIVE BOLTZ RUN", fill=TEAL, font=font(18, True))
    metrics = [
        (f"{CONF:.2f}", "structure confidence"),
        (f"{PLDDT:.2f}", "complex pLDDT"),
        (f"{PTM:.2f}", "pTM"),
        ("30", "residues (GLP-1 7–36)"),
    ]
    y = 340
    for val, lab in metrics:
        d.text((1000, y), val, fill=WHITE, font=font(52, True))
        d.text((1000, y + 60), lab, fill=MUTED, font=font(20))
        y += 130
    d.text((1000, 860), "prediction-input-glp1.json → CIF", fill=MUTED, font=font(16))
    return base


def scene_fold(frame: Image.Image) -> Image.Image:
    base = gut_world(0.55)
    fold = fit_contain(frame, 1500, 880, bg=(6, 10, 16))
    # frame chrome like product
    d = ImageDraw.Draw(base)
    d.rounded_rectangle([180, 60, 1740, 980], 16, outline=PINK, width=3)
    base.paste(fold, ((W - 1500) // 2, 90))
    d = ImageDraw.Draw(base)
    badge(d, 210, 80, "BOLTZ CIF  ·  GLP-1", TEAL)
    d.rectangle([0, H - 88, W, H], fill=(6, 8, 12))
    d.text((48, H - 44), "Fold from Omnigent session  ·  conf 0.83  ·  pLDDT 0.90", fill=WHITE, font=font(22, True), anchor="lm")
    d.text((W - 48, H - 44), "omni run ./agents/protein-lab", fill=TEAL, font=font(18, True), anchor="rm")
    return base


def scene_cta() -> Image.Image:
    base = gut_world(0.4)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle([200, 280, W - 200, 760], 20, fill=(10, 14, 22), outline=PINK, width=3)
    d.text((W // 2, 380), "Run the session", fill=MUTED, font=font(22), anchor="mm")
    d.text((W // 2, 480), "omni run ./agents/protein-lab", fill=TEAL, font=font(44, True), anchor="mm")
    d.text((W // 2, 580), "Boltz  ·  GLP-1  ·  Omnigent on Databricks", fill=MUTED, font=font(24), anchor="mm")
    d.text((W // 2, 680), "docs.databricks.com/aws/en/omnigent", fill=PURPLE, font=font(18), anchor="mm")
    return base


def hold(img: Image.Image, sec: float) -> List[Image.Image]:
    n = max(1, int(round(sec * FPS)))
    return [img.copy() for _ in range(n)]


def drift(img: Image.Image, sec: float, z1: float = 1.04) -> List[Image.Image]:
    n = max(1, int(round(sec * FPS)))
    out = []
    for i in range(n):
        t = i / max(n - 1, 1)
        z = 1.0 + (z1 - 1.0) * t
        iw, ih = img.size
        nw, nh = int(iw / z), int(ih / z)
        ox, oy = (iw - nw) // 2, int((ih - nh) * 0.4)
        out.append(img.crop((ox, oy, ox + nw, oy + nh)).resize((W, H), Image.Resampling.LANCZOS))
    return out


def spin(sec: float) -> List[Image.Image]:
    files = sorted((PREMIUM / "frames").glob("frame_*.png"))
    n = max(1, int(round(sec * FPS)))
    if not files:
        return hold(scene_stack(), sec)
    out = []
    for i in range(n):
        idx = int((i / max(n, 1)) * len(files)) % len(files)
        out.append(scene_fold(Image.open(files[idx]).convert("RGB")))
    return out


def ensure_vo() -> List[Path]:
    VO.mkdir(parents=True, exist_ok=True)
    for p in VO.glob("*.mp3"):
        p.unlink()
    script = json.loads((ROOT / "demo/vo_script_deep.json").read_text())
    key_path = ROOT / ".env"
    if not key_path.exists():
        key_path = Path.home() / "Developer/video-use/.env"
    key = key_path.read_text().split("ELEVENLABS_API_KEY=", 1)[1].strip().splitlines()[0]
    files = []
    for seg in script["segments"]:
        out = VO / f"{seg['id']}.mp3"
        files.append(out)
        print("TTS", seg["id"])
        body = json.dumps(
            {
                "text": seg["text"],
                "model_id": script["model_id"],
                "voice_settings": {
                    "stability": 0.48,
                    "similarity_boost": 0.8,
                    "style": 0.22,
                    "use_speaker_boost": True,
                },
            }
        ).encode()
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{script['voice_id']}",
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
        time.sleep(0.15)
    return files


def concat_audio(files: List[Path], gap: float = 0.18) -> Tuple[Path, List[float], float]:
    sil = OUT / "sil.mp3"
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
            str(sil),
        ],
        check=True,
        capture_output=True,
    )
    durs, lines = [], []
    for i, f in enumerate(files):
        d = ffprobe_dur(f)
        g = gap if i < len(files) - 1 else 0.3
        durs.append(d + g)
        lines.append(f"file '{f.resolve()}'")
        if g:
            if i == len(files) - 1:
                end = OUT / "end.mp3"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        "anullsrc=r=44100:cl=mono",
                        "-t",
                        str(g),
                        "-q:a",
                        "9",
                        "-acodec",
                        "libmp3lame",
                        str(end),
                    ],
                    check=True,
                    capture_output=True,
                )
                lines.append(f"file '{end.resolve()}'")
            else:
                lines.append(f"file '{sil.resolve()}'")
    lp = OUT / "a.txt"
    lp.write_text("\n".join(lines) + "\n")
    audio = OUT / "narration.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lp), "-c", "copy", str(audio)],
        check=True,
        capture_output=True,
    )
    return audio, durs, ffprobe_dur(audio)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir()

    if not (PREMIUM / "frames").exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/render_glp1_premium.py")], check=True, cwd=str(ROOT))

    # require UI assets
    for need in ["composition-dark.png", "control-dark.png", "collaboration-dark.png"]:
        if not (UI / need).exists():
            print("missing UI asset", need, file=sys.stderr)

    print("=== VO deep ===")
    vo = ensure_vo()
    audio, durs, atot = concat_audio(vo)
    print("durs", [round(x, 2) for x in durs], "total", round(atot, 2))

    carousel = sorted((UI / "carousel_frames").glob("f_*.png"))
    timeline: List[Image.Image] = []

    # 01 GUT deep
    timeline += drift(scene_gut_deep(), durs[0], z1=1.03)

    # 02 UI HEAVY — real Omnigent product
    d1 = durs[1]
    # carousel walkthrough (official Databricks workspace UI)
    if carousel:
        n = max(1, int(d1 * 0.45 * FPS))
        for i in range(n):
            fp = carousel[min(len(carousel) - 1, 6 + (i * 2) % max(1, len(carousel) - 6))]
            timeline.append(
                scene_carousel_hold(
                    fp,
                    "Omnigent workspace UI  ·  chat · files · Share · agents",
                )
            )
    # composition hero
    if (UI / "composition-dark.png").exists():
        timeline += hold(
            scene_ui_hero(
                UI / "composition-dark.png",
                "Composition — multi-agent sessions",
                ["Share live URL", "Agents panel", "Tool streaming", "Chat + Terminal"],
                "COMPOSITION",
            ),
            d1 * 0.25,
        )
    # triptych pillars
    timeline += hold(scene_ui_triptych(), d1 * 0.30)

    # 03 stack yaml + boltz
    d2 = durs[2]
    timeline += drift(scene_stack(), d2 * 0.55, z1=1.02)
    if (UI / "control-dark.png").exists():
        timeline += hold(
            scene_ui_hero(
                UI / "control-dark.png",
                "Control — contextual policies",
                ["Approvals", "Guardrails", "Pre-tool gates", "Session safety"],
                "CONTROL",
            ),
            d2 * 0.20,
        )
    timeline += spin(d2 * 0.25)

    # 04 fold + cta
    d3 = durs[3]
    timeline += spin(d3 * 0.65)
    timeline += hold(scene_cta(), d3 * 0.35)

    need = int(round(atot * FPS))
    if len(timeline) < need:
        timeline += [timeline[-1].copy() for _ in range(need - len(timeline))]
    else:
        timeline = timeline[:need]

    print(f"frames {len(timeline)} ({len(timeline)/FPS:.1f}s)")
    for i, fr in enumerate(timeline):
        fr.save(FRAMES / f"f_{i:05d}.png")
        if i % 200 == 0:
            print(i)

    silent = OUT / "silent.mp4"
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
            "15",
            "-movflags",
            "+faststart",
            str(silent),
        ],
        check=True,
        capture_output=True,
    )
    loud = OUT / "narr.m4a"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(audio),
            "-af",
            "loudnorm=I=-15:TP=-1.5:LRA=11",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(loud),
        ],
        check=True,
        capture_output=True,
    )

    final = ROOT / "outputs" / "omnigent_boltz_glp1_deep_ui.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent),
            "-i",
            str(loud),
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
    for name in [
        "omnigent_boltz_glp1_straight.mp4",
        "FINAL_omnigent_glp1_demo.mp4",
        "omnigent_glp1_30s_nyt.mp4",
        "omnigent_glp1_hormone_e2e_demo.mp4",
    ]:
        shutil.copy(final, ROOT / "outputs" / name)

    meta = {
        "final": str(final),
        "duration_s": ffprobe_dur(final),
        "ui": [
            "carousel (Databricks Omnigent workspace)",
            "composition-dark.png",
            "control-dark.png",
            "collaboration-dark.png",
            "triptych + hero composites on gut backdrop",
        ],
        "metrics": {"confidence": CONF, "plddt": PLDDT, "ptm": PTM},
    }
    (ROOT / "outputs" / "deep_ui_session.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
