"""Export the circuit contract: python -m packages.schema.export [--check]."""

import argparse
import json
from pathlib import Path

from .models import Circuit

SCHEMA_PATH = Path(__file__).with_name("circuit.schema.json")


def rendered_schema() -> str:
    return json.dumps(Circuit.model_json_schema(), indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the export is stale")
    args = parser.parse_args()
    expected = rendered_schema()
    if args.check:
        if not SCHEMA_PATH.exists() or SCHEMA_PATH.read_text(encoding="utf-8") != expected:
            parser.exit(1, "Circuit schema is stale; run python -m packages.schema.export\n")
    else:
        SCHEMA_PATH.write_text(expected, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
