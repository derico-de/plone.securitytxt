"""Pytest configuration for plone.securitytxt tests."""

from pytest_plone import fixtures_factory

from plone.securitytxt.testing import ACCEPTANCE_TESTING
from plone.securitytxt.testing import FUNCTIONAL_TESTING
from plone.securitytxt.testing import INTEGRATION_TESTING


globals().update(
    fixtures_factory((
        (INTEGRATION_TESTING, "integration"),
        (FUNCTIONAL_TESTING, "functional"),
    ))
)
globals().update(
    fixtures_factory(
        ((ACCEPTANCE_TESTING, "acceptance"),),
        keep_session=False,
    )
)
