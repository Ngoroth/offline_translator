# Phase 2: Deploy to Pi - Research

**Researched:** 2026-02-21
**Domain:** One-command cross-platform deployment to Raspberry Pi via SSH + rsync + uv
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Device readiness baseline
- Required precondition is minimal setup: Raspberry Pi must be reachable over SSH as `pi@translator`.
- Deploy flow should not require full manual pre-provisioning beyond SSH reachability.

### Setup guidance and preflight behavior
- Onboarding/setup documentation format is left to Claude's discretion.
- Preflight checks before sync are left to Claude's discretion.

### Failure message style
- When preflight fails, errors should be concise and actionable: one clear cause plus 1-2 concrete next-step commands.

### Claude's Discretion
- Exact onboarding document format and depth.
- Exact set of preflight checks prior to file sync.

### Deferred Ideas (OUT OF SCOPE)
- Raspberry Pi OS selection and installation workflow (captured for a separate phase/backlog item).
- Broader device-level configuration guide may warrant a separate discussion/phase if it expands beyond deployment preconditions.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEPLOY-01 | User can run `uv run scripts/deploy.py` to sync codebase to Raspberry Pi | Defines script entrypoint pattern, rsync command structure, and local/remote preflight checks |
| DEPLOY-02 | Deploy script excludes `.venv/`, `__pycache__/`, `.git/`, `logs/` from sync | Provides rsync exclude pattern strategy and dry-run verification pattern |
| DEPLOY-03 | Deploy script runs `uv sync` on Pi after file sync completes | Defines SSH remote command pattern and error handling for remote install step |
| DEPLOY-04 | Deploy script connects to Pi via SSH at `pi@translator` | Defines SSH connectivity preflight and explicit host target pattern |
| DEPLOY-05 | Deploy script shows progress/success/failure status | Defines progress output options (`rsync --progress`) and structured success/failure messaging |
</phase_requirements>

## Summary

Phase 2 should use a thin Python orchestration script around battle-tested system tools (`rsync`, `ssh`, and `uv`) rather than implementing custom copy/install logic in Python. This aligns with project decisions (`rsync + uv sync`) and with platform reality: rsync handles delta transfer, excludes, and progress output with fewer edge cases than a hand-rolled file walker.

`uv run scripts/deploy.py` should perform a small preflight sequence first (tool presence + SSH reachability to `pi@translator`), then run rsync with explicit excludes, then run `uv sync` remotely over SSH. Keep output operator-friendly: stage banners, streaming command output, and one final success/failure line with next action.

For planning, the highest-risk areas are operational details, not architecture: rsync trailing-slash behavior, exclude pattern correctness, and mapping subprocess failures into concise, actionable messages. A focused preflight and explicit command construction eliminate most deployment surprises.

**Primary recommendation:** Implement `scripts/deploy.py` as a three-stage pipeline (`preflight -> rsync -> remote uv sync`) using `subprocess.run(..., check=True, text=True)` and explicit, tested command argument lists.

## Standard Stack

### Core
| Library/Tool | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| Python `subprocess` | Stdlib (Py 3.12 project baseline) | Execute `ssh`, `rsync`, and remote install commands safely | Official process API with return-code exceptions and timeout support |
| `rsync` CLI | 3.x family | Incremental file sync with excludes and progress | Industry standard for remote code sync; robust filtering/delta behavior |
| OpenSSH client (`ssh`) | Current OpenSSH client | Connectivity check and remote command execution | Required transport for both direct remote commands and rsync remote-shell mode |
| `uv sync` | Current uv (docs Jan 2026) | Install/update dependencies on Pi after sync | Project-standard package manager and lock/sync model |

### Supporting
| Library/Tool | Version | Purpose | When to Use |
|--------------|---------|---------|-------------|
| Python `shutil.which` | Stdlib | Preflight check for required executables | Validate `ssh`/`rsync` availability before running deployment |
| Python `pathlib` | Stdlib | Resolve project root / script paths predictably | Build robust local paths and avoid cwd-sensitive behavior |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `rsync` | `scp -r` | Simpler but no rsync-style exclude/filter and weaker incremental behavior |
| remote `uv sync` via `ssh` | custom SSH library (`paramiko`) | More code surface and dependency overhead for no phase-level benefit |
| shell-script deploy | Python-only orchestration | Shell scripts are short but less portable/testable in this repository's Python workflow |

**Preflight checks:**
```bash
rsync --version
ssh -V
ssh pi@translator "uv --version"
```

## Architecture Patterns

### Recommended Project Structure
```text
scripts/
├── deploy.py             # Entry point for one-command deploy
└── ...existing scripts

tests/
└── unit/
    └── test_deploy.py    # Command construction + failure mapping tests
```

### Pattern 1: Stage-Based Deployment Pipeline
**What:** Execute deployment as explicit stages with clear boundaries and failure handling.
**When to use:** Always; this phase's success criteria are stage-oriented.
**Example:**
```python
for stage_name, command in stages:
    print(f"[deploy] {stage_name}...")
    subprocess.run(command, check=True, text=True)
```

### Pattern 2: Explicit Command Arrays (No `shell=True`)
**What:** Build commands as argument lists.
**When to use:** Any local/remote command execution.
**Example:**
```python
rsync_cmd = [
    "rsync", "-az", "--progress",
    "--exclude=.venv/", "--exclude=__pycache__/", "--exclude=.git/", "--exclude=logs/",
    f"{source_dir}/", f"pi@translator:{remote_dir}/",
]
subprocess.run(rsync_cmd, check=True, text=True)
```

### Pattern 3: Remote Command as Single SSH Payload
**What:** Run post-sync dependency install over SSH after rsync succeeds.
**When to use:** DEPLOY-03 enforcement.
**Example:**
```python
ssh_cmd = ["ssh", "pi@translator", f"cd {remote_dir} && uv sync"]
subprocess.run(ssh_cmd, check=True, text=True)
```

### Anti-Patterns to Avoid
- **Hand-rolled recursive copy:** re-implements filtering, delta logic, and progress poorly.
- **Running remote install before successful sync:** creates mismatched code/dependency states.
- **Opaque error pass-through:** raw tracebacks without next-step guidance violate context constraints.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Incremental network file sync | Custom Python `os.walk` copier | `rsync` with exclude flags | Handles deltas, metadata, and large trees with proven semantics |
| SSH connectivity probing | Custom socket/auth probe logic | `ssh` command + return code | Matches real execution path and catches auth/host-key failures |
| Dependency resolver/install pipeline | Ad-hoc pip bootstrap scripts | `uv sync` on Pi | Uses project lock/sync model and keeps env reproducible |

**Key insight:** Deployment reliability comes from composing mature tools with strict orchestration, not from writing custom transfer logic.

## Common Pitfalls

### Pitfall 1: Rsync trailing-slash confusion
**What goes wrong:** Destination gets unexpected extra directory nesting.
**Why it happens:** Source path with/without trailing slash changes semantics.
**How to avoid:** Use one canonical convention (`{source_dir}/ -> {remote_dir}/`) and test once.
**Warning signs:** Remote path contains duplicated project directory levels.

### Pitfall 2: Exclude patterns appear set but caches still sync
**What goes wrong:** `__pycache__` or logs still transfer.
**Why it happens:** Pattern syntax or source root assumptions are wrong.
**How to avoid:** Use explicit `--exclude` per required path and validate with `--dry-run` during development.
**Warning signs:** rsync output shows excluded directories being created/updated.

### Pitfall 3: SSH error 255 not translated into actionable guidance
**What goes wrong:** User sees generic failure with no recovery step.
**Why it happens:** Script raises raw subprocess exception text only.
**How to avoid:** Catch `CalledProcessError` for SSH stages and map to concise hints (hostname, auth key, known_hosts).
**Warning signs:** Fail output contains only `returned non-zero exit status 255`.

### Pitfall 4: Remote `uv sync` runs in wrong directory
**What goes wrong:** Dependencies install against wrong project or fail to locate `pyproject.toml`.
**Why it happens:** Missing `cd` in SSH command.
**How to avoid:** Always execute `cd <remote_dir> && uv sync` as one remote command.
**Warning signs:** uv errors mention missing project metadata or lockfile mismatch at unexpected path.

## Code Examples

Verified patterns from official sources:

### Safe subprocess execution pattern
```python
subprocess.run(["rsync", "--version"], check=True, text=True)
```

### Tool availability preflight
```python
if shutil.which("rsync") is None:
    raise RuntimeError("rsync is not installed")
```

### SSH remote command with exit-status semantics
```bash
ssh pi@translator "cd /home/pi/offline_translator && uv sync"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual copy commands and manual dependency install | One command orchestration: sync then remote install | Current project phase | Faster iteration and fewer missed steps |
| `scp`-style full copy | `rsync` delta sync with excludes/progress | Longstanding ecosystem standard | Better speed and visibility for code iteration loops |

**Deprecated/outdated:**
- Treating deployment as two manual steps (`copy` then `install`) without scripted ordering.

## Open Questions

1. **What exact remote deployment directory should be canonicalized?**
   - What we know: Target host/user is fixed (`pi@translator`).
   - What's unclear: Final remote path convention (e.g., `/home/pi/offline_translator`).
   - Recommendation: Lock this in Plan 1 and hardcode as a constant for repeatability.

2. **Should deploy preflight fail if remote `uv` is missing, or attempt bootstrap?**
   - What we know: minimal pre-provisioning beyond SSH is preferred.
   - What's unclear: whether automatic uv bootstrap is desired in this phase.
   - Recommendation: For this phase, fail fast with actionable install commands; defer bootstrap automation.

## Sources

### Primary (HIGH confidence)
- `https://docs.astral.sh/uv/concepts/projects/sync/` - `uv sync` behavior, exact/inexact semantics, lock/sync model (dated Jan 9, 2026)
- `https://docs.python.org/3/library/subprocess.html` - recommended `subprocess.run`, `check=True`, exception behavior
- `https://docs.python.org/3/library/shutil.html#shutil.which` - executable discovery for preflight
- `https://man.openbsd.org/ssh` - SSH command execution and exit status (`255` on SSH client error)
- `https://man7.org/linux/man-pages/man1/rsync.1.html` - rsync usage, remote-shell mode, exclude/progress options, trailing-slash behavior

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` - phase requirement definitions (DEPLOY-01..05)
- `.planning/phases/02-deploy-to-pi/02-CONTEXT.md` - locked user decisions and out-of-scope boundaries
- `.planning/PROJECT.md` - project-level deployment direction (`rsync + uv sync`)

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Based on official docs for uv, Python stdlib, SSH, and rsync man page
- Architecture: HIGH - Directly constrained by phase requirements and locked context decisions
- Pitfalls: MEDIUM - Operational pitfalls are well-known, but environment-specific failure signatures may vary

**Research date:** 2026-02-21
**Valid until:** 2026-03-23 (30 days)
