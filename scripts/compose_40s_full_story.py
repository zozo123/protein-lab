#!/usr/bin/env python3
"""
Crisp ~40s full-story live demo:

  GLP-1 sequence  →  Omnigent (Databricks) UI  →  meta-harness + Boltz metrics
  →  protein structure movie  →  CTA

Keep what works: real Omnigent UI, sequence board, structure spin.
Cut fluff. Sharp cuts. Live-demo energy.
Target total ~40s (VO-driven).
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
OUT = ROOT / "outputs" / "story-40s"
FRAMES = OUT / "frames"
VO = ROOT / "outputs" / "vo_40s"
UI = ROOT / "docs" / "assets" / "omnigent-ui"
PREMIUM = ROOT / "outputs" / "glp1_premium"
W, H, FPS = 1920, 1080, 24

BG = (7, 9, 14)
WHITE = (250, 250, 252)
MUTED = (168, 176, 192)
TEAL = (0, 220, 170)
PURPLE = (130, 100, 255)
PINK = (236, 72, 153)
YELLOW = (255, 200, 60)

SEQ = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
CONF, PLDDT = 0.83, 0.90


def font(size: int, bold: bool = False):
    cands = (
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


def gut_bg(dim: float = 0.25) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    layer = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(layer)
    for cx, cy, r, c in [
        (280, 900, 480, (30, 75, 55)),
        (1550, 250, 420, (50, 28, 85)),
        (960, 1050, 500, (22, 60, 48)),
    ]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    layer = layer.filter(ImageFilter.GaussianBlur(75))
    img = Image.blend(img, layer, 0.55)
    d = ImageDraw.Draw(img)
    for i in range(20):
        x = 30 + i * 100
        h = 60 + (i * 13 % 80)
        d.ellipse([x, H - 20 - h, x + 80, H + 40], fill=(20, 50, 38), outline=(40, 90, 65), width=1)
    if dim:
        img = Image.blend(img, Image.new("RGB", (W, H), BG), dim)
    return img


def crisp(im: Image.Image) -> Image.Image:
    """Sharpen UI text after resize — real product snapshots stay readable."""
    from PIL import ImageEnhance, ImageFilter

    im = im.convert("RGB")
    im = im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=140, threshold=2))
    im = ImageEnhance.Contrast(im).enhance(1.05)
    im = ImageEnhance.Sharpness(im).enhance(1.2)
    return im


def fit_cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    out = ImageOps.fit(im.convert("RGB"), (tw, th), method=Image.Resampling.LANCZOS)
    return crisp(out)


def fit_contain(im: Image.Image, tw: int, th: int, bg=BG) -> Image.Image:
    """High-quality contain: scale with LANCZOS, center, no blurry pad upscale."""
    im = im.convert("RGB")
    iw, ih = im.size
    scale = min(tw / iw, th / ih)
    nw, nh = max(1, int(round(iw * scale))), max(1, int(round(ih * scale)))
    # never upscale past 1.05× native (keeps UI text crisp)
    if scale > 1.05:
        nw, nh = iw, ih
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    im = crisp(im)
    c = Image.new("RGB", (tw, th), bg)
    c.paste(im, ((tw - nw) // 2, (th - nh) // 2))
    return c


def load_ui(path: Path) -> Image.Image:
    """Load product PNG/GIF frame as RGB, flatten alpha on dark."""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA"):
        bg = Image.new("RGBA", im.size, (8, 8, 12, 255))
        im = Image.alpha_composite(bg, im.convert("RGBA")).convert("RGB")
    else:
        im = im.convert("RGB")
    return im


def bar(img: Image.Image, left: str, right: str = "") -> Image.Image:
    out = img.copy()
    d = ImageDraw.Draw(out)
    d.rectangle([0, H - 78, W, H], fill=(5, 6, 10))
    d.rectangle([0, H - 80, W, H - 78], fill=PINK)
    d.text((40, H - 40), left, fill=WHITE, font=font(22, True), anchor="lm")
    if right:
        d.text((W - 40, H - 40), right, fill=TEAL, font=font(16, True), anchor="rm")
    return out


# ---------- scenes (crisp, live-demo) ----------


def scene_sequence() -> Image.Image:
    """Hero sequence board — what worked before, sharper."""
    img = gut_bg(0.15)
    d = ImageDraw.Draw(img)
    # live chip
    d.rounded_rectangle([40, 36, 200, 72], 10, fill=PINK)
    d.text((120, 54), "● LIVE DEMO", fill=WHITE, font=font(14, True), anchor="mm")

    d.text((40, 110), "GLP-1 (7–36)", fill=WHITE, font=font(52, True))
    d.text((40, 180), "gut incretin  ·  30 amino acids  ·  ~2 min half-life (DPP-4)", fill=MUTED, font=font(24))

    colors = [PURPLE, TEAL, PINK, YELLOW, (100, 180, 255), (200, 130, 255)]
    for i, aa in enumerate(SEQ):
        row, col = divmod(i, 15)
        x = 40 + col * 122
        y = 280 + row * 130
        c = colors[i % len(colors)]
        d.rounded_rectangle([x, y, x + 105, y + 105], 12, fill=(14, 18, 28), outline=c, width=3)
        d.text((x + 52, y + 42), aa, fill=c, font=font(36, True), anchor="mm")
        d.text((x + 52, y + 82), str(i + 1), fill=(90, 95, 115), font=font(13), anchor="mm")

    d.text((40, 600), SEQ, fill=TEAL, font=font(22, True))
    d.text((40, 680), "Molecular root of major metabolic medicines", fill=MUTED, font=font(22))
    d.text((40, 740), "prediction-input-glp1.json", fill=(100, 105, 125), font=font(16))
    return bar(img, "SEQUENCE  ·  GLP-1", "biocomputing")


def scene_omnigent_live(path: Path, caption: str, label: str) -> Image.Image:
    """Real Omnigent UI snapshot — near full-bleed, crisp, minimal chrome."""
    # dark stage (clean, not blurry gut over UI)
    base = Image.new("RGB", (W, H), (6, 7, 12))
    raw = load_ui(path)
    # max readable window: almost full frame
    win = fit_contain(raw, 1860, 960, bg=(6, 7, 12))
    # soft outer vignette only outside window
    base.paste(win, ((W - 1860) // 2, 55))

    d = ImageDraw.Draw(base)
    # thin top strip — product truth
    d.rectangle([0, 0, W, 48], fill=(4, 5, 10))
    d.rounded_rectangle([16, 10, 210, 38], 8, fill=PINK)
    d.text((113, 24), "● REAL UI  ·  OMNIGENT", fill=WHITE, font=font(12, True), anchor="mm")
    d.text((230, 24), "Databricks", fill=MUTED, font=font(14), anchor="lm")
    d.text((W - 24, 24), label, fill=TEAL, font=font(13, True), anchor="rm")
    return bar(base, caption, "docs.databricks.com/aws/en/omnigent")


def scene_meta_boltz() -> Image.Image:
    """Meta-harness + Boltz in one crisp split — full story engineering beat."""
    img = gut_bg(0.35)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([32, 24, 200, 58], 10, fill=PINK)
    d.text((116, 41), "● LIVE DEMO", fill=WHITE, font=font(13, True), anchor="mm")

    # left: meta-harness
    d.rounded_rectangle([40, 90, 920, 980], 16, fill=(12, 14, 24), outline=PURPLE, width=3)
    d.text((80, 130), "META-HARNESS", fill=PURPLE, font=font(18, True))
    d.text((80, 180), "Omnigent", fill=WHITE, font=font(44, True))
    d.text((80, 250), "one session over agents", fill=MUTED, font=font(24))
    lines = [
        ("harness: claude-sdk", "swap codex · pi · grok"),
        ("tools: boltz + viz", "portable across harnesses"),
        ("policies: max 40 calls", "guardrails as code"),
        ("Share URL", "live collab session"),
    ]
    y = 340
    for a, b in lines:
        d.text((80, y), a, fill=TEAL, font=font(26, True))
        d.text((80, y + 36), b, fill=MUTED, font=font(20))
        y += 100
    d.text((80, 900), "agents/protein-lab/config.yaml", fill=(100, 105, 125), font=font(16))

    # right: Boltz live numbers
    d.rounded_rectangle([980, 90, W - 40, 980], 16, fill=(12, 14, 24), outline=TEAL, width=3)
    d.text((1020, 130), "BOLTZ CLOUD", fill=TEAL, font=font(18, True))
    d.text((1020, 180), "structure-and-binding", fill=WHITE, font=font(32, True))
    d.text((1020, 280), f"{CONF:.2f}", fill=TEAL, font=font(100, True))
    d.text((1020, 400), "structure confidence", fill=MUTED, font=font(22))
    d.text((1020, 500), f"{PLDDT:.2f}", fill=PURPLE, font=font(100, True))
    d.text((1020, 620), "complex pLDDT", fill=MUTED, font=font(22))
    d.text((1020, 720), "30 residues  ·  live CIF", fill=MUTED, font=font(24))
    d.text((1020, 800), "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR", fill=TEAL, font=font(16, True))
    d.text((1020, 900), "sequence → coordinates", fill=MUTED, font=font(18))
    return bar(img, "META-HARNESS  ·  BOLTZ  ·  PROTEIN LAB", "e2e")


def scene_fold(frame: Image.Image) -> Image.Image:
    base = Image.new("RGB", (W, H), (6, 8, 14))
    fold = fit_contain(crisp(frame.convert("RGB")), 1780, 940, bg=(6, 8, 14))
    base.paste(fold, ((W - 1780) // 2, 50))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle([40, 16, 340, 48], 8, fill=TEAL)
    d.text((190, 32), "STRUCTURE  ·  BOLTZ CIF", fill=BG, font=font(13, True), anchor="mm")
    return bar(base, f"GLP-1 fold  ·  conf {CONF}  ·  pLDDT {PLDDT}", "N→C rainbow")


def scene_cta() -> Image.Image:
    img = gut_bg(0.4)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([220, 300, W - 220, 720], 18, fill=(10, 12, 20), outline=PINK, width=3)
    d.text((W // 2, 400), "Full story in one session", fill=MUTED, font=font(22), anchor="mm")
    d.text((W // 2, 500), "omni run ./agents/protein-lab", fill=TEAL, font=font(42, True), anchor="mm")
    d.text((W // 2, 600), "Omnigent  ·  Boltz  ·  GLP-1  ·  sequence  ·  structure", fill=MUTED, font=font(20), anchor="mm")
    return img


def hold(img: Image.Image, sec: float) -> List[Image.Image]:
    n = max(1, int(round(sec * FPS)))
    return [img.copy() for _ in range(n)]


def spin(sec: float) -> List[Image.Image]:
    files = sorted((PREMIUM / "frames").glob("frame_*.png"))
    n = max(1, int(round(sec * FPS)))
    if not files:
        return hold(scene_meta_boltz(), sec)
    out = []
    for i in range(n):
        # smooth full rotation across segment
        idx = int((i / max(n, 1)) * len(files)) % len(files)
        out.append(scene_fold(Image.open(files[idx]).convert("RGB")))
    return out


def ensure_vo() -> List[Path]:
    VO.mkdir(parents=True, exist_ok=True)
    for p in VO.glob("*.mp3"):
        p.unlink()
    script = json.loads((ROOT / "demo/vo_script_40s.json").read_text())
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
                    "stability": 0.45,
                    "similarity_boost": 0.82,
                    "style": 0.25,
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
        time.sleep(0.12)
    return files


def concat_audio(files: List[Path], gap: float = 0.12) -> Tuple[Path, List[float], float]:
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
        g = gap if i < len(files) - 1 else 0.2
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


def speed_to_target(audio_in: Path, target: float = 40.0) -> Tuple[Path, float]:
    """If VO is longer than target, slightly speed up (atempo) to land ~40s."""
    dur = ffprobe_dur(audio_in)
    if dur <= target + 0.5:
        return audio_in, dur
    # atempo range 0.5–2.0; may chain
    factor = dur / target
    if factor > 1.35:
        factor = 1.35  # don't mutilate speech
    out = OUT / "narration_tempo.m4a"
    # chain atempo if needed
    tempo = factor
    filters = []
    while tempo > 2.0:
        filters.append("atempo=2.0")
        tempo /= 2.0
    while tempo < 0.5:
        filters.append("atempo=0.5")
        tempo /= 0.5
    filters.append(f"atempo={tempo:.4f}")
    filters.append("loudnorm=I=-15:TP=-1.5:LRA=10")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(audio_in),
            "-af",
            ",".join(filters),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out, ffprobe_dur(out)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir()

    if not (PREMIUM / "frames").exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/render_glp1_premium.py")], check=True, cwd=str(ROOT))

    print("=== VO 40s story ===")
    # reuse VO if present (crisp visual rebuild only)
    existing = sorted(VO.glob("*.mp3"))
    if len(existing) >= 4:
        vo = [VO / f"{s}.mp3" for s in ["01_glp1", "02_omnigent", "03_boltz", "04_fold"]]
        if all(p.exists() for p in vo):
            print(" reusing VO")
        else:
            vo = ensure_vo()
    else:
        vo = ensure_vo()
    audio_raw, durs, atot = concat_audio(vo, gap=0.12)
    print("raw durs", [round(x, 2) for x in durs], "total", round(atot, 2))

    audio, adur = speed_to_target(audio_raw, target=40.0)
    # scale segment visual times proportionally if sped
    scale = adur / atot if atot > 0 else 1.0
    durs = [d * scale for d in durs]
    print("final audio", round(adur, 2), "s  scale", round(scale, 3))

    # Prefer unsharp hero snapshots (native 1920×1080) then marketing stills
    heroes = sorted((UI / "carousel_crisp").glob("hero_*.png"))
    if not heroes:
        heroes = sorted((UI / "carousel_crisp").glob("raw_*.png"))[::40]
    composition = UI / "composition-dark.png"
    control = UI / "control-dark.png"
    collab = UI / "collaboration-dark.png"

    timeline: List[Image.Image] = []

    # 01 GLP-1 sequence (strength)
    timeline += hold(scene_sequence(), durs[0])

    # 02 Omnigent — REAL crisp product snapshots only (no muddy composites)
    d1 = durs[1]
    # hold each hero a beat for readability
    if heroes:
        per = d1 * 0.42 / max(len(heroes), 1)
        per = max(per, 0.55)
        for i, fp in enumerate(heroes[:6]):
            timeline += hold(
                scene_omnigent_live(
                    fp,
                    "Omnigent workspace  ·  chat · files · Share · agents",
                    "LIVE WORKSPACE",
                ),
                per,
            )
    # full-res marketing stills (composition 2314×1668 — sharper than gif)
    if composition.exists():
        timeline += hold(
            scene_omnigent_live(
                composition,
                "Composition  ·  multi-agent  ·  Share  ·  Agents panel",
                "COMPOSITION",
            ),
            d1 * 0.28,
        )
    if control.exists():
        timeline += hold(
            scene_omnigent_live(
                control,
                "Control  ·  policies  ·  tool approvals",
                "CONTROL",
            ),
            d1 * 0.15,
        )
    if collab.exists():
        timeline += hold(
            scene_omnigent_live(
                collab,
                "Collaboration  ·  shared session  ·  comments",
                "COLLABORATION",
            ),
            d1 * 0.15,
        )

    # 03 meta-harness + Boltz numbers
    d2 = durs[2]
    timeline += hold(scene_meta_boltz(), d2 * 0.55)
    timeline += spin(d2 * 0.45)

    # 04 structure movie (strength) + CTA
    d3 = durs[3]
    timeline += spin(d3 * 0.70)
    timeline += hold(scene_cta(), d3 * 0.30)

    need = int(round(adur * FPS))
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
            "15",
            "-movflags",
            "+faststart",
            str(silent),
        ],
        check=True,
        capture_output=True,
    )

    # ensure audio is aac
    if audio.suffix == ".mp3":
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
        audio = loud

    final = ROOT / "outputs" / "omnigent_boltz_glp1_40s.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent),
            "-i",
            str(audio),
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
        "FINAL_omnigent_glp1_demo.mp4",
        "omnigent_boltz_glp1_deep_ui.mp4",
        "omnigent_boltz_glp1_straight.mp4",
        "omnigent_glp1_30s_nyt.mp4",
    ]:
        shutil.copy(final, ROOT / "outputs" / name)

    meta = {
        "final": str(final),
        "duration_s": ffprobe_dur(final),
        "story": [
            "GLP-1 sequence + half-life",
            "Omnigent meta-harness UI (live)",
            "Boltz metrics + Protein Lab",
            "Structure movie + CTA",
        ],
        "metrics": {"confidence": CONF, "plddt": PLDDT},
    }
    (ROOT / "outputs" / "story_40s_session.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
