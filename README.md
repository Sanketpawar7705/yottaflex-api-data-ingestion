# YottaFlex AI — API Data Ingestion Challenge

A locally runnable Python pipeline for a paginated REST API. It demonstrates API-key authentication, pagination, HTTP 429/5xx retries, raw response retention, schema/business validation, quarantine, incremental checkpoints, idempotent UPSERT, run metrics, and automated tests.

## Architecture

```text
Synthetic records -> FastAPI mock API -> Python client (auth/pagination/retry)
                                      -> raw_responses (SQLite)
                                      -> validate + transform
                                      -> events (accepted) / rejects (quarantine)
                                      -> checkpoints + run metrics + report
```

## Setup (Python 3.11+)

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Terminal 1 — start mock API:

```bash
uvicorn app.mock_api:app --reload
```

Terminal 2 — run pipeline:

```bash
python -m app.pipeline
python -m app.report
pytest -q
```

API docs: http://127.0.0.1:8000/docs. Default key: `local-demo-token` (local demo only). Configure with environment variables shown in `.env.example`. Set `MOCK_RECORD_COUNT=100000` before launching the API for a larger dataset. API controls: `POST /admin/configure` accepts `{"rate_limit_every":2,"fail_once":true,"schema_drift":false}`; `POST /admin/reset` regenerates source data.

## Data model and rules

**Grain:** one event per `event_id`. Required source columns: `event_id` (stable key), `customer_id` (must be CUST-0001 through CUST-0100), `amount` (numeric and >= 0), `currency` (three uppercase letters), `status` (pending/completed/cancelled), `event_time`, `updated_at` (timezone-aware ISO-8601). All fields are required; unknown fields are rejected.

`events` is the accepted current-state table with primary key `event_id`, amount in source units and integer minor units, UTC timestamps, source page, run ID, and ingestion timestamp. `raw_responses` retains full fetched page bodies. `rejects` stores original rejected JSON, reason, run ID and page. `runs` stores operational metrics and failure status. `checkpoints` stores the last successfully observed update timestamp.

## Reliability and idempotency

- Retries HTTP 429, 500, 502, 503, and 504 with `Retry-After` or capped exponential backoff; other HTTP errors fail fast.
- Raw response is saved before validation.
- Checkpoint advances only after all pages complete. Failed runs leave the previous checkpoint intact.
- A configurable lookback re-reads recent records; `event_id` primary key plus UPSERT prevents duplicate target rows. Latest accepted source version wins.
- Duplicate IDs within the same run are counted and skipped. Invalid records are quarantined, not silently dropped.
- Backfill: increase `LOOKBACK_SECONDS` or use a fresh local database. A lookback catches late updates within its configured horizon.

## Tests and performance

`pytest -q` covers valid/invalid records, missing fields, nulls, negative amounts, invalid references, schema drift, empty input, retry behavior, and reruns. Replace `evidence/test_results.txt` with your real test output after running tests. Page size controls request volume; SQLite primary-key/index lookups support the demo. For production scale consider PostgreSQL, bulk writes, object storage for raw payloads, cursor pagination, and bounded concurrency.

## Limitations and trade-offs

This is a local vertical slice, not a production deployment. The mock dataset is deterministic and offset-paginated. `events` stores latest state rather than a complete event-version history; raw page payloads retain source evidence. A mutable production API should prefer cursor/snapshot pagination and stronger late-arrival/backfill semantics. SQLite is not intended for high-concurrency workloads.

## AI-use disclosure

See `PROMPT_HISTORY.md`. Update it to include every prompt you actually sent to every AI tool. Be accurate about what AI drafted and what you personally ran, reviewed, changed, and validated. You must be able to explain the code in your own words.

Run `python -m app.benchmark` after ingestion for a small local measurement of target row count and 1,000 indexed customer lookups. Record the actual output and machine details in your submission notes; this is a lookup micro-benchmark, not a claim about end-to-end production throughput.
