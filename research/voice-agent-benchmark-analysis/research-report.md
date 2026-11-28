# AI Voice Agent Benchmarks: Latency, Reliability and Cost — SXF Research

Original analysis by SXF / AI Research, based on publicly available benchmark data.

Version 1.0 — 2026-11-28. Secondary analysis only; no SXF vendor calls.

## Method and provenance

OpenBenchmarks: https://openbenchmarks.com/voice-agent-latency/voice-agent-end-to-end-latency; methodology/code https://github.com/openbenchmarks-labs/voice-agent-latency. Publisher self-describes as independent and says it does not accept payments for ranking; funding not independently audited. MIT repository; public API described as CC BY 4.0 at https://openbenchmarks.com/about. Only aggregate facts and new derived values are included; no recordings or upstream datasets.

Ray et al., ICML 2026: https://proceedings.mlr.press/v306/ray26a.html; version-specific Table 6: https://arxiv.org/html/2603.13686v1 (CC BY 4.0). Authors: Sierra.ai and Princeton affiliations. Historical models, simulated English audio, 278 tasks. Pipecat component benchmark: https://www.pipecat.ai/benchmarks/speech-to-text; maintained by Daily and community, announced Deepgram acquisition: https://www.daily.co/blog/deepgram-is-acquiring-daily-and-establishing-an-independent-pipecat-foundation/. Not treated as a fully independent platform test.

## Latency results

| Platform | p50 ms | p95 ms | Usable/observed | Coverage % | Tail gap ms | Index 50/50 |
|---|---:|---:|---:|---:|---:|---:|
| Telnyx | 1296 | 1856 | 419/432 | 97.0 | 560 | 97.6 |
| ElevenLabs | 1424 | 1768 | 429/432 | 99.3 | 344 | 95.5 |
| Bland AI | 1520 | 2248 | 429/432 | 99.3 | 728 | 82.0 |
| Vapi | 1558 | 2008 | 382/432 | 88.4 | 450 | 85.6 |
| Retell AI | 1740 | 2259 | 419/430 | 97.4 | 519 | 76.4 |

Coverage = usable/observed × 100; tail gap = p95 − p50; tail ratio = p95/p50. Index = 100 × [w × 1296/p50 + (1−w) × 1768/p95]. Weight 0.5 by default; no overall rank or reliability prediction. 2078/2158 retained turns; Vapi coverage 88.4% is a measurement caveat, not task failure rate. Telnyx lowest median, ElevenLabs lowest p95. Missing platforms not scored.

## Task outcomes

| Historical model | Clean % | Realistic % | Drop pp | Retention % |
|---|---:|---:|---:|---:|
| gemini-live-2.5-flash-native-audio | 31 | 26 | 5 | 83.9 |
| gpt-realtime-1.5 | 49 | 35 | 14 | 71.4 |
| grok-voice-agent | 51 | 38 | 13 | 74.5 |

Retention = realistic/clean × 100. Text reference 85%. Rounded figures; no causal attribution of degradation to one condition. Do not combine these task rates with unrelated vendor phone costs. Pipecat 1,000-sample STT benchmark measures semantic errors and final-transcript delay rather than task completion.

## Cost sensitivity

Hypothetical cost per verified success = (minute rate × minutes + other cost per attempt)/success fraction. At $0.10/min, five minutes, $0.20 extras and 50% success: $1.40. Zero success is undefined. Not a vendor measurement.

## Reproduction and limitations

Run python reproduce.py alongside latency-summary.csv and task-summary.csv. No APIs. Repeated turns are not independent; aggregate values cannot establish statistical significance. No joint platform reliability or overall performance score. Source facts stay attributed to their publishers; figures and derived metrics are SXF's. Future primary tests are planned, not executed.
