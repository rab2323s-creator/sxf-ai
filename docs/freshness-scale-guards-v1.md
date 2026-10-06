# Freshness and Scale Guards v1

## Reverification queue

`data/model-reverification.json` is generated deterministically from the canonical model catalog.

The queue does not publish changes. It schedules human reverification against primary sources. Any discovered factual change must enter the candidate/review pipeline before the canonical catalog changes.

Current cadence:

- preview: 7 days
- current + official paid pricing: 30 days
- current + other pricing status: 45 days
- legacy: 90 days
- deprecated: 180 days

The artifact uses `data/model-pricing.json.source_verified` as its clock. This keeps builds reproducible; advancing the catalog verification date intentionally regenerates the queue.

Each item includes identity, last verification date, due date, age, priority, review scope, and the relevant official source URLs.

## CI scale guards

`scripts/validate_catalog_scale.py` enforces structural scale readiness rather than timing-dependent benchmarks.

Guards include:

- exact catalog/index order and coverage parity
- exact catalog/identity-registry coverage parity
- exact catalog/reverification coverage parity
- lightweight-index bytes-per-model budget
- deterministic synthetic 500-model index generation
- 500-model payload ceiling
- unique IDs preserved through the 500-model stress build

The scale guard intentionally avoids wall-clock performance assertions because shared CI runners make them noisy. Runtime profiling can be added later as an informational benchmark without making merge safety depend on machine load.
