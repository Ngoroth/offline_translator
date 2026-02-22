# Phase 2: User Setup Required

**Generated:** 2026-02-22
**Phase:** 02-deploy-to-pi
**Status:** Incomplete

Complete these items for Raspberry Pi deployment to function.

## Environment Variables

None.

## Account Setup

None.

## Dashboard Configuration

- [ ] **Ensure `pi@translator` resolves and accepts SSH authentication from this machine**
  - Location: Local SSH configuration / network DNS or hosts
  - Set to: `ssh pi@translator` connects without credential prompts that block non-interactive runs
  - Notes: Deployment preflight depends on this baseline before rsync and remote `uv sync`.

## Verification

After completing setup, verify with:

```bash
ssh pi@translator "echo ok"
```

Expected results:
- SSH command returns `ok` with exit code 0.

---

**Once all items complete:** Mark status as "Complete" at top of file.
