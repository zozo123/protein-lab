#!/usr/bin/env python3
"""
Straight-to-point e2e short: gut/GLP-1 backdrop → Omnigent → Boltz → fold.

No hype. No flip rhetoric. Facts + real artifacts only.
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
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "straight-e2e"
FRAMES = OUT / "frames"
VO = ROOT / "outputs" / "vo_straight"
PREMIUM = ROOT / "outputs" / "glp1_premium"
UI = ROOT / "docs" / "assets" / "omnigent-ui"
W, H, FPS = 1920, 1080, 24

BG = (8, 12, 18)
WHITE = (245, 245, 250)
MUTED = (160, 170, 185)
GUT = (40, 90, 70)       # intestinal green
GUT_DK = (18, 40, 32)
PURPLE = (124, 92, 255)
TEAL = (0, 200, 160)
PINK = (220, 80, 120)

SEQ = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
CONF, PLDDT = 0.83, 0.90


def font(size: int, bold: bool = False):
    for p in (
        [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
        ]
        if bold
        else [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    ):
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


def gut_background() -> Image.Image:
    """Abstract gut / villi field — scientific backdrop, not cartoon organs."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # soft gut-toned gradient blobs
    layer = Image.new("RGB", (W, H), BG)
    ld = ImageDraw.Draw(layer)
    for cx, cy, r, col in [
        (400, 700, 500, (35, 80, 60)),
        (1400, 400, 450, (50, 40, 80)),
        (960, 900, 400, (30, 70, 55)),
        (200, 200, 300, (45, 35, 70)),
    ]:
        ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    layer = layer.filter(ImageFilter.GaussianBlur(80))
    img = Image.blend(img, layer, 0.55)

    # stylized villi ridges (bottom third)
    d = ImageDraw.Draw(img)
    for i in range(18):
        x = 40 + i * 110
        h = 80 + (i % 4) * 35
        d.ellipse([x, H - 40 - h, x + 90, H + 40], fill=(25, 55, 42), outline=(50, 100, 75), width=2)
    # peptide dots floating
    for i, aa in enumerate(SEQ[:12]):
        x = 200 + i * 130
        y = 180 + int(30 * math.sin(i * 0.9))
        d.ellipse([x, y, x + 36, y + 36], fill=(60, 50, 100), outline=PURPLE, width=2)

    # label
    d.text((48, 40), "GUT  ·  GLP-1", fill=TEAL, font=font(18, True))
    return img


def overlay_card(base: Image.Image, lines: List[Tuple[str, tuple]], y0: int = 200) -> Image.Image:
    out = base.copy()
    d = ImageDraw.Draw(out)
    # translucent panel
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([80, y0, W - 80, y0 + 80 + 70 * len(lines)], 16, fill=(8, 12, 18, 210))
    out = Image.alpha_composite(out.convert("RGBA"), panel).convert("RGB")
    d = ImageDraw.Draw(out)
    y = y0 + 40
    for text, col in lines:
        d.text((120, y), text, fill=col, font=font(36, True))
        y += 70
    return out


def fit_cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    return ImageOps.fit(im.convert("RGB"), (tw, th), method=Image.Resampling.LANCZOS)


def fit_contain(im: Image.Image, tw: int, th: int, bg=(8, 12, 18)) -> Image.Image:
    c = Image.new("RGB", (tw, th), bg)
    im = im.convert("RGB")
    im.thumbnail((tw, th), Image.Resampling.LANCZOS)
    c.paste(im, ((tw - im.width) // 2, (th - im.height) // 2))
    return c


def scene_gut_glp1() -> Image.Image:
    base = gut_background()
    d = ImageDraw.Draw(base)
    d.text((80, 120), "GLP-1", fill=WHITE, font=font(72, True))
    d.text((80, 220), "30 aa  ·  ~2 min half-life  ·  DPP-4", fill=MUTED, font=font(28))
    # sequence strip
    d.text((80, 320), SEQ, fill=TEAL, font=font(26, True))
    d.text((80, H - 80), "incretin from intestinal L-cells", fill=MUTED, font=font(20))
    return base


def scene_omnigent_boltz() -> Image.Image:
    base = gut_background()
    # darken
    base = Image.blend(base, Image.new("RGB", (W, H), BG), 0.35)
    d = ImageDraw.Draw(base)

    # left: omnigent
    d.rounded_rectangle([60, 120, 920, 960], 18, fill=(12, 14, 24), outline=PURPLE, width=3)
    d.text((100, 160), "OMNIGENT", fill=PURPLE, font=font(28, True))
    d.text((100, 220), "Databricks meta-harness", fill=WHITE, font=font(32, True))
    for i, line in enumerate(
        [
            "agent: protein-lab",
            "harness: claude-sdk",
            "tool: run_boltz_api_prediction",
            "tool: make_structure_movie",
            "policy: max_tool_calls 40",
        ]
    ):
        d.text((100, 320 + i * 55), "▸  " + line, fill=MUTED, font=font(24))

    # right: boltz
    d.rounded_rectangle([1000, 120, W - 60, 960], 18, fill=(12, 14, 24), outline=TEAL, width=3)
    d.text((1040, 160), "BOLTZ", fill=TEAL, font=font(28, True))
    d.text((1040, 220), "cloud structure", fill=WHITE, font=font(32, True))
    d.text((1040, 360), f"{CONF:.2f}", fill=TEAL, font=font(90, True))
    d.text((1040, 470), "structure confidence", fill=MUTED, font=font(22))
    d.text((1040, 560), f"{PLDDT:.2f}", fill=PURPLE, font=font(90, True))
    d.text((1040, 670), "complex pLDDT", fill=MUTED, font=font(22))
    d.text((1040, 780), "30 residues  ·  live CIF", fill=MUTED, font=font(22))

    # real UI chip if available
    ui = UI / "composition-dark.png"
    if ui.exists():
        thumb = fit_cover(Image.open(ui), 320, 180)
        base.paste(thumb, (100, 720))
        d = ImageDraw.Draw(base)
        d.text((100, 910), "Omnigent UI", fill=MUTED, font=font(16))

    return base


def scene_fold(frame: Image.Image) -> Image.Image:
    gut = gut_background()
    # darken gut
    gut = Image.blend(gut, Image.new("RGB", (W, H), BG), 0.5)
    fold = fit_contain(frame, 1400, 900, bg=(8, 12, 18))
    # center fold
    gut.paste(fold, ((W - 1400) // 2, 80))
    d = ImageDraw.Draw(gut)
    d.rectangle([0, H - 90, W, H], fill=(6, 8, 12))
    d.text((48, H - 45), "GLP-1 fold  ·  Boltz  ·  Omnigent Protein Lab", fill=WHITE, font=font(24, True), anchor="lm")
    d.text((W - 48, H - 45), f"conf {CONF}  ·  pLDDT {PLDDT}", fill=TEAL, font=font(20, True), anchor="rm")
    return gut


def scene_cta() -> Image.Image:
    base = gut_background()
    base = Image.blend(base, Image.new("RGB", (W, H), BG), 0.4)
    d = ImageDraw.Draw(base)
    d.text((W // 2, H // 2 - 60), "omni run ./agents/protein-lab", fill=TEAL, font=font(44, True), anchor="mm")
    d.text((W // 2, H // 2 + 30), "Boltz  ·  GLP-1  ·  Omnigent on Databricks", fill=MUTED, font=font(24), anchor="mm")
    return base


def hold(img: Image.Image, sec: float) -> List[Image.Image]:
    n = max(1, int(round(sec * FPS)))
    return [img.copy() for _ in range(n)]


def spin(sec: float) -> List[Image.Image]:
    files = sorted((PREMIUM / "frames").glob("frame_*.png"))
    n = max(1, int(round(sec * FPS)))
    if not files:
        return hold(scene_omnigent_boltz(), sec)
    out = []
    for i in range(n):
        idx = int((i / max(n, 1)) * len(files)) % len(files)
        out.append(scene_fold(Image.open(files[idx]).convert("RGB")))
    return out


def ensure_vo() -> List[Path]:
    VO.mkdir(parents=True, exist_ok=True)
    for p in VO.glob("*.mp3"):
        p.unlink()
    script = json.loads((ROOT / "demo/vo_script_straight.json").read_text())
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
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.2,
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


def concat_audio(files: List[Path], gap: float = 0.15) -> Tuple[Path, List[float], float]:
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
        g = gap if i < len(files) - 1 else 0.25
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

    print("=== VO ===")
    vo = ensure_vo()
    audio, durs, atot = concat_audio(vo)
    print("durs", [round(x, 2) for x in durs], "total", round(atot, 2))

    # 3 beats only — straight
    timeline: List[Image.Image] = []
    timeline += hold(scene_gut_glp1(), durs[0])
    timeline += hold(scene_omnigent_boltz(), durs[1] * 0.55)
    timeline += spin(durs[1] * 0.45)
    timeline += spin(durs[2] * 0.55)
    timeline += hold(scene_cta(), durs[2] * 0.45)

    need = int(round(atot * FPS))
    if len(timeline) < need:
        timeline += [timeline[-1].copy() for _ in range(need - len(timeline))]
    else:
        timeline = timeline[:need]

    print(f"frames {len(timeline)} ({len(timeline)/FPS:.1f}s)")
    for i, fr in enumerate(timeline):
        fr.save(FRAMES / f"f_{i:05d}.png")

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
            "16",
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
            "loudnorm=I=-15:TP=-1.5:LRA=10",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(loud),
        ],
        check=True,
        capture_output=True,
    )

    final = ROOT / "outputs" / "omnigent_boltz_glp1_straight.mp4"
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
        "omnigent_glp1_30s_nyt.mp4",
        "FINAL_omnigent_glp1_demo.mp4",
        "omnigent_glp1_hormone_e2e_demo.mp4",
    ]:
        shutil.copy(final, ROOT / "outputs" / name)

    meta = {
        "final": str(final),
        "duration_s": ffprobe_dur(final),
        "script": [
            "Gut releases GLP-1 after a meal. Thirty amino acids. Gone in about two minutes.",
            "Omnigent agent on Databricks. Tool call: Boltz. Sequence in. Structure out. Confidence 0.83. pLDDT 0.9.",
            "omni run agents protein-lab. That's the demo.",
        ],
        "metrics": {"confidence": CONF, "plddt": PLDDT},
    }
    (ROOT / "outputs" / "straight_e2e_session.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
