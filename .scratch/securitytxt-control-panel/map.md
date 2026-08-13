# Chart an implementation-ready Plone security.txt specification

Type: wayfinder:map
Status: resolved

## Destination

An implementation-ready specification for a Plone control panel that manages a site-wide Security Policy, publishes an RFC-compliant `/.well-known/security.txt`, and optionally clear-signs it when signing support is installed. The specification must settle UX, validation, permissions, REST exposure, HTTP behavior, expiry warnings, signing, packaging, compatibility, and verification.

## Notes

- This is a planning effort; implementing the add-on is outside this map.
- Consult `/grilling` and `/domain-modeling` for product decisions, `/research` for external standards and dependencies, `/prototype` for owner-facing UX, and `/plonecli` before specifying Plone artifacts.
- Support the current security-supported patch of every tested Plone 6 minor line and keep the public endpoint frontend-independent.
- Maintain one language-independent Security Policy per Plone site.
- Allow incomplete drafts, but require explicit enablement and successful validation before publication.
- Provide structured standard fields plus repeatable, validated Extension Fields; do not provide raw-file editing.
- Grant management through a dedicated permission, defaulted to Manager and Site Administrator; published output is anonymous.
- Keep the Classic UI control panel simple and standard with `z3c.form`; do not introduce custom control-panel views or a custom Volto UI. Preserve a `plone.restapi`-aware contract without building a separate frontend.
- Serve the endpoint at the Plone site root and document reverse-proxy routing when the public site is mounted below the origin root.
- Require an explicit expiry. Show authorized administrators a persistent site-wide warning on every page from 30 days before expiry and after expiry; do not send email or run notification jobs.
- Make OpenPGP clear-signing optional through a `signing` package extra. Keep private keys and passphrases in deployment-managed secrets, replace the public representation with the signed form when enabled, and fail closed rather than silently downgrading.

## Decisions so far

<!-- Closed-ticket answers are indexed here by ticket name and link. -->

- [Establish the security.txt standards baseline](issues/01-establish-standards-baseline.md) — RFC 9116 plus the live IANA registry define the protocol baseline; securitytxt.org is a structured-generator UX reference, while caching, extension handling, and stronger signing invariants remain product choices.
- [Define the Security Policy field model](issues/02-define-policy-field-model.md) — Use structured RFC 9116 fields plus validated, forward-compatible Extension Fields, with explicit lifecycle states, deterministic ordering, strict value validation, and warnings separated from publication blockers.
- [Define publication and HTTP semantics](issues/03-define-publication-http-semantics.md) — Serve one anonymous, deterministic well-known representation with explicit state/status behavior, Canonical host enforcement, strong ETag validation, expiry-bounded caching, and a deployment-owned proxy/TLS boundary.
- [Prototype the owner control-panel experience](issues/04-prototype-control-panel.md) — Use a single standard guided `z3c.form` page with four fieldsets, a top lifecycle summary, inline plus summarized validation, side-effect-free preview, explicit publication actions, and permission-gated maintenance states.
- [Evaluate OpenPGP signing approaches](issues/05-evaluate-openpgp-approaches.md) — Prefer optional `python-gnupg` plus deployment-managed GnuPG behind an adapter, while retaining exact signed artifacts and keeping all private keys and passphrase handling outside Plone.
- [Define the optional signing contract](issues/06-define-signing-contract.md) — Use Linux-only deployment-owned Signing Profiles, bounded sign-then-verify generation, atomically retained artifacts, simple standard control-panel controls, explicit rotation and invalidation, and no unsigned failover.
- [Confirm the Plone integration seams](issues/07-confirm-plone-integration-seams.md) — Plone 6 supplies supported control-panel, REST, permission, traversal, registry, viewlet, purge, and upgrade seams, while the generic REST permission boundary and other integration choices must be resolved explicitly by the architecture.
- [Choose the Plone integration architecture](issues/08-choose-integration-architecture.md) — Put one versioned site record behind an authoritative application module, retain exact artifacts on publication writes, and connect Classic UI, dedicated REST, strict well-known traversal, warning, signing, and optional purge adapters through that seam.
- [Define release acceptance and compatibility](issues/09-define-release-acceptance.md) — Require the full supported Plone/Python matrix and every automatable behavior gate on each pull request, independent protocol/signature checks, exhaustive security/lifecycle/upgrade coverage, blocking documentation, and a human-only verified distribution process.

## Not yet specified

<!-- No remaining fog. -->

## Out of scope

- Implementing the add-on during this planning effort.
- Detailed implementation task slicing and execution after the specification handoff.
- A checker or validator for arbitrary external website URLs.
- Arbitrary raw `security.txt` editing.
- A custom Volto control-panel frontend.
- Scheduled email or background expiry notifications.
- S/MIME, SSH, or bespoke signature formats.
- Storing private keys or passphrases in Plone.
- Modifying the Zope application root or automatically configuring the deployment reverse proxy.
