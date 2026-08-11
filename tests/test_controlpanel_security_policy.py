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
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_controlpanel_registered(self):
        """Test control panel is registered."""
        controlpanel = self.portal.portal_controlpanel
        actions = [a.getAction(self.portal)["id"] for a in controlpanel.listActions()]
        assert "security-policy-controlpanel" in actions

    def test_controlpanel_view(self):
        """Test control panel view is accessible."""
        from zope.component import getMultiAdapter
        from zope.publisher.browser import TestRequest

        request = TestRequest()
        view = getMultiAdapter(
            (self.portal, request),
            name="security-policy-controlpanel",
        )
        assert view is not None

    def test_policy_is_not_exposed_as_registry_settings(self):
        """Generic registry/control-panel mutation cannot bypass policy rules."""
        from zope.component import getUtility

        from plone.registry.interfaces import IRegistry

        registry = getUtility(IRegistry)
        assert not any(
            name.startswith("plone.securitytxt.securitypolicy") for name in registry.records
        )
