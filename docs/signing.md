# Signing your security.txt (step by step)

Signing is **optional**. Most sites publish `security.txt` unsigned and that is perfectly
valid. Sign it when you want researchers to be able to prove that the contact details
they found really come from you and were not modified on the way.

This guide is written for site administrators, not for OpenPGP experts. Follow the steps
in order; each one ends with a check you can run.

## Before you start

You need:

- A **Linux server** where you can run shell commands and restart Plone.
- **GnuPG 2.2.27 or newer** on that server.
- Your site reachable over **HTTPS**. Signed publication requires a Canonical URL, and
  Canonical URLs must be `https://`.
- About 30 minutes.

Read this first:

> **Signed mode never falls back to unsigned.** Once you publish in signed mode, every
> new publication must be signed. If the key or GnuPG becomes unavailable, you cannot
> publish changes until you fix it or switch back to unsigned mode. The bytes that are
> already published keep being served in the meantime, so visitors never see a broken
> `security.txt` — you just cannot update it.

Three terms used below:

| Term | Meaning |
| --- | --- |
| **GnuPG home** | A directory that holds one OpenPGP keyring. You will create a dedicated one just for this. |
| **Signing Profile** | A named entry in a small JSON file that tells Plone which key to use. You choose the name, e.g. `incident-response`. |
| **Fingerprint** | The 40-character identifier of a key. You will need the one of the **signing subkey**, not of the primary key. |

## Step 1 — Install the signing extra

Signing needs one extra Python package (`python-gnupg`). Add the `signing` extra to the
dependency you already have:

```python
# pyproject.toml of your Plone project
dependencies = [
    "plone.securitytxt[signing]",
]
```

Then reinstall your environment (`uv sync`, `pip install -e .`, … — whatever your project
uses). Do not restart Plone yet; Step 7 does that.

**Check:** `python -c "import gnupg; print(gnupg.__version__)"` inside your Plone
environment prints a version number.

## Step 2 — Check the GnuPG version

```bash
gpg --version | head -1
```

**Check:** the version is `2.2.27` or higher. Older versions are rejected. Note the path
of the binary, usually `/usr/bin/gpg` (`command -v gpg`) — you need it in Step 6.

## Step 3 — Create a dedicated GnuPG home

Never reuse a personal keyring. Create a directory that only the operating-system user
running Plone can read. Replace `plone` with that user name:

```bash
sudo install -d -o plone -g plone -m 0700 /var/lib/plone-securitytxt/incident-response
```

**Check:** `ls -ld /var/lib/plone-securitytxt/incident-response` shows `drwx------` and
the Plone user as owner.

## Step 4 — Create the signing key

Run these commands **as the Plone user**, so the created files belong to it:

```bash
sudo -u plone -H bash
export GNUPGHOME=/var/lib/plone-securitytxt/incident-response

# 1. Primary key (RSA 3072, valid until 2028-01-01 — pick your own date)
gpg --batch --pinentry-mode loopback --passphrase '' \
    --quick-generate-key 'Example Org security.txt <security@example.com>' \
    rsa3072 sign 2028-01-01

# 2. Add a separate signing subkey — this is the key that will sign
PRIMARY=$(gpg --list-keys --with-colons | awk -F: '/^fpr:/{print $10; exit}')
gpg --batch --pinentry-mode loopback --passphrase '' \
    --quick-add-key "$PRIMARY" rsa3072 sign 2028-01-01

# 3. Print the fingerprint you need for the configuration file
gpg --list-secret-keys --with-colons |
    awk -F: '/^ssb:/{f=1;next} /^fpr:/ && f {print $10; exit}'
```

The last command prints 40 characters such as
`A1386297CB43C9CC8D6EAEE939F7644B309DBF3B`. **Write it down — this is the
`signing_fingerprint`.** It is the fingerprint of the subkey (the `ssb` line), not of the
primary key (the `sec` line).

Why no passphrase? Plone has to sign without a human present. A passphrase that a server
process can use automatically protects nothing extra, and the add-on refuses to store one
anyway. The protection here is filesystem permissions: mode `0700`, owned by the Plone
user, on a server where only administrators have accounts. If you need stronger
protection, use a hardware token (YubiKey, smartcard) or a `gpg-agent` with a preset
passphrase — both work, and neither changes anything in Steps 5 to 9.

The key must satisfy all of these, otherwise signing is refused:

- RSA, at least 3072 bits, both for the primary key and the signing subkey
- signing capability, not revoked, not expired, not disabled
- **valid at least as long as the `Expires` value of your security.txt**
- exactly one secret subkey in this GnuPG home matching the fingerprint

**Check:** `gpg --list-secret-keys --keyid-format LONG` shows one `sec rsa3072 … [SC]`
line and one `ssb rsa3072 … [S]` line, both with an expiry date in the future.

## Step 5 — Publish your public key

Researchers can only verify a signature if they have your public key. Export it:

```bash
gpg --armor --export "$PRIMARY" > /tmp/pgp-key.txt
```

Upload that file somewhere on your site, for example
`https://example.com/pgp-key.txt`, and add that URL later in the control panel under
**Disclosure → Encryption**.

**Check:** opening the URL in a browser shows a block starting with
`-----BEGIN PGP PUBLIC KEY BLOCK-----`.

## Step 6 — Write the Signing Profile configuration

Create a small JSON file, for example `/etc/plone/securitytxt-signing.json`:

```json
{
  "profiles": {
    "incident-response": {
      "enabled": true,
      "revision": "2026-01",
      "gpg": "/usr/bin/gpg",
      "gnupghome": "/var/lib/plone-securitytxt/incident-response",
      "signing_fingerprint": "A1386297CB43C9CC8D6EAEE939F7644B309DBF3B"
    }
  }
}
```

| Field | What to put in |
| --- | --- |
| `incident-response` | The profile ID you invent. You type this exact string into the control panel in Step 8. |
| `enabled` | `true` or `false`. Setting it to `false` immediately stops all signing with this profile. |
| `revision` | A label you choose, e.g. `2026-01`. Change it only together with a key change; see "Rotating the key". |
| `gpg` | Absolute path of the `gpg` binary from Step 2. |
| `gnupghome` | Absolute path of the directory from Step 3. |
| `signing_fingerprint` | The 40-character subkey fingerprint from Step 4. |

All five fields are required and no other field is allowed — a typo makes the whole
profile invalid and it will simply not appear in Plone. Both paths must be absolute.

The file contains **no secrets**, so it may live in your configuration management. The
Plone user only needs to read it:

```bash
sudo chown root:plone /etc/plone/securitytxt-signing.json
sudo chmod 0640 /etc/plone/securitytxt-signing.json
```

**Check:** `python -m json.tool /etc/plone/securitytxt-signing.json` prints the file back
without an error.

## Step 7 — Point Plone at the file and restart

Set the environment variable `PLONE_SECURITYTXT_SIGNING_CONFIG` for the **Plone process**.
With systemd:

```ini
# /etc/systemd/system/plone.service  (or a drop-in)
[Service]
Environment=PLONE_SECURITYTXT_SIGNING_CONFIG=/etc/plone/securitytxt-signing.json
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart plone
```

> The configuration file is read **once, when Plone starts**. After every change to the
> JSON file, to the key, or to the variable, restart Plone — otherwise Plone keeps using
> the values from startup.

**Check:** Plone starts normally. If the file is missing or invalid, Plone still starts,
but no profile is available and Step 8 will tell you so.

## Step 8 — Switch the policy to signed mode

Open **Site Setup → Security Policy** and:

1. On the **Contact & expiry** tab, make sure **Expires** is set to a date **before** the
   key expiry from Step 4.
2. On the same tab, fill in **Canonical** with your public URL — the form shows the exact
   value to copy, e.g. `https://example.com/.well-known/security.txt`. Signed publication
   without Canonical is refused.
3. On the **Disclosure** tab, add the public key URL from Step 5 under **Encryption**.
4. On the **Signing** tab, set **Publication mode** to `Signed` and type your profile ID
   (`incident-response`) into **Signing Profile**.
5. Press **Save draft**.
6. Press **Test signing**. This signs a short test text and verifies the result.
7. Press **Publish**.

**Check:** the status box at the top of the control panel shows **Signing capability:
Verified** together with the primary and signing fingerprints, and the lifecycle changes
to **Published**.

## Step 9 — Verify from the outside

On any machine:

```bash
curl -s https://example.com/.well-known/security.txt > securitytxt.asc
head -3 securitytxt.asc                      # -----BEGIN PGP SIGNED MESSAGE-----
curl -s https://example.com/pgp-key.txt | gpg --import
gpg --verify securitytxt.asc
```

**Check:** GnuPG prints `Good signature from "Example Org security.txt …"`. A warning
that the key is not certified by a trusted signature is normal — it only means you have
not personally signed that key.

You are done.

## Everyday operations

**Editing the policy.** Change values as usual and press **Publish**. The file is signed
again automatically on every publication. Between publications nothing calls GnuPG:
visitors are served the stored signed bytes, so normal traffic never touches your key.

**Renewing an expiring key.** Extend the key expiry *before* it passes, and keep it later
than the policy `Expires` value:

```bash
export GNUPGHOME=/var/lib/plone-securitytxt/incident-response
PRIMARY=$(gpg --list-keys --with-colons | awk -F: '/^fpr:/{print $10; exit}')
gpg --batch --pinentry-mode loopback --passphrase '' \
    --quick-set-expire "$PRIMARY" 2030-01-01
gpg --batch --pinentry-mode loopback --passphrase '' \
    --quick-set-expire "$PRIMARY" 2030-01-01 '*'   # subkeys as well
```

Then republish once so the stored signature is made with the renewed key.

**Rotating to a new key (planned).** Do not edit an existing profile in place. Instead:

1. Create the new key and add a **second** profile with a new ID, e.g. `incident-response-2027`.
2. Restart Plone.
3. In the control panel enter the new profile ID, press **Test signing**, then **Publish**.
4. Publish the new public key and update the **Encryption** URL.
5. Only now remove the old profile from the JSON file and restart again.

**Emergency (key compromised).** Set `"enabled": false` on the profile (or change
`revision`) and restart Plone. This is a deliberate fail-closed switch: the stored
signature is no longer accepted as current, and you must either publish again with a new
profile or switch the policy back to unsigned mode.

**Uninstalling the add-on** deletes the policy and the stored bytes. It never touches your
GnuPG home or your configuration file.

## Troubleshooting

| What you see | What it means | What to do |
| --- | --- | --- |
| Signing tab saved, but **Signing capability: Unavailable** | Plone found no usable profile | Check the profile ID spelling, that `enabled` is `true`, that the JSON has exactly the five allowed fields, that the environment variable is set **for the Plone process**, and that you restarted Plone. |
| *The selected Signing Profile is unavailable* or *Signing support is unavailable* | Same as above, or `python-gnupg` is not installed | Redo Steps 1, 6 and 7. |
| *Signed publication requires Canonical* | Canonical is empty | Fill in the HTTPS URL shown in the form (Step 8.2). |
| *Signing capability test failed* | GnuPG ran but the operation failed | Most common causes, in this order: the fingerprint is the **primary** key instead of the signing subkey; the key (or subkey) expires **before** the policy `Expires` date; the key is not RSA 3072+; the Plone user cannot read the GnuPG home; GnuPG is older than 2.2.27. |
| *Signing capability test failed*, and the server was under load | The 30-second limit was hit | Retry. If it keeps happening, check that `gpg-agent` starts in that GnuPG home and is not waiting for a PIN or passphrase prompt. |
| *The Security Policy revision is stale* | Someone else changed the policy in another browser tab | Reload the control panel and redo your change. |
| Endpoint returns `503` | Publication is blocked, usually because `Expires` has passed | Set a future `Expires` and publish again. |

Error messages are intentionally short and never contain raw GnuPG output — that output
can leak paths and key details. For details look at the GnuPG side yourself, as the Plone
user, with the same `GNUPGHOME`.

## Rules and limits

- **Never** put a passphrase, PIN or private key into the JSON file, an environment
  variable, the control panel or the REST API. The configuration loader rejects fields
  such as `passphrase` or `private_key` outright.
- The JSON file describes *which* key to use. Creating, backing up, revoking and
  destroying keys stays entirely in your hands.
- Anonymous requests never start GnuPG.
- Signing is bounded: 30 seconds per operation, at most 32 KiB of input and 64 KiB of
  signed output. A normal `security.txt` is far below that.
- Only the clear-signed form is produced (signature and readable text in one file), as
  RFC 9116 requires.
