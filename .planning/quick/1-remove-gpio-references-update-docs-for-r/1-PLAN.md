---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - AGENTS.md
  - ARCHITECTURE.md
  - prd.md
autonomous: true
requirements: []
must_haves:
  truths:
    - "Documentation reflects current target hardware (RPi 4 2GB with USB peripherals)"
    - "No GPIO references remain in main documentation files"
    - "Development platform (Windows PC) is mentioned where relevant"
  artifacts:
    - path: "AGENTS.md"
      provides: "AI agent guidance"
      contains: "USB numpad, USB mic"
    - path: "ARCHITECTURE.md"
      provides: "System architecture overview"
      contains: "evdev"
    - path: "prd.md"
      provides: "Product requirements"
      contains: "2GB RAM"
  key_links:
    - from: "AGENTS.md"
      to: "Target platform description"
      via: "Hardware & Cross-Platform Notes section"
---

<objective>
Update main documentation files to remove GPIO references and accurately reflect the current target platform: Raspberry Pi 4 (2GB RAM) with USB mic, numpad, speakers. Development is done on Windows PC.

Purpose: Eliminate confusion from outdated GPIO references and ensure documentation matches actual hardware configuration.
Output: Updated AGENTS.md, ARCHITECTURE.md, and prd.md with correct hardware specifications.
</objective>

<execution_context>
@./.opencode/get-shit-done/workflows/execute-plan.md
@./.opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
Current target hardware:
- **Production:** Raspberry Pi 4 (2GB RAM) with USB microphone, USB numpad (for PTT), and speakers
- **Development:** Windows PC
- **PTT Input:** USB numpad via evdev (NOT GPIO buttons)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update AGENTS.md</name>
  <files>AGENTS.md</files>
  <action>
    Update the "Hardware & Cross-Platform Notes" section at the bottom of AGENTS.md:
    
    1. Change the Raspberry Pi bullet from:
       - `**Raspberry Pi**: Target platform, needs \`GPIOInput\` implementation.`
       
       To:
       - `**Raspberry Pi 4 (2GB RAM)**: Target platform with USB mic, USB numpad (PTT via evdev), and speakers.`
    
    2. Update Windows bullet to clarify it's the development platform:
       - `**Windows**: Development platform, uses \`pynput\` for keyboard PTT.`
  </action>
  <verify>`grep -c "GPIO" AGENTS.md` returns 0, and file contains "2GB RAM" and "evdev"</verify>
  <done>AGENTS.md has no GPIO references and accurately describes target and development platforms</done>
</task>

<task type="auto">
  <name>Task 2: Update ARCHITECTURE.md</name>
  <files>ARCHITECTURE.md</files>
  <action>
    Update the Hardware Abstraction Layer section:
    
    1. Change line 59 from:
       - `*   **InputProvider:** Abstract interface for PTT (Keyboard/GPIO).`
       
       To:
       - `*   **InputProvider:** Abstract interface for PTT (Keyboard/Evdev).`
    
    This reflects the actual input methods: pynput keyboard on Windows dev, evdev for USB numpad on Raspberry Pi.
  </action>
  <verify>`grep -c "GPIO" ARCHITECTURE.md` returns 0, and file contains "Evdev"</verify>
  <done>ARCHITECTURE.md has no GPIO references and lists correct input methods</done>
</task>

<task type="auto">
  <name>Task 3: Update prd.md RAM specification</name>
  <files>prd.md</files>
  <action>
    Update the Hardware section to reflect actual target:
    
    1. Change line 43 from:
       - `- **Compute**: Raspberry Pi 4 Model B (4GB RAM).`
       
       To:
       - `- **Compute**: Raspberry Pi 4 Model B (2GB RAM).`
    
    Also update line 53 if it mentions 4GB:
       - Change "~512MB for OS/System" to "~256MB for OS/System" (proportional to 2GB total)
  </action>
  <verify>`grep "2GB RAM" prd.md` returns a match, no "4GB RAM" references remain</verify>
  <done>prd.md accurately specifies 2GB RAM target hardware</done>
</task>

</tasks>

<verification>
After completing all tasks:
1. Run `grep -r "GPIO" *.md` in project root - should return no matches in main docs
2. Verify all three files have been modified with correct content
</verification>

<success_criteria>
- AGENTS.md: No GPIO references, mentions RPi 4 2GB with USB peripherals
- ARCHITECTURE.md: No GPIO references, mentions Evdev instead
- prd.md: Specifies 2GB RAM (not 4GB)
</success_criteria>

<output>
After completion, create `.planning/quick/1-remove-gpio-references-update-docs-for-r/1-SUMMARY.md`
</output>
