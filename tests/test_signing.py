"""Base-package tests for the optional signing boundary."""

import json
import sys

import pytest

from plone.securitytxt.signing import load_signing_profiles
from plone.securitytxt.signing import SigningConfigurationError


def test_loading_public_profile_metadata_does_not_import_gnupg(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text(
        json.dumps({
            "profiles": {
                "incident-response": {
                    "enabled": True,
                    "revision": "2026-01",
                    "gpg": "/usr/bin/gpg",
                    "gnupghome": "/run/plone-securitytxt/incident-response",
                    "signing_fingerprint": "A" * 40,
                }
            }
        })
    )

    profiles = load_signing_profiles(path)

    assert profiles["incident-response"]["signing_fingerprint"] == "A" * 40
    assert "gnupg" not in sys.modules


def test_profile_rejects_secret_values_and_non_absolute_paths(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text(
        json.dumps({
            "profiles": {
                "unsafe": {
                    "enabled": True,
                    "revision": "1",
                    "gpg": "gpg",
                    "gnupghome": "/run/plone-securitytxt/unsafe",
                    "signing_fingerprint": "A" * 40,
                    "passphrase": "must-never-be-accepted",
                }
            }
        })
    )

    with pytest.raises(SigningConfigurationError):
        load_signing_profiles(path)
