# Define the Security Policy field model

Type: grilling
Status: resolved
Blocked by: 01 — [Establish the security.txt standards baseline](01-establish-standards-baseline.md)

## Question

What is the complete product-level model for a Security Policy? Decide the supported standard fields, multiplicity and ordering, URI and language validation, explicit expiry rules, Canonical handling, repeatable Extension Field constraints, draft-versus-published transitions, and which conditions are errors versus warnings. Keep the answer independent of a particular Plone storage schema.

## Answer

### Field model

The Security Policy provides first-class structured values for the eight fields defined directly by RFC 9116:

- `Contact`: ordered, repeatable, and required for publication. Order expresses contact preference.
- `Expires`: exactly one value, required for publication.
- `Encryption`, `Acknowledgments`, `Canonical`, `Policy`, and `Hiring`: optional and repeatable.
- `Preferred-Languages`: one optional list containing one or more BCP 47 tags. The list order is preserved for deterministic output, but every language has equal semantic priority.

`CSAF`, `Bug-Bounty`, later IANA registrations, and unregistered names all use ordered Extension Field rows rather than first-class controls. Each row contains one field name and one single-line value.

The add-on ships a release-versioned, offline snapshot of known IANA field rules. Known Extension Fields receive their registered value and multiplicity validation. It never contacts IANA during save or publication. An unknown but syntactically valid name is allowed with a non-blocking warning, so newly registered fields remain immediately usable before an add-on release recognizes them.

Extension Field names are compared case-insensitively. They must satisfy the RFC field-name grammar and must not collide with a first-class field. Values must be nonempty, single-line, valid text. Repeatable fields preserve entered order, but an identical value may not appear twice under the same case-insensitive field name. Known singleton extensions cannot repeat.

### Value validation

URI-valued fields accept any syntactically valid absolute RFC 3986 URI rather than using a small scheme allowlist. A web URI must use HTTPS wherever RFC 9116 requires it, so `http:` is rejected while legitimate non-web schemes such as `mailto:`, `tel:`, `dns:`, and `openpgp4fpr:` remain available. Validation is syntactic only: saving or publishing a Security Policy never makes outbound requests to referenced resources.

Canonical values are an explicit, ordered list of stable, owner-approved URLs. Each must be an absolute HTTPS URL, contain no credentials, query, or fragment, and point to a `/.well-known/security.txt` path. Values are never derived dynamically from the request host. Canonical remains optional for unsigned publication. Enabling signing requires at least one Canonical value that matches an authoritative public endpoint configured for the site; this is an intentional product rule stronger than RFC 9116's recommendation.

Preferred language tags must be valid BCP 47 tags. Empty and case-insensitive duplicate tags are errors; valid entered order is preserved without implying priority.

Expires represents an exact instant and is rendered in UTC with uppercase `Z`. Publication requires a future instant. A value more than one year ahead is allowed with a warning because the RFC's one-year horizon is a recommendation. The fixed approaching-expiry window begins 30 days before expiry.

### Draft and publication lifecycle

A new or publication-disabled Security Policy is Draft. A Draft may omit publication-required values and may exceed publication interoperability limits, but every populated value must be individually well-formed. Malformed URIs, field names, language tags, singleton violations, and duplicate values are rejected even in Draft.

Enabling publication validates the complete policy atomically. Missing required values, expired values, a missing matching Canonical when signing is enabled, or exceeded publication limits prevent the transition and leave the policy Draft. While publication remains enabled, edits that would make the policy invalid are rejected; there is no separate staged draft alongside a live version.

A valid publication-enabled policy is Published. A condition that becomes false without an accepted edit—initially expiry, with operational signing failures defined by the signing contract—changes the effective state to Publication Blocked while preserving the owner's publication intent. Correcting the blocker restores Published automatically. Explicitly disabling publication always returns the policy to Draft.

### Errors, warnings, and limits

Structural value errors reject saving. Publication-completeness errors may exist in Draft but block publication. Non-binding RFC guidance produces warnings rather than blockers, including:

- expiry more than one year ahead;
- expiry within 30 days;
- an unregistered Extension Field;
- omitted recommended information such as Canonical or Policy; and
- an email Contact without Encryption information.

These advisories appear in the control panel. Only approaching or passed expiry produces the persistent site-wide warning for authorized administrators.

Publication is blocked when the generated unsigned representation exceeds 32 KiB, any generated field line exceeds 2,048 characters, or the representation exceeds 1,000 lines. Draft may retain content that exceeds these limits so the owner can correct it.

### Ordering and authoring boundary

Rendering uses this deterministic first-class field order: `Contact`, `Expires`, `Encryption`, `Acknowledgments`, `Preferred-Languages`, `Canonical`, `Policy`, `Hiring`. Values within repeatable fields preserve their entered order. Extension Fields follow all first-class fields and preserve their global row order.

The model does not support arbitrary comments, blank-line authoring, or raw-file editing.
