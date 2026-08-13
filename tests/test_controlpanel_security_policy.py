"""Tests for SecurityPolicy control panel."""

import pytest

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.securitytxt.testing import INTEGRATION_TESTING


class TestControlPanelSecurityPolicy:
    """Test SecurityPolicy control panel."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        self.request = integration["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_controlpanel_registered(self):
        """Test control panel is registered."""
        controlpanel = self.portal.portal_controlpanel
        actions = [a.getAction(self.portal)["id"] for a in controlpanel.listActions()]
        assert "security-policy-controlpanel" in actions

    def test_controlpanel_view(self):
        """Test control panel view is accessible."""
        from zope.component import getMultiAdapter

        view = getMultiAdapter(
            (self.portal, self.request),
            name="security-policy-controlpanel",
        )
        assert view is not None
        view.update()
        rendered = view.render()
        assert "Contact" in view.contents
        assert "mailto:security@example.com" in view.contents
        assert "The official URL where this security.txt is published" in view.contents
        assert "Canonical requires a public HTTPS URL" in view.contents
        assert "http://nohost/plone/.well-known/security.txt" in view.contents
        assert "December 31, 2027 at 23:59 UTC" in view.contents
        assert "de-CH (German as used in Switzerland)" in view.contents
        assert "Example: en, de-CH" in view.contents
        assert "Publication summary" in rendered
        assert "Generated unsigned preview" in rendered
        assert view.form_instance.preview == ""
        assert 'name="form.widgets.expires"' in view.contents
        assert 'type="datetime-local"' in view.contents
        assert view.form_instance.actions["save"].title == "Save draft"
        assert "disable" not in view.form_instance.actions
        publish_confirmation = view.form_instance.actions["publish"].onclick
        assert "window.confirm" in publish_confirmation
        assert "http://nohost/plone/.well-known/security.txt" in publish_confirmation

    def test_preferred_languages_use_comma_separated_form_value(self):
        """The RFC field syntax is converted to the internal ordered list."""
        from zope.component import getMultiAdapter

        view = getMultiAdapter(
            (self.portal, self.request),
            name="security-policy-controlpanel",
        )
        view.update()

        candidate = view.form_instance._candidate({"preferred_languages": "en, de-CH, fr"})

        assert candidate["preferred_languages"] == ["en", "de-CH", "fr"]

    def test_policy_is_not_exposed_as_registry_settings(self):
        """Generic registry/control-panel mutation cannot bypass policy rules."""
        from zope.component import getUtility

        from plone.registry.interfaces import IRegistry

        registry = getUtility(IRegistry)
        assert not any(
            name.startswith("plone.securitytxt.securitypolicy") for name in registry.records
        )
