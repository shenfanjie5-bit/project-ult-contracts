# Contract Fixtures

This directory contains small JSON payloads shared by contract tests and
downstream integration tests. They are intentionally minimal and should stay
aligned with the Pydantic models exported through `SCHEMA_MODEL_REGISTRY`.

`manifest.json` is the index. Each fixture entry records:

- `path`: repository-relative JSON fixture path.
- `model`: import path for the Pydantic model used to validate the payload.
- `schema_name`: JSON Schema artifact name from `SCHEMA_MODEL_REGISTRY`.
- `valid`: whether the fixture is expected to validate.
- `consumer`: downstream consumers expected to reuse the fixture.
- `case`: short reason for the fixture.

Valid Ex payload fixtures must not contain Layer B ingest metadata fields:
`submitted_at` or `ingest_seq`. `backtest_result` is not a formal object and
is present only as an invalid registry fixture.
