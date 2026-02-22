from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REMOTE_HOST = "pi@translator"
REMOTE_DIR = "/home/pi/offline_translator"


@dataclass(frozen=True)
class Stage:
    name: str
    command: list[str]


class DeployError(RuntimeError):
    pass


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _build_rsync_command() -> list[str]:
    source = f"{_project_root()}/"
    destination = f"{REMOTE_HOST}:{REMOTE_DIR}/"
    return ["rsync", "-az", source, destination]


def _build_remote_sync_command() -> list[str]:
    return ["ssh", REMOTE_HOST, f"cd {REMOTE_DIR} && uv sync"]


def _run_stage(stage: Stage) -> None:
    print(f"[deploy] {stage.name}...")
    try:
        subprocess.run(stage.command, check=True, text=True)
    except subprocess.CalledProcessError as exc:
        command = " ".join(stage.command)
        raise DeployError(f"{stage.name} failed while running `{command}`.") from exc


def _require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise DeployError(
            f"Missing required tool: `{name}`. Install it, then rerun `uv run scripts/deploy.py`."
        )


def _verify_ssh_reachability() -> None:
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", REMOTE_HOST, "true"]
    try:
        subprocess.run(command, check=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise DeployError(
            "Unable to reach `pi@translator` over SSH. Verify host resolution and key auth: "
            "`ssh pi@translator`"
        ) from exc


def _verify_remote_uv() -> None:
    command = ["ssh", REMOTE_HOST, "uv --version"]
    try:
        subprocess.run(command, check=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise DeployError(
            "`uv` is not available on the Raspberry Pi. Install it on the Pi (`curl -LsSf "
            "https://astral.sh/uv/install.sh | sh`) and ensure it is on PATH, then retry."
        ) from exc


def _run_preflight() -> None:
    print("[deploy] preflight...")
    _require_tool("ssh")
    _require_tool("rsync")
    _verify_ssh_reachability()
    _verify_remote_uv()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deploy project files to pi@translator and run uv sync remotely."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _ = _parse_args(argv)

    try:
        _run_preflight()
        _run_stage(Stage(name="rsync", command=_build_rsync_command()))
        _run_stage(Stage(name="remote uv sync", command=_build_remote_sync_command()))
    except DeployError as exc:
        print(f"[deploy] failed: {exc}", file=sys.stderr)
        return 1

    print("[deploy] success")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
