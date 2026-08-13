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
        self.request = integration["request"]

    def _portal_header_manager(self, request=None):
        request = request or self.request
        view = queryMultiAdapter(
            (self.portal, request),
            name="plone",
        )
        manager = queryMultiAdapter(
            (self.portal, request, view),
            IViewletManager,
            name="plone.portalheader",
        )
        return request, view, manager

    def test_viewlet_registered(self):
        """Test viewlet is registered in the manager."""
        request, view, manager = self._portal_header_manager()
        assert manager is not None
        viewlet = queryMultiAdapter(
            (self.portal, request, view, manager),
            IViewlet,
            name="securitypolicywarning",
        )
        assert viewlet is not None
        viewlet.update()
        viewlet.render()

    def test_viewlet_not_registered_without_addon_browser_layer(self):
        """The viewlet must not run on a new site before add-on install."""
        request, view, manager = self._portal_header_manager(BrowserTestRequest())
        viewlet = queryMultiAdapter(
            (self.portal, request, view, manager),
            IViewlet,
            name="securitypolicywarning",
        )
        assert viewlet is None

    def test_portal_header_update_before_profile_install_does_not_fail(self):
        """A loaded package must not break rendering on a new Plone site."""
        from zope.annotation.interfaces import IAnnotations
        from zope.interface import alsoProvides
        from zope.interface import noLongerProvides

        from plone.securitytxt.interfaces import IPloneSecuritytxtLayer
        from plone.securitytxt.policy import ANNOTATION_KEY

        noLongerProvides(self.request, IPloneSecuritytxtLayer)
        try:
            del IAnnotations(self.portal)[ANNOTATION_KEY]
            _request, _view, manager = self._portal_header_manager()
            manager.update()
        finally:
            alsoProvides(self.request, IPloneSecuritytxtLayer)
