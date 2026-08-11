# Security Policy REST API

All operations require authentication and `plone.securitytxt.ManageSecurityPolicy`.

- `GET /@security-policy` returns values, lifecycle, endpoint status, diagnostics, actions, signing status, and an opaque revision. The response `ETag` is that revision.
- `PATCH /@security-policy` saves the JSON candidate without enabling publication.
- `POST /@security-policy/preview` validates candidate JSON and returns the canonical unsigned preview with `Cache-Control: no-store`.
- `POST /@security-policy/publish` publishes current values, or the optional `values` object in the request.
- `POST /@security-policy/disable` disables publication.
- `POST /@security-policy/test-signing` tests the selected deployment profile.

Every mutating request requires `If-Match` containing the revision ETag returned by GET. Missing preconditions return `428`; stale revisions return `412`. Validation returns `400` with structured errors, blockers, and warnings and does not partially persist.

The policy is not stored in `plone.registry`; generic `@registry` and `@controlpanels` routes cannot read or mutate it.
