# ADR-013: Import pending via KnowledgeItem.batch_id

- Status: Accepted
- Date: 2026-08-11
- Deciders: engineering

## Context

Architecture sketched a separate `PendingIngest` table linked to `ImportBatch`. MVP-2 already stores proposals as `KnowledgeItem(status=proposed)`.

## Decision

Reuse `KnowledgeItem` for batch proposals: add `ImportBatch` + nullable `knowledge_items.batch_id` / `source_filename`. Do not introduce `PendingIngest` for MVP-3.

## Consequences

- Single confirm path (`confirm_ingest`) for paste and batch.
- Batch GET filters proposed/confirmed by `batch_id`.
- Future richer file audit can still add side tables without migrating pending identity.
