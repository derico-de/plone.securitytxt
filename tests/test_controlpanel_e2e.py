"""End-to-end browser tests for the Security Policy control panel."""

import base64

from zope.testbrowser.browser import Browser

from plone.securitytxt.testing import ACCEPTANCE_TESTING
from plone.securitytxt.testing import SITE_OWNER_NAME
from plone.securitytxt.testing import SITE_OWNER_PASSWORD


class TestSecurityPolicyControlPanelE2E:
    """Exercise the published control panel through the HTTP stack."""

    layer = ACCEPTANCE_TESTING

    def _browser(self, acceptance, *, authenticated=True):
        browser = Browser()
        browser.handleErrors = False
        if authenticated:
            credentials = base64.b64encode(
                f"{SITE_OWNER_NAME}:{SITE_OWNER_PASSWORD}".encode()
            ).decode()
            browser.addHeader("Authorization", f"Basic {credentials}")
        browser.open(
            f"http://{acceptance['host']}:{acceptance['port']}"
            f"/{acceptance['portal'].getId()}/@@security-policy-controlpanel"
        )
        return browser

    def test_first_open_renders_complete_control_panel(self, acceptance):
        """A manager can open a newly installed policy without a template error."""
        browser = self._browser(acceptance)

        assert browser.headers["Status"] == "200 OK"
        assert "Security Policy" in browser.contents
        assert "Publication summary" in browser.contents
        assert "Generated unsigned preview" in browser.contents
        assert "mailto:security@example.com" in browser.contents
        assert "The official URL where this security.txt is published" in browser.contents
        endpoint = (
            f"http://{acceptance['host']}:{acceptance['port']}"
            f"/{acceptance['portal'].getId()}/.well-known/security.txt"
        )
        assert "Canonical requires a public HTTPS URL" in browser.contents
        assert endpoint in browser.contents
        assert 'name="form.widgets.expires"' in browser.contents
        assert 'type="datetime-local"' in browser.contents
        assert "December 31, 2027 at 23:59 UTC" in browser.contents
        assert "de-CH (German as used in Switzerland)" in browser.contents
        assert "Example: en, de-CH" in browser.contents
        assert browser.getControl(name="form.buttons.save").value == "Save draft"

        browser.getControl(name="form.widgets.preferred_languages").value = "en, de-CH"
        browser.getControl(name="form.widgets.expires").value = "2027-12-31T23:59"
        browser.getControl(name="form.buttons.validate").click()

        assert browser.headers["Status"] == "200 OK"
        assert "0 errors" in browser.contents
        assert browser.getControl(name="form.widgets.preferred_languages").value == "en, de-CH"

    def test_published_policy_is_available_at_well_known_url(self, acceptance):
        """Publishing through the form exposes the artifact over anonymous HTTP."""
        browser = self._browser(acceptance)
        endpoint = (
            f"http://{acceptance['host']}:{acceptance['port']}"
            f"/{acceptance['portal'].getId()}/.well-known/security.txt"
        )
        browser.getControl(name="form.widgets.contact").value = "mailto:security@example.com"
        browser.getControl(name="form.widgets.expires").value = "2099-12-31T23:59"
        browser.getControl(name="form.buttons.publish").click()

        assert browser.getLink(url=endpoint) is not None

        anonymous = Browser()
        anonymous.handleErrors = False
        anonymous.open(endpoint)

        assert anonymous.headers["Status"] == "200 OK"
        assert "Contact: mailto:security@example.com" in anonymous.contents
        assert "Expires: 2099-12-31T23:59:00Z" in anonymous.contents
