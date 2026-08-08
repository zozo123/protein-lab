#!/usr/bin/env python3
"""
Standalone Omnigent Protein Lab demo (no LLM / no `omni` required).

Simulates the same tool calls the Omnigent agent would make, so you can
preview stills + the structure movie before wiring credentials.

Usage:
  python -m demo.run_demo
  python -m demo.run_demo --target gfp --frames 90
  python -m demo.run_demo --all
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure project root is importable when run as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.protein_tools import (  # noqa: E402
    DEMO_TARGETS,
    list_demo_targets,
    make_structure_movie,
    predict_structure,
    render_structure,
)


BANNER = r"""
 ╔══════════════════════════════════════════════════════════════╗
 ║   Omnigent · Protein Lab                                     ║
 ║   sequence → structure (Boltz / RCSB) → spin movie           ║
 ║   https://docs.databricks.com/aws/en/omnigent/               ║
 ╚══════════════════════════════════════════════════════════════╝
"""


def _print_json(label: str, payload: dict) -> None:
    print(f"\n── {label} ──")
    print(json.dumps(payload, indent=2))


def run_one(target: str, n_frames: int, fps: int, engine: str) -> dict:
    meta = DEMO_TARGETS[target]
    print(f"\n{'═' * 60}")
    print(f"  Target : {meta['name']}  ({target})")
    print(f"  PDB    : {meta['pdb_id']}")
    print(f"  Note   : {meta['description']}")
    print(f"{'═' * 60}")

    t0 = time.time()

    # 1. Same first tool call the Omnigent agent makes
    print("\n[1/4] predict_structure(...)")
    manifest = predict_structure(target=target, engine=engine)
    _print_json("manifest", manifest)
    if "error" in manifest:
        return manifest

    structure_path = manifest["structure_path"]
    color = manifest.get("color", meta["color"])

    # 2. Hero still
    print("\n[2/4] render_structure(...)")
    still = render_structure(
        structure_path=structure_path,
        title=meta["name"],
        color=color,
        out_name=target,
    )
    _print_json("still", still)

    # 3. Spin movie
    print(f"\n[3/4] make_structure_movie(... n_frames={n_frames}, fps={fps})")
    movie = make_structure_movie(
        structure_path=structure_path,
        title=f"{meta['name']} · Omnigent",
        color=color,
        out_name=target,
        n_frames=n_frames,
        fps=fps,
    )
    _print_json("movie", movie)

    # 4. Narration the agent would deliver in chat
    summary = manifest.get("summary", {})
    print("\n[4/4] Agent narration (what Omnigent would say)")
    print(
        f"""
  Folded **{meta['name']}** with engine `{manifest.get('engine')}`.

  • {summary.get('n_ca', '?')} Cα atoms across {summary.get('n_chains', '?')} chain(s)
  • Radius of gyration ≈ {summary.get('radius_of_gyration_A', '?')} Å
  • {meta['description']}

  Still : {still.get('image_path')}
  Movie : {movie.get('movie_path')}
  Hero  : {movie.get('hero_image')}
"""
    )
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s")

    return {
        "target": target,
        "manifest": manifest,
        "still": still,
        "movie": movie,
        "elapsed_s": round(elapsed, 2),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Omnigent Protein Lab demo")
    parser.add_argument(
        "--target",
        default="ubiquitin",
        choices=sorted(DEMO_TARGETS.keys()),
        help="Demo protein to fold/visualize",
    )
    parser.add_argument("--all", action="store_true", help="Run every demo target")
    parser.add_argument("--frames", type=int, default=72, help="Frames in the spin movie")
    parser.add_argument("--fps", type=int, default=24, help="Movie frame rate")
    parser.add_argument(
        "--engine",
        default="demo",
        choices=["auto", "boltz", "demo"],
        help="Structure engine (demo is fast + reliable for walkthroughs)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List demo targets and exit",
    )
    args = parser.parse_args(argv)

    print(BANNER)

    if args.list:
        _print_json("demo targets", list_demo_targets())
        return 0

    targets = list(DEMO_TARGETS.keys()) if args.all else [args.target]
    results = []
    for t in targets:
        results.append(run_one(t, n_frames=args.frames, fps=args.fps, engine=args.engine))

    # Write a session summary the Omnigent UI could share
    out = ROOT / "outputs" / "demo_session.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"\nSession summary → {out}")
    print(
        """
Next steps
──────────
• Open the MP4/GIF in outputs/<target>/
• Install Omnigent and chat with the same tools:
    curl -fsSL https://omnigent.ai/install.sh | sh
    omni run ./agents/protein-lab
• Optional real predictions:
    pip install boltz
    python -m demo.run_demo --engine boltz --target crambin
"""
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
