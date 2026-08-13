# Domain glossary

## Security Policy

The single, language-independent set of security contact and disclosure information for a Plone site from which its `security.txt` representation is generated.

## Draft Security Policy

A saved Security Policy that is not publicly available and may be incomplete.

## Published Security Policy

A valid Security Policy that the website owner has explicitly enabled and that is currently available to the public. Disabling publication returns it to draft status.

## Publication-Blocked Security Policy

A Security Policy for which the website owner still intends publication but which cannot currently be made public because a required publication condition is no longer met, such as expiry. Correcting the blocking condition restores published status; disabling publication returns it to draft status.

## Signing Profile

A named, deployment-operator-controlled identity for one permitted OpenPGP signer, with a stable identifier and revision. A website owner may select or enable an available Signing Profile but cannot change which signer it denotes.

## Signed Publication Mode

A website-owner-selected publication mode in which the public Security Policy representation must be a Signed Publication Artifact produced by the selected Signing Profile; it never permits unsigned fallback.

## Signing Capability

The evaluated availability of a Signing Profile: Unavailable when required support is absent or invalid, Configured when its identity and prerequisites are recognized, and Verified after it successfully produces a verified test signature.

## Signed Publication Artifact

The exact public OpenPGP clear-signed bytes produced and verified from a Security Policy, retained atomically and bound to the policy content and Signing Profile inputs that produced it. It is served without invoking the signer until a publication input requires regeneration.
