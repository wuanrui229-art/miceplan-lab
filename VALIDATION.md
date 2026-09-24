# Validation of this source package

Verified on 2026-09-25 with Python 3.12:

- All 208 original supplement file checksums matched, before and after testing.
- `verify_reported_results.py`: all manuscript-level count checks passed against captured formal outcomes.
- Implementation tests: **55 passed**.
- Protocol and dataset manifests: verified.
- Append-only journals: **22 journals / 13,151 records** verified.

These checks reproduce recorded evidence and validate the supplied implementation. No new model requests were made; this is not an independent rerun against current provider endpoints.

Commands are documented in [supplement/README.md](supplement/README.md). Tested dependencies: pytest 8.4.2, Shapely 2.1.2 and jsonschema 4.26.0.
