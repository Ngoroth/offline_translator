import subprocess

from scripts import deploy


def test_build_rsync_command_includes_required_exclude_flags() -> None:
    command = deploy._build_rsync_command()

    assert command[0] == "rsync"
    assert "--progress" in command
    assert "--exclude=.venv/" in command
    assert "--exclude=__pycache__/" in command
    assert "--exclude=.git/" in command
    assert "--exclude=logs/" in command


def test_build_rsync_command_targets_pi_host_with_trailing_slash_semantics() -> None:
    command = deploy._build_rsync_command()

    assert command[-1] == f"{deploy.REMOTE_HOST}:{deploy.REMOTE_DIR}/"
    assert command[-2].endswith("/")


def test_build_remote_uv_sync_command_uses_ssh_and_uv_sync() -> None:
    command = deploy._build_remote_sync_command()

    assert command == ["ssh", deploy.REMOTE_HOST, f"cd {deploy.REMOTE_DIR} && uv sync"]


def test_map_subprocess_failure_ssh_code_has_actionable_guidance() -> None:
    stage = deploy.Stage(name="rsync", command=deploy._build_rsync_command())
    error = subprocess.CalledProcessError(returncode=255, cmd=stage.command)

    message = deploy._map_subprocess_failure(stage, error)

    assert "SSH connection" in message
    assert "ssh pi@translator" in message
