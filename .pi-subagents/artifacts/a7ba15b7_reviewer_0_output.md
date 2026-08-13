## Review
- Correct: 28 tests pass; `git diff --check` and Ruff lint pass.
- **Hard, medium:** `services/security_policy.py:108-116` decodes bytes outside error handling. Invalid UTF-8 raises `UnicodeDecodeError`, producing 500 instead of documented 400 invalid JSON.
- **Hard, medium:** `policy.py:51-53,237-256` does not validate BCP 47 correctly: valid `i-klingon` is rejected while invalid dangling extension `en-u` is accepted.
- **Hard, medium:** `policy.py:214-235,451-470` accepts Canonical URL port `99999`, then normalization rejects it. Verified outcome: management reports `published`/200 while the endpoint returns 404.
- Note: No material judgement-call smells found. Requested `plan.md` and `progress.md` were absent.