# Pitfalls Research

**Domain:** Offline Speech-to-Speech Translation (Edge Device Deployment)
**Researched:** 2026-02-18
**Confidence:** HIGH

---

## Critical Pitfalls

Mistakes that cause rewrites, failed deployments, or unusable systems.

### Pitfall 1: Thermal Throttling on Edge Devices

**What goes wrong:**
Raspberry Pi CPU temperature spikes past 80°C within minutes of running AI inference, causing automatic thermal throttling. Performance degrades from 300ms response time to 2+ seconds, making real-time conversation impossible.

**Why it happens:**
- Continuous AI model inference (STT → LLM → TTS pipeline) saturates CPU
- Default Pi 5 case has poor ventilation
- SD card I/O under sustained load generates additional heat
- No thermal headroom planned in the pipeline architecture

**Consequences:**
- Latency balloons beyond acceptable conversational thresholds (1s → 3s+)
- User perceives system as "broken" or "unresponsive"
- Silent failures during model loading under memory pressure

**Prevention:**
- Use active cooling (heatsink + fan) for any Pi 5 deployment
- Monitor CPU temperature: `vcgencmd measure_temp` 
- Profile thermal behavior during stress testing before deployment
- Consider model quantization to reduce compute load

**Warning signs:**
- Response times gradually increasing during extended use
- System responsiveness drops after 5-10 minutes of continuous use
- `dmesg` shows throttling warnings

**Phase to address:** Deployment Verification

---

### Pitfall 2: ALSA Device Index Fragility

**What goes wrong:**
Audio works during development but fails on production Pi. The USB microphone that was device index 1 during testing becomes device index 2 after reboot, causing "device not found" errors.

**Why it happens:**
- ALSA device enumeration order is not deterministic
- HDMI audio, built-in audio, and USB devices compete for indices
- Hot-plugging USB devices changes the ordering
- Development machine (Windows/PortAudio) uses different indexing than production (ALSA)

**Consequences:**
- "Works on my machine" failures during deployment
- Silent audio capture (recording from wrong device)
- User frustration when system appears to "hear nothing"

**Prevention:**
- Use ALSA device names (`plughw:1,0`) instead of numeric indices
- Or use descriptive device identifiers: `aplay -l` / `arecord -l` to list devices
- Add device auto-discovery that searches by device name substring
- Test with `arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -t raw test.raw`

**Warning signs:**
- Config has numeric `input_device_index` instead of string device names
- Audio tests pass on dev machine but fail on Pi
- Recording produces empty/silent files

**Phase to address:** Deployment Verification

---

### Pitfall 3: GPIO Active-Low Hardcoding

**What goes wrong:**
Physical PTT buttons don't respond correctly. Pressing the button triggers nothing, or releasing triggers the action (inverted behavior).

**Why it happens:**
- Many button circuits are "active low" (press = 0V, release = 3.3V) due to pull-up resistors
- Developers assume "active high" by default (press = 3.3V)
- Different button hardware has different wiring conventions
- The code currently has a TODO comment about this exact issue (line 377 in input.py)

**Consequences:**
- System appears unresponsive to user input
- Erroneous triggers on release instead of press
- Confusing debugging because "the button works, just backwards"

**Prevention:**
- Make `active_low` configurable in `GPIOSettings` (it already is!)
- Document expected button circuit wiring in README
- Add input mode verification during startup (log detected state changes)
- Test with actual hardware before declaring "works"

**Warning signs:**
- Buttons trigger on release instead of press
- `lgpio` callbacks fire on unexpected edge
- `is_pressed` logic seems inverted

**Phase to address:** Deployment Verification

---

### Pitfall 4: Cross-Platform Input Mode Mismatch

**What goes wrong:**
Keyboard input (`pynput`) works on Windows dev machine but fails on headless Pi. Or GPIO input works on Pi but dev tests on Windows crash with "lgpio not found."

**Why it happens:**
- `pynput` requires X server on Linux (fails headless)
- `lgpio` only exists on Linux with GPIO hardware
- `evdev` requires `/dev/input/eventX` devices and permissions
- Tests written on one platform don't test the other

**Consequences:**
- System unusable on production hardware
- Silent crashes during input initialization
- "Works on my machine" syndrome

**Prevention:**
- Use `input_mode` config to select appropriate input handler
- Add platform detection with graceful fallbacks
- Mock input interfaces in tests (already done with `mock_input.py`)
- Create separate profiles for `desktop_rtx4070` and `rpi_deployment` (already in config.yaml)

**Warning signs:**
- `ImportError: No module named 'lgpio'` on Windows
- `pynput` hangs or fails on headless Pi
- Tests only exercise one input mode

**Phase to address:** Deployment Verification

---

### Pitfall 5: VAD Exception Swallowing

**What goes wrong:**
Voice Activity Detection silently fails. The `is_speech()` method catches all exceptions and returns `False`, masking actual errors like incorrect sample rates or corrupted audio frames.

**Why it happens:**
- Current VAD code (line 44-49 in vad.py) has bare `except Exception: pass`
- Originally intended to handle frame size mismatches
- Now hides real problems: wrong sample rate, corrupted buffer, etc.

**Consequences:**
- Silent failures are impossible to debug
- VAD appears to "never detect speech"
- Users think microphone is broken when it's actually a configuration error

**Prevention:**
- Replace silent exception swallowing with proper error logging
- Add validation at VAD initialization for sample rate compatibility
- Log warning on first exception, then optionally suppress duplicates
- Add VAD health check during startup

**Warning signs:**
- VAD never returns `True` despite clear speech
- No error messages in logs
- Debug logging shows exceptions are being caught and ignored

**Phase to address:** Deployment Verification

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoded device indices | Faster development | Broken on device reorder | Never |
| Exception swallowing in VAD | "Robust" against crashes | Silent failures impossible to debug | Never |
| Single sample rate assumption | Simpler code | Incompatibility with some TTS models | Never |
| Platform-specific code without abstraction | Faster MVP | Cross-platform bugs | MVP only, with TODO |
| Skipping thermal testing | Faster deployment | Field failures | Never |

---

## Integration Gotchas

Common mistakes when connecting components.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `faster-whisper` STT | Assuming model auto-downloads | Pre-download models, use local paths |
| `llama.cpp` LLM | Using full-precision models | Use quantized GGUF (Q4_K_M) for Pi |
| Piper TTS | Single speaker ID for all voices | Check model's speaker_ids, use correct one |
| WebRTC VAD | Wrong sample rate (not 8/16/32/48kHz) | Resample to valid rate before VAD |
| ALSA arecord | Using `hw:` instead of `plughw:` | Use `plughw:` for automatic format conversion |
| GPIO callbacks | No debouncing (bounce causes double-fires) | Software debounce (50ms) + hardware pull-up |

---

## Performance Traps

Patterns that work at small scale but fail under load.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Sequential pipeline (STT→LLM→TTS) | Latency accumulates | Stream where possible | Phrase > 5 seconds |
| Large LLM context window | Slow inference | Use minimum needed (512-1024 for translation) | Pi with 4GB RAM |
| No session cancellation | Stuck processing old input | Implement barge-in cancellation | Already implemented |
| Blocking I/O in event loop | UI freezes, audio stutters | Use `asyncio.to_thread()` for CPU work | Any blocking call |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Loading untrusted models | Code execution via model files | Verify model checksums |
| Writing to `/dev/input` without permissions | Input capture fails | Add user to `input` group |
| No input validation on config | Path traversal, arbitrary code | Validate all config paths are within expected directories |
| Logging audio data | Privacy violation | Never log raw audio, only transcription results |

---

## UX Pitfalls

Common user experience mistakes in speech-to-speech systems.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No auditory feedback | User doesn't know system is "listening" | Add beep on PTT press |
| Latency > 1 second | Conversation feels broken, users talk over each other | Profile and optimize pipeline |
| No visual indicator | User can't tell if system is processing | LED or console output during processing |
| Silent error handling | User thinks system is broken | Voice or visual error indication |
| Missing echo mode | Can't verify audio setup works | Add "echo mode" that plays back recorded audio |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Audio Input:** Often missing device auto-discovery — verify with `arecord -l`
- [ ] **Audio Output:** Often missing sample rate match verification — verify TTS output rate matches player expectations
- [ ] **GPIO Input:** Often missing active_low configuration matching hardware — verify with physical button press
- [ ] **Error Paths:** Often missing tests for error conditions — verify `test_error_resilience.py` covers all services
- [ ] **Thermal Testing:** Often skipped in verification — verify sustained load doesn't cause throttling
- [ ] **Cross-Platform:** Often only tested on dev machine — verify on actual Pi hardware

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Thermal throttling | LOW | Add cooling, reduce model size, optimize pipeline |
| Wrong audio device | LOW | Update config.yaml with correct device string |
| GPIO inverted logic | LOW | Toggle `active_low` in config |
| Model not found | MEDIUM | Download model, update path in config |
| Platform input mismatch | MEDIUM | Add proper abstraction layer, update config profile |
| VAD not detecting | MEDIUM | Add verbose logging, verify sample rate, check audio levels |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Thermal throttling | Deployment Verification | Run 10-minute sustained load test |
| ALSA device fragility | Deployment Verification | Test with `arecord` on target hardware |
| GPIO active_low | Deployment Verification | Physical button press test |
| Cross-platform input | Architecture (done) | Verify both profiles work |
| VAD exception swallowing | Deployment Verification | Add test for VAD error logging |
| Audio device discovery | Architecture (TODO) | Implement device auto-detection |
| Echo mode verification | Architecture (TODO) | Implement echo mode for audio testing |

---

## Sources

- [Raspberry Pi 5 AI Deployment Guide](https://www.alibaba.com/product-insights/how-to-run-open-source-ai-models-locally-on-a-raspberry-pi-5-without-overheating-or-crashing.html) - Thermal and memory constraints (HIGH confidence)
- [Raspberry Pi Audio Troubleshooting](https://minipctech.com/troubleshooting-common-raspberry-pi-audio-issues/) - ALSA configuration issues (HIGH confidence)
- [Adafruit USB Audio Cards Guide](https://learn.adafruit.com/usb-audio-cards-with-a-raspberry-pi/updating-alsa-config) - Device enumeration pitfalls (HIGH confidence)
- [Picovoice VAD Comparison](https://picovoice.ai/blog/best-voice-activity-detection-vad/) - WebRTC VAD limitations (HIGH confidence)
- [GPIO Debouncing Guide](https://learn.adafruit.com/make-it-switch/debouncing) - Contact bounce and debouncing (HIGH confidence)
- [llama.cpp Raspberry Pi Issues](https://github.com/ggml-org/llama.cpp/issues/5237) - ARM deployment issues (MEDIUM confidence)
- [Voice Latency Challenges](https://dev.to/jackmorris10/why-voicebot-latency-is-the-hardest-problem-in-real-time-voice-ai-386k) - Real-time latency requirements (HIGH confidence)
- [Python Asyncio Best Practices](https://www.shanechang.com/p/python-asyncio-best-practices-pitfalls/) - Threading/async pitfalls (HIGH confidence)
- [Codebase analysis] - Identified TODOs and existing concerns (HIGH confidence)
- [Home Assistant Asyncio Thread Safety](https://developers.home-assistant.io/docs/asyncio_thread_safety) - Thread safety with asyncio (HIGH confidence)

---

*Pitfalls research for: Offline Speech-to-Speech Translation (Neuromancer Pi)*
*Researched: 2026-02-18*
