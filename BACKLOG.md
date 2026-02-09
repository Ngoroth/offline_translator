# Project Backlog: Raspberry Pi Optimization

This backlog addresses critical stability and performance issues identified during the initial deployment on Raspberry Pi 4 (2GB RAM).

## 🚨 Priority 1: Robust Audio Subsystem (Epic-01)
**Goal:** Replace unstable PortAudio implementation with robust Linux-native tools.

### Story 1.1: Implement Native `arecord` Subprocess Recorder
- **Status:** ✅ DONE
- **Implementation:** `src/app/core/audio/recorder.py` replaced with subprocess implementation.
- **Verification:** `tools/test_arecord.py` verified 160KB wav file generation.

### Story 1.2: Audio Device Auto-Discovery
- **Problem:** USB device indices change after reboot (`hw:2,0` becomes `hw:1,0`).
- **Solution:** Identify devices by name (e.g., "USB PnP Sound Device") not index.
- **DoD:** Config allows `input_device_name: "USB PnP"` and system resolves it to `hw:X,Y` at runtime.

---

## ⚡ Priority 2: Performance & Feedback (Epic-02)
**Goal:** Make the system responsive and transparent on low-RAM hardware.

### Story 2.1: Echo/Passthrough Mode
- **Problem:** Full pipeline (STT+LLM+TTS) takes 60s to load and hides I/O issues.
- **Solution:** Add `pipeline_mode` to config.
  - `translation`: Standard mode.
  - `echo`: STT -> Text -> TTS (Bypass LLM).
- **DoD:** System starts in <10s in Echo mode.

### Story 2.2: Auditory Feedback (UX)
- **Problem:** User pushes button blindly while system is loading or hanging.
- **Solution:** Play UI sounds.
  - `startup.wav`: System loaded, ready for input.
  - `listening.wav`: PTT pressed.
  - `processing.wav`: PTT released (optional).
  - `error.wav`: Something broke.
- **DoD:** Sounds play correctly at correct lifecycle events.

---

## 🛠️ Priority 3: Infrastructure (Epic-03)

### Story 3.1: Hardware Validation Script
- **Problem:** "It works on my machine" vs "It fails on Pi".
- **Solution:** A unified `scripts/doctor.py`.
  - Checks RAM/Swap.
  - Checks Mic access.
  - Checks Speaker access.
  - Checks Model checksums.
- **DoD:** Script provides Pass/Fail report.

### Story 3.2: Systemd Service
- **Problem:** Running via SSH/tmux is manual.
- **Solution:** Create `offline-translator.service`.
- **DoD:** System starts automatically on boot.
