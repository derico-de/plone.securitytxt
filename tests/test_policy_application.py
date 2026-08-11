"""Behavior tests for the authoritative Security Policy application seam."""

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest

from plone.securitytxt.policy import canonical_url_matches
from plone.securitytxt.policy import new_record
from plone.securitytxt.policy import PolicyCommandError
from plone.securitytxt.policy import SecurityPolicyApplication


NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)


def valid_policy(**changes):
    values = {
        "contact": ["mailto:security@example.com", "https://example.com/security"],
        "expires": "2026-09-10T12:00:00Z",
        "encryption": [],
        "acknowledgments": [],
        "preferred_languages": ["en", "de-CH"],
        "canonical": ["https://example.com/.well-known/security.txt"],
        "policy": ["https://example.com/security-policy"],
        "hiring": [],
        "extensions": [
            {
                "name": "CSAF",
                "value": "https://example.com/.well-known/csaf/provider-metadata.json",
            },
            {"name": "Bug-Bounty", "value": "True"},
        ],
        "publication_mode": "unsigned",
        "signing_profile": None,
    }
    values.update(changes)
    return values


@pytest.fixture
def application():
    return SecurityPolicyApplication(
        record=new_record(),
        clock=lambda: NOW,
        check_permission=False,
    )


def test_draft_evaluation_allows_missing_publication_values(application):
    result = application.evaluate({})

    assert result["errors"] == []
    assert {item["code"] for item in result["blockers"]} == {
        "contact.required",
        "expires.required",
    }
    assert result["preview"] == ""


def test_populated_draft_values_must_be_well_formed(application):
    result = application.evaluate({
        "contact": ["not an absolute uri"],
        "expires": "not-a-date",
        "extensions": [{"name": "Contact", "value": "mailto:other@example.com"}],
    })

    assert {item["code"] for item in result["errors"]} == {
        "contact.uri",
        "expires.invalid",
        "extension.collision",
    }


def test_publish_retains_deterministic_unsigned_artifact(application):
    draft = application.execute("save", valid_policy(), expected_revision="1")
    state = application.execute("publish", expected_revision=draft["revision"])

    assert state["lifecycle"] == "published"
    publication = application.resolve_publication("https://example.com/.well-known/security.txt")
    assert publication.status == "published"
    assert publication.body == (
        b"Contact: mailto:security@example.com\r\n"
        b"Contact: https://example.com/security\r\n"
        b"Expires: 2026-09-10T12:00:00Z\r\n"
        b"Preferred-Languages: en, de-CH\r\n"
        b"Canonical: https://example.com/.well-known/security.txt\r\n"
        b"Policy: https://example.com/security-policy\r\n"
        b"CSAF: https://example.com/.well-known/csaf/provider-metadata.json\r\n"
        b"Bug-Bounty: True\r\n"
    )
    assert publication.etag.startswith('"') and publication.etag.endswith('"')


def test_invalid_published_edit_preserves_previous_policy_and_artifact(application):
    saved = application.execute("save", valid_policy(), expected_revision="1")
    published = application.execute("publish", expected_revision=saved["revision"])
    before = application.resolve_publication("https://example.com/.well-known/security.txt")

    with pytest.raises(PolicyCommandError):
        application.execute(
            "save",
            valid_policy(contact=[]),
            expected_revision=published["revision"],
        )

    after = application.resolve_publication("https://example.com/.well-known/security.txt")
    assert after.body == before.body
    assert application.inspect()["revision"] == published["revision"]


def test_expiry_blocks_publication_without_changing_owner_intent(application):
    application.execute(
        "save",
        valid_policy(expires=(NOW + timedelta(seconds=1)).isoformat()),
        expected_revision="1",
    )
    application.execute("publish", expected_revision="2")
    application.clock = lambda: NOW + timedelta(seconds=1)

    state = application.inspect()
    assert state["publication_enabled"] is True
    assert state["lifecycle"] == "publication-blocked"
    assert (
        application.resolve_publication("https://example.com/.well-known/security.txt").status
        == "not-found"
    )


def test_canonical_matching_normalizes_host_case_idna_and_default_https_port():
    assert canonical_url_matches(
        "https://EXAMPLE.com:443/.well-known/security.txt",
        ["https://example.com/.well-known/security.txt"],
    )
    assert canonical_url_matches(
        "https://xn--bcher-kva.example/.well-known/security.txt",
        ["https://bücher.example/.well-known/security.txt"],
    )
    assert not canonical_url_matches(
        "https://example.com/.well-known/security%2Etxt",
        ["https://example.com/.well-known/security.txt"],
    )
