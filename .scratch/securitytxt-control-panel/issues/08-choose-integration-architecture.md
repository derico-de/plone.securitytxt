# Choose the Plone integration architecture

Type: grilling
Status: resolved
Blocked by: 02 — [Define the Security Policy field model](02-define-policy-field-model.md); 03 — [Define publication and HTTP semantics](03-define-publication-http-semantics.md); 04 — [Prototype the owner control-panel experience](04-prototype-control-panel.md); 06 — [Define the optional signing contract](06-define-signing-contract.md); 07 — [Confirm the Plone integration seams](07-confirm-plone-integration-seams.md)

## Question

Which Plone module boundaries and integration design produce the specified behavior with the least coupling? Decide the deep interfaces between policy storage and validation, deterministic rendering, publication, signing, control-panel and REST adapters, permission checks, site-wide expiry warnings, and cache invalidation. Identify the `plonecli` artifacts, GenericSetup and upgrade responsibilities, optional-extra boundaries, and any trade-off significant enough to record as an ADR.

## Comments

- Architecture round 1: use one dedicated site-local persistent Security Policy object; place all mutations behind one deep application module; expose a dedicated permission-protected REST resource rather than generic registry/control-panel mutation; keep GnuPG integration behind the optional signing adapter while artifact serving remains in the base package; treat active proxy purging as optional best-effort acceleration; and remove policy data and retained artifacts on uninstall.
- Architecture round 2: expose explicit inspect, evaluate/preview, command, and publication operations rather than stored-object CRUD; persist one versioned record in a namespaced site-root annotation; use domain-specific REST operations with revision ETags and required `If-Match`; enforce the dedicated permission both at Plone registrations and management entry points; and synchronously validate, render when publication requires it, optionally sign-and-verify, recheck revision, commit atomically, then perform commit-aware invalidation/purging.
- Architecture round 3: retain and bind exact public bytes in both signed and unsigned modes; publish through a strict site-root `.well-known` namespace object accepting only `security.txt`; expose dedicated read, save, preview, publish, disable, and test-signing REST operations; scaffold and adapt a standard control panel rather than using registry persistence; and keep the permission-gated expiry viewlet presentation-only by sourcing its state from the application interface.
- Architecture round 4: expose one cohesive policy package with thin Plone adapters; use `plone.securitytxt.ManageSecurityPolicy` throughout management surfaces; create the Draft record on install and remove it on uninstall; never invoke signing during upgrades; avoid an additional process-local response cache; and record the authoritative-module and retained-artifact trade-offs as ADRs.

## Answer

### Authoritative application module

One deep policy application module is the only supported way to inspect or change a Security Policy. Its conceptual interface has four operations:

- **inspect** returns the saved values, lifecycle and endpoint state, warnings and blockers, signing capability/status, permitted actions, and opaque policy revision;
- **evaluate** validates candidate values and optionally returns the deterministic unsigned preview without persistence or signing;
- **execute** accepts a typed command—save, publish, disable, or test signing—plus the expected revision, and returns the resulting management state;
- **resolve publication** returns the current exact artifact or a sanitized unavailable/not-found result after checking lifecycle, expiry, Canonical URL, signing-profile metadata, and artifact binding.

The interface never exposes the persistent object or generic field-level storage operations. Validation, lifecycle calculation, deterministic rendering, artifact binding, persistence, and audit-status updates remain implementation details. The Classic UI, REST, warning, and public publisher are thin adapters to this interface rather than independent implementations of policy rules.

Every management operation checks the dedicated `plone.securitytxt.ManageSecurityPolicy` permission inside the application module as well as at its Plone registration. The public publication operation is deliberately anonymous. `rolemap.xml` grants the dedicated permission to Manager and Site Administrator by default.

### Persistence and atomic changes

Each Plone site owns one explicitly versioned persistent record in a namespaced annotation on `IPloneSiteRoot`. The record contains normalized policy values and ordering, publication intent, revision, publication mode and selected Signing Profile, exact retained publication bytes, their binding and ETag, and the current signing/audit status defined by the signing contract. It contains no deployment secret. No policy values are registered as `plone.registry` records, so generic `@registry` and `@controlpanels` mutation cannot bypass the application interface.

Both unsigned and signed publication modes retain the exact bytes that will be served whenever a public representation is created or replaced. Draft-only saves validate and persist candidate values without creating a new publication artifact; selecting signed mode on a Draft never invokes the signer. An unsigned publication transition or accepted edit to an enabled unsigned policy renders and binds the artifact before commit. Signed artifacts are generated only for the publication transitions and enabled-policy changes enumerated by the signing contract, using its bounded sign-and-verify flow. A mutating operation then rechecks its expected revision and commits the policy, revision, any new artifact and binding, and status atomically in one ZODB transaction. Validation, signing, verification, revision mismatch, or conflict before commit leaves the previous record and public artifact unchanged. Duplicate work caused by a transaction retry is tolerable, but a stale REST client receives `412 Precondition Failed` rather than overwriting a newer revision.

No separate process-local response cache is needed. During a successful state-changing request, an optional cache-purge adapter may emit a purge event whose virtual-host-aware paths include `.well-known/security.txt`; `plone.cachepurging` queues it when configured and sends it only after the request transaction succeeds. Purging is an acceleration only: its absence or failure does not fail the policy mutation, and the already-decided five-minute, expiry-bounded HTTP freshness contract remains authoritative.

### Plone adapters

**Classic UI:** Start with `plonecli add controlpanel --defaults -d controlpanel_name="SecurityPolicy" -d controlpanel_title="Security Policy"`, then adapt the generated standard `z3c.form` to the application interface instead of `RegistryEditForm` persistence. The configlet and form use the dedicated permission. The selected guided fieldsets, lifecycle summary, validation, preview, and explicit publication actions remain as specified by the prototype.

**REST:** Start with `plonecli add restapi_service --defaults -d service_name="security-policy" -d service_for="Products.CMFPlone.interfaces.IPloneSiteRoot" -d http_get=true -d http_patch=true -d http_post=true` and adapt the scaffold into the dedicated permission-protected resource:

- `GET @security-policy` returns management state and a revision ETag;
- `PATCH @security-policy` saves candidate fields without implicitly publishing;
- `POST @security-policy/preview` validates and returns an unsigned, side-effect-free, `no-store` preview;
- `POST @security-policy/publish` enables publication;
- `POST @security-policy/disable` disables publication; and
- `POST @security-policy/test-signing` performs the bounded capability test.

Every mutating operation requires `If-Match`; field and global validation failures use structured diagnostics and never partially persist. These dedicated operations, not generic control-panel or registry endpoints, are the supported frontend-independent contract.

**Public endpoint:** Register a browser traversal object named `.well-known` for `IPloneSiteRoot`. It accepts only the terminal `security.txt` segment and rejects siblings and further traversal, preventing acquisition-created variants. The terminal publisher accepts anonymous `GET` and `HEAD`, delegates state and artifact resolution to the application module, and maps the result to the already-decided HTTP status, conditional-request, header, and generic-error contract. It uses Plone/Zope's externally resolved virtual-host URL for Canonical matching and registers nothing at the Zope application root.

**Expiry warning:** Start with `plonecli add viewlet --defaults -d viewlet_name="securitypolicywarning" -d viewlet_class_name="SecurityPolicyWarning" -d viewlet_manager="plone.portalheader"` in the global Classic UI header manager. Its registration and application query use the dedicated permission. It renders only the warning state, countdown, and control-panel link returned by **inspect**; it does not read persistence, calculate lifecycle, or invoke signing itself.

**Signing:** The base package owns Signing Profile public types, capability/status values, artifact binding and validation, and serving retained artifacts. The `signing` extra adds `python-gnupg`; only a lazily loaded adapter and its bounded helper process import or execute it. Base-only installations never import `gnupg`, while a matching retained signed artifact remains servable without currently available signing support, as defined by the signing contract.

### Profiles, upgrades, and uninstall

The default GenericSetup profile installs the browser layer, control-panel registration, dedicated role mapping, and profile metadata. An install handler creates one empty versioned Draft record; reads never create persistent state. ZCML declares the permission and component registrations. There is no policy `registry.xml` schema.

Any installed-site change to profile data or record format starts from `plonecli add upgrade_step --defaults -d upgrade_step_title="<migration title>"`. Each focused step migrates transactionally and has an existing-site test. Upgrade code never invokes GnuPG: it may deterministically regenerate unsigned artifacts, retains signed bytes when their binding remains valid and their serializer remains supported, and otherwise marks signed publication operationally blocked until an authorized regeneration succeeds.

The uninstall profile removes the configlet, browser-layer and role registrations, and its handler deletes the site annotation and all retained artifacts. Deployment-owned Signing Profiles, key homes, agents, and secrets are never modified. The exact supported Plone/Python matrix, compatibility CI, upgrade fixtures, and administrator/deployment documentation are carried into [Define release acceptance and compatibility](09-define-release-acceptance.md).

### Architecture records

- [Place the Security Policy behind an authoritative application module](../../../docs/adr/0001-authoritative-security-policy-application-module.md) records why a dedicated site annotation and application interface replace conventional registry CRUD.
- [Retain exact publication artifacts](../../../docs/adr/0002-retain-exact-publication-artifacts.md) records why rendering and optional signing happen on accepted writes rather than anonymous requests.

This architecture resolves the remaining integration choices without surfacing another independent decision ticket. Implementation sequencing is a handoff concern beyond this planning map; installation, upgrade, verification, compatibility, and documentation acceptance are already covered by [Define release acceptance and compatibility](09-define-release-acceptance.md).
