"""HTTP adapter tests for the anonymous well-known publication seam."""

from datetime import datetime
from datetime import timezone

import pytest
from zExceptions import NotFound
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest as BrowserTestRequest

from plone.securitytxt.policy import new_record
from plone.securitytxt.policy import SecurityPolicyApplication
from plone.securitytxt.publisher import SecurityTxtPublisher


NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)


class Response:
    def __init__(self):
        self.status = 200
        self.headers = {}

    def setStatus(self, status):
        self.status = status

    def setHeader(self, name, value):
        self.headers[name] = str(value)


class Request(dict):
    def __init__(self, method="GET", **headers):
        super().__init__(
            REQUEST_METHOD=method, ACTUAL_URL="https://example.com/.well-known/security.txt"
        )
        self.response = Response()
        self.headers = headers

    def getHeader(self, name, default=None):
        return self.headers.get(name, default)


def published_record():
    record = new_record()
    app = SecurityPolicyApplication(record=record, clock=lambda: NOW, check_permission=False)
    saved = app.execute(
        "save",
        {
            "contact": ["mailto:security@example.com"],
            "expires": "2026-08-11T12:01:01Z",
            "canonical": ["https://example.com/.well-known/security.txt"],
        },
        expected_revision="1",
    )
    app.execute("publish", expected_revision=saved["revision"])
    return record


def publisher(record, request):
    view = SecurityTxtPublisher(None, request)
    view.application = SecurityPolicyApplication(
        record=record, clock=lambda: NOW, check_permission=False
    )
    return view


def test_get_returns_exact_public_bytes_and_expiry_bounded_cache_headers():
    request = Request()
    body = publisher(published_record(), request)()

    assert request.response.status == 200
    assert body == (
        b"Contact: mailto:security@example.com\r\n"
        b"Expires: 2026-08-11T12:01:01Z\r\n"
        b"Canonical: https://example.com/.well-known/security.txt\r\n"
    )
    assert request.response.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert request.response.headers["Content-Length"] == str(len(body))
    assert request.response.headers["Cache-Control"] == "public, max-age=61, must-revalidate"
    assert request.response.headers["X-Content-Type-Options"] == "nosniff"
    assert "ETag" in request.response.headers


def test_head_has_get_headers_but_no_body():
    request = Request("HEAD")
    body = publisher(published_record(), request)()

    assert request.response.status == 200
    assert body == b""
    assert int(request.response.headers["Content-Length"]) > 0


def test_conditional_request_is_evaluated_after_publication_qualifies():
    record = published_record()
    etag = record["etag"]
    request = Request(**{"If-None-Match": etag})

    body = publisher(record, request)()

    assert request.response.status == 304
    assert body == b""
    assert request.response.headers["ETag"] == etag

    weak_request = Request(**{"If-None-Match": f"W/{etag}"})
    weak_body = publisher(record, weak_request)()
    assert weak_request.response.status == 304
    assert weak_body == b""


def test_well_known_namespace_is_registered_and_strict(integration):
    portal = integration["portal"]
    request = BrowserTestRequest()
    namespace = getMultiAdapter((portal, request), name=".well-known")

    terminal = namespace.publishTraverse(request, "security.txt")

    assert isinstance(terminal, SecurityTxtPublisher)
    with pytest.raises(NotFound):
        namespace.publishTraverse(request, "another-segment")


def test_draft_and_unsupported_methods_are_generic_and_not_cacheable():
    draft_request = Request()
    draft_body = publisher(new_record(), draft_request)()
    assert draft_request.response.status == 404
    assert draft_request.response.headers["Cache-Control"] == "no-store"
    assert b"policy" not in draft_body.lower()

    post_request = Request("POST")
    post_body = publisher(published_record(), post_request)()
    assert post_request.response.status == 405
    assert post_request.response.headers["Allow"] == "GET, HEAD"
    assert post_request.response.headers["Cache-Control"] == "no-store"
    assert post_body
