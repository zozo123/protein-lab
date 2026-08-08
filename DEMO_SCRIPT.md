# Live demo script — Omnigent Protein Lab (~3 minutes)

## Setup (once)

```bash
cd protein-folding-fun
source .venv/bin/activate
export PYTHONPATH=$PWD

# Offline safety net (already generated movies if you ran run_demo)
open outputs/omnigent_protein_lab_ubiquitin_promo.mp4
open demo/viewer.html

# Live agent (needs Omnigent + a model provider)
# curl -fsSL https://omnigent.ai/install.sh | sh && omnigent setup
omni run ./agents/protein-lab
```

## Beat sheet

| Time | What you say | What you show |
|------|----------------|---------------|
| 0:00 | “Omnigent is Databricks’ meta-harness — one YAML agent, swap harnesses, policies, share the session.” | [docs.databricks.com/aws/en/omnigent](https://docs.databricks.com/aws/en/omnigent/) |
| 0:20 | “Here is **Protein Lab**: a custom Omnigent agent with tools for sequence → structure → movie.” | `agents/protein-lab/config.yaml` (highlight `tools:` and `harness:`) |
| 0:40 | Chat: *“Fold ubiquitin and make a spin movie.”* | Omnigent web UI — tool cards for `predict_structure` → `render_structure` → `make_structure_movie` |
| 1:20 | “Engine was `demo-rcsb` so the demo is fast; install Boltz for live predictions.” | Agent reply quoting engine + Rg + paths |
| 1:40 | Play the spin + promo films. | `outputs/ubiquitin/ubiquitin_spin.mp4` then promo MP4 |
| 2:10 | Optional: open interactive viewer, switch to GFP. | `demo/viewer.html` |
| 2:30 | “One-line harness swap keeps tools identical — that’s the meta-harness idea.” | Change `harness: claude-sdk` → `codex` (don’t save if you can’t re-run) |
| 2:50 | CTA: clone repo, `python -m demo.run_demo`, then `omni run ./agents/protein-lab`. | README |

## Fallback if Omnigent isn’t installed

Run the offline pipeline and narrate the same tool sequence:

```bash
python -m demo.run_demo --target ubiquitin
python -m demo.run_demo --target gfp --frames 48
python scripts/make_promo_storyboard.py --target ubiquitin
```

Talk track: “These are the exact callables wired into the Omnigent YAML — when `omni` is up, the agent drives them for you.”

## Sample prompts for the agent

- Fold ubiquitin and make a movie
- Show me green fluorescent protein
- List demo targets, then fold crambin with engine demo
- Fetch UniProt P0CG48 and summarize what you would predict
- Run Boltz on prediction-input.json and make a spin movie of the complex

## Boltz API live path (recommended)

```bash
export BOLTZ_API_KEY='sk_bc_...'   # never commit the key
./scripts/run_boltz_e2e.sh
open outputs/boltz-aspirin-peptide/boltz-aspirin-peptide_spin.mp4
open outputs/omnigent_boltz_e2e_promo.mp4
```

Talk track: peptide + aspirin went to Boltz cloud, confidence came back, then the same Omnigent viz tools rendered the spin movie.
