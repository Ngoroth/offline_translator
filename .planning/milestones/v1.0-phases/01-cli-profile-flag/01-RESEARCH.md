# Phase 1: CLI Profile Flag - Research

**Researched:** 2026-02-20
**Domain:** Python CLI argument parsing + profile-aware config loading
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### CLI invocation behavior
- Support `--profile <profile_name>` as an optional launch flag.
- If `--profile` is omitted, app behavior stays unchanged and uses `current_profile` from `config.yaml`.
- Profile name matching is exact to the config key name (case-sensitive).

### Profile precedence and persistence
- `--profile` takes precedence over `current_profile` for that process run.
- Runtime override must not modify `config.yaml`.
- Once selected, the chosen profile drives the full app settings load path for that run.

### Invalid profile error UX
- Unknown profile should fail fast with a clear error that includes the invalid name.
- Error should list available profile names to help immediate correction.
- Process exits non-zero on invalid profile input.

### Startup profile visibility
- On successful launch, print a concise startup line indicating the active profile.

### Claude's Discretion
- Exact wording/formatting of success and error messages.
- Whether profile names in error output are sorted or kept in file order.
- Minor help-text phrasing for the CLI flag description.

### Deferred Ideas (OUT OF SCOPE)
- None - discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLI-01 | User can specify profile via `--profile <name>` flag when launching the app | Add `argparse.ArgumentParser` in `src/app/main.py` with optional `--profile`; pass parsed value into config loader. |
| CLI-02 | Flag overrides `current_profile` in config.yaml without modifying the file | Extend `load_settings()` with optional in-memory `profile_override`; choose profile at runtime only; never write YAML. |
| CLI-03 | Error message shown if specified profile does not exist in config.yaml | Validate override against `root.profiles`; raise `ValueError` containing invalid name + available profiles; let process exit non-zero. |
</phase_requirements>

## Summary

This phase fits cleanly into the existing architecture: `src/app/main.py` is the only runtime entrypoint, and all profile resolution currently happens inside `load_settings()` in `src/app/core/config.py`. The least-risk implementation is to add CLI parsing in `main.py`, then pass an optional profile override to `load_settings()` so selection happens once in the config layer.

Because the app already logs startup information (`logger.info(f"Profile: {settings.platform} ({settings.input_mode})")`), the visibility requirement is already mostly satisfied after profile selection is correct. The only strict gap is supporting user-selected profile names and erroring cleanly for unknown names. This can be implemented without touching model/service startup logic.

**Primary recommendation:** Implement `--profile` with `argparse` in `src/app/main.py` and add `profile_override: str | None = None` to `load_settings()` in `src/app/core/config.py`, with explicit validation/error messaging for unknown profiles.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python `argparse` | Python 3.12 stdlib | Parse `--profile` CLI flag | Built-in, stable, automatic help/error, no extra dependency. |
| Pydantic v2 (`BaseModel.model_validate`) | `pydantic>=2.0.0` (project) | Validate root/profile config structures | Already used by `RootConfig` and `AppSettings`; keeps strong validation path intact. |
| PyYAML (`yaml.safe_load`) | `pyyaml>=6.0` (project) | Read `config.yaml` safely | Existing config loader already uses `safe_load`; no format/parser migration needed. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Loguru | `loguru>=0.7.3` | Startup profile visibility message | Keep the concise active-profile line in startup logs. |
| pytest | `pytest>=7.0` | Regression tests for override and errors | Add unit tests for config override and optional CLI parsing tests. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `argparse` | Click/Typer | Adds dependency and new CLI style for a single optional flag; unnecessary for this phase. |
| Config-layer validation | Ad hoc checks in `main.py` | Duplicates profile logic and drifts from current single source of truth in `load_settings()`. |

## Architecture Patterns

### Recommended Project Structure
```
src/app/
├── main.py          # Parse CLI args; pass profile override into loader
└── core/config.py   # Resolve profile (override > current_profile), validate, return AppSettings
tests/
├── unit/            # load_settings override and invalid-profile behavior
└── smoke/           # optional launch path behavior if added
```

### Pattern 1: Entry-point Parses, Config Layer Decides
**What:** Parse CLI in `main.py`, but keep profile selection and validation in `load_settings()`.
**When to use:** Any runtime option that affects config source/selection.
**Example:**
```python
import argparse

def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--profile", help="Config profile name from config.yaml")
    return parser.parse_args()

args = parse_cli_args()
settings = load_settings(profile_override=args.profile)
```

### Pattern 2: Override Precedence in One Expression
**What:** Resolve active profile with explicit override precedence.
**When to use:** Optional runtime overrides that must not mutate persisted config.
**Example:**
```python
active_profile = profile_override if profile_override is not None else root.current_profile
```

### Anti-Patterns to Avoid
- **Duplicate profile checks in multiple files:** Validate in one place (`load_settings`) to avoid inconsistent behavior.
- **Writing back to YAML for runtime override:** Violates CLI-02 and introduces side effects.
- **Using argparse `choices` from static constants:** Profile list is dynamic from YAML, so validate after loading config.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI parsing | Custom `sys.argv` string parser | `argparse.ArgumentParser` | Handles help/errors/unknown args consistently and exits with standard non-zero behavior. |
| Schema validation | Manual nested dict checks | Pydantic `RootConfig`/`AppSettings` | Existing strong validation path is already in place and tested. |

## Common Pitfalls

### Pitfall 1: Breaking Existing `load_settings(config_path)` Callers
**What goes wrong:** Signature change causes tests/call sites to fail.
**How to avoid:** Add override as optional keyword-compatible parameter and keep current positional `config_path` behavior.

### Pitfall 2: Error Message Missing Available Profiles
**What goes wrong:** CLI-03 UX fails.
**How to avoid:** Raise explicit `ValueError` including invalid name and available profile keys.

### Pitfall 3: Ambiguous Flag Matching
**What goes wrong:** `--prof` may be accepted due argparse abbreviation.
**How to avoid:** Use `allow_abbrev=False` and exact profile-key matching.

### Pitfall 4: Hidden Active Profile
**What goes wrong:** Operators cannot tell which profile actually ran.
**How to avoid:** Include profile key in startup output (not only platform/input mode).

## Code Examples

### Add Optional `--profile` Flag
```python
import argparse

def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--profile", metavar="NAME", help="Use profile NAME from config.yaml")
    return parser.parse_args()
```

### Config Override Resolution and Validation
```python
def load_settings(config_path: str | Path = "config.yaml", profile_override: str | None = None) -> AppSettings:
    # ... load + validate root config ...
    active_profile = profile_override if profile_override is not None else root.current_profile
    if active_profile not in root.profiles:
        raise ValueError(
            f"Profile '{active_profile}' not found in 'profiles'. "
            f"Available: {list(root.profiles.keys())}"
        )
    return AppSettings.model_validate(root.profiles[active_profile])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual `current_profile` editing in YAML before each run | Runtime profile selection via CLI override | Planned in Phase 1 | Faster switching, less operator error, no config file churn. |

## Open Questions

1. **Error list order:** sorted vs config file order for available profile names.
   - Recommendation: sorted for deterministic test assertions.

2. **Startup message content:** include profile key explicitly or rely on platform/input_mode line.
   - Recommendation: include profile key explicitly for unambiguous run visibility.

## Sources

### Primary (HIGH confidence)
- https://docs.python.org/3.12/library/argparse.html - parser behavior, error/exit behavior, `allow_abbrev`
- https://docs.pydantic.dev/latest/concepts/models/ - `model_validate`, validation behavior

### Secondary (MEDIUM confidence)
- https://pyyaml.org/wiki/PyYAMLDocumentation - `safe_load` behavior

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - components are already in this repo.
- Architecture: HIGH - based on current `main.py` + `config.py` flow.
- Pitfalls: HIGH - based on current signatures/tests and stdlib defaults.

**Research date:** 2026-02-20
**Valid until:** 2026-03-22
