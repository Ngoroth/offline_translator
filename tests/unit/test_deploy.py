import subprocess

import pytest

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


def test_verify_remote_uv_reports_install_steps_when_uv_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del args
        del kwargs
        raise subprocess.CalledProcessError(
            returncode=127,
            cmd=["ssh", deploy.REMOTE_HOST, "uv --version"],
            stderr="uv: command not found",
            output="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(deploy.DeployError) as excinfo:
        deploy._verify_remote_uv()

    message = str(excinfo.value)
    assert "Install it on the Pi" in message
    assert "uv --version" in message


def test_verify_remote_uv_reports_ssh_connectivity_for_255(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del args
        del kwargs
        raise subprocess.CalledProcessError(
            returncode=255,
            cmd=["ssh", deploy.REMOTE_HOST, "uv --version"],
            stderr="Connection timed out",
            output="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(deploy.DeployError) as excinfo:
        deploy._verify_remote_uv()

    message = str(excinfo.value)
    assert "SSH failed" in message
    assert "ssh pi@translator" in message


def test_main_runs_stages_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_parse_args(argv: list[str] | None = None) -> object:
        del argv
        return object()

    def fake_preflight() -> None:
        calls.append("preflight")

    def fake_build_rsync_command() -> list[str]:
        return ["rsync", "fake"]

    def fake_build_remote_sync_command() -> list[str]:
        return ["ssh", "fake"]

    def fake_run_stage(stage: deploy.Stage) -> None:
        calls.append(stage.name)

    monkeypatch.setattr(deploy, "_parse_args", fake_parse_args)
    monkeypatch.setattr(deploy, "_run_preflight", fake_preflight)
    monkeypatch.setattr(deploy, "_build_rsync_command", fake_build_rsync_command)
    monkeypatch.setattr(deploy, "_build_remote_sync_command", fake_build_remote_sync_command)
    monkeypatch.setattr(deploy, "_run_stage", fake_run_stage)

    result = deploy.main([])

    assert result == 0
    assert calls == ["preflight", "rsync", "remote uv sync"]


def test_main_returns_failure_with_actionable_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_parse_args(argv: list[str] | None = None) -> object:
        del argv
        return object()

    def fail_preflight() -> None:
        raise deploy.DeployError("SSH failed. Try `ssh pi@translator`.")

    monkeypatch.setattr(deploy, "_parse_args", fake_parse_args)
    monkeypatch.setattr(deploy, "_run_preflight", fail_preflight)

    result = deploy.main([])

    assert result == 1
    assert "[deploy] failed:" in capsys.readouterr().err
