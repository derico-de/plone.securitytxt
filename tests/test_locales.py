"""Translation catalog tests for plone.securitytxt."""

from datetime import datetime
from datetime import timezone

import pytest
from zope.i18n import translate

from plone.securitytxt.i18n import _
from plone.securitytxt.policy import localize_diagnostics
from plone.securitytxt.policy import new_record
from plone.securitytxt.policy import PolicyCommandError
from plone.securitytxt.policy import SecurityPolicyApplication


def test_german_catalog_is_registered(integration):
    """The package domain resolves German UI messages and mappings."""
    request = integration["request"]

    assert (
        translate(_("Security Policy"), context=request, target_language="de")
        == "Sicherheitsrichtlinie"
    )
    message = _(
        "Publish at ${url} in ${mode} mode until ${expiry}?",
        mapping={
            "url": "https://example.com/.well-known/security.txt",
            "mode": "unsigniert",
            "expiry": "2027-12-31T23:59:00Z",
        },
    )
    translated = translate(message, context=request, target_language="de")
    assert translated == (
        "Unter https://example.com/.well-known/security.txt im Modus unsigniert "
        "bis 2027-12-31T23:59:00Z veröffentlichen?"
    )


def test_validation_diagnostics_are_translatable(integration):
    """Diagnostics raised by the application module resolve in German."""
    request = integration["request"]
    application = SecurityPolicyApplication(
        record=new_record(),
        clock=lambda: datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc),
        check_permission=False,
    )

    result = application.evaluate({})
    messages = {
        item["code"]: translate(item["message"], context=request, target_language="de")
        for item in result["blockers"]
    }
    assert messages["contact.required"] == "Mindestens ein Kontakt ist erforderlich."
    assert messages["expires.required"] == "Ein Ablaufzeitpunkt ist erforderlich."


def test_diagnostic_mappings_survive_localization(integration):
    """Interpolated diagnostics keep their values through ``localize_diagnostics``."""
    request = integration["request"]
    application = SecurityPolicyApplication(
        record=new_record(),
        clock=lambda: datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc),
        check_permission=False,
    )

    result = application.evaluate({"contact": ["not a uri"], "preferred_languages": ["nope!"]})
    english = localize_diagnostics(result)
    by_code = {item["code"]: item["message"] for item in english["errors"]}
    assert by_code["contact.uri"] == ("Value 1 must be an absolute URI; web URIs must use HTTPS.")
    assert by_code["preferred_languages.invalid"] == (
        "'nope!' is not a supported BCP 47 language tag."
    )

    raw = {item["code"]: item["message"] for item in result["errors"]}
    assert translate(raw["contact.uri"], context=request, target_language="de") == (
        "Wert 1 muss eine absolute URI sein; Web-URIs müssen HTTPS verwenden."
    )


def test_command_errors_carry_translatable_messages(integration):
    """``PolicyError.message`` is a Message while ``str(exc)`` stays English."""
    request = integration["request"]
    application = SecurityPolicyApplication(
        record=new_record(),
        clock=lambda: datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc),
        check_permission=False,
    )

    with pytest.raises(PolicyCommandError) as error:
        application.execute("publish", {}, expected_revision="1")

    assert str(error.value) == "The Security Policy cannot be published"
    assert (
        translate(error.value.message, context=request, target_language="de")
        == "Die Sicherheitsrichtlinie kann nicht veröffentlicht werden"
    )
