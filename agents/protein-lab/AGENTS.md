# Protein Lab — agent notes

You run inside **Omnigent**, Databricks' open meta-harness
([docs](https://docs.databricks.com/aws/en/omnigent/), [omnigent.ai](https://omnigent.ai/)).

## Repo layout

```
protein-folding-fun/
  agents/protein-lab/   ← this agent (config.yaml + AGENTS.md)
  tools/protein_tools.py
  demo/run_demo.py      ← offline walkthrough (no LLM required)
  outputs/              ← structures, stills, movies land here
```

## Tools

| Tool | Purpose |
|------|---------|
| `list_demo_targets` | Curated proteins for demos |
| `fetch_uniprot_sequence` | Pull FASTA from UniProt |
| `predict_structure` | Boltz (if installed) or RCSB demo |
| `summarize_structure` | Geometry stats |
| `render_structure` | Hero PNG still |
| `make_structure_movie` | Spinning MP4 / GIF |

## Boltz

[Boltz](https://github.com/jwohlwend/boltz) is an open biomolecular structure
model (Boltz-1 / Boltz-2). Install with:

```bash
pip install boltz
# or: uv pip install 'protein-folding-fun[boltz]'
```

When Boltz is absent, `predict_structure(engine="auto")` transparently loads
experimental structures from RCSB so demos never hang.

## Demo script (what a great session looks like)

Human: *Fold ubiquitin and make a movie.*

You:
1. `predict_structure(target="ubiquitin", engine="auto")`
2. `render_structure(structure_path=..., title="Ubiquitin", color="#7C5CFF")`
3. `make_structure_movie(structure_path=..., title="Ubiquitin · Omnigent")`
4. Reply with engine, stats, still path, movie path, and a short scientific note.
