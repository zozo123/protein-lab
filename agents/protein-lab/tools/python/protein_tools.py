"""Omnigent tool wrappers for Protein Lab.

The implementation lives in the repository-level ``tools/protein_tools.py`` so
it can also be used by standalone demos.  These decorated wrappers make the
same functions available as native Omnigent local tools when running the agent
image in ``agents/protein-lab``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# agents/protein-lab/tools/python/protein_tools.py -> repository root
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from omnigent.tools import tool
from tools import protein_tools as impl


@tool
def list_demo_targets() -> dict[str, Any]:
    """List curated demo proteins, including GLP-1, with sequence metadata."""
    return impl.list_demo_targets()


@tool
def fetch_uniprot_sequence(accession: str) -> dict[str, Any]:
    """Fetch a protein sequence from UniProt or the curated local demo catalog."""
    return impl.fetch_uniprot_sequence(accession)


@tool
def predict_structure(
    target: str | None = None,
    sequence: str | None = None,
    pdb_id: str | None = None,
    engine: str = "auto",
) -> dict[str, Any]:
    """Predict or fetch a structure with Boltz or the explicit RCSB demo fallback."""
    return impl.predict_structure(
        target=target,
        sequence=sequence,
        pdb_id=pdb_id,
        engine=engine,
    )


@tool
def summarize_structure(structure_path: str) -> dict[str, Any]:
    """Return geometry and chain statistics for a PDB or mmCIF structure."""
    return impl.summarize_structure(structure_path)


@tool
def render_structure(
    structure_path: str,
    title: str | None = None,
    color: str = "#7C5CFF",
    out_name: str | None = None,
    angle: float = 25.0,
) -> dict[str, Any]:
    """Render a high-quality PNG still of a protein structure."""
    return impl.render_structure(
        structure_path=structure_path,
        title=title,
        color=color,
        out_name=out_name,
        angle=angle,
    )


@tool
def make_structure_movie(
    structure_path: str,
    title: str | None = None,
    color: str = "#7C5CFF",
    out_name: str | None = None,
    n_frames: int = 72,
    fps: int = 24,
    elevation: float = 18.0,
) -> dict[str, Any]:
    """Render a rotating MP4 (or GIF fallback) for the predicted structure."""
    return impl.make_structure_movie(
        structure_path=structure_path,
        title=title,
        color=color,
        out_name=out_name,
        n_frames=n_frames,
        fps=fps,
        elevation=elevation,
    )


@tool
def run_boltz_api_prediction(
    input_json_path: str,
    name: str = "omnigent-boltz-run",
    root_dir: str | None = None,
) -> dict[str, Any]:
    """Run a live Boltz cloud prediction using ``boltz-api`` and return metrics."""
    return impl.run_boltz_api_prediction(
        input_json_path=input_json_path,
        name=name,
        root_dir=root_dir,
    )
