# Evaluate OpenPGP signing approaches

Type: research
Status: resolved
Blocked by: 01 — [Establish the security.txt standards baseline](01-establish-standards-baseline.md)

## Question

Which maintained OpenPGP approach is suitable for optional standards-compliant clear-signing in a Plone add-on? Produce a linked Markdown research asset comparing viable Python libraries and external `gpg` integration across supported Python and Plone versions, including maintenance, licensing, packaging weight, subprocess and sandbox implications, key selection, passphrase handling, deterministic output, interoperability, error reporting, and testability. Recommend a dependency arrangement for the `signing` extra without storing secrets in Plone.

## Answer

Resolved in [OpenPGP signing approaches for `plone.securitytxt`](../research/openpgp-signing-approaches.md).

The recommended starting point is `python-gnupg>=0.5.6,<0.6` in the optional `signing` extra, behind a narrow internal adapter and backed by a deployment-supplied, vendor-supported GnuPG executable. Direct `gpg` integration remains the fallback if the signing contract requires hard timeout and cancellation control that `python-gnupg` does not expose; GPGME is technically strong but too heavy for one clear-sign operation, while PGPy is rejected because of stale maintenance, its RFC 4880 focus, and in-process secret handling.

Plone stores only the selected full fingerprint, public signing metadata, and the generated public clear-signed artifact. Operators provision the private key and noninteractive passphrase availability through a dedicated external `GNUPGHOME` and `gpg-agent` or hardware token. Signing uses canonical unsigned bytes, exact fingerprint selection, sign-then-verify, and fail-closed errors. Since signatures contain creation-time and sometimes random inputs, byte identity comes from atomically retaining and re-serving one generated artifact rather than independently reproducing the same signature.

The exact GnuPG version range, timeout/isolation choice, key profile, activation checks, rotation workflow, and multi-instance locking remain product decisions for [Define the optional signing contract](06-define-signing-contract.md).
