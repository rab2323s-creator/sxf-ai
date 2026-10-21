# SXF / AI Vector Search Vendor Evaluation Protocol

This is an evaluation TEMPLATE, not completed performance research.

## Scope
Pin the same source documents, stable chunk IDs, embedding model and dimensions, metric, metadata fields and authorization rules for each candidate. Record database version and real cloud/host hardware, cost tier, region and service limits.

## Relevance
Collect representative labeled questions, including exact identifier, paraphrase, deletion, zero-answer, version-specific and multilingual cases. Prepare exact top-k within each authorized tenant as the geometric ANN oracle. Independently annotate human relevance so geometric recall is never passed off as answer quality.

## Performance
Run cold and warm cache, selective and broad filters, burst and steady concurrent requests, index-build/restore and update/delete operations. Measure p50/p95/p99, timeout rate, throughput at SLO, filter recall, index lag, cost and operational labor. Use multiple repetitions and publish run conditions.

## Security
Every query is scoped by trusted identity before retrieval; test cross-tenant authorization, deleted documents and revocation freshness. Avoid logging sensitive prompts or raw documents.

## Reporting
Release query-level raw results, versions, index/search parameters, exclusions, failure modes, and the complete cost structure. Never interpret the separate SXF synthetic 240-vector demonstration as a benchmark of any database vendor.
