# Engineering Standards

This repository treats source-data reconciliation as a production concern.

## Principles

- Keep domain calculations deterministic and independently testable.
- Validate configuration at startup rather than silently accepting invalid values.
- Preserve an audit trail for reconciliation checks: expected value, actual value, tolerance, and outcome.
- Keep private workbooks, source documents, credentials, and customer data outside the public repository.
- Prefer explicit typed models over unstructured dictionaries at module boundaries.
- Add regression tests when calculation behavior changes.

## InfoBay readiness

The repository is being strengthened with genuine engineering work. Source-file and LOC counts should represent useful source code, not generated filler. Pull requests should represent real changes and reviews; historical development duration and merged-PR counts are not fabricated or backdated.
