"""Translation catalog tests for plone.securitytxt."""

from zope.i18n import translate

from plone.securitytxt.i18n import _


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
