"""Optional OpenPGP adapter.

This base module never imports :mod:`gnupg`.  Actual GnuPG work happens in a
short-lived helper process so the parent can enforce a hard deadline.
"""

from __future__ import annotations

import base64
import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any

from plone.securitytxt.policy import MAX_SIGNED_BYTES


CONFIG_ENVIRONMENT_VARIABLE = "PLONE_SECURITYTXT_SIGNING_CONFIG"
SECRET_KEYS = {
    "passphrase",
    "password",
    "pin",
    "private_key",
    "secret",
    "token",
}
PROFILE_KEYS = {
    "enabled",
    "revision",
    "gpg",
    "gnupghome",
    "signing_fingerprint",
}
_PROFILE_CACHE: dict[str, dict[str, Any]] | None = None


class SigningConfigurationError(ValueError):
    """Deployment-owned profile configuration is unsafe or malformed."""


class SigningOperationError(RuntimeError):
    """A bounded helper operation failed with a sanitized category."""

    def __init__(self, category: str):
        super().__init__(category)
        self.category = category


def load_signing_profiles(  # noqa: C901 - strict schema is intentionally explicit
    path: str | os.PathLike[str],
) -> dict[str, dict[str, Any]]:
    """Load and strictly validate non-secret Signing Profile metadata."""
    config_path = Path(path)
    if not config_path.is_absolute():
        raise SigningConfigurationError("The signing configuration path must be absolute")
    try:
        document = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SigningConfigurationError("The signing configuration cannot be loaded") from exc
    profiles = document.get("profiles") if isinstance(document, dict) else None
    if not isinstance(profiles, dict):
        raise SigningConfigurationError("The configuration needs a profiles object")

    normalized = {}
    for profile_id, raw in profiles.items():
        if not isinstance(profile_id, str) or not profile_id.strip():
            raise SigningConfigurationError("Profile IDs must be nonempty strings")
        if not isinstance(raw, dict) or set(raw) != PROFILE_KEYS:
            if isinstance(raw, dict) and (set(raw) & SECRET_KEYS):
                raise SigningConfigurationError("Signing profiles must not contain secrets")
            raise SigningConfigurationError("A Signing Profile has unsupported or missing fields")
        if not isinstance(raw["enabled"], bool):
            raise SigningConfigurationError("Profile enabled must be boolean")
        if not isinstance(raw["revision"], str) or not raw["revision"].strip():
            raise SigningConfigurationError("Profile revision must be nonempty")
        if not Path(raw["gpg"]).is_absolute() or not Path(raw["gnupghome"]).is_absolute():
            raise SigningConfigurationError("GnuPG paths must be absolute")
        fingerprint = raw["signing_fingerprint"].replace(" ", "").upper()
        if len(fingerprint) != 40 or any(
            character not in "0123456789ABCDEF" for character in fingerprint
        ):
            raise SigningConfigurationError("Use a full version-4 signing fingerprint")
        normalized[profile_id] = {
            **raw,
            "signing_fingerprint": fingerprint,
        }
    return normalized


def initialize_profile_cache() -> None:
    """Load public profile metadata once during process startup."""
    global _PROFILE_CACHE
    path = os.environ.get(CONFIG_ENVIRONMENT_VARIABLE)
    if not path:
        _PROFILE_CACHE = {}
        return
    try:
        _PROFILE_CACHE = load_signing_profiles(path)
    except SigningConfigurationError:
        _PROFILE_CACHE = {}


def signing_profile_metadata(profile_id: str | None) -> dict[str, Any] | None:
    """Return startup-cached metadata without serving-time file access."""
    if _PROFILE_CACHE is None:
        initialize_profile_cache()
    return (_PROFILE_CACHE or {}).get(profile_id)


def configured_signer() -> GnuPGSigner | None:
    """Create a signer lazily for a management command, never for serving."""
    if _PROFILE_CACHE is None:
        initialize_profile_cache()
    if not _PROFILE_CACHE:
        return None
    return GnuPGSigner(_PROFILE_CACHE)


class GnuPGSigner:
    """Run sign-and-verify operations in a bounded process group."""

    timeout = 30

    def __init__(self, profiles):
        self.profiles = profiles

    def test(self, values):
        profile_id = values.get("signing_profile")
        self.sign_and_verify(
            b"plone.securitytxt signing capability probe\r\n",
            profile_id,
            expires=values.get("expires"),
        )
        return {"capability": "verified", "last_error": None, "profile_id": profile_id}

    def sign_and_verify(self, unsigned: bytes, profile_id: str, *, expires: str | None):
        if len(unsigned) > 32 * 1024:
            raise SigningOperationError("input-too-large")
        profile = self.profiles.get(profile_id)
        if profile is None:
            raise SigningOperationError("profile-missing")
        if not profile["enabled"]:
            raise SigningOperationError("profile-disabled")
        payload = json.dumps({
            "profile": profile,
            "unsigned": base64.b64encode(unsigned).decode("ascii"),
            "expires": expires,
        }).encode("utf-8")
        process = subprocess.Popen(  # noqa: S603 - fixed interpreter/module invocation
            [sys.executable, "-m", "plone.securitytxt.signing_helper"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            output, _ = process.communicate(payload, timeout=self.timeout)
        except subprocess.TimeoutExpired as exc:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise SigningOperationError("timeout") from exc
        if process.returncode != 0 or len(output) > 128 * 1024:
            raise SigningOperationError("signing-failure")
        try:
            result = json.loads(output)
            artifact = base64.b64decode(result["artifact"], validate=True)
            binding = result["binding"]
        except (KeyError, TypeError, ValueError) as exc:
            raise SigningOperationError("verification-failure") from exc
        if len(artifact) > MAX_SIGNED_BYTES:
            raise SigningOperationError("output-too-large")
        return artifact, binding
