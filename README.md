# Protein Lab

Protein Lab is a small structural-biology agent built for **[Omnigent](https://omnigent.ai/)** with an optional **[Boltz](https://github.com/jwohlwend/boltz)** prediction path.

The repository contains the actual Omnigent agent image, native Python tool wrappers, reusable structure/prediction code, the GLP-1 input payload, renderers, and demo-film scripts.

```text
GLP-1 sequence
    ↓
Omnigent agent
    ↓
Boltz prediction (or explicit RCSB demo fallback)
    ↓
confidence + structure file
    ↓
hero still + rotating movie
```

## What is really wired into Omnigent

The runnable agent lives at:

```text
agents/protein-lab/
├── config.yaml
├── AGENTS.md
└── tools/python/protein_tools.py
```

`tools/python/protein_tools.py` uses Omnigent's native `@tool` decorator so the functions are auto-discovered as local tools. The wrappers delegate to the reusable implementation in `tools/protein_tools.py`.

The agent exposes these real operations:

- `list_demo_targets`
- `fetch_uniprot_sequence`
- `predict_structure`
- `summarize_structure`
- `render_structure`
- `make_structure_movie`
- `run_boltz_api_prediction`

The implementation writes generated structures, images, metrics, and movies under `outputs/`.

## GLP-1 demo

The checked-in input is `prediction-input-glp1.json` and contains the 30-residue GLP-1 (7-36) sequence:

```text
HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR
```

For the live cloud path:

```bash
# install / authenticate Boltz API first
boltz-api auth login

# then run the repository helper
.venv/bin/python -m demo.run_boltz_e2e --input prediction-input-glp1.json
```

For the Omnigent path:

```bash
# install Omnigent using the official installer
curl -fsSL https://omnigent.ai/install.sh | sh
omnigent setup

# from the repository root
omni run ./agents/protein-lab
```

Example prompt:

```text
Fold the GLP-1 sequence with Boltz, report the confidence metrics,
render a still, and make a rotating movie.
```

The Omnigent agent is instructed to identify the engine used and to avoid presenting the RCSB fallback as a prediction.

## Quick offline/demo path

```bash
uv venv .venv && source .venv/bin/activate
uv pip install -e .

python -m demo.run_demo --target ubiquitin
open outputs/ubiquitin/ubiquitin_spin.mp4
```

If local Boltz is installed, `predict_structure(engine="auto")` can use it. Otherwise the curated demo path uses RCSB experimental structures and reports that explicitly.

## Source layout

```text
agents/protein-lab/          Omnigent agent image + native local tools
tools/protein_tools.py       prediction, metrics, render, movie implementation
demo/                        standalone runners and narration assets
scripts/                     film composers and high-resolution GLP-1 renderer
prediction-input-glp1.json   exact 30-residue GLP-1 Boltz payload
outputs/                     generated artifacts (gitignored)
```

## Validate the Omnigent agent

With Omnigent installed, its own parser/validator can check the agent image:

```bash
python scripts/validate_omnigent_agent.py
```

A successful result prints the parsed agent name and confirms the spec is valid.

## Demo films

The repository includes film-composition source, while generated MP4/audio outputs are intentionally gitignored.

| Script | Purpose |
|---|---|
| `scripts/render_glp1_premium.py` | high-resolution GLP-1 structure renderer |
| `scripts/compose_28s_nyt.py` | ~28s full story |
| `scripts/compose_straight_e2e.py` | short E2E cut |
| `scripts/compose_40s_full_story.py` | longer story cut |

## References

- [Omnigent](https://omnigent.ai/)
- [Omnigent source](https://github.com/omnigent-ai/omnigent)
- [Databricks](https://www.databricks.com/)
- [Boltz](https://github.com/jwohlwend/boltz)

## License

Demo code in this repository is free to reuse. Omnigent, Boltz, RCSB, Databricks, and ElevenLabs have their own terms and licenses.
