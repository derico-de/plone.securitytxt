"""Test plone.securitytxt installation."""

import pytest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID


class TestSetup:
    """Test installation and setup."""

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]

    def test_addon_installed(self):
        """Test addon is installed."""
        installer = api.addon.get_installer(self.portal)
        assert installer.is_product_installed("plone.securitytxt")

    def test_browserlayer(self):
        """Test browserlayer is registered."""
        from plone.browserlayer import utils
        from plone.securitytxt.interfaces import IPloneSecuritytxtLayer

        assert IPloneSecuritytxtLayer in utils.registered_layers()

    def test_install_creates_one_empty_draft_record(self):
        """The default profile initializes authoritative site storage."""
        from zope.annotation.interfaces import IAnnotations

        from plone.securitytxt.policy import ANNOTATION_KEY

        record = IAnnotations(self.portal)[ANNOTATION_KEY]
        assert record["format_version"] == 1
        assert record["publication_enabled"] is False
        assert record["revision"] == 1
        assert record["artifact"] == b""


class TestUninstall:
    """Test uninstallation."""

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer = api.addon.get_installer(self.portal)
        self.installer.uninstall_product("plone.securitytxt")

    def test_addon_uninstalled(self):
        """Test addon is uninstalled."""
        assert not self.installer.is_product_installed("plone.securitytxt")

    def test_uninstall_removes_policy_and_artifact(self):
        from zope.annotation.interfaces import IAnnotations

        from plone.securitytxt.policy import ANNOTATION_KEY

        assert ANNOTATION_KEY not in IAnnotations(self.portal)
