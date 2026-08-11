"""Isolated python-gnupg helper; invoked only by :mod:`.signing`."""

from __future__ import annotations

import base64
import json
import sys
from datetime import datetime
from datetime import timezone
from hashlib import sha256


MAX_INPUT = 48 * 1024
MAX_ARTIFACT = 64 * 1024


def _expiry_epoch(value):
    if not value:
        return int(datetime.now(timezone.utc).timestamp())
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def _usable_rsa_signer(info, required_expiry):
    expires = info.get("expires") or "0"
    return (
        info.get("algo") == "1"
        and int(info.get("length") or 0) >= 3072
        and "s" in (info.get("cap") or "").casefold()
        and info.get("trust") not in {"r", "e", "d"}
        and (expires == "0" or int(expires) >= required_expiry)
    )


def _selected_key_metadata(gpg, fingerprint, required_expiry):
    """Require one exact usable secret RSA signing subkey and primary key."""
    matches = []
    for primary in gpg.list_keys(secret=True):
        for keyid, _kind, subkey_fingerprint, _keygrip in primary.get("subkeys", []):
            if subkey_fingerprint == fingerprint:
                matches.append((primary, primary.get("subkey_info", {}).get(keyid, {})))
    if len(matches) != 1:
        return None
    primary, subkey = matches[0]
    if not _usable_rsa_signer(primary, required_expiry):
        return None
    if not _usable_rsa_signer(subkey, required_expiry):
        return None
    primary_fingerprint = primary.get("fingerprint", "")
    if len(primary_fingerprint) != 40:
        return None
    return primary_fingerprint


def _used_sha256(verified):
    for line in (verified.stderr or "").splitlines():
        marker = "[GNUPG:] VALIDSIG "
        if marker in line:
            parts = line.split(marker, 1)[1].split()
            return len(parts) >= 8 and parts[7] == "8"
    return False


def main() -> int:
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        return 2
    try:
        payload = json.loads(raw)
        profile = payload["profile"]
        unsigned = base64.b64decode(payload["unsigned"], validate=True)
        import gnupg  # Imported only in this optional helper process.

        gpg = gnupg.GPG(
            gpgbinary=profile["gpg"],
            gnupghome=profile["gnupghome"],
            options=["--batch", "--no-tty"],
        )
        version = tuple(int(part) for part in gpg.version[:3])
        if version < (2, 2, 27):
            return 3
        fingerprint = profile["signing_fingerprint"]
        primary_fingerprint = _selected_key_metadata(
            gpg, fingerprint, _expiry_epoch(payload.get("expires"))
        )
        if primary_fingerprint is None:
            return 4
        signed = gpg.sign(
            unsigned,
            keyid=f"{fingerprint}!",
            clearsign=True,
            detach=False,
            digest_algo="SHA256",
        )
        artifact = bytes(signed.data)
        if not signed or not artifact or len(artifact) > MAX_ARTIFACT:
            return 5
        verified = gpg.decrypt(artifact)
        recovered = bytes(verified.data)
        actual_fingerprint = (verified.fingerprint or "").replace(" ", "").upper()
        if (
            not verified.valid
            or actual_fingerprint != fingerprint
            or recovered != unsigned
            or not _used_sha256(verified)
        ):
            return 6
        result = {
            "artifact": base64.b64encode(artifact).decode("ascii"),
            "binding": {
                "profile_revision": profile["revision"],
                "primary_fingerprint": primary_fingerprint,
                "signing_fingerprint": fingerprint,
                "artifact_hash": sha256(artifact).hexdigest(),
                "gnupg_version": ".".join(str(part) for part in version),
            },
        }
        sys.stdout.write(json.dumps(result, separators=(",", ":")))
        return 0
    except Exception:
        # Raw GnuPG errors and environment details never cross this boundary.
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
