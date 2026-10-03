"""Exercise a running API using only the Python standard library."""

import argparse
import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request_json(url: str, payload: dict[str, object] | None = None) -> tuple[int, dict[str, Any]]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base_url = str(args.base_url).rstrip("/")
    previous_counts: dict[str, int] | None = None
    for prefix in ("", "/v1"):
        status, health = request_json(f"{base_url}{prefix}/health")
        assert status == 200 and health["status"] == "ok", health
        status, result = request_json(
            f"{base_url}{prefix}/simulate", {"backend": "aer", "shots": 256, "seed": 17},
        )
        assert status == 200, result
        counts = result["counts"]
        assert set(counts) == {"00", "11"} and sum(counts.values()) == 256, result
        assert result["backend"]["name"] == "aer", result
        if previous_counts is not None:
            assert previous_counts == counts, "Seeded results differ between route aliases"
        previous_counts = counts
        status, invalid = request_json(f"{base_url}{prefix}/simulate", {"shots": 0})
        assert status == 422 and invalid["error"]["type"] == "syntax", invalid
    print("Live API smoke check passed: health, seeded Bell counts, aliases, structured errors.")


if __name__ == "__main__":
    main()
