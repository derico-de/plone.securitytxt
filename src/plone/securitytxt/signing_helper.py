"""Isolated python-gnupg helper; invoked only by :mod:`.signing`."""

from __future__ import annotations

import base64
import json
import sys
from hashlib import sha256


MAX_INPUT = 40 * 1024
MAX_ARTIFACT = 64 * 1024


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
        signed = gpg.sign(
            unsigned,
            keyid=f"{fingerprint}!",
            clearsign=True,
            detach=False,
            digest_algo="SHA256",
        )
        artifact = bytes(signed.data)
        if not signed or not artifact or len(artifact) > MAX_ARTIFACT:
            return 4
        verified = gpg.decrypt(artifact)
        recovered = bytes(verified.data)
        actual_fingerprint = (verified.fingerprint or "").replace(" ", "").upper()
        if not verified.valid or actual_fingerprint != fingerprint or recovered != unsigned:
            return 5
        result = {
            "artifact": base64.b64encode(artifact).decode("ascii"),
            "binding": {
                "profile_revision": profile["revision"],
                "signing_fingerprint": fingerprint,
                "artifact_hash": sha256(artifact).hexdigest(),
                "gnupg_version": ".".join(str(part) for part in version),
            },
        }
        sys.stdout.write(json.dumps(result, separators=(",", ":")))
        return 0
    except Exception:
        # Raw GnuPG errors and environment details never cross this boundary.
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
