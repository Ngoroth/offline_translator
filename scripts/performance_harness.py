"""Launch one explicitly labelled performance trial.

Example:
    uv run python scripts/performance_harness.py \
        --trial-kind cold --profile rpi_deployment --n-threads 4 -- \
        uv run python src/app/main.py --profile rpi_deployment

The harness never defaults a trial to warm. Each invocation gets its own run
identifier, while each PTT session emitted by the application gets its own
trial identifier.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True)
class HarnessArgs:
    trial_kind: str
    profile: str
    n_threads: int
    revision: str | None
    command: tuple[str, ...]


def _argument(namespace: argparse.Namespace, name: str) -> object:
    return vars(namespace).get(name)


def parse_args(argv: Sequence[str] | None = None) -> HarnessArgs:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--trial-kind", choices=("cold", "warm"), required=True,
        help="Whether this run includes the first post-start cycle.",
    )
    _ = parser.add_argument("--profile", required=True, help="Application profile name.")
    _ = parser.add_argument(
        "--n-threads", type=int, required=True,
        help="LLM CPU thread count for this run.",
    )
    _ = parser.add_argument(
        "--revision", help="Optional source revision to record in the run fingerprint."
    )
    _ = parser.add_argument(
        "command", nargs=argparse.REMAINDER,
        help="Application command after `--`, for example `uv run python src/app/main.py`.",
    )
    args = parser.parse_args(argv)
    trial_kind = _argument(args, "trial_kind")
    profile = _argument(args, "profile")
    n_threads = _argument(args, "n_threads")
    revision = _argument(args, "revision")
    raw_command = _argument(args, "command")
    if not isinstance(trial_kind, str) or not isinstance(profile, str):
        parser.error("trial kind and profile must be strings")
    if not isinstance(n_threads, int) or not 1 <= n_threads <= 64:
        parser.error("n-threads must be between 1 and 64")
    if revision is not None and not isinstance(revision, str):
        parser.error("revision must be a string")
    if not isinstance(raw_command, list) or not all(
        isinstance(item, str) for item in raw_command
    ):
        parser.error("application command must be a list of strings")
    command = [cast(str, item) for item in raw_command]
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("an application command is required after `--`")
    return HarnessArgs(trial_kind, profile, n_threads, revision, tuple(command))


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    environment = os.environ.copy()
    environment["PERF_RUN_ID"] = str(uuid.uuid4())
    environment["PERF_TRIAL_KIND"] = args.trial_kind
    environment["PERF_PROFILE"] = args.profile
    if args.revision:
        environment["PERF_REVISION"] = args.revision

    command = [*args.command, "--profile", args.profile, "--n-threads", str(args.n_threads)]
    completed = subprocess.run(command, env=environment, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
