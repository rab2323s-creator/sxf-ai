# SXF AI Model Licensing — Reproducible Evidence Audit Protocol

Last evidence review: 2026-10-21.

## Experiment and limits

Execute: python sxf-license-evidence-lab.py

This is an actual programmatic inspection of 12 deliberately fictional ML release manifests. The code evaluates whether a minimal *document evidence packet* includes origin, weight revision, full license text and model card; for custom-licensed artifacts it also requests the referenced usage policy and a human terms-review signal; for distribution it checks a packaged license copy and notice evidence. These are editorial checklist controls, **not** a complete legal obligations engine and **not** software-license scanning of real model weights.

Expected deterministic results: 12/12 manifests contain a license label; six have a complete packet under these simplified rules; six are flagged for missing evidence. A "complete evidence packet" is ready for human review, not "approved", "legal", or "commercially permitted."

Synthetic scenarios intentionally include MIT, Apache-2.0 and fictional custom-license records for internal, SaaS/API and weight-redistribution cases. No specific vendor release was automatically tested, and no legal or EU AI Act determination follows.

## Real source verification procedure

1. Identify the exact model/repository, publisher, artifact, revision and SHA256 and archive the release snapshot.
2. Open the complete governing license text and version-specific supplementary acceptable-use/redistribution terms.
3. Map the **activity**: internal inference, hosted SaaS/API, modified/fine-tuned checkpoint, redistribution, training other models, branding, territory.
4. Save copyright and notice text, modification notices, model card, runtime/dependency licenses, training data information and provenance evidence.
5. Have a qualified reviewer resolve ambiguous terms and applicable laws; record sign-off with scope and review date.
6. Re-evaluate on any model upgrade, terms changes or changes to deployment/region/product use.

## Primary official source set

- MIT: https://opensource.org/license/mit
- Apache-2.0: https://www.apache.org/licenses/LICENSE-2.0
- OSI Open Source AI Definition 1.0: https://opensource.org/ai/open-source-ai-definition
- Llama 4 agreement: https://github.com/meta-llama/llama-models/blob/main/models/llama4/LICENSE
- Llama 4 acceptable use policy: https://github.com/meta-llama/llama-models/blob/main/models/llama4/USE_POLICY.md
- EU AI Act GPAI provider obligations: https://digital-strategy.ec.europa.eu/en/faqs/guidelines-obligations-general-purpose-ai-providers

This content is education and operational evidence design, not professional legal advice.
