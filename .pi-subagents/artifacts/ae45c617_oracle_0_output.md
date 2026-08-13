# Implementation plan

## Inherited decisions

- One language-independent Security Policy per Plone site, stored as a versioned site-root annotation—not registry records.
- One authoritative application API: `inspect`, `evaluate`, `execute`, and `resolve_publication`.
- Drafts may be incomplete; publication requires explicit action and full validation. Published edits replace retained bytes atomically.
- Exact unsigned or signed publication bytes, binding, and strong ETag are retained.
- Dedicated `plone.securitytxt.ManageSecurityPolicy` permission protects every management path; anonymous access is limited to `/.well-known/security.txt`.
- Signing is optional through `[signing]`, deployment-configured, bounded, sign-then-verify, and fail-closed without invalidating an otherwise matching retained artifact.
- Classic UI uses one standard `z3c.form`; REST is domain-specific; no registry CRUD, custom Volto UI, jobs, or email.

## Diagnosis

The repository is only a package scaffold. `tests/test_setup.py` still contains a placeholder browser-layer assertion, and `setuphandlers.py` does not create/remove policy state. “Minimal but spec-complete” cannot mean only adding a control panel: the application seam, retained artifacts, public endpoint, REST concurrency, signing boundary, lifecycle warning, migrations, compatibility, and documentation are mutually required.

Pre-agreed TDD seams are already specified:

1. **Pure policy seam:** candidate policy → normalized values, diagnostics, state, canonical CRLF bytes.
2. **Application seam:** the four authoritative operations against a real site annotation, injected clock, principal, and signer.
3. **HTTP seam:** anonymous WSGI/browser requests to the exact well-known route.
4. **REST seam:** authenticated HTTP requests, revision ETag, required `If-Match`, diagnostics, and no partial writes.
5. **Classic UI seam:** form actions and warning rendering through browser requests.
6. **Signing seam:** bounded adapter/helper contract, with deterministic fake adapters plus real-GnuPG boundary tests.
7. **GenericSetup seam:** install/reinstall/upgrade/uninstall against real sites.

## Recommended file structure

```text
src/plone/securitytxt/
  policy/
    model.py             # enums, immutable candidates/state/results
    validation.py        # field, extension, limits, warning/blocker rules
    rendering.py         # deterministic RFC 9116 bytes
    canonical.py         # URI/request URL normalization
    iana_fields.json     # release-versioned offline extension snapshot
  application.py         # authoritative four-operation facade + permission checks
  commands.py            # typed save/publish/disable/test-signing commands
  storage.py             # versioned annotation record and atomic replacement
  clock.py               # injectable UTC clock
  artifacts.py           # binding/hash/ETag verification
  signing/
    interfaces.py
    profiles.py          # integrity-checked JSON config/public metadata
    adapter.py           # lazy optional import
    helper.py            # process-group timeout and bounded IPC
  browser/
    controlpanel.py
    wellknown.py
    warning.py
    templates/
    configure.zcml
  restapi/
    services.py          # GET/PATCH and named POST operation services
    configure.zcml
  purge.py
  upgrades/
tests/
  policy/
  application/
  browser/
  restapi/
  signing/
  fixtures/
  test_setup.py
docs/
  administrator.md
  rest-api.md
  deployment.md
  signing.md
  release-checklist.md
```

Keep Plone imports out of `policy/`. Replace the complete annotation record on mutation so nested non-persistent list/dict changes cannot escape ZODB tracking.

## PloneCLI scaffolding

Run on a clean/stashed tree, or use `--no-git` because the current workspace is dirty:

```bash
plonecli add controlpanel --defaults --no-git \
  -d controlpanel_name="SecurityPolicy" \
  -d controlpanel_title="Security Policy"

plonecli add restapi_service --defaults --no-git \
  -d service_name="security-policy" \
  -d service_for="Products.CMFPlone.interfaces.IPloneSiteRoot" \
  -d http_get=true -d http_patch=true -d http_post=true

plonecli add viewlet --defaults --no-git \
  -d viewlet_name="securitypolicywarning" \
  -d viewlet_class_name="SecurityPolicyWarning" \
  -d viewlet_manager="plone.portalheader"
```

Adapt the generated control panel away from `RegistryEditForm`; remove generated policy registry persistence. Extend the REST scaffold with explicit preview/publish/disable/test-signing registrations. Hand-write strict `.well-known` traversal because no specialized scaffold exists.

Because the already-installable profile gains a configlet and changed role mapping, scaffold:

```bash
plonecli add upgrade_step --defaults --no-git \
  -d upgrade_step_title="Install Security Policy management"
```

Add `python-gnupg>=0.5.6` only to the `signing` extra.

## Implementation order

1. **Installation tracer:** permission, annotation Draft creation/removal, real browser-layer assertion, role mappings.
2. **Pure unsigned model:** one red-green slice per validation/rendering behavior; byte fixtures and limit boundaries.
3. **Application module:** inspect/evaluate, revisioned commands, permission denial, expiry transitions, atomic retained unsigned artifacts.
4. **Public endpoint:** strict traversal first; then state/status, GET/HEAD/405, headers, ETags, conditional ordering, Canonical host checks.
5. **REST:** GET state; PATCH save; then each POST operation, `If-Match`, `412`, CSRF/auth boundaries, structured diagnostics.
6. **Classic UI:** fieldsets/widgets, summary, preview, confirmations, publish/disable; then permission-gated expiry viewlet.
7. **Signing:** profile parsing/passive capability, fake adapter, helper timeout/process group, real sign-verify, artifact retention/rotation/failure categories.
8. **Purge and lifecycle:** commit-aware optional purge; install/reinstall/upgrade/uninstall tests.
9. **Acceptance:** docs, hostile-input/security suite, independent `sectxt`/GnuPG fixtures, distribution smoke tests, full supported Plone/Python CI matrix, then full review and commit.

## Drift / contradiction check

- **Blocker:** Do not leave the scaffolded control panel registry-backed; that violates ADR 0001 and creates permission/invariant bypasses.
- **Blocker:** Missing signing capability alone must not produce `503` when an exact retained signed artifact still has a valid binding.
- **High:** An expired enabled policy may accept a corrective future expiry even though ordinary enabled-policy edits must remain publishable.
- **High:** Public response bodies and headers must be constructed deliberately; default Zope exception pages can leak details or alter the specified contract.

## Risks

REST subpath traversal, dotted `.well-known` traversal, VirtualHostMonster Canonical URLs, transaction retry/signing races, GnuPG process-group termination, and custom repeatable z3c.form widgets require early integration proofs. The current single Plone 6.2.1 environment cannot itself attest the required release matrix.

## Suggested execution prompt

Implement the plan in vertical red-green slices at the seven public seams. Preserve both ADRs, use PloneCLI scaffolds before adapting artifacts, run focused tests after every slice and the complete suite/matrix at the end, perform two-axis review against `HEAD` and `.scratch/securitytxt-control-panel`, fix findings, then commit only implementation-owned files.