---
phase: quick
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/PROJECT.md
  - .planning/STATE.md
  - .planning/codebase/ARCHITECTURE.md
  - .planning/codebase/STACK.md
  - .planning/codebase/INTEGRATIONS.md
  - .planning/codebase/CONCERNS.md
  - .planning/research/ARCHITECTURE.md
  - .planning/milestones/v1.0-MILESTONE-AUDIT.md
autonomous: true
requirements: []
must_haves:
  truths:
    - "Planning docs accurately reflect target hardware (RPi4 with USB numpad via evdev)"
    - "No misleading GPIO references in planning documentation"
    - "GPIOInput code remains intact in src/app/core/input.py and tests/"
  artifacts:
    - path: ".planning/PROJECT.md"
      provides: "Accurate project overview"
    - path: ".planning/codebase/INTEGRATIONS.md"
      provides: "Correct hardware integration docs"
  key_links:
    - from: ".planning/PROJECT.md"
      to: "Target platform section"
      via: "hardware description"
---

<objective>
Update planning documentation to accurately reflect the target hardware configuration, removing misleading GPIO references while preserving the GPIOInput implementation in source code.

Purpose: Prevent confusion about actual target device deployment (RPi4 with USB numpad via evdev, NOT GPIO buttons).
Output: Clean planning docs with accurate hardware descriptions.
</objective>

<execution_context>
@./.opencode/get-shit-done/workflows/execute-plan.md
@./.opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md

**Target Device:** Raspberry Pi 4 (2GB RAM) with USB mic, USB numpad (PTT via evdev), speakers.
**GPIO is NOT used** on target device - only evdev for USB numpad PTT.

**GPIOInput code to PRESERVE:**
- `src/app/core/input.py` - GPIOInput class implementation
- `src/app/core/config.py` - GPIOSettings configuration
- `tests/` - GPIO-related tests and mocks

**Historical context:** GPIO support was implemented for flexibility but the actual target device uses USB numpad via evdev.
</context>

<tasks>

<task type="auto">
  <name>Update PROJECT.md with accurate hardware description</name>
  <files>.planning/PROJECT.md</files>
  <action>
Update PROJECT.md to accurately reflect target hardware:
1. Line ~16: Change "PTT input handling (Keyboard, Evdev, GPIO)" to "PTT input handling (Keyboard, Evdev)" with note that GPIO implementation exists but is not used on target device
2. Line ~30: Remove "Fix GPIO active_low hardcoding" from Active requirements - add note it's deferred/low-priority since GPIO not used on target
3. Line ~52: Update "GPIO active-low hardcoding needs configuration" to clarify GPIO is available but not used on target
4. Line ~64: Change "Raspberry Pi 4 with USB numpad or GPIO buttons" to "Raspberry Pi 4 with USB numpad (PTT via evdev)"

Keep the Key Decisions table entry for "Hardcoded GPIO active_low" as it's still valid tech debt.
</action>
  <verify>grep -n "GPIO\|gpio" .planning/PROJECT.md returns only accurate references</verify>
  <done>PROJECT.md accurately describes target hardware without misleading GPIO claims</done>
</task>

<task type="auto">
  <name>Update STATE.md to reflect actual target device</name>
  <files>.planning/STATE.md</files>
  <action>
Update STATE.md:
1. Line ~50: Change "Hardcoded GPIO Config" entry to note GPIO is available but not used on target device
2. Line ~58: Update blockers/concerns to clarify GPIO fix is low-priority since USB numpad via evdev is the actual input method

The quick task history already shows GPIO reference cleanup was done - add context that this doc cleanup is a follow-up.
</action>
  <verify>grep -n "GPIO" .planning/STATE.md shows accurate context</verify>
  <done>STATE.md accurately reflects current project state regarding GPIO</done>
</task>

<task type="auto">
  <name>Update codebase docs (ARCHITECTURE, STACK, INTEGRATIONS, CONCERNS)</name>
  <files>
    .planning/codebase/ARCHITECTURE.md
    .planning/codebase/STACK.md
    .planning/codebase/INTEGRATIONS.md
    .planning/codebase/CONCERNS.md
  </files>
  <action>
Update codebase documentation:

**ARCHITECTURE.md:**
- Line ~12: Change "Platform-independent input (Keyboard/Evdev/GPIO)" to "Platform-independent input (Keyboard/Evdev) - GPIO available but not used on target"
- Line ~57: Update input trigger to mention GPIO is available
- Line ~78: Keep GPIOInput in implementations list but note it's optional

**STACK.md:**
- Lines 87-88: Change "Optional: GPIO for hardware button input" to note GPIO is supported but not used on target device

**INTEGRATIONS.md:**
- Lines 116-119: Keep GPIO option documented as available, but clarify actual deployment uses evdev
- Line ~123: Update to note GPIO is available in code but evdev is target method

**CONCERNS.md:**
- Lines 7-11: Keep GPIO active_low issue but note it's low priority since GPIO not used on target
- Lines 100-103: Update multi-input handler section to clarify EvdevInput is the production input method
- Lines 152-155: Update lgpio dependency risk to note it's optional
- Lines 187-191: Update GPIO testing section to note hardware testing is optional since GPIO not used on target
</action>
  <verify>grep -n "GPIO\|gpio" .planning/codebase/*.md shows only accurate references</verify>
  <done>Codebase docs accurately describe input options and target configuration</done>
</task>

<task type="auto">
  <name>Update research and milestone docs</name>
  <files>
    .planning/research/ARCHITECTURE.md
    .planning/milestones/v1.0-MILESTONE-AUDIT.md
  </files>
  <action>
Update research and milestone documentation:

**research/ARCHITECTURE.md:**
- Keep architecture diagrams showing GPIOInput (it exists in code)
- Add notes where relevant that GPIO is available but target device uses evdev
- Line ~170: Add note that production uses EvdevInput
- Line ~424-428: Update Phase 3 target device verification to clarify GPIO is optional, evdev is primary
- Line ~554: Update Phase 5 on-device verification to prioritize evdev testing

**milestones/v1.0-MILESTONE-AUDIT.md:**
- Line ~88: Keep ERRO-03 but add context that GPIO not used on target makes this lower priority
- Lines ~105, ~109-110: Update integration flow notes to reflect evdev is primary, GPIO is secondary
- Line ~146: Keep ERRO-03 in unsatisfied requirements with priority context
- Lines ~153, ~158: Update broken flow descriptions with context that GPIO is not primary input method

Historical milestone records should remain largely intact - just add context where GPIO fixes are mentioned.
</action>
  <verify>grep -n "GPIO" .planning/research/ARCHITECTURE.md and milestones file show contextualized references</verify>
  <done>Research and milestone docs have accurate context about target hardware</done>
</task>

</tasks>

<verification>
- All planning docs have been updated with accurate hardware descriptions
- No source code files were modified (GPIOInput preserved)
- grep for "GPIO" in .planning/ shows only contextualized, accurate references
- Target device description consistently states: Raspberry Pi 4 with USB numpad via evdev
</verification>

<success_criteria>
- [ ] PROJECT.md accurately describes target platform
- [ ] STATE.md reflects current GPIO status correctly
- [ ] All codebase docs updated with accurate input method context
- [ ] Research/milestone docs updated with appropriate context
- [ ] No GPIOInput source code was modified
- [ ] All changes committed to git
</success_criteria>

<output>
After completion, create `.planning/quick/2-clean-gpio-references-from-planning-docs/2-SUMMARY.md`
</output>
