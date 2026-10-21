# SXF Speech-to-Text Evaluation Protocol

Last reviewed: 2026-10-21

## Published evidence

The comparison's Deepgram and ElevenLabs capabilities and audio-time price snapshots are taken from the linked vendors' own official documentation. These are not independent accuracy data. Promotional prices, tiers, regions, supported modes and add-ons may change.

## Original, executed offline evidence

`python sxf-stt-evaluation-lab.py` runs six synthetically authored reference/hypothesis text pairs and computes WER and CER using exact Levenshtein distance. The sentences are fictional. **None is from Deepgram Nova-3 or ElevenLabs Scribe v2**. No provider API calls, real audio, invoices, streaming tests or latency benchmarks were performed. Claims of measured STT vendor superiority are unsupported.

The script also accepts an externally created CSV with `sample_id,reference,hypothesis`, allowing independent reproduction when **reviewed** real transcripts are available. Do not submit unauthorized private recordings or transcripts.

## Honest live benchmark protocol

1. Obtain legal consent to process representative recordings and define an allowed retention policy.
2. Stratify a sample across languages and dialects, noisy phone calls, multi-speaker overlap, proper nouns, numbers and real-world formatting.
3. Have independent human labelers create reference transcripts and adjudicate disagreements, including a written normalization standard.
4. Run both **batch** products over the identical WAV source and document provider version, model ID, keyterms, diarization mode and all additional features.
5. Record per-job provider billable audio minutes, retries, actual invoices, wall time, API errors, output format, word timestamps, speaker labels and privacy controls.
6. Evaluate WER and CER for normalized text with the same protocol; measure keyterm recall and speaker DER separately using verified reference labels.
7. Publish sample sizes, failures, uncertainty and any unsupported language/mode mismatches. Keep source audio private unless permission explicitly allows release.
8. If evaluating streaming, compare Deepgram Nova-3 streaming to **Scribe v2 Realtime** as a separate experiment.

Avoid declaring a winner on the basis of the vendor's published self-benchmark numbers, or SXF's own synthetic text cases.
