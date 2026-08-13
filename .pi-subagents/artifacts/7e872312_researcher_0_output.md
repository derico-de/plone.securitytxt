Created `.scratch/securitytxt-control-panel/research/securitytxt-standards-baseline.md`.

Strongest conclusions:
- RFC 9116 requires one or more `Contact` fields and exactly one unexpired `Expires`; other registered fields are optional.
- HTTPS `/.well-known/security.txt`, UTF-8 `text/plain`, bounded cache freshness, and correct redirect/status handling form the publication baseline.
- OpenPGP signing is optional, but signed files require a matching `Canonical`.
- The document separates RFC requirements from securitytxt.org generator conveniences and identifies 12 remaining product decisions.

Source gap: live web retrieval was unavailable, so current errata status and the generator’s exact deployed controls should be rechecked before implementation.