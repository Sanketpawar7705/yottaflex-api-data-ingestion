# Design and Trade-offs

1. Offset pagination is easy to evaluate against a static mock; production APIs with mutable data should use cursor/snapshot pagination.
2. At-least-once fetching plus a lookback window and primary-key UPSERT gives safe replay and catches late updates within the configured horizon.
3. Checkpoint advances only after all pages succeed; failed runs can be replayed.
4. Raw response retention occurs before row validation so rejected data remains auditable.
5. Quarantine preserves source JSON and a reason rather than dropping bad rows.
6. The target is latest-state; raw payloads preserve page history. A production extension could add immutable event versions.
7. Retry policy is bounded and limited to rate limits/transient server errors; permanent client errors fail fast.
8. For larger production workloads use bulk writes, PostgreSQL, object storage, and source-aware concurrency.
