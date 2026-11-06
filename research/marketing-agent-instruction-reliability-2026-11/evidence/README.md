# SXF / AI — Marketing Agent Instruction Reliability Lab
Observed: November 6, 2026. Original platform UI text pasted by the operator.

This is a controlled test of ten *fictional companies* per run, not real
lead research, email sending, spreadsheet writing, or marketing ROI.

Files here: source-packet.csv (the fixture), instructions-v1.1.txt
(the shared revised specification), input-prompt-make.txt,
input-prompt-zapier.txt, original transcripts for three Make and three
Zapier runs, run-scorecard.csv, and validate.py (Python CSV checker).

Make round 1 was a pilot using an earlier prompt. Only Make rounds 2–3
and Zapier rounds 1–3 use revised v1.1 instructions. Platform model
settings: Make GPT-5 nano / low reasoning (operator reported), Zapier
model not captured. Make round 2 usage and Zapier usage were not captured.

Important: The displayed original transcripts are operator-pasted text,
not provider-signed logs. Zapier run 2's UI copy flattened rows and
therefore its structural CSV score is not reliably auditable.

A CSV row passes only if it has exactly 10 parsed fields and the header
matches the ten exact specified fields. Draft length passes only at
50 through 80 whitespace-delimited words. Counts for malformed row
bodies are diagnostic only. Models' own self-reports are not scores.

This is a narrow single-task observation, not a general platform ranking.
