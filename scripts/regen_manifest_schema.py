#!/usr/bin/env python3
"""Regenerate ``halcytone_contracts/bundles/manifest.schema.json``.

Run from the repo root::

    python scripts/regen_manifest_schema.py          # write file in place
    python scripts/regen_manifest_schema.py --stdout # emit to stdout

The generated JSON is what AgentGrounds (TypeScript side) consumes, so any
drift between the pydantic model and the checked-in schema is a contract
break. A test in ``tests/test_manifest.py`` asserts byte-equality between
``--stdout`` output and the committed file — CI catches drift for free.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from halcytone_contracts.bundles.manifest import SessionManifest  # noqa: E402

_OUTPUT_PATH = _REPO_ROOT / "halcytone_contracts" / "bundles" / "manifest.schema.json"


def render_schema() -> bytes:
    """Return the canonical JSON-bytes rendering of the manifest schema."""
    schema = SessionManifest.model_json_schema()
    text = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    return text.encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="write to stdout instead of the on-disk schema file",
    )
    args = parser.parse_args(argv)

    payload = render_schema()
    if args.stdout:
        sys.stdout.buffer.write(payload)
    else:
        _OUTPUT_PATH.write_bytes(payload)
        print(f"wrote {_OUTPUT_PATH.relative_to(_REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
