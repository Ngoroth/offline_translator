#!/usr/bin/env python
"""
Diagnostics utility for Offline Translator.
Parses JSON logs and prints a summary of errors and warnings.
"""

import json
import sys
from pathlib import Path
from typing import cast


def analyze_logs(log_path: Path) -> None:
    if not log_path.exists():
        print(f"Log file not found: {log_path}")
        return

    print(f"Analyzing log file: {log_path}")
    print("-" * 60)

    error_count: int = 0
    warning_count: int = 0
    start_time: str | None = None
    end_time: str | None = None

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record: dict[str, object] = cast(dict[str, object], json.loads(line))
                    # Loguru serialize=True usually puts everything at root or in 'record' depending on version
                    # Actually standard loguru JSON has 'record' key with 'level', 'time', 'message'

                    data: dict[str, object]
                    if "record" in record and isinstance(record["record"], dict):
                        data = cast(dict[str, object], record["record"])
                    else:
                        data = record

                    level_dict = data.get("level", {})
                    level = "UNKNOWN"
                    if isinstance(level_dict, dict):
                        # Ensure we are passing a known type to str()
                        val = level_dict.get("name", "UNKNOWN")
                        # Explicitly cast to object to avoid Unknown
                        level = str(cast(object, val)) if val is not None else "UNKNOWN"

                    time_dict = data.get("time", {})
                    timestamp = ""
                    if isinstance(time_dict, dict):
                        val = time_dict.get("repr", "")
                        timestamp = str(cast(object, val)) if val is not None else ""

                    message = str(data.get("message", ""))

                    if not start_time:
                        start_time = timestamp
                    end_time = timestamp

                    if level == "ERROR":
                        error_count += 1
                        print(f"[{timestamp}] ERROR: {message}")
                        if "exception" in data:
                            print(f"  Exception: {data['exception']}")
                    elif level == "WARNING":
                        warning_count += 1

                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Failed to parse log file: {e}")
        return

    print("-" * 60)
    print("Summary:")
    print(f"  Start Time: {start_time}")
    print(f"  End Time:   {end_time}")
    print(f"  Errors:     {error_count}")
    print(f"  Warnings:   {warning_count}")


if __name__ == "__main__":
    log_file = Path("logs/app.log")
    if len(sys.argv) > 1:
        log_file = Path(sys.argv[1])

    analyze_logs(log_file)
