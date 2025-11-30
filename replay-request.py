import os
import sys
import json
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path
from src.util import normalize_to_eom
from src.scheduler import get_day_ahead_schedule

REQUEST_MARKER = "===== REQUEST ====="
RESPONSE_MARKER_PREFIX = "===== RESPONSE"

if __name__ == "__main__":

    # argument handling
    parser = argparse.ArgumentParser(description="Scheduler Replay Request from log")
    parser.add_argument("request_file", help=f"Path to logged JSON file")
    args = parser.parse_args()
    request_path = Path(args.request_file)
    if not request_path.is_file():
        print(f"ERROR: Request file not found: {request_path}", file=sys.stderr)
        sys.exit(1)

    # read request log file and extract request JSON
    with request_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    request_start = None
    request_end = None
    for i, line in enumerate(lines):
        if REQUEST_MARKER in line and request_start is None:
            request_start = i + 1
        elif RESPONSE_MARKER_PREFIX in line and request_start is not None:
            request_end = i
            break
    if request_start is None or request_end is None:
        raise ValueError(f"Could not find JSON block in {request_path}")
    json_str = "".join(lines[request_start:request_end]).strip()
    if not json_str:
        raise ValueError(f"No JSON content found between markers in {request_path}")
    try:
        payload = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from log {request_path}: {e}") from e

    # replay scheduler request from payload
    start_time = datetime.fromisoformat(payload["start_time"])
    data = pd.DataFrame(payload["data"])
    parameters = payload["parameters"]
    config_path = str((Path(".") / "opt").resolve())
    data = normalize_to_eom(data, start_time)
    result_data = get_day_ahead_schedule(data, parameters, config_path)
    print(result_data)
