import subprocess
from pathlib import Path

import pytest

from scripts import deploy


def test_build_rsync_command_includes_required_exclude_flags() -> None:
    command = deploy._build_rsync_command()

    assert command[0].endswith("rsync") or command[0].endswith("rsync.exe")
    assert "--blocking-io" in command
    assert "--progress" in command
    assert "--exclude=.venv/" in command
    assert "--exclude=__pycache__/" in command
    assert "--exclude=.git/" in command
    assert "--exclude=logs/" in command
    assert "--mkpath" in command
    assert "-e" in command
    assert "--rsync-path=/usr/bin/rsync" in command


def test_build_rsync_command_targets_pi_host_with_trailing_slash_semantics() -> None:
    command = deploy._build_rsync_command()

    assert command[-1] == f"{deploy.REMOTE_HOST}:{deploy.REMOTE_DIR}/"
    assert command[-2].endswith("/")


def test_build_rsync_command_normalizes_windows_drive_source_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(deploy, "_project_root", lambda: Path("C:/Projects/offline_translator"))

    command = deploy._build_rsync_command()

    assert command[-2] == "/c/Projects/offline_translator/"


def test_build_remote_uv_sync_command_uses_ssh_and_uv_sync() -> None:
    command = deploy._build_remote_sync_command()

    assert command[0] == deploy._ssh_binary()
    assert command[1:] == [deploy.REMOTE_HOST, f"cd {deploy.REMOTE_DIR} && uv sync"]


def test_map_subprocess_failure_ssh_code_has_actionable_guidance() -> None:
    stage = deploy.Stage(name="rsync", command=deploy._build_rsync_command())
    error = subprocess.CalledProcessError(returncode=255, cmd=stage.command)

    message = deploy._map_subprocess_failure(stage, error)

    assert "SSH connection" in message
    assert "ssh pi@translator" in message


def test_map_subprocess_failure_rsync_code_12_has_actionable_guidance() -> None:
    stage = deploy.Stage(name="rsync", command=deploy._build_rsync_command())
    error = subprocess.CalledProcessError(returncode=12, cmd=stage.command)

    message = deploy._map_subprocess_failure(stage, error)

    assert "remote stream closed unexpectedly" in message
    assert 'ssh pi@translator "/usr/bin/rsync --version"' in message


def test_rsync_remote_shell_uses_msys_ssh_with_windows_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssh_bin = tmp_path / "ssh.exe"
    ssh_bin.write_text("", encoding="utf-8")
    userprofile = tmp_path / "User"
    ssh_dir = userprofile / ".ssh"
    ssh_dir.mkdir(parents=True)
    identity = ssh_dir / "id_ed25519"
    known_hosts = ssh_dir / "known_hosts"
    identity.write_text("dummy", encoding="utf-8")
    known_hosts.write_text("dummy", encoding="utf-8")

    monkeypatch.setattr(deploy, "_is_windows", lambda: True)
    monkeypatch.setattr(deploy, "WINDOWS_MSYS_SSH_PATH", ssh_bin)
    monkeypatch.setenv("USERPROFILE", str(userprofile))

    shell = deploy._rsync_remote_shell()

    assert shell.startswith("/usr/bin/ssh -T -o BatchMode=yes")
    assert "-i" in shell
    assert "UserKnownHostsFile=" in shell
    assert "StrictHostKeyChecking=yes" in shell


def test_rsync_remote_shell_raises_when_msys_ssh_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(deploy, "_is_windows", lambda: True)
    monkeypatch.setattr(deploy, "WINDOWS_MSYS_SSH_PATH", tmp_path / "missing-ssh.exe")

    with pytest.raises(deploy.DeployError):
        deploy._rsync_remote_shell()


def test_run_stage_sets_msys_arg_conv_exclusion_for_rsync(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_env: dict[str, str] = {}

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del args
        env = kwargs.get("env")
        assert isinstance(env, dict)
        captured_env.update(env)
        return subprocess.CompletedProcess(args=[], returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    deploy._run_stage(deploy.Stage(name="rsync", command=deploy._build_rsync_command()))

    assert captured_env.get("MSYS2_ARG_CONV_EXCL") == "*"
    assert captured_env.get("MSYS_NO_PATHCONV") == "1"


def test_verify_remote_rsync_reports_install_steps_when_rsync_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del args
        del kwargs
        raise subprocess.CalledProcessError(
            returncode=127,
            cmd=["ssh", deploy.REMOTE_HOST, "rsync --version"],
            stderr="rsync: command not found",
            output="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(deploy.DeployError) as excinfo:
        deploy._verify_remote_rsync()

    message = str(excinfo.value)
    assert "Install it on the Pi" in message
    assert "rsync --version" in message


def test_verify_clean_noninteractive_shell_reports_extra_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del args
        del kwargs
        return subprocess.CompletedProcess(
            args=["ssh", deploy.REMOTE_HOST, "printf __DEPLOY_SHELL_OK__"],
            returncode=0,
            stdout="Welcome\n__DEPLOY_SHELL_OK__",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(deploy.DeployError) as excinfo:
        deploy._verify_clean_noninteractive_shell()

    message = str(excinfo.value)
    assert "emits extra output" in message
    assert "__DEPLOY_SHELL_OK__" in message


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
