# Protein Lab

Simple structural-biology demo agent for **[Omnigent](https://docs.databricks.com/aws/en/omnigent/)** (Databricks meta-harness) + optional **[Boltz](https://github.com/jwohlwend/boltz)** cloud structure prediction.

```
sequence → Boltz (or RCSB demo) → still + spin movie
              ↑
     Omnigent agent (YAML + Python tools)
```

## Quick start (offline, no API keys)

```bash
uv venv .venv && source .venv/bin/activate
uv pip install -e .

python -m demo.run_demo --target ubiquitin
open outputs/ubiquitin/ubiquitin_spin.mp4
```

## Live Boltz (GLP-1 story)

```bash
# boltz-api: https://install.boltz.bio/boltz-api/install.sh
boltz-api auth login   # or export BOLTZ_API_KEY=...

.venv/bin/python -m demo.run_boltz_e2e --input prediction-input-glp1.json
```

Input: `prediction-input-glp1.json` (GLP-1 7–36: `HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR`).

## Omnigent agent

```bash
export PYTHONPATH=$PWD
omni run ./agents/protein-lab
# "Fold GLP-1 with Boltz and make a spin movie"
```

Agent config: `agents/protein-lab/config.yaml`  
Tools: `tools/protein_tools.py`

## Demo films

| Script | Output |
|--------|--------|
| `scripts/compose_28s_nyt.py` | ~28s NYT-style full story (structure-forward) |
| `scripts/compose_40s_full_story.py` | ~40s cut |
| `scripts/compose_straight_e2e.py` | short straight cut |

ElevenLabs VO needs `ELEVENLABS_API_KEY` in `.env` (gitignored).

```bash
.venv/bin/python scripts/compose_28s_nyt.py
open outputs/omnigent_boltz_glp1_28s.mp4
```

## Layout

```
agents/protein-lab/     Omnigent custom agent
tools/protein_tools.py  predict / render / movie / boltz-api
demo/                   offline + boltz runners, VO scripts
scripts/                film composers
prediction-input*.json  Boltz entity payloads
```

## Docs

- [Omnigent on Databricks](https://docs.databricks.com/aws/en/omnigent/)
- [omnigent.ai](https://omnigent.ai/)
- [Boltz](https://github.com/jwohlwend/boltz)

## License

Demo code is free to reuse. Boltz, RCSB, Omnigent, and ElevenLabs have their own terms.
