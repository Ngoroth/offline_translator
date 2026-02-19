# Phase 4: Deployment Verification - Research

**Researched:** 2026-02-18
**Domain:** Raspberry Pi hardware verification, ALSA audio, evdev input
**Confidence:** HIGH

## Summary

Phase 4 validates the offline translator runs correctly on target Raspberry Pi hardware through live SSH session testing. This is NOT automated CI - it's interactive verification where Claude SSHs into the Pi and runs manual tests. The codebase already has the infrastructure needed: `EvdevInput` class for numpad PTT, `AudioRecorder`/`AudioPlayer` for audio I/O, and `StartupVerifier` for pre-flight checks. The research focuses on the shell commands and verification procedures needed for live testing.

**Primary recommendation:** Use existing `hardware_check.py` script for numpad testing, ALSA tools (`arecord`/`aplay`) for audio I/O verification, and standard file checks for model verification. Execute tests sequentially with abort-on-failure behavior.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Test Execution Format
- Live session testing: Claude SSHs into Pi and runs tests interactively
- User participates only to press numpad buttons when prompted
- Test order: Pre-flight checks → Audio I/O → Numpad PTT
- Manual checklist approach (not automated script)

#### Hardware Configuration
- Target: Pi 4 accessible at `pi@translator`
- PTT via USB numpad using evdev (NOT GPIO)
- Numpad keys: 5 for Speaker A, 6 for Speaker B
- Evdev device: `/dev/input/event1` ("SIGMACHIP USB Keyboard")
- Audio input: `plughw:1,0` (USB microphone)
- Audio output: `plughw:0,0` (built-in or USB speakers)
- Profile: `rpi_deployment`

#### Failure Handling
- Abort on failure: stop and report, fix before continuing
- No automatic retry - one attempt per test
- Detailed error output: exact error message, failed command, and fix suggestion

#### Results Reporting
- Console output only - no log files created
- Per-test pass/fail status printed as tests run
- Overall summary at the end with pass/fail verdict

#### Pre-flight Checks
- Model files: verify STT (tiny), LLM (Qwen3-0.6B-Q4_K_M.gguf), and TTS (both voices) exist
- Audio devices: verify both `plughw:1,0` and `plughw:0,0` are available
- Evdev: verify `/dev/input/event1` exists and is readable by user

### Claude's Discretion
- Exact commands to verify each check
- How to test audio I/O (record sample, play back)
- How to verify numpad input is captured

### Deferred Ideas (OUT OF SCOPE)
- 10-minute sustained load test (removed from scope per CONTEXT.md)

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEPL-01 | System runs thermal stress test (10-minute sustained load) | **REMOVED FROM SCOPE** per CONTEXT.md |
| DEPL-02 | System validates GPIO button input on target hardware | **MODIFIED**: USB numpad via evdev, NOT GPIO. See evdev verification below. |
| DEPL-03 | System validates audio I/O on target hardware | ALSA commands: `arecord` for capture, `aplay` for playback. Device: `plughw:1,0` (input), `plughw:0,0` (output) |

</phase_requirements>

## Standard Stack

### Core
| Library/Tool | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| `arecord` | alsa-utils | Record audio from ALSA device | Standard Linux audio capture tool |
| `aplay` | alsa-utils | Play audio to ALSA device | Standard Linux audio playback tool |
| `evdev` | Python lib | Read input events from `/dev/input/eventX` | Already used in codebase (`input.py`) |
| `ssh` | OpenSSH | Remote connection to Pi | Standard remote access |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `ls -la /dev/input/` | List input devices, check permissions | Evdev pre-flight check |
| `cat /proc/asound/cards` | List ALSA sound cards | Audio pre-flight check |
| `groups` | Check user group membership | Verify `input` group for evdev access |
| `lsusb` | List USB devices | Verify USB microphone/numpad detected |

### Codebase Components to Use
| Component | Location | Purpose |
|-----------|----------|---------|
| `EvdevInput` | `src/app/core/input.py:152-274` | Numpad PTT input handling |
| `AudioRecorder` | `src/app/core/audio/recorder.py` | Audio capture via arecord |
| `AudioPlayer` | `src/app/core/audio/player.py` | Audio playback via sounddevice |
| `StartupVerifier` | `src/app/core/startup.py` | Model file verification |
| `hardware_check.py` | `scripts/hardware_check.py` | Existing numpad test script |
| `rpi_deployment` | `config.yaml:56-122` | Target hardware profile |

## Architecture Patterns

### Test Session Structure
```
SSH Session Flow:
1. Connect: ssh pi@translator
2. Pre-flight: Verify models, audio devices, evdev access
3. Audio I/O Test: Record 3s sample, play back, verify audible
4. Numpad PTT Test: Run hardware_check.py, user presses keys
5. Report: Print pass/fail summary
```

### Pre-flight Check Pattern
```bash
# Check 1: Model files exist
ls -la models/llm/Qwen3-0.6B-Q4_K_M.gguf
ls -la models/tts/en_US-libritts_r-medium.onnx
ls -la models/tts/ru_RU-denis-medium.onnx

# Check 2: Audio devices available
arecord -l | grep -E "card [0-9]:"
aplay -l | grep -E "card [0-9]:"

# Check 3: Evdev device exists and readable
ls -la /dev/input/event1
test -r /dev/input/event1 && echo "READABLE" || echo "NOT READABLE"

# Check 4: User in 'input' group (for evdev access)
groups | grep -q input && echo "INPUT GROUP OK" || echo "MISSING INPUT GROUP"
```

### Audio I/O Test Pattern
```bash
# Record 3 seconds from USB mic to temp file
arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/test_mic.wav

# Play back through speakers
aplay -D plughw:0,0 /tmp/test_mic.wav

# Verify: User confirms they heard the playback
```

### Numpad PTT Test Pattern
```bash
# Run existing hardware check script
cd /path/to/offline_translator
uv run python scripts/hardware_check.py

# Script prompts user to press KP_5 or KP_6
# Logs key press events to console
# User confirms events detected
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Audio recording test | Custom Python script | `arecord` command | Standard, reliable, no dependencies |
| Audio playback test | Custom Python script | `aplay` command | Standard, reliable, no dependencies |
| Numpad input test | New test script | `scripts/hardware_check.py` | Already exists and works |
| Model file check | New verification code | `StartupVerifier` or `ls -la` | Existing code + simple shell |

## Common Pitfalls

### Pitfall 1: Evdev Permission Denied
**What goes wrong:** User can't read `/dev/input/eventX` - gets "Permission denied".

**Why it happens:** `/dev/input/eventX` files are owned by root:input with mode `crw-rw----`. User must be in `input` group.

**How to avoid:**
```bash
# Check group membership
groups

# Add user to input group if needed
sudo usermod -a -G input $USER

# Requires logout/login to take effect
```

**Warning signs:** `ls -la /dev/input/event1` shows `crw-rw---- 1 root input`, but `groups` doesn't show `input`.

### Pitfall 2: ALSA Device Not Found
**What goes wrong:** `arecord: main:788: audio open error: No such file or directory`.

**Why it happens:** Device `plughw:1,0` doesn't exist, or USB mic not connected, or card number changed.

**How to avoid:**
```bash
# List available capture devices
arecord -l

# List available playback devices  
aplay -l

# Find correct device names
cat /proc/asound/cards
```

**Warning signs:** Output of `arecord -l` doesn't show expected device.

### Pitfall 3: Device Number Instability
**What goes wrong:** USB audio device shows as `plughw:1,0` one boot, `plughw:0,0` the next.

**Why it happens:** Kernel assigns device numbers in discovery order; not stable across reboots.

**How to avoid:**
```bash
# Use device name instead of number (more stable)
arecord -L | grep -i usb

# Or use config with device name:
# input_device: "default:CARD=Device"
```

**Note:** Current config uses `plughw:1,0` which may need adjustment after reboot.

### Pitfall 4: Numpad Key Mapping Wrong
**What goes wrong:** Pressing numpad 5 doesn't trigger PTT event.

**Why it happens:** Evdev returns key names like `KEY_KP5`, but config may have `kp5` or `KP_5`.

**How to avoid:**
```bash
# Check what evdev actually sees
uv run python scripts/hardware_check.py

# Look for log line: "Evdev key detected: KEY_KP5"
```

**Config mapping:** `config.yaml` uses `speaker_a_key: "KEY_KP5"` which matches evdev output.

### Pitfall 5: Audio Recording Silent
**What goes wrong:** Recording succeeds but audio is silent when played back.

**Why it happens:** Microphone not selected as input, or gain too low.

**How to avoid:**
```bash
# Check and adjust input levels
alsamixer -c 1  # Card 1 is typically USB mic

# Or set capture volume
amixer -c 1 sset Mic 80%  # Adjust percentage as needed
```

## Code Examples

### Pre-flight Verification Commands
```bash
# === MODEL FILES ===
echo "=== Checking Model Files ==="
MODELS=(
    "models/llm/Qwen3-0.6B-Q4_K_M.gguf"
    "models/tts/en_US-libritts_r-medium.onnx"
    "models/tts/ru_RU-denis-medium.onnx"
)
MISSING=0
for model in "${MODELS[@]}"; do
    if [ -f "$model" ]; then
        echo "  [OK] $model"
    else
        echo "  [MISSING] $model"
        MISSING=1
    fi
done
if [ $MISSING -eq 1 ]; then
    echo "ERROR: Missing model files. Run: uv run python scripts/download_models.py"
    exit 1
fi

# === AUDIO DEVICES ===
echo "=== Checking Audio Devices ==="
if arecord -l | grep -q "card 1"; then
    echo "  [OK] Capture device available"
else
    echo "  [FAIL] No capture device at card 1"
fi
if aplay -l | grep -q "card 0"; then
    echo "  [OK] Playback device available"
else
    echo "  [FAIL] No playback device at card 0"
fi

# === EVDEV DEVICE ===
echo "=== Checking Evdev Device ==="
if [ -e /dev/input/event1 ]; then
    echo "  [OK] /dev/input/event1 exists"
    if [ -r /dev/input/event1 ]; then
        echo "  [OK] /dev/input/event1 is readable"
    else
        echo "  [FAIL] /dev/input/event1 not readable - add user to 'input' group"
    fi
else
    echo "  [FAIL] /dev/input/event1 does not exist"
fi
```

### Audio I/O Test Commands
```bash
# === RECORD TEST ===
echo "=== Recording 3-second test sample ==="
echo "Speak into the microphone now..."
arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/pi_audio_test.wav
if [ $? -eq 0 ]; then
    echo "  [OK] Recording completed"
    ls -la /tmp/pi_audio_test.wav
else
    echo "  [FAIL] Recording failed"
    exit 1
fi

# === PLAYBACK TEST ===
echo "=== Playing back test sample ==="
echo "You should hear your recording..."
aplay -D plughw:0,0 /tmp/pi_audio_test.wav
if [ $? -eq 0 ]; then
    echo "  [OK] Playback completed"
    echo "Did you hear the audio? (y/n)"
    read -r HEARD
    if [ "$HEARD" = "y" ]; then
        echo "  [OK] Audio verified by user"
    else
        echo "  [FAIL] Audio not heard - check speaker connection"
    fi
else
    echo "  [FAIL] Playback failed"
fi
```

### Numpad PTT Test (Using Existing Script)
```bash
# === NUMPAD PTT TEST ===
echo "=== Testing Numpad PTT Input ==="
echo "Run: uv run python scripts/hardware_check.py"
echo "Press KP_5 or KP_6 when prompted"
echo "Watch for 'EVENT DETECTED: Role X PRESSED' in output"
```

## Verification Checklist

### Pre-flight Checks (All Must Pass)
- [ ] SSH connection to `pi@translator` works
- [ ] `models/llm/Qwen3-0.6B-Q4_K_M.gguf` exists
- [ ] `models/tts/en_US-libritts_r-medium.onnx` exists
- [ ] `models/tts/ru_RU-denis-medium.onnx` exists
- [ ] `arecord -l` shows capture device at card 1
- [ ] `aplay -l` shows playback device at card 0
- [ ] `/dev/input/event1` exists
- [ ] User can read `/dev/input/event1` (in `input` group)

### Audio I/O Test
- [ ] `arecord -D plughw:1,0` records without error
- [ ] `aplay -D plughw:0,0` plays without error
- [ ] User confirms audible playback

### Numpad PTT Test
- [ ] `scripts/hardware_check.py` runs without error
- [ ] Pressing KP_5 logs "Role a PRESSED"
- [ ] Pressing KP_6 logs "Role b PRESSED"
- [ ] Key release events detected

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| GPIO button input | USB numpad via evdev | Pre-phase 4 | Simpler hardware setup, no wiring needed |
| Automated CI tests | Live SSH session testing | Phase 4 | Hardware-specific verification |
| 10-minute thermal test | Removed | Phase 4 | Not needed per user decision |

## Open Questions

1. **Should we test the full application or just components?**
   - What we know: Pre-flight + Audio I/O + Numpad tests are defined
   - What's unclear: Whether to also run `main.py` for end-to-end test
   - Recommendation: Start with component tests. Full app test is optional bonus.

2. **What if device numbers changed after reboot?**
   - What we know: `plughw:1,0` and `plughw:0,0` are in config
   - What's unclear: Whether to verify or adjust config dynamically
   - Recommendation: Verify devices exist with `arecord -l`/`aplay -l`. If numbers differ, note it for user to fix.

3. **Should we check STT model "tiny"?**
   - What we know: STT model_path is "tiny" which is a huggingface ID, not a local file
   - What's unclear: Whether to verify huggingface cache
   - Recommendation: No - faster-whisper downloads "tiny" on first use if not cached. Not a blocking check.

## Sources

### Primary (HIGH confidence)
- Codebase analysis - `src/app/core/input.py`, `src/app/core/audio/recorder.py`, `scripts/hardware_check.py`
- ALSA documentation - `arecord(1)`, `aplay(1)` man pages
- ArchWiki udev article - https://wiki.archlinux.org/title/Udev

### Secondary (MEDIUM confidence)
- HiFiBerry audio testing guide - https://www.hifiberry.com/docs/software/simple-recordings-using-arecord-aplay/
- Raspberry Pi audio setup - https://iotbytes.wordpress.com/connect-configure-and-test-usb-microphone-and-speaker-with-raspberry-pi/

### Tertiary (LOW confidence)
- None - all critical procedures verified in codebase or official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all tools are standard Linux utilities already used in codebase
- Architecture: HIGH - test structure follows existing patterns
- Pitfalls: HIGH - identified from ALSA/evdev documentation and common issues

**Research date:** 2026-02-18
**Valid until:** 30 days (stable Linux utilities)
