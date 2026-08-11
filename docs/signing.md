# Optional OpenPGP signing

Install `plone.securitytxt[signing]` on Linux and provide GnuPG 2.2.27 or newer. Set `PLONE_SECURITYTXT_SIGNING_CONFIG` to an absolute path containing integrity-protected JSON:

```json
{"profiles":{"incident-response":{"enabled":true,"revision":"2026-01","gpg":"/usr/bin/gpg","gnupghome":"/run/plone-securitytxt/incident-response","signing_fingerprint":"FULL_40_CHARACTER_V4_SUBKEY_FINGERPRINT"}}}
```

The file contains no secrets. GnuPG homes, private keys, passphrases, agent sockets, PIN handling, backup, revocation, and destruction are deployment responsibilities. Use a dedicated mode-0700 home and provision noninteractive `gpg-agent` or hardware-token access. Never put a passphrase or private key in JSON, ZODB, an environment variable, a form, or a command line.

A management command starts a short-lived helper in a new process group, applies a 30-second deadline, clear-signs with SHA-256 and the exact fingerprint, verifies the signature and recovered cleartext, and then atomically retains the exact bytes. Anonymous requests never invoke GnuPG. Signed mode has no unsigned fallback; matching retained signed bytes remain servable when the signer is temporarily unavailable.

For planned rotation, add a new profile ID and publish with it before retiring the old profile. A disabled profile or in-place revision change is an emergency fail-closed operation and requires regeneration or switching to unsigned mode.
