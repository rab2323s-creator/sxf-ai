# SXF Runway Gen-4.5 versus Kling VIDEO 3.0: Reproduction and Evidence
Reviewed: 2026-10-22.

## Original, reproducible arithmetic experiment
Run `python sxf-video-economics-lab.py` with Python 3 stdlib only.
No API calls or videos generated. Exactly 48 arithmetic scenarios: 6 selected Runway Dev model/mode SKUs × 2 shared-length outputs (5,10 seconds) × 4 hypothetical Kling accept-rate assumptions. Gen-4.5 acceptance rate is HYPOTHETICALLY 80% in all cases.
The Runway Dev credit values are 12/sec Gen-4.5; Kling standard 9 silent/13 with audio; Kling Pro 12 silent/17 with audio; Kling 4K 43. One developer credit costs $0.01. This avoids the invalid comparison of consumer credit bundles from two unrelated subscription products.
Under the explicitly fictional assumption that Gen-4.5 usable output acceptance equals 80%, Kling Standard no-audio breaks even at 60% acceptance on output-only spend for equal durations: 0.80 × $0.09 / $0.12.
Rates differ by resolution and audio. A cheaper unit price is not evidence of better/fairer quality. No measured acceptance, latency, audio fidelity or video output is included.

## Real head-to-head measurement protocol
- Confirm vendor source/API plan, time and tier; never compare one provider's consumer credits to another's dollars.
- Compare five and ten second video tasks, because only Kling supports 15 seconds on the selected product configurations; use separate 15s task if relevant.
- Pin text prompts, authorized image references, aspect ratio, camera and output requirements; test audio separately.
- Blind-review motion coherence, camera execution, image/identity consistency, prompt adherence, temporal defects, captions, native audio synchronization and human editing labor.
- Record exact model_id, API version, timeout, error/retry cost, task completion time, output artifacts and individual clip acceptance.
- Keep video rights, actor/model release consent, privacy and geographic restrictions in the audit record.
- Report independently labeled results by workload; don't invent vendor winner from marketing demos.

Official Runway Dev pricing: https://docs.dev.runwayml.com/guides/pricing/
Official Runway Dev inputs: https://docs.dev.runwayml.com/assets/inputs/
Runway Gen-4.5 product: https://help.runwayml.com/hc/en-us/articles/46974685288467-Creating-with-Gen-4-5
Kling VIDEO 3.0 official guide: https://kling.ai/quickstart/klingai-video-3-model-user-guide
Runway Dev API changelog: https://docs.dev.runwayml.com/api-details/api_changelog/
