"""Tests for SecurityPolicyWarning viewlet."""

import pytest
from zope.component import queryMultiAdapter
from zope.publisher.browser import TestRequest as BrowserTestRequest
from zope.viewlet.interfaces import IViewlet
from zope.viewlet.interfaces import IViewletManager

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.securitytxt.testing import INTEGRATION_TESTING


class TestViewletSecurityPolicyWarning:
    """Test SecurityPolicyWarning viewlet."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.request = BrowserTestRequest()

    def test_viewlet_registered(self):
        """Test viewlet is registered in the manager."""
        view = queryMultiAdapter(
            (self.portal, self.request),
            name="plone",
        )
        manager = queryMultiAdapter(
            (self.portal, self.request, view),
            IViewletManager,
            name="plone.portalheader",
        )
        assert manager is not None
        viewlet = queryMultiAdapter(
            (self.portal, self.request, view, manager),
            IViewlet,
            name="securitypolicywarning",
        )
        assert viewlet is not None
