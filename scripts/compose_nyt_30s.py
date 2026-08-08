#!/usr/bin/env python3
"""
30-second NYT-style short — measured, specific, no hype rhetoric.

Visual grammar (documentary / NYT video essay):
  - Quiet opens, long enough holds to read
  - One idea per beat
  - Real assets only (Boltz CIF spin, official Omnigent UI, real metrics)
  - Lower-thirds as captions, not shouts
  - No "not X, it's Y" framing; no scoreboard gimmicks

Audio: George (storyteller), slower delivery, loudnorm broadcast.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "nyt-30s"
FRAMES = OUT / "frames"
VO = ROOT / "outputs" / "vo_nyt"
UI = ROOT / "docs" / "assets" / "omnigent-ui"
PREMIUM = ROOT / "outputs" / "glp1_premium"
W, H, FPS = 1920, 1080, 24

# Restrained palette
BG = (12, 14, 20)
WHITE = (242, 242, 245)
MUTED = (150, 155, 170)
INK = (230, 230, 235)
LINE = (80, 85, 100)
ACCENT = (180, 160, 220)  # soft violet, not neon scream
TEAL = (120, 180, 170)

SEQ = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
CONF, PLDDT = 0.83, 0.90


def font(size: int, bold: bool = False):
    paths = (
        [
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        ]
        if bold
        else [
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
    )
    paths += ["/System/Library/Fonts/Helvetica.ttc"]
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


def canvas(color=BG) -> Image.Image:
    return Image.new("RGB", (W, H), color)


def soft_field() -> Image.Image:
    img = canvas()
    g = canvas()
    d = ImageDraw.Draw(g)
    d.ellipse([W // 2 - 480, H // 2 - 280, W // 2 + 480, H // 2 + 320], fill=(28, 30, 48))
    g = g.filter(ImageFilter.GaussianBlur(90))
    return Image.blend(img, g, 0.45)


def fit_cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    return ImageOps.fit(im.convert("RGB"), (tw, th), method=Image.Resampling.LANCZOS)


def fit_contain(im: Image.Image, tw: int, th: int, bg=BG) -> Image.Image:
    c = canvas(bg)
    im = im.convert("RGB")
    im.thumbnail((tw, th), Image.Resampling.LANCZOS)
    c.paste(im, ((tw - im.width) // 2, (th - im.height) // 2))
    return c


def caption(img: Image.Image, text: str, small: str = "") -> Image.Image:
    """Thin documentary caption bar."""
    out = img.copy()
    d = ImageDraw.Draw(out)
    d.rectangle([0, H - 88, W, H], fill=(8, 9, 12))
    d.line([48, H - 88, 48, H], fill=ACCENT, width=3)
    d.text((64, H - 50), text, fill=WHITE, font=font(22), anchor="lm")
    if small:
        d.text((W - 48, H - 50), small, fill=MUTED, font=font(16), anchor="rm")
    return out


def scene_open() -> Image.Image:
    img = soft_field()
    d = ImageDraw.Draw(img)
    d.text((W // 2, H // 2 - 60), "GLP-1", fill=WHITE, font=font(72, True), anchor="mm")
    d.text(
        (W // 2, H // 2 + 30),
        "thirty amino acids  ·  roughly two minutes",
        fill=MUTED,
        font=font(26),
        anchor="mm",
    )
    d.line([W // 2 - 40, H // 2 + 80, W // 2 + 40, H // 2 + 80], fill=ACCENT, width=2)
    return img


def scene_sequence() -> Image.Image:
    img = canvas()
    d = ImageDraw.Draw(img)
    d.text((80, 80), "Sequence", fill=MUTED, font=font(18))
    d.text((80, 120), "GLP-1 (7–36) amide", fill=WHITE, font=font(40, True))

    # restrained sequence row — two lines
    mono = font(28, True)
    y = 280
    for row, chunk in enumerate([SEQ[:15], SEQ[15:]]):
        x = 80
        for i, aa in enumerate(chunk):
            d.text((x, y + row * 100), aa, fill=INK if (i + row * 15) % 2 == 0 else MUTED, font=mono)
            x += 52

    d.text((80, 520), "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR", fill=TEAL, font=font(22))
    d.text((80, 600), "Incretin from the gut. Clears under DPP-4 in about one to two minutes.", fill=MUTED, font=font(24))
    d.text((80, 680), "The same molecular idea, stabilized, underpins modern metabolic medicines.", fill=MUTED, font=font(24))
    d.text((80, H - 100), "Source: prediction-input-glp1.json", fill=LINE, font=font(16))
    return img


def scene_omnigent() -> Image.Image:
    """Official product still + quiet label."""
    stage = canvas((10, 10, 14))
    # Prefer real product screenshot
    for p in [
        UI / "composition-dark.png",
        UI / "carousel_frames" / "f_010.png",
        UI / "control-dark.png",
    ]:
        if p.exists():
            win = fit_contain(Image.open(p), 1680, 900, bg=(10, 10, 14))
            stage.paste(win, ((W - 1680) // 2, 40))
            break
    return caption(stage, "Omnigent on Databricks  ·  shared agent session", "meta-harness")


def scene_yaml_quiet() -> Image.Image:
    img = canvas()
    d = ImageDraw.Draw(img)
    d.text((120, 100), "Protein Lab", fill=WHITE, font=font(36, True))
    d.text((120, 160), "agents/protein-lab/config.yaml", fill=MUTED, font=font(20))
    lines = [
        "name: protein-lab",
        "executor:",
        "  harness: claude-sdk",
        "tools:",
        "  run_boltz_api_prediction: …",
        "  make_structure_movie: …",
        "policies:",
        "  max_tool_calls: 40",
    ]
    y = 260
    for line in lines:
        col = ACCENT if "harness" in line or line.startswith("name") else MUTED
        if line.startswith("tools") or line.startswith("policies"):
            col = WHITE
        d.text((140, y), line, fill=col, font=font(28))
        y += 48
    d.text((120, H - 120), "One agent file. Tools, policies, and a live session.", fill=MUTED, font=font(22))
    return img


def scene_metrics() -> Image.Image:
    img = soft_field()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 160), "Boltz prediction", fill=MUTED, font=font(20), anchor="mm")
    d.text((W // 2, 230), "Live run", fill=WHITE, font=font(44, True), anchor="mm")

    pairs = [
        (f"{CONF:.2f}", "structure confidence"),
        (f"{PLDDT:.2f}", "complex pLDDT"),
        ("30", "residues"),
    ]
    x = 200
    for val, lab in pairs:
        d.text((x + 200, 480), val, fill=WHITE, font=font(72, True), anchor="mm")
        d.text((x + 200, 580), lab, fill=MUTED, font=font(22), anchor="mm")
        x += 500
    d.text((W // 2, 780), "boltz-api  ·  sab_pred_…_predicted.cif", fill=LINE, font=font(18), anchor="mm")
    return img


def scene_fold(frame: Image.Image) -> Image.Image:
    base = fit_cover(frame, W, H)
    # slight vignette
    vig = Image.new("RGB", (W, H), (0, 0, 0))
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([-200, -200, W + 200, H + 200], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(80))
    base = Image.composite(base, Image.blend(base, vig, 0.35), mask)
    return caption(base, "GLP-1 fold  ·  Boltz  ·  N→C", "Protein Lab")


def scene_close() -> Image.Image:
    img = soft_field()
    d = ImageDraw.Draw(img)
    d.text((W // 2, H // 2 - 40), "Sequence to structure.", fill=WHITE, font=font(44, True), anchor="mm")
    d.text((W // 2, H // 2 + 40), "omni run ./agents/protein-lab", fill=TEAL, font=font(28), anchor="mm")
    d.text((W // 2, H - 100), "docs.databricks.com/aws/en/omnigent", fill=LINE, font=font(18), anchor="mm")
    return img


def hold(img: Image.Image, sec: float) -> List[Image.Image]:
    n = max(1, int(round(sec * FPS)))
    return [img.copy() for _ in range(n)]


def ease_hold(img: Image.Image, sec: float, zoom: float = 1.03) -> List[Image.Image]:
    """Very slight drift — documentary, not kinetic chaos."""
    n = max(1, int(round(sec * FPS)))
    out = []
    for i in range(n):
        t = i / max(n - 1, 1)
        z = 1.0 + (zoom - 1.0) * t
        iw, ih = img.size
        nw, nh = int(iw / z), int(ih / z)
        ox = (iw - nw) // 2
        oy = int((ih - nh) * (0.45 + 0.05 * t))
        out.append(img.crop((ox, oy, ox + nw, oy + nh)).resize((W, H), Image.Resampling.LANCZOS))
    return out


def spin(sec: float) -> List[Image.Image]:
    files = sorted((PREMIUM / "frames").glob("frame_*.png"))
    n = max(1, int(round(sec * FPS)))
    if not files:
        return hold(scene_metrics(), sec)
    out = []
    # slow spin: use every other frame or stretch
    for i in range(n):
        # map i across full rotation slowly
        idx = int((i / max(n, 1)) * len(files)) % len(files)
        fr = Image.open(files[idx]).convert("RGB")
        out.append(scene_fold(fr))
    return out


def ensure_vo() -> List[Path]:
    VO.mkdir(parents=True, exist_ok=True)
    # Force regenerate for new script
    script = json.loads((ROOT / "demo/vo_script_nyt.json").read_text())
    key_path = ROOT / ".env"
    if not key_path.exists():
        key_path = Path.home() / "Developer/video-use/.env"
    key = key_path.read_text().split("ELEVENLABS_API_KEY=", 1)[1].strip().splitlines()[0]
    files = []
    for seg in script["segments"]:
        out = VO / f"{seg['id']}.mp3"
        files.append(out)
        print(" TTS", seg["id"])
        body = json.dumps(
            {
                "text": seg["text"],
                "model_id": script["model_id"],
                "voice_settings": {
                    "stability": 0.55,
                    "similarity_boost": 0.75,
                    "style": 0.15,
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
        time.sleep(0.2)
    return files


def concat_audio(files: List[Path], gap: float = 0.20) -> Tuple[Path, List[float], float]:
    silence = OUT / "sil.mp3"
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
    durs, lines = [], []
    for i, f in enumerate(files):
        d = ffprobe_dur(f)
        g = gap if i < len(files) - 1 else 0.35  # breath at end
        durs.append(d + g)
        lines.append(f"file '{f.resolve()}'")
        if g > 0:
            # for end breath use longer silence
            if i == len(files) - 1:
                end_sil = OUT / "end_sil.mp3"
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
                        str(end_sil),
                    ],
                    check=True,
                    capture_output=True,
                )
                lines.append(f"file '{end_sil.resolve()}'")
            else:
                lines.append(f"file '{silence.resolve()}'")
    lp = OUT / "alist.txt"
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

    print("=== VO (NYT) ===")
    # wipe old VO to force new takes
    if VO.exists():
        for p in VO.glob("*.mp3"):
            p.unlink()
    vo = ensure_vo()
    audio, durs, atot = concat_audio(vo, gap=0.22)
    print("segment durs", [round(d, 2) for d in durs], "total", round(atot, 2))

    # If VO is longer than ~32s, we still sync to audio (target ~30)
    # Visual plan mapped 1:1 to 4 VO segments
    timeline: List[Image.Image] = []

    # 01 open + sequence
    d0 = durs[0]
    timeline += ease_hold(scene_open(), d0 * 0.45, zoom=1.02)
    timeline += ease_hold(scene_sequence(), d0 * 0.55, zoom=1.015)

    # 02 medicine line — still sequence context + metrics whisper
    d1 = durs[1]
    timeline += ease_hold(scene_sequence(), d1 * 0.4, zoom=1.01)
    timeline += ease_hold(scene_metrics(), d1 * 0.6, zoom=1.02)

    # 03 Omnigent + yaml + boltz proof
    d2 = durs[2]
    timeline += hold(scene_omnigent(), d2 * 0.35)
    timeline += ease_hold(scene_yaml_quiet(), d2 * 0.25, zoom=1.01)
    timeline += ease_hold(scene_metrics(), d2 * 0.15, zoom=1.02)
    timeline += spin(d2 * 0.25)

    # 04 close on fold + CTA
    d3 = durs[3]
    timeline += spin(d3 * 0.65)
    timeline += ease_hold(scene_close(), d3 * 0.35, zoom=1.02)

    need = int(round(atot * FPS))
    if len(timeline) < need:
        timeline += [timeline[-1].copy() for _ in range(need - len(timeline))]
    else:
        timeline = timeline[:need]

    # If still over 34s of content, that's ok — VO drives length
    # Target was 30s script; actual depends on delivery

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
    # gentler processing for documentary feel
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(audio),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(loud),
        ],
        check=True,
        capture_output=True,
    )

    final = ROOT / "outputs" / "omnigent_glp1_30s_nyt.mp4"
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

    # Also update main ship names to the 30s cut as primary
    for name in [
        "FINAL_omnigent_glp1_demo.mp4",
        "omnigent_glp1_hormone_e2e_demo.mp4",
        "BEAST_omnigent_boltz_glp1_demo.mp4",
    ]:
        shutil.copy(final, ROOT / "outputs" / name)

    dur = ffprobe_dur(final)
    meta = {
        "final": str(final),
        "duration_s": dur,
        "style": "NYT short / measured documentary",
        "rhetoric": "no not-X-but-Y; specific facts only",
        "metrics": {"structure_confidence": CONF, "plddt": PLDDT},
        "voice": "George (storyteller, restrained)",
        "script": "demo/vo_script_nyt.json",
    }
    (ROOT / "outputs" / "nyt_30s_session.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
