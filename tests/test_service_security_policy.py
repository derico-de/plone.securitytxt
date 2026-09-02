"""Tests for security-policy REST API service."""

import json
from datetime import datetime
from datetime import timezone

import pytest

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.securitytxt.policy import new_record
from plone.securitytxt.policy import SecurityPolicyApplication
from plone.securitytxt.services.security_policy import SecurityPolicyService
from plone.securitytxt.testing import INTEGRATION_TESTING


NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)


class DummyResponse:
    def __init__(self):
        self.status = 200
        self.headers = {}

    def setStatus(self, status):
        self.status = status

    def setHeader(self, name, value):
        self.headers[name] = str(value)


class DummyRequest(dict):
    def __init__(self, body=None, **headers):
        super().__init__()
        self.json = body
        self.headers = headers
        self.response = DummyResponse()

    def getHeader(self, name, default=None):
        return self.headers.get(name, default)


def service(request, params=()):
    instance = object.__new__(SecurityPolicyService)
    instance.request = request
    instance.params = list(params)
    instance.application = SecurityPolicyApplication(
        record=new_record(), clock=lambda: NOW, check_permission=False
    )
    return instance


class TestServiceSecurityPolicyService:
    """Test security-policy REST API service."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_service_importable(self):
        """Test the service class can be imported."""
        assert SecurityPolicyService is not None


def test_get_exposes_management_state_and_revision_etag():
    request = DummyRequest()

    state = service(request).reply()

    assert state["lifecycle"] == "draft"
    assert request.response.headers["ETag"] == '"1"'


def test_mutation_requires_if_match_and_rejects_stale_revisions():
    missing = DummyRequest(body={})
    service(missing).PATCH()
    assert missing.response.status == 428

    stale = DummyRequest(body={}, **{"If-Match": '"9"'})
    service(stale).PATCH()
    assert stale.response.status == 412


def test_malformed_json_is_rejected_without_erasing_the_draft():
    request = DummyRequest(body="not an object", **{"If-Match": '"1"'})
    instance = service(request)

    result = instance.PATCH()

    assert request.response.status == 400
    assert result["error"]["code"] == "invalid-json"
    assert instance.application.inspect()["revision"] == "1"


def test_invalid_utf8_is_a_structured_error():
    request = DummyRequest(body=None, **{"If-Match": '"1"'})
    request["BODY"] = b"\xff"
    instance = service(request)

    result = instance.PATCH()

    assert request.response.status == 400
    assert result["error"]["code"] == "invalid-json"
    assert instance.application.inspect()["revision"] == "1"


def test_preview_is_side_effect_free_and_not_cacheable():
    request = DummyRequest(
        body={
            "contact": ["mailto:security@example.com"],
            "expires": "2026-09-01T00:00:00Z",
        }
    )
    instance = service(request, ("preview",))

    result = instance.POST()

    assert result["preview"].startswith("Contact: ")
    assert instance.application.inspect()["revision"] == "1"
    assert request.response.headers["Cache-Control"] == "no-store"


def test_command_failure_returns_interpolated_diagnostics():
    """Validation failures serialize as plain text, not raw message ids."""
    request = DummyRequest(
        body={"values": {"contact": ["not a uri"]}},
        **{"If-Match": '"1"'},
    )
    instance = service(request, ("publish",))

    result = instance.POST()

    assert request.response.status == 400
    assert result["error"]["message"] == "The Security Policy contains invalid values"
    messages = {item["code"]: item["message"] for item in result["diagnostics"]["errors"]}
    assert messages["contact.uri"] == ("Value 1 must be an absolute URI; web URIs must use HTTPS.")
    assert json.dumps(result)
