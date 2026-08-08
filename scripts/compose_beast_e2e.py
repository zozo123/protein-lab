#!/usr/bin/env python3
"""
Beast-mode retention film for Omnigent × Boltz × GLP-1.

Retention craft (adapted for tech — not clickbait fluff):
  - 0–3s cold open: number + stakes + promise
  - Re-hook every ~12–20s with a new question / number / visual pattern interrupt
  - Proof early (real metrics, real UI, real structure)
  - Multi-audience payoffs: bio / eng / tech leadership
  - Abrupt clean CTA while energy is high

Visual language: big kinetic type, countdown, scoreboard metrics,
official Omnigent screenshots, premium GLP-1 spin from OUR Boltz run.
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

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "beast-film"
FRAMES = OUT / "frames"
VO = ROOT / "outputs" / "vo_beast"
UI = ROOT / "docs" / "assets" / "omnigent-ui"
PREMIUM = ROOT / "outputs" / "glp1_premium"
W, H, FPS = 1920, 1080, 24

BG = (6, 8, 14)
WHITE = (255, 255, 255)
MUTED = (170, 178, 200)
PURPLE = (124, 92, 255)
TEAL = (0, 230, 180)
PINK = (255, 45, 120)
YELLOW = (255, 210, 40)
GREEN = (40, 230, 140)

SEQ = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
METRICS = {"structure_confidence": 0.83, "plddt": 0.90, "ptm": 0.58, "residues": 30}


def font(size: int, bold: bool = False):
    paths = []
    if bold:
        paths += [
            "/System/Library/Fonts/Supplemental/Impact.ttf",
            "/System/Library/Fonts/Supplemental/Arial Black.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ]
    paths += [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
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


def rrect(d, box, r, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def fit_cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    return ImageOps.fit(im.convert("RGB"), (tw, th), method=Image.Resampling.LANCZOS)


def fit_contain(im: Image.Image, tw: int, th: int, bg=BG) -> Image.Image:
    c = Image.new("RGB", (tw, th), bg)
    im = im.convert("RGB")
    im.thumbnail((tw, th), Image.Resampling.LANCZOS)
    c.paste(im, ((tw - im.width) // 2, (th - im.height) // 2))
    return c


def glow() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    g = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(g)
    d.ellipse([W // 2 - 600, H // 2 - 350, W // 2 + 600, H // 2 + 400], fill=(55, 10, 70))
    g = g.filter(ImageFilter.GaussianBlur(100))
    return Image.blend(img, g, 0.6)


def big_number(num: str, label: str, sub: str = "", accent=PINK) -> Image.Image:
    img = glow()
    d = ImageDraw.Draw(img)
    d.text((W // 2, H // 2 - 80), num, fill=accent, font=font(160, True), anchor="mm")
    d.text((W // 2, H // 2 + 80), label, fill=WHITE, font=font(48, True), anchor="mm")
    if sub:
        d.text((W // 2, H // 2 + 150), sub, fill=MUTED, font=font(26), anchor="mm")
    return img


def kinetic_hook(line1: str, line2: str = "", badge: str = "") -> Image.Image:
    img = glow()
    d = ImageDraw.Draw(img)
    if badge:
        rrect(d, [W // 2 - 200, 160, W // 2 + 200, 210], 20, (40, 20, 50), PINK, 3)
        d.text((W // 2, 185), badge, fill=PINK, font=font(20, True), anchor="mm")
    d.text((W // 2, H // 2 - 40), line1, fill=WHITE, font=font(64, True), anchor="mm")
    if line2:
        d.text((W // 2, H // 2 + 50), line2, fill=TEAL, font=font(36, True), anchor="mm")
    # bottom retention bar fake
    d.rectangle([0, H - 12, W, H], fill=(30, 30, 40))
    d.rectangle([0, H - 12, int(W * 0.08), H], fill=PINK)
    return img


def lower(img: Image.Image, text: str) -> Image.Image:
    out = img.copy()
    d = ImageDraw.Draw(out)
    d.rectangle([0, H - 90, W, H], fill=(0, 0, 0))
    d.rectangle([0, H - 92, W, H - 90], fill=PINK)
    d.text((40, H - 45), text, fill=WHITE, font=font(24, True), anchor="lm")
    d.text((W - 40, H - 45), "Omnigent × Boltz × GLP-1", fill=MUTED, font=font(16), anchor="rm")
    return out


def three_promises() -> Image.Image:
    img = glow()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 100), "3 THINGS. UNDER 2 MINUTES.", fill=PINK, font=font(36, True), anchor="mm")
    cards = [
        ("01", "BIO", "The 30-letter hormone\nthat dies in 120 seconds", TEAL),
        ("02", "ENG", "YAML agents you can\nswap without rewrites", PURPLE),
        ("03", "BOLTZ", "Real confidence:\n0.83 · pLDDT 0.90", YELLOW),
    ]
    x = 100
    for num, title, body, col in cards:
        rrect(d, [x, 220, x + 540, 820], 24, (18, 20, 32), col, 4)
        d.text((x + 40, 280), num, fill=col, font=font(48, True))
        d.text((x + 40, 380), title, fill=WHITE, font=font(42, True))
        for i, line in enumerate(body.split("\n")):
            d.text((x + 40, 500 + i * 50), line, fill=MUTED, font=font(26))
        x += 580
    return img


def audience_scoreboard() -> Image.Image:
    img = glow()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 90), "WHO THIS IS FOR", fill=WHITE, font=font(40, True), anchor="mm")
    rows = [
        ("BIOCOMPUTING", "Sequence → structure → shareable artifact in one session", TEAL),
        ("ENGINEERING", "Portable agents · harness swap · policies as code", PURPLE),
        ("TECH LEADERS", "One meta-layer above model chaos · governable sessions", PINK),
        ("SCIENTISTS", "Real Boltz metrics · real CIF · no fake slides", YELLOW),
    ]
    y = 200
    for title, body, col in rows:
        rrect(d, [120, y, W - 120, y + 150], 16, (18, 20, 32), col, 3)
        d.rectangle([120, y, 140, y + 150], fill=col)
        d.text((180, y + 40), title, fill=col, font=font(28, True))
        d.text((180, y + 90), body, fill=MUTED, font=font(24))
        y += 180
    return img


def bio_sequence() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((80, 50), "THE MOLECULE", fill=PINK, font=font(22, True))
    d.text((80, 100), "GLP-1 (7–36)  ·  30 amino acids", fill=WHITE, font=font(44, True))
    d.text((80, 165), "Gut incretin  ·  UniProt P01275  ·  prediction-input-glp1.json", fill=MUTED, font=font(20))

    colors = [PURPLE, TEAL, PINK, YELLOW, (100, 180, 255), (200, 120, 255)]
    for i, aa in enumerate(SEQ):
        row, col = divmod(i, 15)
        x = 80 + col * 118
        y = 240 + row * 130
        c = colors[i % len(colors)]
        rrect(d, [x, y, x + 100, y + 100], 12, (20, 22, 36), c, 3)
        d.text((x + 50, y + 40), aa, fill=c, font=font(34, True), anchor="mm")
        d.text((x + 50, y + 78), str(i + 1), fill=(90, 95, 120), font=font(14), anchor="mm")

    # facts strip
    facts = [
        ("↑ INSULIN", "when glucose high"),
        ("↓ APPETITE", "brain signaling"),
        ("DPP-4", "kills it in ~2 min"),
    ]
    x = 80
    for a, b in facts:
        rrect(d, [x, 560, x + 560, 720], 14, (22, 24, 40), TEAL, 2)
        d.text((x + 30, 600), a, fill=TEAL, font=font(28, True))
        d.text((x + 30, 660), b, fill=MUTED, font=font(22))
        x += 600
    d.text((80, H - 60), "Scientifically: incretin hormone · glucose-dependent insulin · short plasma half-life", fill=(100, 105, 130), font=font(16))
    return img


def drug_story() -> Image.Image:
    img = glow()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 100), "THE PLOT TWIST", fill=PINK, font=font(28, True), anchor="mm")
    d.text((W // 2, 170), "Same signal. Different half-life.", fill=WHITE, font=font(48, True), anchor="mm")

    # before after
    rrect(d, [100, 280, 880, 850], 20, (22, 24, 40), YELLOW, 4)
    d.text((490, 340), "NATURAL", fill=YELLOW, font=font(32, True), anchor="mm")
    d.text((490, 480), "~2 MIN", fill=WHITE, font=font(90, True), anchor="mm")
    d.text((490, 600), "DPP-4 destroys it", fill=MUTED, font=font(26), anchor="mm")
    d.text((490, 680), "Useless as a drug as-is", fill=MUTED, font=font(22), anchor="mm")

    rrect(d, [1040, 280, 1820, 850], 20, (22, 24, 40), TEAL, 4)
    d.text((1430, 340), "ENGINEERED", fill=TEAL, font=font(32, True), anchor="mm")
    d.text((1430, 480), "DAYS", fill=WHITE, font=font(90, True), anchor="mm")
    d.text((1430, 600), "Same fold-family idea", fill=MUTED, font=font(26), anchor="mm")
    d.text((1430, 680), "Metabolic drug class", fill=MUTED, font=font(22), anchor="mm")

    d.text((W // 2, H - 80), "Not medical advice — structural biology storytelling", fill=(90, 95, 110), font=font(16), anchor="mm")
    return img


def eng_yaml() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((80, 50), "THE ENGINEERING STEAL", fill=PINK, font=font(22, True))
    d.text((80, 100), "One YAML. Swap the brain. Keep the tools.", fill=WHITE, font=font(40, True))

    rrect(d, [80, 200, W - 80, H - 100], 16, (16, 18, 30), PURPLE, 2)
    lines = [
        (TEAL, "name: protein-lab"),
        (MUTED, "executor:"),
        (PURPLE, "  harness: claude-sdk   # ← change ONE line"),
        (MUTED, "  # codex | pi | grok | openai-agents"),
        (MUTED, ""),
        (WHITE, "tools:  # stay identical across harnesses"),
        (PINK, "  run_boltz_api_prediction:"),
        (MUTED, "    callable: tools.protein_tools.run_boltz_api_prediction"),
        (PINK, "  make_structure_movie:"),
        (MUTED, "    callable: tools.protein_tools.make_structure_movie"),
        (MUTED, ""),
        (YELLOW, "policies:"),
        (YELLOW, "  max_tool_calls: 40   # guardrails as code"),
    ]
    y = 240
    for col, line in lines:
        bold = ("harness" in line) or line.startswith("name")
        d.text((140, y), line, fill=col, font=font(28, bold))
        y += 48
    return lower(img, "Omnigent meta-harness · portable agent contract")


def product_ui(path: Path, caption: str) -> Image.Image:
    stage = Image.new("RGB", (W, H), (4, 4, 8))
    raw = Image.open(path).convert("RGB")
    win = fit_contain(raw, 1720, 920, bg=(4, 4, 8))
    stage.paste(win, ((W - 1720) // 2, 30))
    # badge
    d = ImageDraw.Draw(stage)
    rrect(d, [60, 40, 420, 100], 12, (0, 0, 0), PINK, 3)
    d.text((240, 70), "REAL PRODUCT UI", fill=PINK, font=font(20, True), anchor="mm")
    return lower(stage, caption)


def metrics_bang() -> Image.Image:
    img = glow()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 80), "NOT A MOCK. OUR LIVE BOLTZ RUN.", fill=PINK, font=font(28, True), anchor="mm")

    cards = [
        (f"{METRICS['structure_confidence']:.2f}", "STRUCTURE\nCONFIDENCE", PURPLE),
        (f"{METRICS['plddt']:.2f}", "COMPLEX\nPLDDT", TEAL),
        (f"{METRICS['ptm']:.2f}", "PTM", PINK),
        (str(METRICS["residues"]), "RESIDUES", YELLOW),
    ]
    x = 80
    for val, lab, col in cards:
        rrect(d, [x, 200, x + 420, 720], 20, (18, 20, 34), col, 4)
        d.text((x + 210, 380), val, fill=col, font=font(90, True), anchor="mm")
        for i, line in enumerate(lab.split("\n")):
            d.text((x + 210, 540 + i * 40), line, fill=MUTED, font=font(24, True), anchor="mm")
        x += 460
    d.text((W // 2, 820), "boltz-api  ·  prediction-input-glp1.json  ·  CIF in outputs/", fill=MUTED, font=font(22), anchor="mm")
    d.text((W // 2, 900), "Proof > pitch", fill=WHITE, font=font(32, True), anchor="mm")
    return img


def structure_overlay(frame: Image.Image, text: str) -> Image.Image:
    im = fit_cover(frame, W, H)
    d = ImageDraw.Draw(im)
    # top banner
    d.rectangle([0, 0, W, 100], fill=(0, 0, 0, 180) if False else (0, 0, 0))
    d.text((40, 50), text, fill=WHITE, font=font(28, True), anchor="lm")
    d.text((W - 40, 50), "LIVE FOLD", fill=TEAL, font=font(22, True), anchor="rm")
    return lower(im, "Boltz-predicted GLP-1 · N→C rainbow · heavy atoms")


def cta() -> Image.Image:
    img = glow()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 200), "YOUR MOVE", fill=PINK, font=font(28, True), anchor="mm")
    d.text((W // 2, 300), "Fold the 2-minute hormone.", fill=WHITE, font=font(56, True), anchor="mm")
    cmds = [
        "omni run ./agents/protein-lab",
        "python -m demo.run_boltz_e2e",
        "scripts/compose_beast_e2e.py",
    ]
    y = 420
    for c in cmds:
        rrect(d, [W // 2 - 500, y, W // 2 + 500, y + 90], 16, (20, 22, 36), TEAL, 3)
        d.text((W // 2, y + 45), c, fill=TEAL, font=font(28, True), anchor="mm")
        y += 120
    d.text((W // 2, H - 100), "docs.databricks.com/aws/en/omnigent", fill=MUTED, font=font(20), anchor="mm")
    return img


def hold(img: Image.Image, sec: float) -> List[Image.Image]:
    n = max(1, int(round(sec * FPS)))
    return [img.copy() for _ in range(n)]


def burn(img: Image.Image, sec: float, z0=1.0, z1=1.06) -> List[Image.Image]:
    n = max(1, int(round(sec * FPS)))
    out = []
    for i in range(n):
        t = i / max(n - 1, 1)
        z = z0 + (z1 - z0) * t
        iw, ih = img.size
        nw, nh = int(iw / z), int(ih / z)
        ox = int((iw - nw) * 0.5 * t)
        oy = int((ih - nh) * 0.25)
        out.append(img.crop((ox, oy, ox + nw, oy + nh)).resize((W, H), Image.Resampling.LANCZOS))
    return out


def spin(sec: float, label: str) -> List[Image.Image]:
    files = sorted((PREMIUM / "frames").glob("frame_*.png"))
    if not files:
        return hold(metrics_bang(), sec)
    n = max(1, int(round(sec * FPS)))
    out = []
    for i in range(n):
        fr = Image.open(files[i % len(files)]).convert("RGB")
        out.append(structure_overlay(fr, label))
    return out


def ensure_vo() -> List[Path]:
    VO.mkdir(parents=True, exist_ok=True)
    script = json.loads((ROOT / "demo/vo_script_beast.json").read_text())
    key_path = ROOT / ".env"
    if not key_path.exists():
        key_path = Path.home() / "Developer/video-use/.env"
    key = key_path.read_text().split("ELEVENLABS_API_KEY=", 1)[1].strip().splitlines()[0]
    files = []
    for seg in script["segments"]:
        out = VO / f"{seg['id']}.mp3"
        files.append(out)
        if out.exists() and out.stat().st_size > 2000:
            print(" cache", seg["id"])
            continue
        print(" TTS", seg["id"])
        body = json.dumps(
            {
                "text": seg["text"],
                "model_id": script["model_id"],
                "voice_settings": {
                    "stability": 0.35,
                    "similarity_boost": 0.85,
                    "style": 0.55,
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


def concat_audio(files: List[Path], gap: float = 0.12) -> Tuple[Path, List[float], float]:
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
    durs, lines, total = [], [], 0.0
    for i, f in enumerate(files):
        d = ffprobe_dur(f)
        gap_i = gap if i < len(files) - 1 else 0.0
        durs.append(d + gap_i)
        total += durs[-1]
        lines.append(f"file '{f.resolve()}'")
        if gap_i:
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
        print("Building premium structure first…")
        subprocess.run([sys.executable, str(ROOT / "scripts/render_glp1_premium.py")], check=True, cwd=str(ROOT))

    print("=== VO (beast) ===")
    vo = ensure_vo()
    audio, durs, atot = concat_audio(vo, gap=0.12)
    print("durs", [round(x, 2) for x in durs], "total", round(atot, 2))

    carousel = sorted((UI / "carousel_frames").glob("f_*.png"))
    composition = UI / "composition-dark.png"
    control = UI / "control-dark.png"
    collab = UI / "collaboration-dark.png"

    timeline: List[Image.Image] = []

    # 01 COLD OPEN — number hook
    d0 = durs[0]
    timeline += hold(big_number("120s", "THIS HORMONE DIES", "then becomes a drug empire story"), d0 * 0.35)
    timeline += hold(kinetic_hook("We fold it LIVE", "with an AI agent on Omnigent", "COLD OPEN"), d0 * 0.35)
    timeline += hold(big_number("$B+", "DRUG CLASS STAKES", "metabolic medicines · GLP-1 story"), d0 * 0.30)

    # 02 PROMISE — three things
    timeline += burn(three_promises(), durs[1])

    # 03 BIO
    d3 = durs[2]
    timeline += hold(big_number("30", "AMINO ACIDS", "GLP-1 (7–36) amide"), d3 * 0.25)
    timeline += burn(bio_sequence(), d3 * 0.75)

    # 04 STAKES / drug
    timeline += burn(drug_story(), durs[3])

    # 05 ENG
    d5 = durs[4]
    timeline += hold(kinetic_hook("ONE LINE.", "Swap the model. Keep the tools.", "ENGINEERING"), d5 * 0.3)
    timeline += burn(eng_yaml(), d5 * 0.7, z0=1.0, z1=1.03)

    # 06 PRODUCT UI — real screenshots pattern interrupt
    d6 = durs[5]
    if carousel:
        n = max(1, int(d6 * 0.4 * FPS))
        for i in range(n):
            cf = fit_cover(Image.open(carousel[i % len(carousel)]), W, H)
            timeline.append(lower(cf, "REAL OMNIGENT WORKSPACE · DATABRICKS"))
    if composition.exists():
        timeline += hold(product_ui(composition, "Share · Agents · multi-agent sessions"), d6 * 0.35)
    if control.exists():
        timeline += hold(product_ui(control, "Policies · approvals · control layer"), d6 * 0.25)

    # 07 BOLTZ proof
    d7 = durs[6]
    timeline += hold(metrics_bang(), d7 * 0.45)
    timeline += spin(d7 * 0.55, "SEQUENCE IN → COORDINATES OUT")

    # 08 SPIN beauty
    timeline += spin(durs[7], "THE FOLD · GLP-1 · BOLTZ")

    # 09 VALUE for everyone
    timeline += burn(audience_scoreboard(), durs[8])

    # 10 CTA
    timeline += hold(cta(), durs[9])

    need = int(round(atot * FPS))
    if len(timeline) < need:
        timeline += [timeline[-1].copy() for _ in range(need - len(timeline))]
    else:
        timeline = timeline[:need]

    print(f"=== frames {len(timeline)} ({len(timeline)/FPS:.1f}s) ===")
    for i, fr in enumerate(timeline):
        fr.save(FRAMES / f"f_{i:05d}.png")
        if i % 300 == 0:
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

    loud = OUT / "narr_loud.m4a"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(audio),
            "-af",
            "loudnorm=I=-14:TP=-1.0:LRA=9,acompressor=threshold=-18dB:ratio=3:attack=5:release=50",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(loud),
        ],
        check=True,
        capture_output=True,
    )

    final = ROOT / "outputs" / "omnigent_glp1_hormone_e2e_demo.mp4"
    # slight audio duck not needed - single track
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

    ship = ROOT / "outputs" / "FINAL_omnigent_glp1_demo.mp4"
    shutil.copy(final, ship)
    # also beast-named alias
    shutil.copy(final, ROOT / "outputs" / "BEAST_omnigent_boltz_glp1_demo.mp4")

    # thumbnail / poster — first hook frame
    timeline[int(0.5 * FPS)].save(ROOT / "docs" / "assets" / "beast_thumbnail.png")
    timeline[len(timeline) // 3].save(ROOT / "docs" / "assets" / "beast_poster.png")

    meta = {
        "final": str(final),
        "aliases": [
            "outputs/FINAL_omnigent_glp1_demo.mp4",
            "outputs/BEAST_omnigent_boltz_glp1_demo.mp4",
        ],
        "duration_s": ffprobe_dur(final),
        "style": "retention hooks + multi-audience value + real proof",
        "metrics": METRICS,
        "voice": "Liam (ElevenLabs energetic)",
        "audiences": ["bio", "eng", "tech leadership", "scientists"],
    }
    (ROOT / "outputs" / "beast_e2e_session.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
