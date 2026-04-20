# Orbital Copilot Usage API

A small Python service that exposes a single `GET /usage` endpoint returning
per-message credit consumption for the current billing period.

It combines:
- the current-period messages endpoint
- the per-report pricing endpoint

and returns usage data in the contract format specified in the task.

## Running it

Requires Python 3.10+ (tested on 3.13).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the API on http://127.0.0.1:8000
uvicorn app.main:app --reload

# In another shell
curl -s http://127.0.0.1:8000/usage | jq
```

Interactive docs are available at `http://127.0.0.1:8000/docs`.

## Running the tests

```bash
pytest
```

30 tests cover the credit rules (unit) and the endpoint itself (integration
against a mocked upstream via `httpx.MockTransport`).

## Project layout

```
app/
  credits.py   # Pure credit-calculation rules (no I/O)
  clients.py   # Thin HTTP wrappers for the two upstream APIs
  service.py   # Orchestration: fetch messages, resolve reports, compute credits
  schemas.py   # Pydantic response models
  main.py      # FastAPI app, /usage and /health endpoints
tests/
  test_credits.py  # Hand-verified unit tests for every rule + edge cases
  test_api.py      # End-to-end tests with mocked upstream
```

The layering is deliberate: `credits.py` has zero imports from the HTTP
layer, and `service.py` is driven by an injected `httpx.AsyncClient` rather
than a module-level one. That makes the billing logic trivial to unit-test
and the service trivial to integration-test without hitting the network.

## Design decisions worth highlighting

### Correctness first

The riskiest part of this task is billing accuracy, so I isolated the credit
calculation rules in credits.py and used Decimal internally rather than
binary floating-point.

### Thin API, explicit service layer

The FastAPI route is deliberately thin. The orchestration logic lives in
service.py, while clients.py is responsible only for upstream HTTP calls.

### Contract compliance

The response contract is important, so:

* the API returns exactly the agreed fields
* report_name is omitted when absent, not returned as null

### Upstream handling

* Valid report lookups are authoritative
* 404 on the report endpoint falls back to text pricing, per spec
* non-404 upstream failures return 502, because silently guessing would risk incorrect billing

### Request-time efficiency

* repeated report_ids are resolved once per request
* report lookups are fetched concurrently with a bounded semaphore

### Interpreting ambiguities

The spec has a few underspecified edges. I chose the interpretation that
seemed least surprising and documented each decision in code:

- **"Word" definition.** I interpreted “a continual sequence of letters, plus ’ and -” as words like don't and well-known counting as a single word. and `well-known` is one 10-character word.
- **Third-vowel positions.** I treated “3rd, 6th, 9th…” as 1-indexed character positions.
- **Unique-word bonus on zero-word messages.** If a message contains no words, the unique-word bonus does not apply.
- **Palindrome on empty-after-normalisation strings.** Same reasoning -
  If a message becomes empty after removing non-alphanumeric characters, it is
not treated as a palindrome.
- **Rounding.** I round `credits_used` to 2 decimal places for stable JSON output. Although the
  spec doesn't say, but this matches how every billing UI I've worked with
  displays money-like values, and keeps the JSON numbers stable.

### Contract compliance

The response shape matters — multiple teams consume it. Two small things
keep us honest:

- `UsageItem` is a Pydantic model with `extra="forbid"`, so any accidental
  new key fails the test suite before it ships.
- The `/usage` route sets `response_model_exclude_none=True`. The spec says
  `report_name` must be **omitted** when absent, not serialised as `null`.
  There's a dedicated test asserting this.



## Concessions / things I'd do next with more time

- **No retries or circuit-breaking** on upstream calls. For a real
  billing service I'd add bounded retries with exponential backoff (for
  idempotent GETs it's safe) and a circuit-breaker so a flaky reports
  service doesn't amplify latency.
- **No metrics/tracing.** I'd add OpenTelemetry spans around each upstream
  call and a counter for "fell back to text rules because report was 404"
  — that specific event is interesting from a data-quality perspective.
- **No authentication.** The task doesn't require it, but in production
  `/usage` would sit behind the same auth layer as the rest of the stack.
- **No pagination.** The sample dataset is small (110 messages); a real
  billing period could be much larger, and I'd stream rather than
  materialise the full list if that became a concern.
- **Python version pinning.** `requirements.txt` uses `>=` bounds for
  brevity. In a real repo I'd use a lockfile (`uv.lock` / `poetry.lock`)
  for reproducible builds.

## Example response

```json
{
  "usage": [
    {
      "message_id": 1000,
      "timestamp": "2024-04-29T02:08:29.375Z",
      "report_name": "Tenant Obligations Report",
      "credits_used": 79.0
    },
    {
      "message_id": 1002,
      "timestamp": "2024-04-29T07:27:34.985Z",
      "credits_used": 3.95
    }
  ]
}
```
