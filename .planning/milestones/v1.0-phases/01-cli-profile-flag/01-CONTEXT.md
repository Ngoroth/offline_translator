# Phase 1: CLI Profile Flag - Context

**Gathered:** 2026-02-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Allow launching the app with a `--profile` CLI flag so users can select an existing profile from `config.yaml` per run, instead of editing `current_profile` manually. This phase covers profile selection and related user-facing behavior for valid/invalid profile input.

</domain>

<decisions>
## Implementation Decisions

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

</decisions>

<specifics>
## Specific Ideas

- No specific stylistic preference provided; optimize for clear, minimal CLI UX.

</specifics>

<deferred>
## Deferred Ideas

- None - discussion stayed within phase scope.

</deferred>

---

*Phase: 01-cli-profile-flag*
*Context gathered: 2026-02-20*
