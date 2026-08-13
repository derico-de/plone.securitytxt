# Define release acceptance and compatibility

Type: grilling
Status: resolved
Blocked by: 08 — [Choose the Plone integration architecture](08-choose-integration-architecture.md)

## Question

What must be true for the resulting specification to be implementation-ready and for a future release to be accepted? Define the supported Plone and Python matrix, unit and integration scenarios, standards fixtures and external interoperability checks, permission and security tests, Classic UI and REST API coverage, expiry-warning behavior, signed and unsigned installation matrices, failure and key-rotation scenarios, caching checks, upgrade expectations, and required administrator and deployment documentation.

## Comments

- Compatibility facts and proposed boundary combinations: [Release compatibility for `plone.securitytxt`](../research/release-compatibility.md).
- Acceptance round 1: run every automatable release-acceptance check on every pull request rather than splitting required checks into scheduled/release tiers; test primarily through the application interface with focused pure and adapter tests; require byte-exact fixtures plus independent interoperability tools; cover base-only, unavailable-signing, configured-signing, retained-artifact, and fail-closed installations; make documentation release-blocking; and use behavior-based coverage with no unexplained skips, expected failures, warnings, flaky retries, or arbitrary percentage as a substitute.
- Acceptance round 2: support the current security-supported patch of every tested Plone 6 minor line rather than historical patches or untested future minors; run the complete official Plone/Python intersection matrix on every pull request; test the vendor-patched GnuPG 2.2.27 floor and pinned current upstream GnuPG on the oldest/newest boundaries while using deterministic signing adapters elsewhere; and preserve unsigned platform independence through base-only Windows/macOS smoke jobs plus full Linux integration.
- Acceptance round 3: require functional form coverage plus a semantic headless-browser owner journey; use pinned `DigitalTrustCenter/sectxt` alongside normative local fixtures; exhaustively test permission denials, hostile inputs, traversal/host hardening, CSRF, and secret-safe failures; inject time and exercise revision/transaction races at exact boundaries; let CI build and install distribution artifacts for verification but never publish, while a human builds, checks, hashes, uploads, and post-install-verifies the exact tested tag manually without CI publishing credentials.
- Acceptance round 4: exhaustively verify endpoint states, methods, bytes, headers, validators, expiry-bounded caching, virtual hosting, and optional purging; cover every signing failure category plus real-GnuPG generation, verification, timeout, rotation, retention, and fail-closed paths; test fresh lifecycle and every supported future record/profile migration without upgrade-time signing; make the administrator, REST, deployment, signing, lifecycle, troubleshooting, compatibility, and manual-release documents blocking; and maintain requirement-to-test/manual-check traceability.

## Answer

### Compatibility promise and required CI

A release supports the current security-supported patch of every tested Plone 6 minor line known when that release is prepared—not every historical patch and not an untested future minor. Before each release, the maintainer rechecks the live Plone release schedule and updates constraints, metadata, classifiers, documentation, and CI together. Dropping a line after security EOL or adding a new Plone minor is an explicit documented support-policy change.

On the 2026-08-10 evidence captured in [Release compatibility for `plone.securitytxt`](../research/release-compatibility.md), every pull request must run the complete supported intersection using official per-release constraints:

| Plone | Required Python jobs |
|---|---|
| 6.0.15 | 3.10, 3.11, 3.12, 3.13 |
| 6.1.5 | 3.10, 3.11, 3.12, 3.13 |
| 6.2.1 | 3.10, 3.11, 3.12, 3.13, 3.14 |

Each job logs and asserts its resolved Python, Plone, `Products.CMFPlone`, `plone.restapi`, and relevant optional-dependency versions. An unconstrained installation does not count as coverage for any Plone line. Future minors enter the promise only after their full supported Python intersection passes.

All automatable acceptance checks must run on every pull request; there is no weaker scheduled-only suite. The full behavior suite must run across the Plone/Python matrix, with expensive environment-specific proofs composed rather than multiplied unnecessarily:

- full Plone integration runs on Linux;
- base-only Windows and macOS jobs at the supported Python floor and ceiling build/install the wheel, import every base module without `gnupg`, and run the pure validation/rendering fixtures;
- real signing runs on the oldest Plone/Python boundary with Ubuntu 22.04's vendor-security-maintained GnuPG 2.2.27 package and on the newest boundary with the pinned upstream-current GnuPG release, 2.5.21 at the research date;
- deterministic signing adapters exercise all signing branches throughout the remaining matrix; and
- the semantic headless-browser owner journey runs on both oldest and newest Plone boundaries.

The complete vendor package revision and `gpg --version` are recorded. “Current GnuPG” and the vendor support status of the minimum are rechecked before release. Signing remains Linux-only; unsigned behavior retains its platform-independent claim only while the Windows/macOS smoke jobs pass.

### Test structure and standards fixtures

The authoritative application interface—**inspect**, **evaluate**, **execute**, and **resolve publication**—is the primary test surface, exercised with real site annotations, security principals, clocks, and ZODB transactions. Pure standards validation and deterministic rendering receive focused tests. Classic UI, REST, strict traversal, the warning viewlet, purge integration, and the GnuPG helper receive thin-adapter tests. Tests should not duplicate internal structure or require implementation details to remain fixed.

Version-controlled byte-exact fixtures cover:

- RFC 9116 examples and the product's selected errata behavior;
- every first-class field, ordering and multiplicity rule;
- known, newly registered, unknown, case-varied, singleton, duplicate, and colliding Extension Fields;
- absolute URI schemes, HTTPS requirements, Canonical normalization/mismatch, BCP 47 values, and exact UTC `Z` expiry rendering;
- UTF-8 without BOM, CRLF after every line including the last, deterministic casing/order, dash-sensitive cleartext, and empty/non-ASCII values;
- the 32 KiB unsigned representation, 64 KiB signed artifact, 2,048-character line, and 1,000-line boundaries immediately below, at, and above each limit; and
- malformed UTF-8, control characters, CR/LF injection, hostile names/values, altered armor, truncation, wrong keys, and content mismatch.

Direct local assertions against RFC 9116 and the settled product rules remain normative. A pinned `DigitalTrustCenter/sectxt` validates successful unsigned fixtures independently. Real signed fixtures are verified with GnuPG machine-readable `--status-fd`, requiring the exact signing-subkey fingerprint and SHA-256; recovered cleartext must byte-match the canonical unsigned input. Optional tools and securitytxt.org may be used manually but no live website is a release dependency.

Behavioral coverage is the gate: every specified state, transition, status, failure category, permission path, and migration has an identified scenario. Branch coverage is reported for visibility, but no repository-wide percentage substitutes for the scenario catalogue. Unexplained skips, expected failures, warnings, retries, or flakes fail acceptance.

### Lifecycle, Classic UI, and REST scenarios

Application and adapter tests cover new and incomplete Drafts; valid/invalid saves; validation-only and side-effect-free preview; publishing unsigned and signed policies; enabled-policy edits; rejected edits preserving the old artifact; disabling; approaching expiry; expiry; automatic recovery after correction; corrupt/mismatched artifacts; and operationally blocked publication.

Classic UI functional tests cover all four fieldsets, repeatable add/remove/reorder behavior, lifecycle summary, inline and summarized diagnostics, unsigned preview labels, confirmation for publish/disable, signing capability and identity states, and authorized maintenance links. A real headless browser repeats the critical owner journey without pixel snapshots, asserting semantic labels, focusable actions, confirmations, and visible state. The expiry warning is non-dismissible and appears for authorized users on every supported standard Classic UI page at exactly 30 days before expiry and thereafter; it is absent earlier and for unauthorized users.

REST tests cover:

- `GET @security-policy` state, diagnostics, actions, and revision ETag;
- `PATCH` save without implicit publication;
- side-effect-free, `no-store` preview;
- publish, disable, and test-signing operations;
- structured field/global errors without partial writes;
- required `If-Match`, stale revisions returning `412`, and concurrent clients; and
- semantic parity with the Classic UI for lifecycle, blockers, warnings, expiry, signing, endpoint state, and permitted actions.

An injected clock makes tests deterministic immediately before, exactly at, and immediately after the 30-day warning boundary and expiry instant. Concurrent-update tests cover stale sequential writes, simultaneous ZODB conflicts/retries, signing during a competing edit, and final revision/binding rechecks so only one complete matching policy/artifact commits.

### Permission and security acceptance

The permission matrix proves that anonymous users and ordinary Members cannot discover or mutate management state, while Manager and Site Administrator can by default. Revoking `plone.securitytxt.ManageSecurityPolicy` immediately removes control-panel, REST, and warning access. Classic UI mutations require CSRF protection; REST requires authentication, the dedicated permission, and `If-Match`. Generic `@registry` and `@controlpanels` routes cannot read or change Security Policy persistence.

Traversal tests prove that only the Plone-site-root `.well-known/security.txt` terminal exists: sibling names, extra segments, folder-relative acquisition, legacy paths, and the Zope application root do not expose it. Raw or spoofed forwarding headers are ignored; only Zope/Plone's resolved virtual-host URL participates in Canonical comparison. Unsupported methods and malicious inputs fail without persistence changes.

Anonymous bodies, headers, logs, exceptions, REST diagnostics, and signing status are checked for policy details, profile-file contents, secret material, passphrases, agent data, command lines, environment leakage, and raw GnuPG stderr. Authorized failures expose only the stable category and correlation ID promised by the signing contract.

### Public HTTP and cache acceptance

State-driven integration tests cover anonymous `GET` and `HEAD`, body suppression and `Content-Length`, and exact `200`, `304`, `404`, `405`, and `503` behavior. They assert `Content-Type`, UTF-8 bytes, `X-Content-Type-Options`, `Allow`, `Retry-After`, absent application `Vary`/language/disposition/CORS headers, and generic non-success bodies. Draft, disabled, expired, and Canonical mismatch produce `404`; operational/corrupt enabled states produce `503`; unsupported methods produce `405`.

Conditional requests are evaluated only after current lifecycle, expiry, Canonical, and artifact-binding checks. Tests prove strong content-derived ETags, stable bytes across repeated requests, ETag replacement after publication changes, matching/nonmatching `If-None-Match`, absence of `Last-Modified` and HTTP `Expires`, and `Cache-Control: public, max-age=<min(300, whole seconds to expiry)>, must-revalidate`. Boundary tests prove a response cannot remain fresh past policy expiry; all non-success responses are `no-store`.

VirtualHostMonster and proxy-mounted layouts cover one and multiple Canonical hosts, default-port/IDNA normalization, exact path and percent-encoding behavior, and deployment routing to the origin-root well-known path. With purging absent, all correctness tests still pass. With `plone.cachepurging` configured, accepted publication-affecting transactions emit the correct virtual-host-relative/domain-root paths and send only after successful commit; aborted transactions emit no delivered purge. Delivery failure does not roll back the policy.

### Signing and installation matrix

Every pull request must cover these package/runtime states:

1. base package only: complete unsigned authoring/publication with no `gnupg` import or executable requirement;
2. signing extra installed without a valid profile: unsigned operation remains healthy and signing is Unavailable;
3. valid profile and key: passive checks, test signing, sign-then-verify, artifact binding, and signed publication succeed;
4. valid retained signed artifact after the extra, executable, key, profile file, or agent becomes unavailable: matching bytes remain servable;
5. missing artifact or artifact binding; corrupt, partial, stale, or mismatched artifact data; or an explicitly loaded disabled/revised profile that invalidates the binding: enabled signed publication returns `503` with no stale/unsigned fallback.

Deterministic adapters exercise every stable failure category. Real-GnuPG tests cover exact subkey selection, RSA/key-size/digest policy, expired/revoked/disabled/wrong keys, agent interaction required, malformed output, altered content/armor, output bounds, verification/recovered-content mismatch, and the 30-second timeout terminating the complete process group. Anonymous requests are instrumented to prove they never import GnuPG, read profile configuration, invoke the helper, or contact an agent.

Transition tests cover unsigned-to-signed, signed-to-unsigned without a signer, content/profile changes, expiry correction, and preserved prior publication after a failed signing edit. Planned rotation proves the replacement artifact commits before the old profile is retired and failure leaves the old artifact live. Emergency profile revision or disablement produces `503` until regeneration or a successful unsigned transition. Concurrent signing may duplicate work but cannot expose a partial or mismatched artifact.

### Install, upgrade, and uninstall

The first release must prove fresh profile installation creates one versioned Draft and installs the browser layer, configlet, role mapping, permission, adapters, and endpoint without policy registry records. Reinstall is idempotent and does not duplicate or unexpectedly overwrite state. Uninstall removes registrations, the site annotation, and retained artifacts while leaving deployment-owned configuration, key homes, agents, and secrets untouched; reinstall begins with a new Draft.

Every later release retains fixtures for each persistent-record/profile format it still supports. CI tests oldest-supported-to-current and immediately-previous-release-to-current migrations, including registry/profile imports, role-map changes, configlet changes, normalized fields/order, revisions, statuses, and artifact bindings. Upgrade steps are transactional, idempotent where applicable, and never invoke GnuPG. They deterministically regenerate unsigned artifacts when safe, preserve signed bytes only while their binding and serializer remain accepted, and otherwise enter the explicit operationally blocked state. Failed upgrades roll back cleanly.

### Documentation and manual distribution

Release-blocking documentation consists of:

- an administrator guide for fields, states, validation, warnings, preview, publication, signing selection, and permissions;
- the complete REST resource/operation schemas, diagnostics, status codes, ETags, and `If-Match` contract;
- deployment guidance for origin-root routing, TLS and trusted proxies, VirtualHostMonster, caching/purging, multi-client consistency, and public Canonical URLs;
- signing installation and operations covering the extra, profile schema, permissions, GnuPG/key/agent or hardware setup, capability testing, rotation, emergency withdrawal, backup/destruction responsibilities, and recovery;
- install, upgrade, migration, uninstall/data-loss, compatibility, and release notes;
- troubleshooting keyed to stable categories and correlation IDs without encouraging secret disclosure; and
- a manual release checklist.

CI must build and verify wheel and sdist solely to check metadata, extras, contents, clean-environment installation, and smoke behavior; it never publishes or holds publishing credentials. Distribution is manual. The releaser verifies the live Plone/GnuPG support facts, confirms every required CI job passed on the exact tagged commit, checks documentation/changelog and a clean tree, builds wheel/sdist in a clean environment, validates metadata and contents, installs/tests both variants from the built artifacts outside the checkout, records hashes, and uploads manually. After publication, the releaser verifies index metadata and installs the base and signing variants from the package index.

A maintained scenario catalogue maps every normative behavior from the wayfinding decisions to at least one automated test or an explicitly named manual distribution check. A release is accepted only when the complete matrix is green on the exact tag, every required scenario is accounted for, release documents are complete, and the human distribution checklist is signed off. No CI job uploads, tags, or releases the package.

This closes the remaining compatibility and verification decisions without surfacing another ticket. The map's destination is implementation-ready; implementation task slicing and execution now belong outside this planning effort.
