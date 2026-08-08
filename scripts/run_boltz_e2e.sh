#!/usr/bin/env bash
# Omnigent × Boltz API end-to-end demo
# Usage:
#   export BOLTZ_API_KEY='sk_bc_...'
#   ./scripts/run_boltz_e2e.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PATH="${HOME}/.local/bin:${PATH}"

if [[ -z "${BOLTZ_API_KEY:-}" ]]; then
  echo "Set BOLTZ_API_KEY first (do not commit the key)."
  echo "  export BOLTZ_API_KEY='sk_bc_...'"
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Create the venv first: uv venv .venv && uv pip install -e ."
  exit 1
fi

if ! command -v boltz-api >/dev/null 2>&1; then
  echo "Installing boltz-api…"
  curl -fsSL https://install.boltz.bio/boltz-api/install.sh | sh
fi

echo "Auth check…"
boltz-api auth whoami --format pretty || true

echo "Running e2e prediction + viz…"
.venv/bin/python -m demo.run_boltz_e2e \
  --input prediction-input.json \
  --name aspirin-peptide-demo \
  --root-dir outputs/boltz-e2e

echo
echo "Open:"
echo "  outputs/boltz-aspirin-peptide/boltz-aspirin-peptide_spin.mp4"
echo "  outputs/omnigent_boltz_e2e_promo.mp4  (if generated)"
