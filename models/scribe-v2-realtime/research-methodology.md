# SXF / AI — Scribe v2 Realtime testing protocol

Last reviewed: 2026-10-21.

## Executed local transport/consumer lab
Run `python sxf-scribe-realtime-event-lab.py` (stdlib only).
24 sessions are served as real localhost HTTP/NDJSON responses. Each event is a manually designed **synthetic fixture** using event names documented by ElevenLabs. The HTTP service is not ElevenLabs, not a WebSocket, not its SDK and not an audio transcription engine. It demonstrates that partial events are ephemeral, committed events are stable, empty/repeated keepalive-like partials must not be appended, and errors must not be silently converted to final text.
Verified result: 24 sessions, 116 mock events, 22 successful committed sessions, 2 injected interruptions, 24 naive-append incorrect/unverified results, 22 event-aware accepted sessions. The results are not a vendor benchmark, accuracy measurement, provider latency test or estimate of error frequency.

## Production-ready live STT study
1. Obtain informed consent for recordings. Create ground truth in at least English and the actual target languages and accents; include noise, pauses, cross-talk and telephony.
2. Capture source WAV quality and sample-rate conversion, chunk sizes, client/server time stamps, commit policy, WebSocket connection failures, partial and committed transcript events.
3. Use a real ElevenLabs subscription and explicitly approved service API. Record model_id, parameters, tier, addon flags, region, official invoices and data retention.
4. Define distinct time-to-first-partial, time-to-committed, end-to-end turn response, p50/p95/p99 latency and real-time factor. Do not treat a provider marketing ~150ms number as an SXF measurement.
5. Human-review reference transcripts; evaluate WER/CER and domain terms, plus stability and partial-correction frequency. No speaker diarization from realtime is presumed.
6. Test VAD vs manual, simultaneous calls, silence keepalives, reconnects, rate limit and quota failures, and stale transcript merging. Guard tool actions against incomplete partials.
7. Publish raw, permission-cleared test data, scripts and uncertainties; never invent vendor-specific observations.

## Official source links
https://elevenlabs.io/docs/api-reference/speech-to-text/v-1-speech-to-text-realtime
https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/event-reference
https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/transcripts-and-commit-strategies
https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/client-side-streaming
https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/server-side-streaming
https://elevenlabs.io/pricing/api
https://elevenlabs.io/realtime-speech-to-text
