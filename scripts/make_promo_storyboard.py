#!/usr/bin/env python3
"""
Build a short multi-scene promo movie for the Omnigent Protein Lab demo.

Scenes:
  1. Title card
  2. "Sequence in" (FASTA-style)
  3. Structure hero
  4. Spin clip (reuses frames from make_structure_movie)
  5. Outro with paths / omni run command

Requires a prior `python -m demo.run_demo --target <t>` so frames exist.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs"


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def title_card(path: Path, w: int, h: int, title: str, subtitle: str) -> None:
    img = Image.new("RGB", (w, h), "#0B0F1A")
    draw = ImageDraw.Draw(img)
    # Accent bar
    draw.rectangle([0, h // 2 - 4, w, h // 2 + 4], fill="#7C5CFF")
    draw.text((w // 2, h // 2 - 80), title, fill="white", font=_font(48), anchor="mm")
    draw.text((w // 2, h // 2 + 50), subtitle, fill="#A0AEC0", font=_font(22), anchor="mm")
    draw.text(
        (w // 2, h - 40),
        "docs.databricks.com/aws/en/omnigent",
        fill="#5A6478",
        font=_font(16),
        anchor="mm",
    )
    img.save(path)


def sequence_card(path: Path, w: int, h: int, name: str, sequence: str) -> None:
    img = Image.new("RGB", (w, h), "#0B0F1A")
    draw = ImageDraw.Draw(img)
    draw.text((48, 48), "SEQUENCE IN", fill="#7C5CFF", font=_font(18))
    draw.text((48, 90), name, fill="white", font=_font(36))
    # Wrap sequence
    seq = sequence[:180] + ("…" if len(sequence) > 180 else "")
    lines = [seq[i : i + 48] for i in range(0, len(seq), 48)]
    y = 180
    mono = _font(20)
    for line in lines:
        draw.text((48, y), line, fill="#00D4AA", font=mono)
        y += 32
    draw.text((48, h - 60), f"{len(sequence)} amino acids", fill="#A0AEC0", font=_font(18))
    img.save(path)


def outro_card(path: Path, w: int, h: int) -> None:
    img = Image.new("RGB", (w, h), "#0B0F1A")
    draw = ImageDraw.Draw(img)
    draw.text((w // 2, h // 2 - 60), "Try it yourself", fill="white", font=_font(40), anchor="mm")
    draw.text(
        (w // 2, h // 2 + 10),
        "omni run ./agents/protein-lab",
        fill="#00D4AA",
        font=_font(28),
        anchor="mm",
    )
    draw.text(
        (w // 2, h // 2 + 70),
        "python -m demo.run_demo --target ubiquitin",
        fill="#A0AEC0",
        font=_font(20),
        anchor="mm",
    )
    img.save(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="ubiquitin")
    parser.add_argument("--fps", type=int, default=24)
    args = parser.parse_args()

    target_dir = OUTPUT / args.target
    frames_src = target_dir / "frames"
    if not frames_src.exists():
        print(f"Missing frames at {frames_src}. Run demo first:", file=sys.stderr)
        print(f"  python -m demo.run_demo --target {args.target}", file=sys.stderr)
        return 1

    # Import sequence from tools
    sys.path.insert(0, str(ROOT))
    from tools.protein_tools import DEMO_TARGETS

    meta = DEMO_TARGETS[args.target]
    promo_frames = target_dir / "promo_frames"
    if promo_frames.exists():
        shutil.rmtree(promo_frames)
    promo_frames.mkdir(parents=True)

    # Probe size from an existing structure frame
    sample = next(frames_src.glob("frame_*.png"))
    with Image.open(sample) as im:
        w, h = im.size

    idx = 0

    def add_hold(src: Path, n: int) -> None:
        nonlocal idx
        for _ in range(n):
            shutil.copy(src, promo_frames / f"frame_{idx:04d}.png")
            idx += 1

    # Scene 1 — title
    t1 = promo_frames / "_title.png"
    title_card(t1, w, h, "Omnigent Protein Lab", "Boltz · structures · spin movies")
    add_hold(t1, args.fps * 2)

    # Scene 2 — sequence
    t2 = promo_frames / "_seq.png"
    sequence_card(t2, w, h, meta["name"], meta["sequence"])
    add_hold(t2, args.fps * 2)

    # Scene 3 — hero still if present
    hero = target_dir / f"{args.target}_hero.png"
    still = target_dir / f"{args.target}_still.png"
    for candidate in (hero, still):
        if candidate.exists():
            add_hold(candidate, args.fps * 1)
            break

    # Scene 4 — full spin
    for fp in sorted(frames_src.glob("frame_*.png")):
        shutil.copy(fp, promo_frames / f"frame_{idx:04d}.png")
        idx += 1

    # Scene 5 — outro
    t5 = promo_frames / "_outro.png"
    outro_card(t5, w, h)
    add_hold(t5, args.fps * 3)

    out_mp4 = OUTPUT / f"omnigent_protein_lab_{args.target}_promo.mp4"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg required for promo stitch", file=sys.stderr)
        return 1

    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(args.fps),
        "-i",
        str(promo_frames / "frame_%04d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    print(f"Promo movie → {out_mp4}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
