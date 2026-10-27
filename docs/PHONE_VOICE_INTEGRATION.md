# Unified Phone Voice Integration

## Goal
Provide one shared voice workflow for the existing Sentinel Hands, Sovereign, and Creighton phone apps. Reuse existing functionality; do not add a competing app or require Muse.

## Architecture
Phone UI and app adapters -> VoiceSession -> speech-to-text -> Unified Field task router -> response -> text-to-speech. Prefer Android on-device speech recognition and TextToSpeech. Remote AI is optional, explicit, time-bounded, and must have an offline fallback.

## Safety and reliability
- Push-to-talk first; no hidden microphone capture.
- Speech transcripts are input, not authorization. Sensitive actions require policy checks and explicit approval.
- Support cancellation, timeouts, permission denial, offline mode, missing speech engines, and app backgrounding.
- Do not log raw audio by default; transcript retention is opt-in.
- Never put provider keys in the mobile client.

## First vertical slice
1. Inventory the three installed apps: package IDs, source repositories, entry points, permissions, speech code, storage, and documented APIs.
2. Choose one canonical host and define adapters only for interfaces that actually exist.
3. Build push-to-talk -> transcript -> local echo -> Android TTS.
4. Test permission denial, silence, recognition/TTS unavailable, cancellation, offline mode, and app lifecycle.
5. Connect the task router only after the local loop passes; verify approval-required and denied outcomes.

## Acceptance criteria
- Local smoke test makes no network requests.
- Every session has a terminal state: completed, cancelled, permission_denied, unavailable, or failed.
- Cancellation releases audio resources.
- A transcript alone cannot authorize sensitive actions.
- Build and tests are recorded against an exact commit.

## Known limitation
The current Sovereign Node README and package manifest describe a Vite/React Google AI Studio web app and a GEMINI_API_KEY setup step. They do not establish that this repository contains a native Android voice service. Native permissions, Android lifecycle behavior, and on-device speech require separate implementation and device testing.

## Coordination
Parallel contributors must claim separate files, work from a recorded SHA, and update one shared contract. Muse is not a required dependency unless explicitly justified by an architecture decision.
