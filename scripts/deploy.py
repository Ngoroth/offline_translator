from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REMOTE_HOST = "pi@translator"
REMOTE_DIR = "/home/pi/offline_translator"
REQUIRED_EXCLUDES = (".venv/", "__pycache__/", ".git/", "logs/")
NONINTERACTIVE_SHELL_TOKEN = "__DEPLOY_SHELL_OK__"
WINDOWS_SSH_PATH = Path("C:/Windows/System32/OpenSSH/ssh.exe")
WINDOWS_RSYNC_PATHS = (Path("C:/msys64/usr/bin/rsync.exe"), Path("C:/msys64/usr/bin/rsync"))
WINDOWS_MSYS_SSH_PATH = Path("C:/msys64/usr/bin/ssh.exe")


@dataclass(frozen=True)
class Stage:
    name: str
    command: list[str]


class DeployError(RuntimeError):
    pass


def _is_windows() -> bool:
    return sys.platform == "win32"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _format_rsync_local_path(path: Path) -> str:
    local_path = path.as_posix()
    if len(local_path) >= 2 and local_path[1] == ":":
        drive = local_path[0].lower()
        remainder = local_path[2:].lstrip("/")
        local_path = f"/{drive}/{remainder}"
    if not local_path.endswith("/"):
        local_path += "/"
    return local_path


def _build_rsync_command() -> list[str]:
    source = _format_rsync_local_path(_project_root())
    destination = f"{REMOTE_HOST}:{REMOTE_DIR}/"
    command = [
        _rsync_binary(),
        "-az",
        "--blocking-io",
        "--progress",
        "--mkpath",
        "-e",
        _rsync_remote_shell(),
        "--rsync-path=/usr/bin/rsync",
    ]
    for path in REQUIRED_EXCLUDES:
        command.append(f"--exclude={path}")
    command.extend([source, destination])
    return command


def _build_remote_sync_command() -> list[str]:
    return [_ssh_binary(), REMOTE_HOST, f"cd {REMOTE_DIR} && uv sync"]


def _ssh_binary() -> str:
    override = os.environ.get("DEPLOY_SSH_BIN")
    if override:
        return override
    if _is_windows() and WINDOWS_SSH_PATH.exists():
        return WINDOWS_SSH_PATH.as_posix()
    return "ssh"


def _rsync_binary() -> str:
    override = os.environ.get("DEPLOY_RSYNC_BIN")
    if override:
        return override
    if _is_windows():
        for candidate in WINDOWS_RSYNC_PATHS:
            if candidate.exists():
                return candidate.as_posix()
    return "rsync"


def _rsync_remote_shell() -> str:
    if not _is_windows():
        return "ssh -T -o BatchMode=yes"

    if not WINDOWS_MSYS_SSH_PATH.exists():
        raise DeployError(
            "MSYS2 ssh is required for rsync transport on Windows. Install/open MSYS2 and ensure `C:/msys64/usr/bin/ssh.exe` is available."
        )

    options = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes"]
    user_ssh_dir = Path(os.environ.get("USERPROFILE", "")) / ".ssh"
    identity = user_ssh_dir / "id_ed25519"
    known_hosts = user_ssh_dir / "known_hosts"

    if identity.exists():
        options.extend(["-i", _format_rsync_local_path(identity).rstrip("/")])
    if known_hosts.exists():
        options.extend(
            [
                "-o",
                f"UserKnownHostsFile={_format_rsync_local_path(known_hosts).rstrip('/')}",
            ]
        )
        options.extend(["-o", "StrictHostKeyChecking=yes"])

    return " ".join(options)


def _run_stage(stage: Stage) -> None:
    print(f"[deploy] {stage.name}...", flush=True)
    env: dict[str, str] | None = None
    if stage.name == "rsync":
        env = os.environ.copy()
        env["MSYS2_ARG_CONV_EXCL"] = "*"
        env["MSYS_NO_PATHCONV"] = "1"
    try:
        _ = subprocess.run(stage.command, check=True, text=True, env=env)
    except subprocess.CalledProcessError as exc:
        raise DeployError(_map_subprocess_failure(stage, exc)) from exc


def _map_subprocess_failure(stage: Stage, exc: subprocess.CalledProcessError) -> str:
    if exc.returncode == 255:
        return (
            f"{stage.name} failed: SSH connection to `{REMOTE_HOST}` failed. "
            "Check host resolution and key auth, then retry: `ssh pi@translator`."
        )
    if stage.name == "rsync" and exc.returncode == 12:
        return (
            "rsync failed: remote stream closed unexpectedly. Confirm `rsync` works on the Pi "
            'with `ssh pi@translator "/usr/bin/rsync --version"`. If it still fails, run '
            "`ssh pi@translator '/usr/bin/rsync --version >/dev/null && echo ok'` "
            "and retry deployment."
        )

    command = " ".join(stage.command)
    return (
        f"{stage.name} failed while running `{command}` (exit code {exc.returncode}). "
        "Review command output and rerun `uv run scripts/deploy.py`."
    )


def _require_tool(name: str, command: str) -> None:
    if any(sep in command for sep in ("/", "\\")):
        if Path(command).exists():
            return
    elif shutil.which(command) is not None:
        return

    raise DeployError(
        f"Missing required tool: `{name}`. Install it, then rerun `uv run scripts/deploy.py`."
    )


def _run_preflight() -> None:
    print("[deploy] preflight...", flush=True)
    _require_tool("ssh", _ssh_binary())
    _require_tool("rsync", _rsync_binary())
    _verify_ssh_reachability()
    _verify_clean_noninteractive_shell()
    _verify_remote_rsync()
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

    print("[deploy] success", flush=True)
    return 0


def _verify_ssh_reachability() -> None:
    command = [_ssh_binary(), "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", REMOTE_HOST, "true"]
    try:
        _ = subprocess.run(command, check=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise DeployError(
            "Unable to reach `pi@translator` over SSH. Verify host resolution and key auth: "
            + "`ssh pi@translator`."
        ) from exc


def _verify_remote_uv() -> None:
    command = [_ssh_binary(), REMOTE_HOST, "uv --version"]
    try:
        _ = subprocess.run(command, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 255:
            raise DeployError(
                "Unable to verify `uv` on the Raspberry Pi because SSH failed. "
                + "Check connectivity with `ssh pi@translator` and retry."
            ) from exc
        if exc.returncode == 127:
            raise DeployError(
                "`uv` is not available on the Raspberry Pi. Install it on the Pi (`curl -LsSf "
                + "https://astral.sh/uv/install.sh | sh`) and verify with "
                + '`ssh pi@translator "uv --version"`.'
            ) from exc
        raise DeployError(
            "Failed to verify `uv` on the Raspberry Pi. Run "
            + '`ssh pi@translator "uv --version"` to inspect the remote error, then retry deployment.'
        ) from exc


def _verify_remote_rsync() -> None:
    command = [_ssh_binary(), REMOTE_HOST, "rsync --version"]
    try:
        _ = subprocess.run(command, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 255:
            raise DeployError(
                "Unable to verify `rsync` on the Raspberry Pi because SSH failed. "
                + "Check connectivity with `ssh pi@translator` and retry."
            ) from exc
        if exc.returncode == 127:
            raise DeployError(
                "`rsync` is not available on the Raspberry Pi. Install it on the Pi "
                + "(`sudo apt update && sudo apt install -y rsync`) and verify with "
                + '`ssh pi@translator "rsync --version"`.'
            ) from exc
        raise DeployError(
            "Failed to verify `rsync` on the Raspberry Pi. Run "
            + '`ssh pi@translator "rsync --version"` to inspect the remote error, then retry deployment.'
        ) from exc


def _verify_clean_noninteractive_shell() -> None:
    command = [_ssh_binary(), REMOTE_HOST, f"printf {NONINTERACTIVE_SHELL_TOKEN}"]
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 255:
            raise DeployError(
                "Unable to verify non-interactive SSH shell output because SSH failed. "
                + "Check connectivity with `ssh pi@translator` and retry."
            ) from exc
        raise DeployError(
            "Failed to verify non-interactive SSH shell output. "
            + "Run `ssh pi@translator 'printf __DEPLOY_SHELL_OK__'` and retry deployment."
        ) from exc

    if result.stdout.strip() != NONINTERACTIVE_SHELL_TOKEN:
        raise DeployError(
            "SSH non-interactive shell emits extra output, which can break rsync. "
            + "Remove startup `echo`/banner output in remote shell init files and verify only "
            + "`__DEPLOY_SHELL_OK__` is printed by `ssh pi@translator 'printf __DEPLOY_SHELL_OK__'`."
        )


if __name__ == "__main__":
    raise SystemExit(main())
