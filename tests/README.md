# Testing notes

These unit tests follow a **white-box** approach: tests are written with the
internal control flow of each module in mind. For every decision point in a
function (each `if` branch, each return-on-failure path), there is at least
one test that exercises it.

## Coverage intent per file

| Test file | Module under test | Branches deliberately covered |
|---|---|---|
| `test_validators.py` | `src/validation/validators.py` | each return statement in every validator: missing input, format mismatch, semantic mismatch (e.g. domain mismatch, expired datetime, unknown role/purpose, unknown route, partial confirmations) |
| `test_share_code_service.py` | `src/services/share_code_service.py` | happy path, unknown purpose branch, unknown individual branch, audit-record side effect, revoke-existing, revoke-missing |
| `test_authorisation_service.py` | `src/services/authorisation_service.py` | success + each of the 6 documented rejection branches (confirmations, email format, unknown org, unauthorised org, role mismatch, domain mismatch) |
| `test_verification_service.py` | `src/services/verification_service.py` | full happy paths for both routes and all five roles; every failure branch in `verify()`, `_verify_share_code()`, `_verify_document()`; role-scoped projection correctness (employer outcome must not leak entry/status data); deterministic outcome stability |
| `test_analytics_service.py` | `src/services/analytics_service.py` | aggregation correctness, failure counting, **privacy invariant** (no personal information - individual identifier, share code, or DOB - ever appears in summary output), empty-state behaviour |

## Why these specific tests

- **Format-then-semantic ordering**: validators are layered so that format checks
  run before semantic checks. Tests exercise the format-fail branch separately
  from the semantic-fail branch to catch reordering regressions.
- **Privacy as test invariant**: `test_summary_contains_no_personal_information`
  encodes a cross-cutting design constraint (analytics is free of personal
  information) directly as a test, so any future change that broadens analytics
  output is caught immediately.
- **Determinism**: `test_determinism_same_input_same_outcome` codifies the
  scenario requirement that identical inputs produce identical outcomes.
- **Outcome projection minimisation**: `test_share_code_employer_eligible`
  asserts that fields irrelevant to the employer role (`status_type`,
  `entry_permitted`) do **not** appear in the response, encoding minimum-
  disclosure as a test.

## Running

```
pip install -r requirements.txt
pytest -v
```
