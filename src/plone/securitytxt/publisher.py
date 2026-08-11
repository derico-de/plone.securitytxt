"""Strict site-root traversal and anonymous security.txt publisher."""

from __future__ import annotations

from zExceptions import NotFound
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse

from plone.securitytxt.policy import SecurityPolicyApplication


NOT_FOUND_BODY = b"The requested resource was not found.\n"
UNAVAILABLE_BODY = b"The requested resource is temporarily unavailable.\n"
METHOD_BODY = b"Method not allowed.\n"


@implementer(IPublishTraverse)
class WellKnownNamespace:
    """A non-acquiring namespace that exposes only ``security.txt``."""

    __allow_access_to_unprotected_subobjects__ = False

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self._used = False

    def publishTraverse(self, request, name):
        if self._used or name != "security.txt":
            raise NotFound(self.context, name, request)
        self._used = True
        return SecurityTxtPublisher(self.context, request)

    # ZPublisher uses this hook for ordinary traversal of registered views.
    def __bobo_traverse__(self, request, name):
        return self.publishTraverse(request, name)


class SecurityTxtPublisher:
    """Map sanitized application results to the RFC 9116 HTTP contract."""

    __allow_access_to_unprotected_subobjects__ = False

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.application = (
            SecurityPolicyApplication(context, check_permission=False)
            if context is not None
            else None
        )

    def __call__(self):
        method = self.request.get("REQUEST_METHOD", "GET").upper()
        if method not in {"GET", "HEAD"}:
            return self._error(405, METHOD_BODY, method, allow=True)

        request_url = self.request.get("ACTUAL_URL") or self.request.getURL()
        result = self.application.resolve_publication(request_url)
        if result.status == "not-found":
            return self._error(404, NOT_FOUND_BODY, method)
        if result.status == "unavailable":
            return self._error(503, UNAVAILABLE_BODY, method, retry=True)

        response = self.request.response
        response.setHeader("Content-Type", "text/plain; charset=utf-8")
        response.setHeader("Content-Length", len(result.body))
        response.setHeader(
            "Cache-Control",
            f"public, max-age={min(300, result.seconds_to_expiry)}, must-revalidate",
        )
        response.setHeader("ETag", result.etag)
        response.setHeader("X-Content-Type-Options", "nosniff")

        if self._etag_matches(result.etag):
            response.setStatus(304)
            return b""
        response.setStatus(200)
        return b"" if method == "HEAD" else result.body

    def HEAD(self):
        return self()

    def _etag_matches(self, etag: str) -> bool:
        value = self.request.getHeader("If-None-Match", "") or ""
        return value.strip() == "*" or etag in {item.strip() for item in value.split(",")}

    def _error(self, status, body, method, *, allow=False, retry=False):
        response = self.request.response
        response.setStatus(status)
        response.setHeader("Content-Type", "text/plain; charset=utf-8")
        response.setHeader("Cache-Control", "no-store")
        response.setHeader("Content-Length", len(body))
        if allow:
            response.setHeader("Allow", "GET, HEAD")
        if retry:
            response.setHeader("Retry-After", "300")
        return b"" if method == "HEAD" else body
