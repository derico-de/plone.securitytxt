# Establish the security.txt standards baseline

Type: research
Status: resolved

## Question

What normative requirements from the current `security.txt` standard and what authoring/generation capabilities from securitytxt.org must the Plone specification preserve? Produce a linked Markdown research asset covering field syntax and multiplicity, expiry, canonical URLs, extension fields, comments and ordering, endpoint discovery, media type and encoding, redirects and HTTP behavior, caching considerations, and OpenPGP clear-signing requirements. Distinguish standards requirements from securitytxt.org conveniences and identify any compatibility choices that still require owner input.

## Answer

Resolved in [security.txt standards baseline](../research/securitytxt-standards-baseline.md).

RFC 9116 requires at least one `Contact`, exactly one `Expires`, the HTTPS `/.well-known/security.txt` location, and UTF-8 `text/plain`. The current IANA registry adds `CSAF` and `Bug-Bounty` to the RFC's initial fields. The live securitytxt.org generator exposes structured controls for the RFC fields plus `CSAF`, but not `Bug-Bounty`, arbitrary raw editing, or server-side signing.

OpenPGP clear-signing and using `Canonical` with a signature are RFC recommendations rather than requirements. The Plone product can intentionally enforce stronger publication rules. Caching, deterministic serialization, extension-field policy, legacy-path support, Canonical derivation, and exact signing invariants remain explicit product decisions assigned to later tickets.

The research also records the live RFC errata status: one verified editorial correction and two reported technical corrections concerning uppercase `Z` and line-ending grammar.
