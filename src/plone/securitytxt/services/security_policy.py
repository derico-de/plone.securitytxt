"""Domain-specific ``@security-policy`` REST API service."""

from __future__ import annotations

import json

from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse

from plone.restapi.services import Service
from plone.securitytxt.policy import PolicyCommandError
from plone.securitytxt.policy import PolicyPermissionError
from plone.securitytxt.policy import PolicyRevisionError
from plone.securitytxt.policy import SecurityPolicyApplication


@implementer(IPublishTraverse)
class SecurityPolicyService(Service):
    """Expose inspect, evaluate, and typed commands without storage CRUD."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []
        self.application = SecurityPolicyApplication(context)

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self

    def reply(self):
        if self.params:
            return self._error(404, "not-found", "Unknown operation.")
        try:
            state = self.application.inspect()
        except PolicyPermissionError:
            return self._error(403, "forbidden", "Permission denied.")
        self.request.response.setHeader("ETag", f'"{state["revision"]}"')
        return state

    def PATCH(self):
        if self.params:
            return self._error(404, "not-found", "Unknown operation.")
        return self._command("save", self._body())

    def POST(self):
        if len(self.params) != 1:
            return self._error(404, "not-found", "Unknown operation.")
        operation = self.params[0]
        if operation == "preview":
            try:
                result = self.application.evaluate(self._body(), preview=True)
            except PolicyPermissionError:
                return self._error(403, "forbidden", "Permission denied.")
            self.request.response.setHeader("Cache-Control", "no-store")
            return result
        commands = {
            "publish": "publish",
            "disable": "disable",
            "test-signing": "test-signing",
        }
        command = commands.get(operation)
        if command is None:
            return self._error(404, "not-found", "Unknown operation.")
        body = self._body()
        candidate = body.get("values") if isinstance(body, dict) else None
        return self._command(command, candidate)

    def _command(self, command, candidate):
        expected = self.request.getHeader("If-Match")
        if expected is None:
            return self._error(428, "precondition-required", "If-Match is required.")
        if isinstance(candidate, dict) and "values" in candidate:
            candidate = candidate["values"]
        try:
            state = self.application.execute(
                command,
                candidate,
                expected_revision=expected,
            )
        except PolicyPermissionError:
            return self._error(403, "forbidden", "Permission denied.")
        except PolicyRevisionError:
            return self._error(412, "revision-mismatch", "The policy changed; reload and retry.")
        except PolicyCommandError as exc:
            result = self._error(400, "validation-failed", str(exc))
            result["diagnostics"] = exc.diagnostics
            return result
        self.request.response.setHeader("ETag", f'"{state["revision"]}"')
        return state

    def _body(self):
        value = getattr(self.request, "json", None)
        if value is not None:
            return value
        body = self.request.get("BODY", b"")
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        if not body:
            return {}
        try:
            parsed = json.loads(body)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _error(self, status, code, message):
        self.request.response.setStatus(status)
        self.request.response.setHeader("Cache-Control", "no-store")
        return {"error": {"code": code, "message": message}}
