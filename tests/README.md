# Tests

Test layers are organized by intent:

- unit: fast, isolated tests (default pack)
- component: phase-level tests in isolation (default pack)
- contract: input/output schema + rules (default pack)
- integration: hits real FS/HTTP (opt-in)
- golden: snapshot regression checks (opt-in)
- smoke: short end-to-end sanity (opt-in)
- e2e: full end-to-end flow (opt-in)
- perf: performance & budgets (opt-in)

Markers

- `@pytest.mark.unit` — included by default
- `@pytest.mark.component` — included by default
- `@pytest.mark.contract` — included by default
- `@pytest.mark.integration` — opt-in
- `@pytest.mark.golden` — opt-in
- `@pytest.mark.smoke` — opt-in
- `@pytest.mark.e2e` — opt-in
- `@pytest.mark.perf` — opt-in

Auto-marking by folder

- Files under `tests/unit` get `unit`, `tests/component` get `component`, `tests/contract` get `contract`, …etc.
- Files at the root `tests/` default to `unit`.

Running

- Default fast pack (unit+component+contract):
  - `pytest`
- All tests (example):
  - `pytest -m "unit or contract or component or integration or smoke"`
- Only smoke:
  - `pytest -m smoke -q`
- Only golden:
  - `pytest -m golden -q`

Local env tips

- Silence OTEL exporter during tests to avoid noisy logs:
  - PowerShell: `$env:OTEL_TRACES_EXPORTER='none'; pytest`
  - Bash: `OTEL_TRACES_EXPORTER=none pytest`
- Make targets (if using Make):
  - `make test` — fast pack with coverage
  - `make test-fast` — fast pack, no coverage
  - `make test-golden` — golden only

Coverage

- CI enforces a minimum coverage threshold (70%).
- Locally:
  - `pytest --cov=core --cov=backend --cov-report=term-missing`

Schema discovery

- File `tests/contract/test_schema_discovery.py` automatically validates every
  `input.schema.json` and `output.schema.json` under `core/validation/contracts/stages/`.
- It checks schema syntax with Draft 2020-12 and that `$id` is present.
- New phases are picked up automatically when you add the two schema files.
- You can override the schema root via env `MEDFLUX_SCHEMA_ROOT` if needed.

Golden updates

- Golden tests compare normalized JSON snapshots under `tests/golden/...`.
- To update snapshots locally after an intentional change:
  - PowerShell: `$env:UPDATE_GOLDEN='1'; pytest -m golden`
  - Bash: `UPDATE_GOLDEN=1 pytest -m golden`
- Snapshot updates are blocked in CI; commit updated golden files in the same PR
  and mention behavior changes in the CHANGELOG.

Phase onboarding checklist

- Schemas
  - Add `input.schema.json` and `output.schema.json` under `core/validation/contracts/stages/<phase>/`.
  - Follow existing `$id` pattern and keep stage-specific fields aligned (e.g., `unified_document.stage`).
- Factories
  - Create `tests/_utils/factories/<phase>.py` with:
    - `make_<phase>_input_minimal/ok/invalid()` and `make_<phase>_output_ok()`.
  - Mirror required fields in schemas; keep `run_id` format consistent.
- Component tests
  - Under `tests/component/<phase>/` add:
    - `test_config.py` to assert `discover_phase(<phase>)` finds both schemas.
    - `test_pipeline_small.py` using factories + `validate_input/validate_output` (+ optional `cross_field_checks`).
- Contract tests
  - Discovery test already validates all schemas; add per-phase tests if you need extra assertions.
  - Place them under `tests/contract/<phase>/`.
- Golden (optional but recommended)
  - Add stable inputs/outputs under `tests/golden/<phase>/...` and `test_golden_*.py` using `assert_json_golden()`.
  - Update snapshots locally with `UPDATE_GOLDEN=1` when behavior changes intentionally.
