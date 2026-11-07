# Data Dictionary

| Table | Grain / key | Purpose |
|---|---|---|
| events | One row per event_id (PK) | Latest accepted event state; customer_id, amount, amount_minor, currency, status, event_time, updated_at, source_file, run_id, ingested_at |
| raw_responses | One row per fetched page | Full raw response body, HTTP status, page, fetch time, run ID |
| rejects | One row per rejected record | Original JSON, rejection reason, source page, event ID if present, run ID, rejected time |
| runs | One row per pipeline execution | Status, start/end, pages, received, loaded, rejected, duplicates, error |
| checkpoints | One row per source | Last successfully observed updated_at |

All timestamps are stored as ISO-8601 UTC strings. Source business fields are non-null. `amount_minor` is rounded amount multiplied by 100. `customer_id` must reference the mock's fixed customer set.
