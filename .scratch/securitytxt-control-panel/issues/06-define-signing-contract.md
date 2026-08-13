# Define the optional signing contract

Type: grilling
Status: resolved
Blocked by: 03 — [Define publication and HTTP semantics](03-define-publication-http-semantics.md); 05 — [Evaluate OpenPGP signing approaches](05-evaluate-openpgp-approaches.md)

## Question

What exact contract should optional signing expose to operators, website owners, and HTTP clients? Choose the dependency approach; define capability detection, deployment-secret configuration, key identity, enablement prerequisites, unsigned preview, clear-signed serialization at the normal endpoint, caching, key rotation, audit and error visibility, and fail-closed behavior. Specify behavior both with and without the `signing` extra installed.

## Answer

### Package and execution boundary

OpenPGP signing is available only through the `signing` package extra. The extra depends on `python-gnupg>=0.5.6` without a routine upper bound, so installation resolves the most recent release satisfying that minimum. A release may exclude or cap a newer version only when a known incompatibility justifies it. The base installation remains capable of complete unsigned publication without importing `gnupg` or requiring a GnuPG executable.

The supported signing platform is Linux. Deployments must provide a vendor-security-supported GnuPG version at or above 2.2.27; release testing must cover that minimum and the current supported GnuPG release. Windows signing is unsupported until it satisfies the same contract in CI, although unsigned publication remains platform-independent.

A narrow internal adapter runs `python-gnupg` inside a short-lived helper process started in a new Linux process group. The parent enforces a hard 30-second deadline and terminates the entire process group on timeout. Input and output are bounded, no shell is used, and anonymous requests never start the helper, GnuPG, or an agent operation.

### Deployment-owned Signing Profiles

The deployment operator provisions named Signing Profiles in an integrity-protected JSON file whose absolute path is supplied through the `PLONE_SECURITYTXT_SIGNING_CONFIG` environment variable. A representative shape is:

```json
{
  "profiles": {
    "incident-response": {
      "enabled": true,
      "revision": "2026-01",
      "gpg": "/usr/bin/gpg",
      "gnupghome": "/run/plone-securitytxt/incident-response",
      "signing_fingerprint": "FULL_SIGNING_SUBKEY_FINGERPRINT"
    }
  }
}
```

Profile IDs and revisions are stable, nonempty opaque strings. Executable and key-home paths are absolute. Fingerprints are normalized full fingerprints, never short or long key IDs, email addresses, or user IDs. The selected signing subkey is forced exactly, without GnuPG fallback to a default key or another subkey. The website owner stores and selects only a profile ID; they cannot alter its executable, key home, fingerprint, revision, or enabled state.

The configuration file contains no secrets, but its integrity controls which key Plone may use. Each `GNUPGHOME` is dedicated to this service, owned by the Plone service account, mode `0700`, writable where GnuPG requires locks or state, and not shared with an administrator's ordinary keyring or unrelated application containers. Private keys, hardware-token stubs, agent sockets, backups, revocation, and destruction remain deployment responsibilities.

The add-on never accepts or stores a private-key export, passphrase, PIN, agent token, or secret-file content in ZODB, a form, an environment variable, a command line, or a Python API call. Noninteractive signing must already be available through deployment-managed `gpg-agent` state or a hardware-backed key. Loopback pinentry is not enabled. A compromised Plone process able to reach that agent can still request signatures; stronger execution isolation requires a separate signer and is outside this contract.

Each Plone process loads and validates profile configuration at startup. Deployments must activate the same configuration consistently across all application clients and restart or reload them after a change. The anonymous endpoint uses only the resulting in-memory public metadata; it performs no configuration-file I/O.

### Key and interoperability requirements

A usable profile must resolve to exactly one available secret signing subkey and its primary key. Both must be enabled, non-revoked, non-expired, signing-capable version-4 RSA keys of at least 3072 bits. Clear-signing uses SHA-256. Activation requires both the primary key and signing subkey to remain valid through the Security Policy's `Expires` instant; non-expiring keys qualify. Newer key formats and algorithms remain unavailable until explicitly added to the tested product profile.

Authorized owners see the full public primary-key and selected signing-subkey fingerprints so they can verify identity. Logs use only a fingerprint suffix.

### Signing Capability

The control panel distinguishes these per-profile capability states:

- **Unavailable**: the Python extra, profile configuration, executable, key material, agent access, or another requirement is absent or invalid.
- **Configured**: profile syntax, paths, supported GnuPG version, and key metadata pass passive checks.
- **Verified**: a bounded test sign-and-verify has also succeeded for the current profile revision.

Capability tests do not change public policy content. A manual **Test signing** action signs a fixed harmless probe, verifies it, discards the result, and records its outcome. Verified status is invalidated by a profile revision or relevant key-validity change; it is not a promise that a later agent operation cannot fail.

Without the `signing` extra, unsigned authoring and publication work normally. Signed Publication Mode cannot be newly selected or published, and any edit that requires re-signing is rejected. An already matching Signed Publication Artifact remains servable and inspectable even when the extra, GnuPG, profile file, private key, or agent later becomes unavailable. An owner may disable signing without the extra.

### Owner configuration and enablement

A Draft Security Policy may select Signed Publication Mode and an available Signing Profile while other publication requirements remain incomplete. Saving that choice requires the profile to exist, but does not publish or retain a policy artifact. Signed publication additionally requires every ordinary publication condition, including at least one matching Canonical URL, plus a successful sign-and-verify using the selected profile.

A new Signed Publication Artifact must be generated and verified before committing any of these operations:

- enabling publication in Signed Publication Mode;
- changing a published policy from unsigned to signed;
- changing content or deterministic ordering while signed publication remains enabled;
- selecting another Signing Profile or accepting a changed profile revision; or
- extending an expired signed policy so publication can resume.

Failure rejects the attempted enablement or edit and preserves any previously committed policy and artifact. Enabling a draft therefore leaves it Draft on failure; a failed edit to an existing publication leaves the old representation live. Switching a published policy from signed to unsigned requires no signer: the deterministic unsigned representation and mode change are committed atomically. Disabling publication returns the policy to Draft and makes the public endpoint return the already-defined `404` response.

### Preview and simple Classic UI

Signing remains part of one ordinary Plone `z3c.form` control panel. Its Signing fieldset contains publication mode, available Signing Profile, read-only capability and key identity, last-attempt status, an inline unsigned preview, and standard Save and Test Signing actions. If useful, an existing signed artifact may appear in a read-only textarea. The form uses normal field validation and status messages: there is no separate signing dashboard, custom preview or download view, bespoke AJAX workflow, custom JavaScript, or custom Volto UI.

The authorized unsigned preview uses the same canonical renderer as publication and is explicitly labelled as non-public and unsigned. It may render individually valid current form values without saving even when the draft has publication blockers. It reports blockers and warnings, uses `Cache-Control: no-store`, and never invokes GnuPG. Preview and signing status require the dedicated Security Policy management permission.

### Generation and verification

The helper receives the canonical unsigned UTF-8 bytes defined by the field and HTTP contracts: no byte-order mark, fixed field ordering and casing, CRLF line endings, and a final line ending. GnuPG performs clear-sign framing, dash escaping, armor, and signature construction. The add-on does not build or post-process armor and does not rewrite the returned line endings.

The complete returned clear-signed representation is capped at 64 KiB. A second GnuPG operation must verify it, report the exact configured signing-subkey fingerprint and SHA-256, and recover cleartext equal to the canonical unsigned input. Malformed, truncated, oversized, unverifiable, differently signed, or content-mismatched output is rejected. The successfully verified exact bytes—not a recipe for recreating them—become the Signed Publication Artifact.

### Artifact binding, storage, and HTTP caching

The public Signed Publication Artifact is non-secret and is retained atomically in site-scoped ZODB storage. Its binding records:

- the canonical unsigned-content hash;
- Signed Publication Mode;
- Signing Profile ID and revision;
- the exact signing-subkey fingerprint;
- serializer version;
- key-validity metadata;
- artifact hash and signing timestamp; and
- signer implementation versions for audit only.

The `python-gnupg` and GnuPG versions are not serving-time binding inputs. Upgrading them does not invalidate an otherwise verified artifact; the next content or profile change signs with the new software. A key, algorithm-policy, profile revision, mode, serializer, or canonical-content change does invalidate the artifact.

Repeated successful requests serve the retained bytes unchanged. The strong ETag is derived from those exact bytes. Signed responses otherwise use the same status, `Content-Type`, Canonical-host enforcement, `Cache-Control: public, max-age=<min(300, seconds-to-policy-expiry)>, must-revalidate`, conditional request, `HEAD`, and auxiliary-header contract already defined for publication. No request-time signature timestamp can change the body or ETag.

Before serving, the endpoint checks the effective policy state and stored binding using local public metadata only. A missing, unreadable, partial, or mismatched artifact for a publication-enabled signed policy returns the generic `503` response with no unsigned or stale fallback. Policy expiry and Canonical mismatch retain their previously defined `404` behavior.

Incidental inability to load signing support or reach the signer does not invalidate matching retained public bytes. Emergency withdrawal must be explicit: the operator successfully loads the profile with `enabled: false` or changes its revision. Once active in all processes, either change invalidates the binding and produces `503` until the owner disables signing or successfully regenerates. Operators must not delete an unreadable profile and assume that doing so revokes an already published signature.

### Rotation

For planned zero-downtime rotation, the operator adds the replacement key as a new Signing Profile ID while retaining the old profile. The owner selects the new profile; Plone signs and verifies the current canonical policy before atomically committing the new selection and artifact. Failure leaves the old profile and artifact live. After successful replacement, the operator may retire the old profile.

An in-place revision change or `enabled: false` is the emergency fail-closed path and intentionally causes `503` until regeneration or a switch to unsigned mode succeeds. Revocation and keyserver discovery are never attempted in the anonymous request path.

### Atomicity and concurrent writes

The policy revision, publication mode, selected profile, artifact binding, and artifact bytes commit in one ZODB transaction. A generated artifact may commit only if its canonical content and profile inputs still match the current transaction. Ordinary ZODB conflict handling rejects a concurrent stale write. Duplicate internal signing operations may occur after simultaneous saves or transaction retries, but only a complete artifact matching the committed inputs can become visible; no custom cluster-wide signing lock is required unless implementation testing proves ZODB atomicity insufficient.

### Error and audit contract

Internal failures are reduced to stable sanitized categories, including support missing, profile missing or invalid, unsupported GnuPG, key missing or unusable, agent unavailable or interaction required, timeout, output too large, signing failure, verification failure, content mismatch, transaction conflict, and internal error. Authorized owners receive an actionable category and correlation ID. Anonymous clients receive only the generic non-success response already defined by the HTTP contract.

The site persists only current public status metadata: the last successful signing principal and time, profile ID and revision, fingerprint suffix, content and artifact hashes, and the latest failed attempt's category, time, and correlation ID. Structured operator logs cover mode changes, profile changes, capability tests, successful artifact generation, rotation, and failures, with site/profile identifiers, duration, outcome category, and correlation ID. Neither status nor logs contain private material, passphrases, policy content, agent protocol data, or raw GnuPG stderr.
