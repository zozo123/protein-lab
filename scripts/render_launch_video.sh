#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VIDEO_USE="${VIDEO_USE:-$HOME/Developer/video-use}"
EDIT="$ROOT/demo-footage/edit"
cd "$VIDEO_USE"
uv run python helpers/render.py "$EDIT/edl.json" -o "$EDIT/final.mp4" --no-subtitles --no-loudnorm
cp "$EDIT/final.mp4" "$ROOT/outputs/omnigent_protein_lab_launch.mp4"
echo "Shipped → $ROOT/outputs/omnigent_protein_lab_launch.mp4"
