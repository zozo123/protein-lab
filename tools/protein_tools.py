"""
Protein structure tools for Omnigent Protein Lab.

Pipeline:
  sequence → predict (Boltz when installed, else AlphaFold DB / RCSB demo)
           → render stills
           → structure movie (rotating 3D CA backbone)

All functions return JSON-serializable dicts so Omnigent can surface them
cleanly in the web UI and chat transcript.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx
import numpy as np
from Bio.PDB import PDBIO, PDBParser, Select
from Bio.PDB.Structure import Structure

# Project roots
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = PROJECT_ROOT / ".cache"

# Curated demo targets — short sequences / classic PDB entries that look great
DEMO_TARGETS: Dict[str, Dict[str, Any]] = {
    "ubiquitin": {
        "name": "Ubiquitin",
        "pdb_id": "1UBQ",
        "uniprot": "P0CG48",
        "description": "76-residue protein that tags substrates for degradation",
        "color": "#7C5CFF",
        "sequence": (
            "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"
        ),
    },
    "crambin": {
        "name": "Crambin",
        "pdb_id": "1CRN",
        "uniprot": "P01542",
        "description": "Tiny plant seed protein — classic crystallography target",
        "color": "#00D4AA",
        "sequence": (
            "TTCCPSIVARSNFNVCRLPGTPEAICATYTGCIIIPGATCPGDYAN"
        ),
    },
    "insulin": {
        "name": "Insulin (A+B chains, 2HIU)",
        "pdb_id": "2HIU",
        "uniprot": "P01308",
        "description": "Hormone that regulates blood glucose",
        "color": "#FF6B9D",
        "sequence": (
            "GIVEQCCTSICSLYQLENYCNFVNQHLCGSHLVEALYLVCGERGFFYTPKT"
        ),
    },
    "hemoglobin": {
        "name": "Hemoglobin (deoxy)",
        "pdb_id": "2HHB",
        "uniprot": "P69905",
        "description": "Oxygen-carrying tetramer in red blood cells",
        "color": "#FF4D4D",
        "sequence": (
            "VLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSHGSAQVKGHGKKVADALTNAVAHVDDMPNALSALSDLHAHKLRVDPVNFKLLSHCLLVTLAAHLPAEFTPAVHASLDKFLASVSTVLTSKYR"
        ),
    },
    "gfp": {
        "name": "Green fluorescent protein",
        "pdb_id": "1EMA",
        "uniprot": "P42212",
        "description": "Beta-barrel fluorophore used as a biology reporter",
        "color": "#39FF14",
        "sequence": (
            "MSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTLVTTFSYGVQCFSRYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTLVNRIELKGIDFKEDGNILGHKLEYNYNSHNVYIMADKQKNGIKVNFKIRHNIEDGSVQLADHYQQNTPIGDGPVLLPDNHYLSTQSALSKDPNEKRDHMVLLEFVTAAGITHGMDELYK"
        ),
    },
    "glp1": {
        "name": "GLP-1 (7–36) — the 2-minute hormone",
        "pdb_id": None,  # prefer live Boltz; no single classic monomer PDB
        "uniprot": "P01275",
        "description": (
            "Gut incretin peptide; natural half-life ~1–2 min. Fold family behind "
            "metabolic drugs (semaglutide class). Use prediction-input-glp1.json + boltz-api."
        ),
        "color": "#7C5CFF",
        "sequence": "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
    },
}


def _ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def list_demo_targets() -> Dict[str, Any]:
    """List curated demo proteins with short sequences and PDB ids."""
    return {
        "targets": [
            {
                "id": key,
                "name": meta["name"],
                "pdb_id": meta["pdb_id"],
                "uniprot": meta["uniprot"],
                "description": meta["description"],
                "length": len(meta["sequence"]),
            }
            for key, meta in DEMO_TARGETS.items()
        ],
        "hint": (
            "Pass any target id to predict_structure(target=...), "
            "or supply a raw amino-acid sequence."
        ),
    }


def fetch_uniprot_sequence(accession: str) -> Dict[str, Any]:
    """
    Fetch a protein sequence from UniProt by accession (e.g. P0CG48).

    Falls back to curated demo data when offline or for known accessions.
    """
    accession = accession.strip().upper()
    for key, meta in DEMO_TARGETS.items():
        if meta["uniprot"].upper() == accession:
            return {
                "accession": accession,
                "name": meta["name"],
                "sequence": meta["sequence"],
                "length": len(meta["sequence"]),
                "source": f"demo-catalog:{key}",
            }

    url = f"https://rest.uniprot.org/uniprotkb/{accession}.fasta"
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            lines = resp.text.strip().splitlines()
            header = lines[0][1:] if lines and lines[0].startswith(">") else accession
            sequence = "".join(line.strip() for line in lines[1:] if line)
            return {
                "accession": accession,
                "name": header.split("|")[-1] if "|" in header else header,
                "sequence": sequence,
                "length": len(sequence),
                "source": "uniprot",
            }
    except Exception as exc:  # noqa: BLE001 — surface as tool error payload
        return {
            "error": f"Could not fetch UniProt {accession}: {exc}",
            "hint": "Try a demo target id via list_demo_targets().",
        }


def _download_pdb(pdb_id: str) -> Path:
    """Download a PDB file from RCSB into the cache."""
    _ensure_dirs()
    pdb_id = pdb_id.upper()
    dest = CACHE_DIR / f"{pdb_id}.pdb"
    if dest.exists() and dest.stat().st_size > 200:
        return dest

    urls = [
        f"https://files.rcsb.org/download/{pdb_id}.pdb",
        f"https://files.rcsb.org/view/{pdb_id}.pdb",
    ]
    last_err: Optional[Exception] = None
    for url in urls:
        try:
            with httpx.Client(timeout=60.0, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()
                dest.write_text(resp.text)
                return dest
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise RuntimeError(f"Failed to download PDB {pdb_id}: {last_err}")


def _boltz_available() -> bool:
    try:
        import boltz  # type: ignore  # noqa: F401
        return True
    except ImportError:
        return shutil.which("boltz") is not None


def _run_boltz_predict(sequence: str, name: str, out_dir: Path) -> Optional[Path]:
    """
    Attempt a real Boltz structure prediction when the package/CLI is present.

    Returns path to predicted PDB/CIF, or None if Boltz is unavailable.
    """
    if not _boltz_available():
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    fasta = out_dir / f"{name}.fasta"
    fasta.write_text(f">{name}\n{sequence}\n")

    # Prefer CLI; fall back to Python API if present.
    boltz_bin = shutil.which("boltz")
    if boltz_bin:
        cmd = [
            boltz_bin,
            "predict",
            str(fasta),
            "--out_dir",
            str(out_dir),
            "--output_format",
            "pdb",
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
            # Boltz lays out predictions under out_dir; pick first pdb/cif.
            for pattern in ("**/*.pdb", "**/*.cif"):
                hits = sorted(out_dir.glob(pattern))
                if hits:
                    return hits[0]
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return None
    return None


def _resolve_target(
    target: Optional[str] = None,
    sequence: Optional[str] = None,
    pdb_id: Optional[str] = None,
) -> Dict[str, Any]:
    if target:
        key = target.strip().lower()
        if key not in DEMO_TARGETS:
            raise ValueError(
                f"Unknown target '{target}'. Known: {', '.join(DEMO_TARGETS)}"
            )
        meta = DEMO_TARGETS[key]
        return {
            "id": key,
            "name": meta["name"],
            "sequence": meta["sequence"],
            "pdb_id": meta["pdb_id"],
            "color": meta["color"],
            "description": meta["description"],
        }
    if pdb_id:
        return {
            "id": pdb_id.lower(),
            "name": pdb_id.upper(),
            "sequence": sequence or "",
            "pdb_id": pdb_id.upper(),
            "color": "#7C5CFF",
            "description": f"Structure {pdb_id.upper()}",
        }
    if sequence:
        clean = "".join(c for c in sequence.upper() if c.isalpha())
        return {
            "id": "custom",
            "name": "Custom sequence",
            "sequence": clean,
            "pdb_id": None,
            "color": "#00B4D8",
            "description": f"Custom sequence ({len(clean)} aa)",
        }
    raise ValueError("Provide target=, sequence=, or pdb_id=")


def predict_structure(
    target: Optional[str] = None,
    sequence: Optional[str] = None,
    pdb_id: Optional[str] = None,
    engine: str = "auto",
) -> Dict[str, Any]:
    """
    Predict or fetch a 3D protein structure.

    engine:
      - "auto"  — try Boltz, else demo fallback (RCSB / AlphaFold-like)
      - "boltz" — require Boltz; error if missing
      - "demo"  — always use curated RCSB structures (fast, offline-friendly)

    Returns paths and metadata for the Omnigent agent to hand to visualization.
    """
    _ensure_dirs()
    resolved = _resolve_target(target=target, sequence=sequence, pdb_id=pdb_id)
    name = resolved["id"]
    work = OUTPUT_DIR / name
    work.mkdir(parents=True, exist_ok=True)

    used_engine = "demo"
    structure_path: Optional[Path] = None
    notes: List[str] = []

    want_boltz = engine in ("auto", "boltz")
    if want_boltz and resolved["sequence"]:
        boltz_out = work / "boltz"
        path = _run_boltz_predict(resolved["sequence"], name, boltz_out)
        if path is not None:
            structure_path = path
            used_engine = "boltz"
            notes.append("Structure predicted with Boltz.")
        elif engine == "boltz":
            return {
                "error": "Boltz is not installed or failed.",
                "install": "pip install 'protein-folding-fun[boltz]'  # or: pip install boltz",
                "hint": "Use engine='demo' for a fast RCSB-backed walkthrough.",
            }
        else:
            notes.append(
                "Boltz not available — using demo fallback (RCSB experimental structure)."
            )

    if structure_path is None:
        if not resolved.get("pdb_id"):
            # Map custom short sequences to the closest demo for visualization.
            notes.append(
                "No PDB id for custom sequence; mapping to ubiquitin demo structure "
                "for visualization (sequence length differs — for real work, install Boltz)."
            )
            resolved["pdb_id"] = "1UBQ"
            name = "custom"
        structure_path = _download_pdb(resolved["pdb_id"])
        # Copy into work dir so outputs are self-contained
        dest = work / f"{resolved['pdb_id']}.pdb"
        if structure_path.resolve() != dest.resolve():
            dest.write_text(structure_path.read_text())
        structure_path = dest
        used_engine = "demo-rcsb"
        notes.append(f"Loaded experimental structure {resolved['pdb_id']} from RCSB.")

    # Write a small manifest the agent can quote
    summary = summarize_structure(str(structure_path))
    manifest = {
        "target": resolved["id"],
        "name": resolved["name"],
        "description": resolved["description"],
        "sequence_length": len(resolved["sequence"]) if resolved["sequence"] else None,
        "engine": used_engine,
        "structure_path": str(structure_path),
        "color": resolved["color"],
        "notes": notes,
        "summary": summary,
    }
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def _parse_structure(structure_path: str) -> Structure:
    """Parse PDB or mmCIF into a Biopython Structure."""
    path = Path(structure_path)
    suffix = path.suffix.lower()
    if suffix in {".cif", ".mmcif"}:
        from Bio.PDB import MMCIFParser

        parser = MMCIFParser(QUIET=True)
    else:
        parser = PDBParser(QUIET=True)
    return parser.get_structure("prot", str(path))


def _load_ca_coords(structure_path: str) -> Tuple[np.ndarray, List[str], List[str]]:
    """
    Load coordinates for visualization.

    - Protein residues: C-alpha atoms
    - Ligands / hetero: heavy atoms (non-H) so small molecules show up
    """
    structure = _parse_structure(structure_path)
    coords: List[List[float]] = []
    resnames: List[str] = []
    chains: List[str] = []
    for model in structure:
        for chain in model:
            for residue in chain:
                hetflag = residue.id[0]
                is_hetero = hetflag != " "
                # Skip waters
                if residue.get_resname() in {"HOH", "WAT"}:
                    continue
                if not is_hetero and "CA" in residue:
                    atom = residue["CA"]
                    coords.append(list(atom.coord))
                    resnames.append(residue.get_resname())
                    chains.append(chain.id)
                elif is_hetero or "CA" not in residue:
                    # Ligand / nonstandard — take heavy atoms
                    for atom in residue:
                        if atom.element == "H":
                            continue
                        coords.append(list(atom.coord))
                        resnames.append(residue.get_resname())
                        chains.append(chain.id)
        break  # first model only
    if not coords:
        raise ValueError(f"No atoms found in {structure_path}")
    arr = np.asarray(coords, dtype=float)
    # Center
    arr = arr - arr.mean(axis=0)
    return arr, resnames, chains


def summarize_structure(structure_path: str) -> Dict[str, Any]:
    """Compute basic geometric stats for a PDB/CIF structure."""
    path = Path(structure_path)
    if not path.exists():
        return {"error": f"File not found: {structure_path}"}
    try:
        coords, resnames, chains = _load_ca_coords(str(path))
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}

    # End-to-end distance and radius of gyration
    e2e = float(np.linalg.norm(coords[-1] - coords[0]))
    rg = float(np.sqrt(np.mean(np.sum(coords**2, axis=1))))
    unique_chains = sorted(set(chains))
    return {
        "path": str(path),
        "n_ca": int(len(coords)),
        "n_chains": len(unique_chains),
        "chains": unique_chains,
        "radius_of_gyration_A": round(rg, 2),
        "end_to_end_A": round(e2e, 2),
        "span_A": {
            "x": round(float(np.ptp(coords[:, 0])), 2),
            "y": round(float(np.ptp(coords[:, 1])), 2),
            "z": round(float(np.ptp(coords[:, 2])), 2),
        },
        "n_terminal_res": resnames[0] if resnames else None,
        "c_terminal_res": resnames[-1] if resnames else None,
    }


def _chain_color_map(chains: Sequence[str], base_hex: str) -> Dict[str, Tuple[float, float, float]]:
    """Assign distinct colors per chain, seeded from base_hex."""
    palette = [
        base_hex,
        "#00D4AA",
        "#FF6B9D",
        "#FFB703",
        "#4CC9F0",
        "#F72585",
        "#7209B7",
        "#3A0CA3",
    ]

    def hex_to_rgb(h: str) -> Tuple[float, float, float]:
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]

    unique = []
    for c in chains:
        if c not in unique:
            unique.append(c)
    return {c: hex_to_rgb(palette[i % len(palette)]) for i, c in enumerate(unique)}


def _rotate_y(coords: np.ndarray, angle_deg: float) -> np.ndarray:
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    r = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return coords @ r.T


def _rotate_x(coords: np.ndarray, angle_deg: float) -> np.ndarray:
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    r = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    return coords @ r.T


def _project(coords: np.ndarray) -> np.ndarray:
    """Simple perspective projection onto 2D."""
    # Camera looks down +z slightly toward origin
    z = coords[:, 2]
    depth = z - z.min() + 8.0
    scale = 180.0 / depth
    xy = coords[:, :2] * scale[:, None]
    return xy


def _draw_structure_frame(
    coords: np.ndarray,
    chains: Sequence[str],
    color_map: Dict[str, Tuple[float, float, float]],
    title: str,
    subtitle: str,
    out_path: Path,
    width: int = 1280,
    height: int = 720,
    show_glow: bool = True,
) -> None:
    """Render one high-quality backbone frame with matplotlib (Agg)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.patches import Circle

    # Depth sort for painter's algorithm
    order = np.argsort(coords[:, 2])
    xy = _project(coords)
    # Normalize into nice canvas margins
    if len(xy) > 0:
        span = max(float(np.ptp(xy[:, 0])), float(np.ptp(xy[:, 1])), 1.0)
        # Fill most of the canvas while leaving room for title chrome
        xy = xy / span * 0.92

    fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    fig.patch.set_facecolor("#0B0F1A")
    ax.set_facecolor("#0B0F1A")

    # Soft radial glow behind the molecule
    if show_glow:
        for r, alpha in [(0.95, 0.08), (0.7, 0.12), (0.45, 0.16)]:
            glow = Circle((0, 0), r, transform=ax.transData, color="#7C5CFF", alpha=alpha, zorder=0)
            ax.add_patch(glow)

    # Backbone segments with depth-based alpha and width
    segments = []
    colors = []
    widths = []
    for i in range(len(coords) - 1):
        # Only connect consecutive residues on the same chain
        if chains[i] != chains[i + 1]:
            continue
        p0 = xy[i]
        p1 = xy[i + 1]
        segments.append([p0, p1])
        depth = (coords[i, 2] + coords[i + 1, 2]) / 2.0
        # Map depth to brightness
        t = (depth - coords[:, 2].min()) / max(float(np.ptp(coords[:, 2])), 1e-6)
        base = np.array(color_map[chains[i]])
        # Lift toward white for near atoms
        rgb = base * (0.55 + 0.45 * t) + np.array([1, 1, 1]) * (0.15 * t)
        rgb = np.clip(rgb, 0, 1)
        colors.append((*rgb, 0.55 + 0.4 * t))
        widths.append(1.5 + 3.5 * t)

    if segments:
        lc = LineCollection(segments, colors=colors, linewidths=widths, capstyle="round", zorder=2)
        ax.add_collection(lc)

    # CA spheres, depth-sorted
    for idx in order:
        c = color_map[chains[idx]]
        depth = coords[idx, 2]
        t = (depth - coords[:, 2].min()) / max(float(np.ptp(coords[:, 2])), 1e-6)
        size = 18 + 55 * t
        ax.scatter(
            xy[idx, 0],
            xy[idx, 1],
            s=size,
            c=[c],
            edgecolors="white",
            linewidths=0.3,
            alpha=0.55 + 0.4 * t,
            zorder=3 + t,
        )

    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-0.72, 0.78)
    ax.set_aspect("equal")
    ax.axis("off")

    # Title block
    ax.text(
        0.02,
        0.96,
        title,
        transform=ax.transAxes,
        color="white",
        fontsize=18,
        fontweight="bold",
        va="top",
        fontfamily="sans-serif",
    )
    ax.text(
        0.02,
        0.90,
        subtitle,
        transform=ax.transAxes,
        color="#A0AEC0",
        fontsize=11,
        va="top",
        fontfamily="sans-serif",
    )
    ax.text(
        0.98,
        0.04,
        "Omnigent · Protein Lab",
        transform=ax.transAxes,
        color="#5A6478",
        fontsize=10,
        ha="right",
        va="bottom",
        fontfamily="sans-serif",
    )

    fig.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def render_structure(
    structure_path: str,
    title: Optional[str] = None,
    color: str = "#7C5CFF",
    out_name: Optional[str] = None,
    angle: float = 25.0,
) -> Dict[str, Any]:
    """
    Render a single still image of a protein backbone.

    Returns path to the PNG and basic stats.
    """
    _ensure_dirs()
    path = Path(structure_path)
    if not path.exists():
        return {"error": f"Structure not found: {structure_path}"}

    coords, _resnames, chains = _load_ca_coords(str(path))
    coords = _rotate_x(coords, 18)
    coords = _rotate_y(coords, angle)
    color_map = _chain_color_map(chains, color)

    stem = out_name or path.stem
    out_dir = OUTPUT_DIR / stem
    out_dir.mkdir(parents=True, exist_ok=True)
    out_png = out_dir / f"{stem}_still.png"

    display_title = title or path.stem
    subtitle = f"{len(coords)} Cα · {len(set(chains))} chain(s) · {path.name}"
    _draw_structure_frame(
        coords,
        chains,
        color_map,
        title=display_title,
        subtitle=subtitle,
        out_path=out_png,
    )
    return {
        "image_path": str(out_png),
        "n_ca": len(coords),
        "n_chains": len(set(chains)),
        "title": display_title,
    }


def make_structure_movie(
    structure_path: str,
    title: Optional[str] = None,
    color: str = "#7C5CFF",
    out_name: Optional[str] = None,
    n_frames: int = 72,
    fps: int = 24,
    elevation: float = 18.0,
) -> Dict[str, Any]:
    """
    Render a rotating 3D backbone movie (MP4 via ffmpeg, GIF fallback).

    Ideal for Omnigent demos and shared sessions — drop the clip into slides
    or the web UI transcript.
    """
    _ensure_dirs()
    path = Path(structure_path)
    if not path.exists():
        return {"error": f"Structure not found: {structure_path}"}

    coords0, _resnames, chains = _load_ca_coords(str(path))
    color_map = _chain_color_map(chains, color)

    stem = out_name or path.stem
    out_dir = OUTPUT_DIR / stem
    frames_dir = out_dir / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    display_title = title or path.stem
    subtitle = f"{len(coords0)} Cα · rotating view · Omnigent Protein Lab"

    frame_paths: List[Path] = []
    for i in range(n_frames):
        angle = 360.0 * i / n_frames
        coords = _rotate_x(coords0, elevation)
        coords = _rotate_y(coords, angle)
        fp = frames_dir / f"frame_{i:04d}.png"
        _draw_structure_frame(
            coords,
            chains,
            color_map,
            title=display_title,
            subtitle=subtitle,
            out_path=fp,
        )
        frame_paths.append(fp)

    mp4_path = out_dir / f"{stem}_spin.mp4"
    gif_path = out_dir / f"{stem}_spin.gif"
    movie_path: Optional[Path] = None
    format_used = None

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        # High quality H.264 with dark letterbox-friendly settings
        cmd = [
            ffmpeg,
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(frames_dir / "frame_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            str(mp4_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            movie_path = mp4_path
            format_used = "mp4"
        except subprocess.CalledProcessError as exc:
            # fall through to GIF
            err = (exc.stderr or "")[:400]
            notes = f"ffmpeg failed: {err}"
        else:
            notes = "Encoded with ffmpeg (H.264)."
    else:
        notes = "ffmpeg not found; building GIF with Pillow."

    if movie_path is None:
        from PIL import Image

        images = [Image.open(fp).convert("P", palette=Image.ADAPTIVE) for fp in frame_paths]
        # Smaller GIF: every other frame if many frames
        step = 2 if n_frames > 48 else 1
        images = images[::step]
        duration = int(1000 / fps * step)
        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0,
            optimize=True,
        )
        movie_path = gif_path
        format_used = "gif"
        notes = "Encoded as GIF with Pillow."

    # Also keep a hero still (mid-rotation)
    mid = frame_paths[len(frame_paths) // 4]
    hero = out_dir / f"{stem}_hero.png"
    shutil.copy(mid, hero)

    return {
        "movie_path": str(movie_path),
        "format": format_used,
        "hero_image": str(hero),
        "n_frames": n_frames,
        "fps": fps,
        "frames_dir": str(frames_dir),
        "notes": notes,
        "title": display_title,
    }


# ---------------------------------------------------------------------------
# Optional: keep only polymer chains when writing cleaned PDBs
# ---------------------------------------------------------------------------


class _PolymerSelect(Select):
    def accept_residue(self, residue):  # type: ignore[no-untyped-def]
        return residue.id[0] == " "


def write_clean_pdb(structure_path: str, out_path: Optional[str] = None) -> Dict[str, Any]:
    """Write a cleaned polymer-only PDB (handy before sharing)."""
    path = Path(structure_path)
    structure = _parse_structure(str(path))
    dest = Path(out_path) if out_path else path.with_name(path.stem + "_clean.pdb")
    io = PDBIO()
    io.set_structure(structure)
    io.save(str(dest), _PolymerSelect())
    return {"path": str(dest)}


def run_boltz_api_prediction(
    input_json_path: str,
    name: str = "omnigent-boltz-run",
    root_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run a Boltz cloud prediction via `boltz-api` CLI.

    Requires BOLTZ_API_KEY in the environment, or a prior
    `boltz-api auth login` session. Input JSON shape:

      {
        "entities": [
          {"type": "protein", "value": "MKT...", "chain_ids": ["A"]},
          {"type": "ligand_smiles", "value": "CC(=O)O...", "chain_ids": ["B"]}
        ]
      }

    Returns run directory, structure path, and confidence metrics.
    """
    boltz = shutil.which("boltz-api") or str(Path.home() / ".local" / "bin" / "boltz-api")
    if not Path(boltz).exists():
        return {
            "error": "boltz-api CLI not found",
            "install": "curl -fsSL https://install.boltz.bio/boltz-api/install.sh | sh",
        }
    input_path = Path(input_json_path).resolve()
    if not input_path.exists():
        return {"error": f"Input not found: {input_json_path}"}

    root = Path(root_dir) if root_dir else (OUTPUT_DIR / "boltz-e2e")
    root.mkdir(parents=True, exist_ok=True)
    cmd = [
        boltz,
        "predictions:structure-and-binding",
        "run",
        "--input",
        f"@json://{input_path}",
        "--name",
        name,
        "--root-dir",
        str(root),
        "--progress-format",
        "text",
        "--format",
        "json",
    ]
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=900)
    except subprocess.CalledProcessError as exc:
        return {
            "error": "boltz-api prediction failed",
            "stderr": (exc.stderr or "")[:800],
            "stdout": (exc.stdout or "")[:400],
        }
    except subprocess.TimeoutExpired:
        return {"error": "boltz-api prediction timed out after 900s"}

    lines = (proc.stdout or "").strip().splitlines()
    run_dir = Path(lines[-1].strip()) if lines else root / name
    if not run_dir.exists():
        run_dir = root / name

    # Locate structure + metrics
    structure_path: Optional[Path] = None
    for pattern in ("**/*_predicted.cif", "**/*.cif", "**/*_predicted.pdb", "**/*.pdb"):
        hits = sorted(run_dir.glob(pattern))
        if hits:
            structure_path = hits[0]
            break
    metrics: Dict[str, Any] = {}
    for mp in run_dir.rglob("metrics.json"):
        try:
            metrics = json.loads(mp.read_text())
            break
        except json.JSONDecodeError:
            continue

    result = {
        "engine": "boltz-api",
        "run_dir": str(run_dir),
        "structure_path": str(structure_path) if structure_path else None,
        "metrics": metrics,
        "name": name,
    }
    if structure_path:
        result["summary"] = summarize_structure(str(structure_path))
    return result
