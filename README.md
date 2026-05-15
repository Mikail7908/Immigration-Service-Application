# Immigration Verification Service - Prototype

A console-based prototype of a controlled immigration status verification
service. Authorised organisations (employers, landlords, education providers)
verify an individual's status via a **share code + date of birth**, and
authorities (border control, law enforcement) verify via **passport or permit
number**. The prototype stores data in JSON files and logs to disk for
observability and audit traceability.

## Project layout

```
.
├── main.py                       # entry point
├── requirements.txt
├── data/                         # JSON persistence (seed individuals, orgs, share codes)
├── logs/                         # app.log (operational) and audit.jsonl (audit trail)
├── src/
│   ├── domain/                   # dataclass models + enums
│   ├── repository/               # FileRepository, AuditRepository (append-only JSONL)
│   ├── validation/               # input validators (format + semantic)
│   ├── services/                 # ShareCode, Authorisation, Verification, Analytics
│   ├── cli/                      # console menu
│   └── logging_setup.py          # rotating file + console logger; JSON if available
└── tests/                        # pytest unit tests (see tests/README.md)
```

## Requirements

- Python 3.9+
- See `requirements.txt`:
  - `pytest` - test runner
  - `python-json-logger` - JSON-formatted file logs (the app degrades gracefully
    to plain text if it isn't installed)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the application

```bash
python main.py
```

You'll see a menu:

```
1. Generate share code (individual)
2. Verify by share code (employer/landlord/education)
3. Verify by document (border control / law enforcement)
4. View operational analytics
5. List seeded individuals and organisations
0. Exit
```

### Suggested walkthrough

1. Choose **5** to list seeded individuals and organisations. Note the IDs.
2. Choose **1** to generate a share code for `IND-0001` with purpose
   `EMPLOYMENT`. Copy the printed share code.
3. Choose **2** to verify it. Use:
   - role: `EMPLOYER`
   - declared purpose: `EMPLOYMENT`
   - organisation ID: `ORG-EMP-01`
   - organisation email: `hr@acme.co.uk`
   - DOB: `1990-04-12`
   - confirm all three confirmations (y/y/y)
4. Try the same code with a wrong DOB → `IDENTITY_MISMATCH`.
5. Try a wrong organisation ID → `UNAUTHORISED`.
6. Choose **3** to verify by passport - use role `BORDER_CONTROL`, organisation
   `ORG-BDR-01`, email `officer@borderforce.gov.uk`, passport `P1234567A`.
7. Choose **4** to view aggregated analytics (no personal information in this view).

## Run the tests

```bash
pytest -v
```

White-box test rationale is documented in [`tests/README.md`](tests/README.md).

## Logging output

Two distinct streams:

| File | Purpose | Format |
|---|---|---|
| `logs/app.log` | operational log (service-level events, correlation IDs, validation outcomes) | JSON (via `python-json-logger`) or plain text fallback |
| `logs/audit.jsonl` | append-only audit trail (share code generation, verification attempts, validation failures) - one JSON object per line | JSONL |

The audit trail is intentionally separate from the operational log so that the
audit history is not affected by operational log rotation or formatting changes.

To inspect them while running the app:

```bash
tail -f logs/app.log
tail -f logs/audit.jsonl
```

## Notes

- The implementation reflects the layered architecture described in the design
  document: CLI → services → validators → repository (file persistence) + audit
  repository.
- All persistence is local JSON / JSONL - no database required.
- Identical inputs deterministically produce identical outcomes (verified by
  `tests/test_verification_service.py::test_determinism_same_input_same_outcome`).
- Outcomes are role-scoped: an employer receives only right-to-work fields, a
  landlord only right-to-rent fields, etc. - verified by tests.
- Analytics output is guaranteed free of personal information by design and by an explicit test.
