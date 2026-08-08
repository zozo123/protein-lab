#!/usr/bin/env python3
"""
Premium all-atom GLP-1 structure renderer (correct for our Boltz CIF).

Uses heavy-atom stick + CA ribbon, N→C rainbow, dark Omnigent-style stage.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

import numpy as np
from Bio.PDB import MMCIFParser
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CIF = ROOT / "outputs/boltz-e2e/glp1-hormone-demo/outputs/files/prediction/sab_pred_rJOi1zeaNY6EhbxtFSAp_predicted.cif"
OUT = ROOT / "outputs" / "glp1_premium"
W, H = 1920, 1080


def font(size: int, bold: bool = False):
    for p in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else None,
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if p and Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def load_atoms(path: Path):
    parser = MMCIFParser(QUIET=True)
    structure = parser.get_structure("g", str(path))
    # backbone CA for ribbon
    cas = []
    # all heavy for sticks (within residue bonds approx by sequential CA + sidechain)
    heavies = []  # (xyz, res_idx, element, resname, atom_name)
    res_list = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.id[0] != " ":
                    continue
                res_list.append(residue)
                ridx = len(res_list) - 1
                if "CA" in residue:
                    cas.append(np.array(residue["CA"].coord, dtype=float))
                for atom in residue:
                    if atom.element == "H":
                        continue
                    heavies.append(
                        (
                            np.array(atom.coord, dtype=float),
                            ridx,
                            atom.element,
                            residue.get_resname(),
                            atom.get_name(),
                        )
                    )
        break
    cas = np.asarray(cas, dtype=float)
    center = cas.mean(axis=0) if len(cas) else np.zeros(3)
    cas = cas - center
    heavies = [(xyz - center, *rest) for xyz, *rest in heavies]
    return cas, heavies, res_list


def rot_y(pts: np.ndarray, deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return pts @ R.T


def rot_x(pts: np.ndarray, deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    R = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    return pts @ R.T


def rainbow(t: float) -> Tuple[int, int, int]:
    # purple → teal → pink for brand
    t = max(0.0, min(1.0, t))
    stops = [
        (0.0, (124, 92, 255)),
        (0.45, (0, 212, 170)),
        (0.75, (100, 180, 255)),
        (1.0, (236, 72, 153)),
    ]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0 + 1e-9)
            return tuple(int(c0[j] + (c1[j] - c0[j]) * u) for j in range(3))  # type: ignore
    return stops[-1][1]


def project(pts: np.ndarray) -> np.ndarray:
    z = pts[:, 2]
    depth = z - z.min() + 10.0
    scale = 520.0 / depth
    return pts[:, :2] * scale[:, None]


def render_frame(
    cas0: np.ndarray,
    heavies0,
    n_res: int,
    angle: float,
    elev: float = 22.0,
    title: str = "GLP-1 (7–36) · Boltz prediction",
    subtitle: str = "30 residues · structure_confidence 0.83 · pLDDT 0.90",
) -> Image.Image:
    img = Image.new("RGB", (W, H), (8, 10, 18))
    # radial glow
    glow = Image.new("RGB", (W, H), (8, 10, 18))
    gd = ImageDraw.Draw(glow)
    cx, cy = W // 2, H // 2 + 20
    for r, a in [(520, 28), (380, 40), (240, 55)]:
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(int(30 * a / 55), int(20 * a / 55), int(70 * a / 55)))
    glow = glow.filter(ImageFilter.GaussianBlur(50))
    img = Image.blend(img, glow, 0.65)
    d = ImageDraw.Draw(img)

    # transform
    cas = rot_y(rot_x(cas0, elev), angle)
    h_xyz = np.array([h[0] for h in heavies0])
    h_xyz = rot_y(rot_x(h_xyz, elev), angle)
    # normalize scale to canvas
    all_pts = np.vstack([cas, h_xyz]) if len(h_xyz) else cas
    xy = project(all_pts)
    span = max(float(np.ptp(xy[:, 0])), float(np.ptp(xy[:, 1])), 1.0)
    xy = xy / span * 0.78
    # map back
    n_ca = len(cas)
    ca_xy = xy[:n_ca]
    h_xy = xy[n_ca:]
    # to pixel
    def to_px(p):
        return (W / 2 + p[0] * (H * 0.42), H / 2 + 30 + p[1] * (H * 0.42))

    # depth sort heavies
    order = np.argsort(h_xyz[:, 2])
    elem_col = {"C": (180, 190, 220), "N": (100, 160, 255), "O": (255, 120, 120), "S": (240, 220, 80)}

    # bonds: within residue sequential atoms roughly distance-based
    # build neighbor bonds for heavy atoms < 1.9 A
    coords = h_xyz
    for i in range(len(coords)):
        for j in range(i + 1, min(i + 8, len(coords))):
            dist = np.linalg.norm(coords[i] - coords[j])
            if dist < 1.85:
                t = (coords[i, 2] + coords[j, 2]) / 2
                tnorm = (t - coords[:, 2].min()) / max(float(np.ptp(coords[:, 2])), 1e-6)
                alpha = int(80 + 140 * tnorm)
                p0 = to_px(h_xy[i])
                p1 = to_px(h_xy[j])
                ridx = heavies0[i][1]
                col = rainbow(ridx / max(n_res - 1, 1))
                col = tuple(int(c * (0.5 + 0.5 * tnorm)) for c in col)
                d.line([p0, p1], fill=col + (alpha,) if False else col, width=max(1, int(1 + 3 * tnorm)))

    # CA ribbon (thick)
    for i in range(n_ca - 1):
        t = (cas[i, 2] + cas[i + 1, 2]) / 2
        tnorm = (t - cas[:, 2].min()) / max(float(np.ptp(cas[:, 2])), 1e-6)
        col = rainbow(i / max(n_ca - 1, 1))
        col = tuple(min(255, int(c * (0.55 + 0.5 * tnorm) + 30 * tnorm)) for c in col)
        p0 = to_px(ca_xy[i])
        p1 = to_px(ca_xy[i + 1])
        d.line([p0, p1], fill=col, width=int(8 + 10 * tnorm))
        # soft outer
        d.line([p0, p1], fill=tuple(min(255, c + 40) for c in col), width=int(3 + 4 * tnorm))

    # CA spheres
    for i in range(n_ca):
        tnorm = (cas[i, 2] - cas[:, 2].min()) / max(float(np.ptp(cas[:, 2])), 1e-6)
        col = rainbow(i / max(n_ca - 1, 1))
        r = 6 + 10 * tnorm
        x, y = to_px(ca_xy[i])
        d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(255, 255, 255), width=1)

    # N / C termini labels
    nx, ny = to_px(ca_xy[0])
    cx, cy = to_px(ca_xy[-1])
    d.text((nx - 28, ny - 28), "N", fill=(124, 92, 255), font=font(22, True))
    d.text((cx + 12, cy - 28), "C", fill=(236, 72, 153), font=font(22, True))

    # chrome
    d.text((48, 40), title, fill=(245, 245, 250), font=font(32, True))
    d.text((48, 88), subtitle, fill=(150, 160, 185), font=font(18))
    d.text((W - 48, H - 40), "Omnigent · Protein Lab · Boltz", fill=(90, 95, 120), font=font(16), anchor="rd")
    # legend
    d.text((48, H - 80), "N→C rainbow  ·  ribbon = Cα  ·  sticks = heavy atoms", fill=(120, 125, 150), font=font(15))
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames_dir = OUT / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir()

    cas, heavies, res_list = load_atoms(CIF)
    n_res = len(res_list)
    print(f"CA={len(cas)} heavy={len(heavies)} residues={n_res}")

    n_frames = 96
    still = None
    for i in range(n_frames):
        angle = 360.0 * i / n_frames
        fr = render_frame(cas, heavies, n_res, angle)
        fr.save(frames_dir / f"frame_{i:04d}.png")
        if i == 12:
            still = fr
            fr.save(OUT / "glp1_premium_still.png")
            fr.save(ROOT / "docs/assets/glp1_premium_still.png")

    mp4 = OUT / "glp1_premium_spin.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            "24",
            "-i",
            str(frames_dir / "frame_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "16",
            "-movflags",
            "+faststart",
            str(mp4),
        ],
        check=True,
        capture_output=True,
    )
    print("wrote", mp4, still)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
