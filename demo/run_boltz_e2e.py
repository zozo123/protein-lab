#!/usr/bin/env python3
"""
End-to-end Boltz API demo for Omnigent Protein Lab.

Flow:
  1. Auth via BOLTZ_API_KEY (or prior `boltz-api auth login`)
  2. Submit structure+binding prediction from prediction-input.json
  3. Wait + download results
  4. Render still + spin movie with local viz tools

Usage:
  export BOLTZ_API_KEY='sk_bc_...'
  python -m demo.run_boltz_e2e

  # reuse an existing run directory (skip API)
  python -m demo.run_boltz_e2e --from-run outputs/boltz-e2e/aspirin-peptide-demo
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.protein_tools import make_structure_movie, render_structure, summarize_structure  # noqa: E402

DEFAULT_INPUT = ROOT / "prediction-input.json"
DEFAULT_ROOT = ROOT / "outputs" / "boltz-e2e"


BANNER = r"""
 ╔══════════════════════════════════════════════════════════════════╗
 ║  Omnigent × Boltz API  ·  e2e structure + binding demo           ║
 ║  peptide + aspirin  →  3D complex  →  spin movie                 ║
 ╚══════════════════════════════════════════════════════════════════╝
"""


def _boltz_bin() -> str:
    path = shutil.which("boltz-api") or str(Path.home() / ".local" / "bin" / "boltz-api")
    if not Path(path).exists():
        raise SystemExit(
            "boltz-api not found. Install with:\n"
            "  curl -fsSL https://install.boltz.bio/boltz-api/install.sh | sh"
        )
    return path


def _require_auth(boltz: str) -> dict:
    env = os.environ.copy()
    proc = subprocess.run(
        [boltz, "auth", "status", "--format", "json"],
        capture_output=True,
        text=True,
        env=env,
    )
    status = {}
    try:
        status = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        pass
    if not status.get("authenticated") and not os.environ.get("BOLTZ_API_KEY"):
        raise SystemExit(
            "Not authenticated.\n"
            "  export BOLTZ_API_KEY='sk_bc_...'\n"
            "  # or: boltz-api auth login --device-code"
        )
    return status


def estimate_cost(boltz: str, input_path: Path) -> dict:
    proc = subprocess.run(
        [
            boltz,
            "predictions:structure-and-binding",
            "estimate-cost",
            "--input",
            f"@json://{input_path}",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(f"estimate-cost failed ({proc.returncode})")
    # CLI may print a wrapper; try last JSON object
    text = proc.stdout.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def run_prediction(boltz: str, input_path: Path, name: str, root_dir: Path) -> Path:
    root_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        boltz,
        "predictions:structure-and-binding",
        "run",
        "--input",
        f"@json://{input_path}",
        "--name",
        name,
        "--root-dir",
        str(root_dir),
        "--progress-format",
        "text",
        "--verbose",
        "--format",
        "json",
    ]
    print("\n→ boltz-api predictions:structure-and-binding run …")
    print("  ", " ".join(cmd[:6]), "…")
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
    elapsed = time.time() - t0
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(f"prediction run failed ({proc.returncode})")
    # stdout is often just the run directory path
    out = (proc.stdout or "").strip().splitlines()
    run_dir = Path(out[-1].strip()) if out else root_dir / name
    if not run_dir.exists():
        # fallback
        run_dir = root_dir / name
    print(f"  completed in {elapsed:.1f}s → {run_dir}")
    return run_dir


def find_predicted_structure(run_dir: Path) -> Path:
    candidates = list(run_dir.rglob("*_predicted.cif")) + list(run_dir.rglob("*.cif"))
    candidates += list(run_dir.rglob("*_predicted.pdb")) + list(run_dir.rglob("*.pdb"))
    # prefer predicted
    preferred = [c for c in candidates if "predicted" in c.name]
    pick = preferred[0] if preferred else (candidates[0] if candidates else None)
    if pick is None:
        raise SystemExit(f"No structure file found under {run_dir}")
    return pick


def find_metrics(run_dir: Path) -> dict:
    for p in run_dir.rglob("metrics.json"):
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
    return {}


def visualize(structure_path: Path, out_name: str, title: str) -> dict:
    summary = summarize_structure(str(structure_path))
    still = render_structure(
        structure_path=str(structure_path),
        title=title,
        color="#7C5CFF",
        out_name=out_name,
    )
    movie = make_structure_movie(
        structure_path=str(structure_path),
        title=f"{title} · Boltz",
        color="#7C5CFF",
        out_name=out_name,
        n_frames=72,
        fps=24,
    )
    return {"summary": summary, "still": still, "movie": movie}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Boltz API e2e demo")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--name", default="aspirin-peptide-demo")
    parser.add_argument("--root-dir", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--from-run",
        type=Path,
        default=None,
        help="Skip API; visualize an existing run directory",
    )
    parser.add_argument("--skip-estimate", action="store_true")
    args = parser.parse_args(argv)

    print(BANNER)

    if not args.input.exists() and args.from_run is None:
        raise SystemExit(f"Missing input: {args.input}")

    boltz = _boltz_bin()
    print(f"boltz-api : {boltz}")
    if os.environ.get("BOLTZ_API_KEY"):
        print("auth      : BOLTZ_API_KEY (env)")
    else:
        status = _require_auth(boltz)
        print(f"auth      : {status.get('effective_mode') or status.get('mode') or 'session'}")

    run_dir: Path
    if args.from_run:
        run_dir = args.from_run
        print(f"\n→ reusing run: {run_dir}")
    else:
        if not args.skip_estimate:
            print("\n→ estimate-cost")
            est = estimate_cost(boltz, args.input.resolve())
            print(json.dumps(est, indent=2)[:800])
        run_dir = run_prediction(boltz, args.input.resolve(), args.name, args.root_dir)

    structure = find_predicted_structure(run_dir)
    metrics = find_metrics(run_dir)
    print(f"\n→ structure: {structure}")
    if metrics:
        best = metrics.get("best_sample", metrics)
        m = best.get("metrics", best) if isinstance(best, dict) else {}
        print("  confidence metrics:")
        for k in (
            "structure_confidence",
            "ptm",
            "iptm",
            "ligand_iptm",
            "complex_plddt",
        ):
            if k in m:
                print(f"    {k}: {m[k]:.3f}")

    print("\n→ visualize (still + spin movie)")
    viz = visualize(
        structure,
        out_name="boltz-aspirin-peptide",
        title="Peptide · Aspirin complex",
    )
    print(json.dumps(viz["summary"], indent=2))
    print(f"\n  Still : {viz['still'].get('image_path')}")
    print(f"  Movie : {viz['movie'].get('movie_path')}")
    print(f"  Hero  : {viz['movie'].get('hero_image')}")

    session = {
        "input": str(args.input),
        "run_dir": str(run_dir),
        "structure": str(structure),
        "metrics": metrics,
        "visualization": viz,
        "omnigent_hint": "omni run ./agents/protein-lab",
    }
    session_path = ROOT / "outputs" / "boltz_e2e_session.json"
    session_path.write_text(json.dumps(session, indent=2, default=str))
    print(f"\nSession → {session_path}")
    print(
        """
Demo complete.
  • Open the MP4 still paths above
  • Wire into Omnigent: omni run ./agents/protein-lab
  • Re-viz only: python -m demo.run_boltz_e2e --from-run """
        + str(run_dir)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
