# Scale Readiness v1

Scale Readiness v1 separates model identity and discovery review from the published canonical catalog.

## Data flow

```text
official source / adapter
        |
        v
candidate record
        |
        v
identity resolution
        |
        v
validation + human review
        |
        v
approved canonical source patch
        |
        v
provider-scoped catalog sources
        |
        v
data/model-pricing.json
```

No candidate publishes directly.

## Model Identity Registry

Canonical registry: `data/model-identity/registry.json`.

The registry owns stable SXF identity and provider-scoped identity resolution:

- `canonical_model_id`
- `provider_native_ids`
- `aliases`
- `family`
- `version`
- `predecessor` / `successor`
- `renamed_from`
- lifecycle state
- primary identity evidence

Unknown relationships or versions remain null rather than inferred.

The validator rejects:

- duplicate canonical IDs
- provider-scoped native-ID / alias / rename collisions
- catalog/registry drift
- dangling relationships
- cross-provider predecessor/successor edges
- non-reciprocal relationships
- successor cycles

## Candidate contract

Canonical queue: `data/model-candidates/queue.json`.
Schema reference: `data/model-candidates/schema.json`.

Supported change types:

- `new_model`
- `identity_change`
- `price_change`
- `context_change`
- `capability_change`
- `lifecycle_change`
- `access_change`
- `source_issue`
- `metadata_correction`

Identity resolution states:

- `exact`
- `alias`
- `renamed`
- `successor`
- `new`
- `possible_duplicate`
- `ambiguous`

Approval invariants:

- validation must pass
- ambiguous or possible-duplicate identity cannot be approved
- reviewed candidates require reviewer and timestamp
- approved catalog changes require a proposed record
- evidence must be explicit and HTTPS-backed

## CI

`Validate model catalog` validates the catalog, identity registry, candidate queue, and regression tests together. A catalog change that is not represented in the identity registry fails CI.
