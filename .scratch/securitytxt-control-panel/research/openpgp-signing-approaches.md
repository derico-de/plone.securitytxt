# OpenPGP signing approaches for `plone.securitytxt`

Research date: **2026-08-08**

## Answer in brief

Use maintained **`python-gnupg` 0.5.x as the Python dependency in a `signing` extra, backed by a deployment-supplied, vendor-supported GnuPG executable and a dedicated external `GNUPGHOME`/`gpg-agent`**. It is the best fit here because it delegates RFC 4880 clear-sign formatting and interoperability to GnuPG, is a small BSD-licensed Python wrapper, supports every Python version in this repository, and avoids the build and image complexity of GPGME. Direct `subprocess` integration has the same runtime dependency but would make this add-on own GnuPG's status protocol and process plumbing; GPGME is stronger as a general native API but disproportionately heavy; PGPy is not recommended because its last stable release is from 2022, it is RFC-4880-oriented rather than RFC-9580-current, and it requires secret key and passphrase material inside the Plone Python process.

The add-on must store **neither private keys nor passphrases in Plone/ZODB**. Plone configuration should contain only an enabled flag and a full signing-key fingerprint. Operations must provide a dedicated key home or agent/socket outside the site database, with passphrase availability managed by `gpg-agent` (or a hardware-backed key). Signing should happen when publication inputs change, not on an anonymous request, and the exact resulting public clear-signed bytes should be cached/persisted as the publication artifact because OpenPGP signatures contain creation time and cannot generally be reproduced byte-for-byte later.

## Settled local constraints

These are verified repository facts, not new recommendations:

- [`pyproject.toml`](../../../pyproject.toml) requires Python `>=3.10`, classifies Python 3.10–3.12, targets Plone 6.0+, and licenses the add-on GPL-2.0-or-later. An optional signer must therefore work on at least Python 3.10–3.12 and be GPL-compatible.
- The [standards baseline](securitytxt-standards-baseline.md) establishes that RFC 9116 **recommends but does not require** OpenPGP cleartext signing; the complete clear-signed document is served, not a `Signature` field. It also settles that dash escaping and text canonicalization should be delegated to an OpenPGP implementation.
- Issue 03's resolved [publication contract](../issues/03-define-publication-http-semantics.md) requires canonical unsigned UTF-8 bytes with CRLF and a final line ending; signing failure yields `503` with no unsigned fallback; unchanged signing inputs must serve byte-identical output; and signing configuration/key changes invalidate the rendered representation.

## Verified comparison

| Approach | Maintenance and compatibility | Runtime/package weight | Secret and signing model | Errors, concurrency, testing | Assessment |
| --- | --- | --- | --- | --- | --- |
| **`python-gnupg` 0.5.6 + GnuPG** | 0.5.6 was released 2025-12-31 after 0.5.5 on 2025-08-04; current docs dated 2026-05-10 state Python >=3.6. PyPI reports BSD licensing. This covers Python 3.10–3.12 and is GPL-2.0-or-later compatible. [PyPI](https://pypi.org/project/python-gnupg/) [official repository](https://github.com/vsajip/python-gnupg) [docs](https://gnupg.readthedocs.io/) | Small Python wrapper, but **not pure-Python OpenPGP**: starts an installed `gpg` process and uses its key home/agent. No extension build. Deployment must install and patch GnuPG separately. | `sign(..., keyid=..., clearsign=True)` delegates clear-signing to GnuPG. The API also accepts a passphrase, but this product should not use that path. A dedicated `GNUPGHOME`, full fingerprint, and external agent keep secret material outside Plone. [source API](https://github.com/vsajip/python-gnupg/blob/master/gnupg.py) | Result objects expose status/stderr/return code derived from GnuPG output, but the adapter must convert them to a small stable product error taxonomy and redact diagnostics. The wrapper has no public operation-timeout parameter: callers needing a hard deadline must isolate it in a killable helper process or accept that limitation; this must be settled and tested before implementation. The wrapper/process boundary is mockable; real interoperability still requires integration tests with `gpg`. Shared home/agent access and duplicate signing should be serialized by the application. | **Recommended**, behind a narrow local adapter; pin compatible 0.5.x and separately check the `gpg` runtime/version. |
| **Direct external `gpg` via `subprocess`** | GnuPG is the reference implementation used for real-world interoperability and is actively released; upstream lists 2.5.21 as stable as of 2026-07-02 and lists 2.4 as end-of-life on 2026-06-30. It is a separate GPL program, compatible with this GPL-2.0-or-later project. [downloads](https://www.gnupg.org/download/) [news](https://www.gnupg.org/news.html) | No Python package, but the same executable, libraries, key home, agent, process, filesystem, and socket requirements as `python-gnupg`. | `--clearsign`, `--local-user`, `--batch`, `--no-tty`, and a dedicated home provide the needed mechanics. Machine-readable status belongs on `--status-fd`; stderr is not a stable API. [GnuPG 2.4 manual](https://www.gnupg.org/documentation/manuals/gnupg24/gpg.1.html) | Maximum control over argv, FDs, timeout, output limit, and cancellation, but the add-on must correctly implement status-FD parsing, FD separation across platforms, process cleanup, version variance, and agent interaction. Easy to fake at a process boundary but more security-sensitive code to own. | **Viable fallback, not preferred**. Saving one small wrapper dependency does not remove GnuPG and shifts protocol/process maintenance into the add-on. |
| **Official GPGME Python bindings (`gpg`)** | PyPI lists `gpg` 2.0.0, released 2026-05-07, Python >=3.6, with the binding/library classified as LGPL-2.1-or-later and tests/examples described as GPL-2.0-or-later. These are compatible with Python 3.10–3.12 and this project's license. GPGME is the official high-level GnuPG API. [PyPI](https://pypi.org/project/gpg/) [GPGME manual](https://www.gnupg.org/documentation/manuals/gpgme/) | Native binding plus GPGME and its development/runtime libraries, and GnuPG engines underneath. Building/installing is materially heavier than a pure Python wrapper and complicates slim/multi-platform Plone images. Historical upstream guidance also cautions that PyPI packaging was not the recommended installation route, so distribution provenance must be validated for each target image. [GnuPG Python-bindings announcement](https://gnupg.org/blog/20160921-python-bindings-for-gpgme.html) | First-class contexts, selected signers, armor and clear-sign mode; secret operations still use the GnuPG key store/agent. Better typed GPGME errors than CLI stderr. | GPGME documents multithreading precautions; contexts should not be shared concurrently. Native calls and engine processes are harder to fake and require system integration tests. [threading overview](https://www.gnupg.org/documentation/manuals/gpgme/Overview.html) | **Technically strong but disproportionate** for one clear-sign operation. Reconsider only if the add-on later needs broad OpenPGP operations and can own native packaging. |
| **PGPy 0.6.0** | Last stable release was 2022-11-23; PyPI says Python >=3.6 and BSD-3-Clause, so declared Python/license compatibility is acceptable, but release recency is not. The project describes conformance to RFC 4880 and does not claim RFC 9580 support. [release](https://github.com/SecurityInnovation/PGPy/releases/tag/v0.6.0) [PyPI](https://pypi.org/project/PGPy/) [repository](https://github.com/SecurityInnovation/PGPy) | Python package with `cryptography`, whose wheels include native code; no external `gpg`, key home, agent, or subprocess. This is operationally compact when supported wheels exist, but the application assumes more OpenPGP implementation risk. | Can construct cleartext `PGPMessage`s, canonicalize/dash-escape their text, and sign them. Protected keys are loaded and unlocked with a passphrase in Python objects, directly exposing key/passphrase material to the long-lived Plone process. [official examples](https://pgpy.readthedocs.io/en/latest/examples.html) | Python exceptions and in-process calls are easy to unit-test and lock around. Cross-implementation tests remain mandatory; its changelog records prior cleartext parsing and GPG interoperability fixes. [changelog](https://pgpy.readthedocs.io/en/latest/changelog.html) | **Reject for this product**: stale stable release, no RFC 9580 claim, and the wrong secret-isolation model. |

No maintained, mature Python binding for Sequoia or RNP was found with primary-source evidence strong enough to add as a production candidate. That is an evidence gap, not proof none exists.

## Clear-sign mechanics and interoperability

### Verified protocol facts

RFC 9116 §2.3 points specifically to the OpenPGP cleartext framework and makes signing optional. A clear-signed representation contains the signed-message header, `Hash` armor header, empty line, dash-escaped cleartext, and armored signature. RFC 4880 §7 requires lines beginning with `-` to be dash-escaped and hashes text after canonicalizing line endings to CRLF; the line ending immediately before the signature armor is not signed. [RFC 9116 §§2.3 and 2.7](https://www.rfc-editor.org/rfc/rfc9116.html#section-2.3) [RFC 4880 §7](https://www.rfc-editor.org/rfc/rfc4880.html#section-7)

RFC 9580 obsoletes RFC 4880 and retains a cleartext signature framework, while RFC 9116 still normatively cites RFC 4880. RFC 9580 introduces newer packet/key formats, but deployed security.txt verifiers cannot be assumed to implement all of them. [RFC 9580 §§6.2 and 7](https://www.rfc-editor.org/rfc/rfc9580.html#section-7)

### Product profile (recommendation)

- Feed the already-canonical unsigned UTF-8 bytes to GnuPG and use its clear-sign mode; never hand-build armor, dash escaping, or signature packets.
- Select the configured signer by **full fingerprint**, not email, user ID, short/long key ID, or GnuPG's default key. Validate at activation and again at signing that exactly the intended, non-revoked, non-expired, signing-capable secret key/subkey is available. GnuPG's `--local-user` syntax can force a particular key; an exclamation suffix forces the exact specified primary/subkey rather than automatic subkey selection. [GnuPG key options](https://www.gnupg.org/documentation/manuals/gnupg/GPG-Key-related-Options.html)
- For widest RFC-4880-era verifier interoperability, document a conservative deployment profile: a v4 RSA signing key/subkey (at least 3072 bits) with SHA-256. This is a product interoperability recommendation, **not** an RFC 9116 requirement and not a claim that newer RFC 9580 algorithms are insecure.
- Independently verify generated fixtures with a second GnuPG invocation and inspect that the recovered cleartext equals the canonical policy text. Do not post-process GnuPG's armor or line endings. RFC 9116 permits LF or CRLF, and implementations may serialize armor differently even though signed text hashing canonicalizes to CRLF.

### Deterministic-output limit

OpenPGP signature packets normally carry a signature-creation-time subpacket; thus signing identical text at a later instant can produce different public bytes. Armor headers, algorithm/subpacket choices, signing subkey selection, and implementation upgrades can also change bytes. Some signature algorithms may use per-signature randomness. `gpg --faked-system-time` exists for testing, not as a sound production determinism mechanism. [RFC 4880 §5.2.3.4](https://www.rfc-editor.org/rfc/rfc4880.html#section-5.2.3.4) [GnuPG manual](https://www.gnupg.org/documentation/manuals/gnupg24/gpg.1.html)

Therefore deterministic *regeneration* is not a valid requirement. To meet issue 03's byte-identity contract, create one clear-signed artifact when policy/signing inputs transition, atomically retain those exact non-secret bytes, and serve them unchanged until invalidated. A process-local cache alone is insufficient across restarts. A key/algorithm/GnuPG upgrade intentionally invalidates and re-signs. The ETag is derived from the retained served bytes.

## Deployment-secret contract

The following is a product recommendation designed to keep secrets out of Plone:

1. **Plone/ZODB stores only:** signing enabled/disabled state; the full public fingerprint (and, if deliberately pinning a signing subkey, its full fingerprint); and public metadata needed to invalidate the artifact. It may store the generated clear-signed artifact because that artifact is public. It stores no private-key export, passphrase, agent token, or secret-file contents.
2. **Deployment supplies:** a vendor-supported `gpg` executable (the upstream-supported baseline at this research date is GnuPG 2.5.x; downstream-maintained older builds require an explicit compatibility decision and CI evidence), a dedicated absolute `GNUPGHOME` owned by the Plone service UID with mode 0700, and the private signing key or hardware-token stubs. The home must not be shared with an administrator's general keyring.
3. **Passphrases:** use a deployment-managed `gpg-agent`/hardware token and arrange noninteractive availability before enabling publication. The add-on does not accept a passphrase field, environment variable, command-line argument, or Python API value. It does not enable loopback pinentry. If the agent cannot sign without interaction, signing fails closed and the endpoint follows issue 03's `503` contract. This avoids command-line/process-environment disclosure and Python string retention. Agent caching is an operational security tradeoff and must be documented by the deployer. [GnuPG agent options](https://www.gnupg.org/documentation/manuals/gnupg/Agent-Options.html)
4. **Containers/sandboxes:** mount the dedicated home read-write (GnuPG needs lock/state files) or mount/connect a correctly permissioned agent socket and token setup; run under a stable UID; include GnuPG and its helper binaries in the image; permit process creation, Unix sockets, and required filesystem operations in seccomp/AppArmor/systemd policy. Do not mount the key home into unrelated web containers. A read-only root filesystem needs explicit writable runtime/home paths. Network access is not needed for signing and keyserver retrieval should not occur in the request path.
5. **Lifecycle:** import/provision, rotate, revoke, back up, and destroy keys outside Plone. Activation performs a non-secret capability check and a test sign/verify. Rotation updates the configured fingerprint and atomically produces a new artifact before publication succeeds.

This contract prevents storage in Plone but cannot prevent the Plone service account from *using* the key: any compromised process with access to the home/agent can request signatures. Stronger isolation requires a separate narrowly authorized signing service or hardware policy; see residual risks.

## Dependency and adapter arrangement

Recommended metadata shape (exact lower bound should be confirmed by implementation tests):

```toml
[project.optional-dependencies]
signing = [
    "python-gnupg>=0.5.6,<0.6",
]
```

The wheel cannot express the non-Python GnuPG dependency, so installation/deployment documentation must require and health-check a supported `gpg` executable. Keep `python-gnupg` out of base dependencies so unsigned RFC 9116 publication remains platform-independent. Do not depend simultaneously on PGPy or GPGME.

Wrap the library in an internal signer interface taking canonical bytes and an exact fingerprint and returning bytes. The production adapter should use a fixed executable/path/home supplied by trusted deployment configuration, fixed options, no shell, batch/no-TTY operation, bounded input/output, and a timeout. Because `python-gnupg` does not expose a public operation timeout, the signing contract must either specify killable process isolation around the adapter or explicitly choose direct `gpg` integration to own timeout/cancellation; it must not claim an in-process hard timeout that the wrapper cannot enforce. Map outcomes to structured internal categories such as `binary_unavailable`, `unsupported_version`, `key_not_found`, `key_unusable`, `agent_unavailable`, `bad_passphrase_or_locked`, `timeout`, `output_invalid`, and `internal_error`; log only redacted category/fingerprint suffix, never key material, agent protocol, passphrases, or unfiltered stderr. GnuPG's machine status channel is authoritative; human stderr text is diagnostic only. [GnuPG status interface](https://www.gnupg.org/documentation/manuals/gnupg/GPG-Esoteric-Options.html)

Serialize artifact generation per site/fingerprint. This avoids duplicate signatures with different creation times and reduces key-home/agent contention. Publish only after sign-then-verify succeeds and the retained artifact is atomically replaced. Anonymous requests read the artifact and never invoke GnuPG.

## Test strategy

- **Unit tests without GnuPG:** inject a fake signer; cover exact canonical-byte input, fingerprint forwarding, invalidation, atomic replacement, every structured error category, redaction, timeout mapping, and fail-closed `503` behavior.
- **Integration tests with GnuPG:** use a temporary mode-0700 `GNUPGHOME` and an ephemeral unprotected test-only RSA key; clear-sign UTF-8, dash-leading lines, blank lines, CRLF input, and final newline; verify via `gpg --status-fd`; recover and compare policy text; assert configured fingerprint/subkey; test absent/revoked/expired/non-signing keys and missing executable. Never reuse production key material.
- **Concurrency tests:** race two invalidations/sign attempts and prove exactly one artifact becomes visible and requests never observe partial armor.
- **Compatibility matrix:** run Python 3.10–3.12 against the chosen minimum and current vendor-supported GnuPG releases on Linux; at the research date upstream's current stable line is 2.5.x, while any downstream-supported 2.4 build needs explicit CI coverage. Add Windows only if the add-on declares Windows signing support; FD, agent, and home semantics need explicit validation there.
- Avoid golden signatures across versions/times. Assert semantic verification and byte identity of the **stored artifact across repeated reads/restarts**, not byte identity of two independent signing operations.

## Evidence gaps and residual risks

1. **GnuPG line/version policy:** upstream now presents 2.5.21 as stable and marks 2.4 end-of-life, but many deployment distributions can lag or backport fixes. The exact minimum version and RFC 9580 generation/verification behavior were not established. Test the chosen vendor-supported range with interoperability fixtures; do not silently equate a version number with maintenance status.
2. **Windows:** declared repository classifiers say “OS Independent,” but GnuPG agent/socket, file-descriptor, and packaging behavior was not tested here. Treat optional signing on Windows as unsupported until CI proves the same contract; unsigned publication remains portable.
3. **PyPI GPGME provenance/builds:** the new `gpg` 2.0.0 metadata is recent, but wheel availability and upstream's current recommended distribution path across target images were not established. This reinforces, but does not by itself decide, the choice against GPGME.
4. **Key compromise boundary:** external storage is not execution isolation. A compromised Plone worker under the signing UID can ask the agent to sign arbitrary content. High-assurance deployments need a separate signer that validates the security.txt payload/policy or a hardware token with operational controls.
5. **Agent availability:** unattended passphrase caching and hardware tokens introduce restart, expiry, PIN-entry, scaling, and failover behavior. The contract intentionally fails closed; operators must monitor pre-publication signing and `503` states.
6. **Multi-instance atomicity:** retaining one public artifact and serializing signing across multiple ZEO/client instances needs an implementation-level lock/transaction design. This research establishes the invariant, not the mechanism.
7. **Alternative implementations:** Sequoia/RNP Python options were not exhaustively disproved; no sufficiently mature, maintained, primary-source-supported Python candidate was identified before the recommendation became clear.

## Sources

- [RFC 9116 — A File Format to Aid in Security Vulnerability Disclosure](https://www.rfc-editor.org/rfc/rfc9116.html)
- [RFC 4880 — OpenPGP Message Format](https://www.rfc-editor.org/rfc/rfc4880.html)
- [RFC 9580 — OpenPGP](https://www.rfc-editor.org/rfc/rfc9580.html)
- [GnuPG 2.4 `gpg` manual](https://www.gnupg.org/documentation/manuals/gnupg24/gpg.1.html)
- [GnuPG option index](https://www.gnupg.org/documentation/manuals/gnupg/Option-Index.html)
- [GnuPG downloads and supported releases](https://www.gnupg.org/download/)
- [GnuPG release news](https://www.gnupg.org/news.html)
- [`python-gnupg` official documentation](https://gnupg.readthedocs.io/)
- [`python-gnupg` PyPI release metadata](https://pypi.org/project/python-gnupg/)
- [`python-gnupg` source repository](https://github.com/vsajip/python-gnupg)
- [GPGME reference manual](https://www.gnupg.org/documentation/manuals/gpgme/)
- [GPGME Python-bindings announcement](https://gnupg.org/blog/20160921-python-bindings-for-gpgme.html)
- [`gpg` (GPGME Python bindings) PyPI metadata](https://pypi.org/project/gpg/)
- [PGPy official documentation and examples](https://pgpy.readthedocs.io/en/latest/examples.html)
- [PGPy changelog](https://pgpy.readthedocs.io/en/latest/changelog.html)
- [PGPy source repository and releases](https://github.com/SecurityInnovation/PGPy/releases)
