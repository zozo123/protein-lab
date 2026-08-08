#!/usr/bin/env python3
"""Validate the Protein Lab agent with Omnigent's own parser and validator."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "agents" / "protein-lab"


def main() -> int:
    try:
        from omnigent.spec.parser import parse
        from omnigent.spec.validator import validate
    except ImportError as exc:
        print("Omnigent is not installed in this Python environment.")
        print("Install it from https://omnigent.ai/ and rerun this script.")
        print(f"Import error: {exc}")
        return 2

    spec = parse(AGENT, expand_env=False)
    result = validate(spec)
    if not result.valid:
        print("Agent validation failed:")
        for error in result.errors:
            print(f"- {error.path}: {error.message}")
        return 1

    print(f"Valid: agent '{spec.name}' parsed and validated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
