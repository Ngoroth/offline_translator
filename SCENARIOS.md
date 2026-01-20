# Neuromancer Pi: Usage Scenarios

This document defines the intended User Experience (UX) and interaction patterns for the offline translator.

## 1. Simple Interaction (Single Phrase)
*   **Action:** Press and hold PTT key (Space or Alt) -> Speak a single sentence -> Release key.
*   **Behavior:** Recording stops immediately upon release. Translation playback begins as soon as the first sentence is synthesized.
*   **Goal:** Fast, direct translation for simple queries.

## 2. Thoughtful Interaction (Streaming/Multi-phrase)
*   **Action:** Press and hold PTT key -> Speak first part -> **Pause (e.g., 0.5s) while still holding the key** -> Speak second part -> Release key.
*   **Behavior:**
    1. During the pause, VAD triggers a "segment harvest". The first part is sent to STT/LLM/TTS in the background.
    2. While the user is speaking the second part, the system is already translating the first part.
    3. **Crucial:** Playback is GATED. No sound is played while the key is still held if playback_during_recording is false.
    4. Upon release, the system plays all translated segments in order (Part 1 -> Part 2).
*   **Goal:** Allow users to think between phrases without losing context or hearing overlapping audio.

## 3. Immediate Interruption (Barge-in)
*   **Action:** While the system is playing a translation, the user presses **any** PTT key.
*   **Behavior:**
    1. The current audio playback is instantly stopped.
    2. All queues (STT, LLM, TTS, Playback) are cleared.
    3. All background processing for the previous session is cancelled (via `session_id` validation).
    4. A new recording session starts immediately.
*   **Goal:** Allow the user to stop the machine and correct it or respond immediately.

## 4. Dual Speaker Dialogue (Dual PTT)
*   **Action:** 
    *   User A uses `Space` (En -> Ru).
    *   User B uses `Alt` (Ru -> En).
*   **Behavior:** Each key identifies the "Role" of the speaker. The system applies the correct translation direction and voice model for that role.
*   **Goal:** Seamless face-to-face conversation with clear linguistic boundaries.

## 5. Environment-Specific Playback
*   **Speaker Mode (Default):** `playback_during_recording: false`. Sound waits for button release to avoid feedback/echo.
*   **Headset Mode:** `playback_during_recording: true`. Sound starts as soon as it's ready, providing near-simultaneous translation.
