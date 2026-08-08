#!/usr/bin/env python3
"""
Compose the full GLP-1 e2e narrated demo film.

Visuals timed to ElevenLabs VO segments + structure spin + Omnigent UI beats.
Output: outputs/omnigent_glp1_hormone_e2e_demo.mp4
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.protein_tools import (  # noqa: E402
    make_structure_movie,
    render_structure,
    summarize_structure,
)

W, H = 1920, 1080
FPS = 24
OUT = ROOT / "outputs" / "glp1-film"
FRAMES = OUT / "frames"
VO = ROOT / "outputs" / "vo"


def font(size: int, bold: bool = False):
    for path in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else None,
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if path and Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


BG = (11, 15, 26)
WHITE = (245, 245, 250)
MUTED = (160, 168, 190)
PURPLE = (124, 92, 255)
TEAL = (0, 212, 170)
PINK = (236, 72, 153)
YELLOW = (251, 191, 36)


def ffprobe_dur(path: Path) -> float:
    out = subprocess.check_output(
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
    return float(out)


def new_canvas(color=BG) -> Image.Image:
    return Image.new("RGB", (W, H), color)


def glow_bg() -> Image.Image:
    img = new_canvas()
    g = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(g)
    d.ellipse([W // 2 - 500, H // 2 - 280, W // 2 + 500, H // 2 + 320], fill=(45, 25, 80))
    g = g.filter(ImageFilter.GaussianBlur(90))
    return Image.blend(img, g, 0.55)


def rrect(d, box, r, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def fit_cover(img: Image.Image, tw: int, th: int) -> Image.Image:
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    l, t = (nw - tw) // 2, (nh - th) // 2
    return img.crop((l, t, l + tw, t + th))


def fit_contain(img: Image.Image, tw: int, th: int, bg=BG) -> Image.Image:
    c = Image.new("RGB", (tw, th), bg)
    iw, ih = img.size
    s = min(tw / iw, th / ih)
    nw, nh = max(1, int(iw * s)), max(1, int(ih * s))
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    c.paste(img, ((tw - nw) // 2, (th - nh) // 2))
    return c


def caption(img: Image.Image, text: str) -> Image.Image:
    out = img.copy()
    d = ImageDraw.Draw(out)
    d.rectangle([0, H - 100, W, H], fill=(6, 8, 14))
    d.rectangle([0, H - 102, W, H - 100], fill=PURPLE)
    d.text((48, H - 50), text, fill=WHITE, font=font(26, True), anchor="lm")
    d.text((W - 48, H - 50), "Omnigent · Databricks · GLP-1", fill=MUTED, font=font(16), anchor="rm")
    return out


def slide_title(title: str, sub: str) -> Image.Image:
    img = glow_bg()
    d = ImageDraw.Draw(img)
    rrect(d, [W // 2 - 200, 280, W // 2 + 200, 320], 16, fill=(40, 30, 70), outline=PURPLE, width=2)
    d.text((W // 2, 300), "Omnigent on Databricks", fill=PURPLE, font=font(16, True), anchor="mm")
    d.text((W // 2, 420), title, fill=WHITE, font=font(56, True), anchor="mm")
    d.text((W // 2, 500), sub, fill=MUTED, font=font(24), anchor="mm")
    d.rectangle([W // 2 - 60, 560, W // 2 + 60, 566], fill=PINK)
    return img


def slide_text_focus(headline: str, body: str, accent: Tuple[int, int, int] = TEAL) -> Image.Image:
    img = glow_bg()
    d = ImageDraw.Draw(img)
    d.text((120, 280), headline, fill=WHITE, font=font(48, True))
    # wrap body
    f = font(28)
    words = body.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.getlength(t) > W - 280:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    y = 400
    for line in lines:
        d.text((120, y), line, fill=MUTED, font=f)
        y += 42
    d.rectangle([120, 220, 200, 228], fill=accent)
    return img


def slide_sequence() -> Image.Image:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.text((80, 80), "GLP-1 (7–36) amide", fill=WHITE, font=font(36, True))
    d.text((80, 140), "30 amino acids · gut incretin hormone", fill=MUTED, font=font(22))
    seq = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
    # colorful residue chips
    x, y = 80, 280
    for i, aa in enumerate(seq):
        col = [
            PURPLE,
            TEAL,
            PINK,
            YELLOW,
            (100, 180, 255),
        ][i % 5]
        rrect(d, [x, y, x + 52, y + 64], 10, fill=(30, 28, 48), outline=col, width=2)
        d.text((x + 26, y + 32), aa, fill=col, font=font(22, True), anchor="mm")
        x += 58
        if x > W - 120:
            x = 80
            y += 84
    d.text((80, H - 160), "Half-life in blood: ~1–2 minutes (DPP-4)", fill=YELLOW, font=font(24, True))
    d.text((80, H - 110), "Drug cousins (semaglutide class): days, not minutes", fill=TEAL, font=font(22))
    return img


def slide_omnigent_ui(path: Optional[Path]) -> Image.Image:
    img = new_canvas((6, 6, 10))
    if path and path.exists():
        raw = Image.open(path).convert("RGB")
        win = fit_contain(raw, 1680, 900, bg=(6, 6, 10))
        img.paste(win, ((W - 1680) // 2, 40))
    else:
        d = ImageDraw.Draw(img)
        d.text((W // 2, H // 2), "Omnigent UI", fill=WHITE, font=font(40, True), anchor="mm")
    return caption(img, "Omnigent workspace · tools · Share · policies")


def slide_with_structure(struct: Image.Image, title: str, sub: str) -> Image.Image:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.text((80, 60), title, fill=WHITE, font=font(36, True))
    d.text((80, 115), sub, fill=MUTED, font=font(20))
    thumb = fit_cover(struct, 1100, 780)
    rrect(d, [80, 180, 1200, 980], 18, fill=(8, 10, 18), outline=PURPLE, width=2)
    img.paste(thumb, (90, 200))
    d = ImageDraw.Draw(img)
    # side cards
    cards = [
        ("Incretin", "Boosts insulin when\nglucose is high"),
        ("Brain", "Quietly reduces\nappetite signals"),
        ("Drugs", "Same fold idea,\nlonger half-life"),
    ]
    y = 200
    for h, b in cards:
        rrect(d, [1280, y, W - 80, y + 180], 14, fill=(28, 26, 44), outline=(60, 56, 84), width=1)
        d.text((1320, y + 40), h, fill=TEAL, font=font(22, True))
        for i, line in enumerate(b.split("\n")):
            d.text((1320, y + 85 + i * 32), line, fill=MUTED, font=font(18))
        y += 210
    return img


def slide_metrics(metrics: dict) -> Image.Image:
    img = glow_bg()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 120), "Boltz confidence", fill=WHITE, font=font(40, True), anchor="mm")
    m = metrics.get("best_sample", metrics).get("metrics", metrics) if isinstance(metrics, dict) else {}
    items = [
        ("structure_confidence", m.get("structure_confidence"), PURPLE),
        ("complex_plddt", m.get("complex_plddt"), TEAL),
        ("ptm", m.get("ptm"), PINK),
        ("iptm", m.get("iptm"), YELLOW),
    ]
    x = 100
    for name, val, col in items:
        rrect(d, [x, 280, x + 400, 520], 18, fill=(28, 26, 44), outline=col, width=2)
        d.text((x + 30, 330), name, fill=MUTED, font=font(18))
        txt = f"{val:.2f}" if isinstance(val, (int, float)) else "—"
        d.text((x + 30, 400), txt, fill=col, font=font(56, True))
        x += 450
    d.text((W // 2, 700), "Live cloud prediction via boltz-api · orchestrated by Omnigent", fill=MUTED, font=font(22), anchor="mm")
    return img


def slide_cta() -> Image.Image:
    img = glow_bg()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 280), "Sequence → Structure → Story", fill=WHITE, font=font(44, True), anchor="mm")
    cmds = [
        "omni run ./agents/protein-lab",
        "python -m demo.run_boltz_e2e --input prediction-input-glp1.json",
    ]
    y = 420
    for c in cmds:
        rrect(d, [W // 2 - 480, y, W // 2 + 480, y + 80], 14, fill=(28, 26, 44), outline=PURPLE, width=2)
        d.text((W // 2, y + 40), c, fill=TEAL, font=font(24, True), anchor="mm")
        y += 110
    d.text((W // 2, H - 120), "docs.databricks.com/aws/en/omnigent", fill=MUTED, font=font(18), anchor="mm")
    return img


def hold_frames(img: Image.Image, seconds: float) -> List[Image.Image]:
    n = max(1, int(round(seconds * FPS)))
    return [img.copy() for _ in range(n)]


def frames_from_spin(spin_dir: Path, seconds: float) -> List[Image.Image]:
    files = sorted(spin_dir.glob("frame_*.png"))
    if not files:
        return hold_frames(new_canvas(), seconds)
    n = max(1, int(round(seconds * FPS)))
    out = []
    for i in range(n):
        fp = files[i % len(files)]
        fr = fit_cover(Image.open(fp).convert("RGB"), W, H)
        out.append(caption(fr, "GLP-1 fold · rotating view · Boltz prediction"))
    return out


def concat_audio(segments: List[Path], out_path: Path, gap: float = 0.25) -> float:
    """Concat VO with short gaps; return total duration."""
    # build with ffmpeg concat demuxer of mp3s + anull gaps is tricky;
    # use filter_complex amix-style adelay chain instead: convert each to wav and concat
    parts = []
    total = 0.0
    list_file = OUT / "audio_list.txt"
    lines = []
    silence = OUT / "silence.mp3"
    # 250ms silence
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
    for i, p in enumerate(segments):
        lines.append(f"file '{p.resolve()}'")
        total += ffprobe_dur(p)
        if i < len(segments) - 1:
            lines.append(f"file '{silence.resolve()}'")
            total += gap
    list_file.write_text("\n".join(lines) + "\n")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(out_path),
        ],
        check=True,
        capture_output=True,
    )
    # re-probe actual
    return ffprobe_dur(out_path)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir()

    # --- structure ---
    run_dir = ROOT / "outputs/boltz-e2e/glp1-hormone-demo"
    cif = next(run_dir.rglob("*_predicted.cif"), None)
    if cif is None:
        cif = next(run_dir.rglob("*.cif"), None)
    if cif is None:
        print("No GLP-1 structure found", file=sys.stderr)
        return 1

    print("structure:", cif)
    metrics = {}
    for mp in run_dir.rglob("metrics.json"):
        metrics = json.loads(mp.read_text())
        break

    still = render_structure(
        str(cif),
        title="GLP-1 · the 2-minute hormone",
        color="#7C5CFF",
        out_name="glp1",
    )
    movie = make_structure_movie(
        str(cif),
        title="GLP-1 · Omnigent × Boltz",
        color="#7C5CFF",
        out_name="glp1",
        n_frames=72,
        fps=24,
    )
    print("still:", still)
    print("movie:", movie)
    struct_img = Image.open(still["image_path"]).convert("RGB")
    spin_dir = Path(movie["frames_dir"])

    # --- VO segments ---
    vo_ids = [
        "01_hook",
        "02_name",
        "03_problem",
        "04_omnigent",
        "05_agent",
        "06_boltz",
        "07_structure",
        "08_ui",
        "09_cta",
    ]
    vo_files = [VO / f"{i}.mp3" for i in vo_ids]
    for f in vo_files:
        if not f.exists():
            print("missing VO", f, file=sys.stderr)
            return 1

    durs = [ffprobe_dur(f) for f in vo_files]
    print("VO durs:", [round(d, 2) for d in durs], "sum", round(sum(durs), 2))

    # --- Visual plan per VO segment (with small pad) ---
    pad = 0.25
    ui_tools = ROOT / "docs/assets/omnigent_ui_tools_frame.png"
    ui_poster = ROOT / "docs/assets/omnigent_ui_demo_poster.png"
    composition = ROOT / "docs/assets/omnigent-ui/composition-dark.png"

    scene_builders = [
        lambda: slide_title("The 2-minute hormone", "A gut peptide that rewrote metabolic medicine"),
        lambda: slide_sequence(),
        lambda: slide_text_focus(
            "Too fragile to be a drug",
            "DPP-4 destroys natural GLP-1 in about two minutes. Medicine needed the same message — with a structure that could survive.",
            YELLOW,
        ),
        lambda: slide_omnigent_ui(composition if composition.exists() else ui_poster),
        lambda: slide_text_focus(
            "Protein Lab on Omnigent",
            "One YAML agent. Tools for Boltz, render, and spin movies. Swap the harness in a single line — policies stay on.",
            PURPLE,
        ),
        lambda: slide_metrics(metrics),
        lambda: slide_with_structure(
            struct_img,
            "GLP-1 folded live",
            "Boltz cloud prediction · Omnigent session artifact",
        ),
        lambda: slide_omnigent_ui(ui_tools if ui_tools.exists() else ui_poster),
        lambda: slide_cta(),
    ]

    all_frames: List[Image.Image] = []
    for i, (builder, dur) in enumerate(zip(scene_builders, durs)):
        sec = dur + pad
        # structure / boltz segments use spin frames
        if i in (5, 6):  # boltz + structure
            # half still scene, half spin
            half = sec * 0.4
            all_frames.extend(hold_frames(builder(), half))
            all_frames.extend(frames_from_spin(spin_dir, sec - half))
        else:
            all_frames.extend(hold_frames(builder(), sec))

    # Write frames
    print(f"writing {len(all_frames)} frames…")
    for i, fr in enumerate(all_frames):
        fr.save(FRAMES / f"f_{i:05d}.png")

    video_silent = OUT / "video_silent.mp4"
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
            "17",
            "-movflags",
            "+faststart",
            str(video_silent),
        ],
        check=True,
        capture_output=True,
    )

    audio_path = OUT / "narration.mp3"
    audio_dur = concat_audio(vo_files, audio_path, gap=pad)
    video_dur = len(all_frames) / FPS
    print(f"video {video_dur:.2f}s audio {audio_dur:.2f}s")

    # Pad shorter side
    final = ROOT / "outputs" / "omnigent_glp1_hormone_e2e_demo.mp4"
    # Mix: video + narration, trim to shortest
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_silent),
            "-i",
            str(audio_path),
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

    # Also copy launch alias
    ship = ROOT / "outputs" / "FINAL_omnigent_glp1_demo.mp4"
    shutil.copy(final, ship)

    summary = {
        "final": str(final),
        "structure": str(cif),
        "metrics": metrics,
        "still": still,
        "spin": movie,
        "vo_segments": len(vo_files),
        "duration_s": ffprobe_dur(final),
        "story": "GLP-1 two-minute hormone · Omnigent · Boltz · ElevenLabs VO",
    }
    (ROOT / "outputs" / "glp1_e2e_session.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({"final": str(final), "duration_s": summary["duration_s"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
