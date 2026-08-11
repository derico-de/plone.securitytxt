"""Classic UI control panel backed by the authoritative policy application."""

from __future__ import annotations

from types import SimpleNamespace

from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from zope import schema

from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.autoform import directives
from plone.securitytxt.policy import PolicyCommandError
from plone.securitytxt.policy import PolicyRevisionError
from plone.securitytxt.policy import SecurityPolicyApplication
from plone.supermodel import model


class ISecurityPolicySettings(model.Schema):
    """Structured Security Policy authoring fields."""

    model.fieldset(
        "contact-expiry",
        label="Contact & expiry",
        fields=("contact", "expires", "preferred_languages", "canonical"),
    )
    model.fieldset(
        "disclosure",
        label="Disclosure",
        fields=("encryption", "acknowledgments", "policy", "hiring"),
    )
    model.fieldset(
        "extensions",
        label="Extension fields",
        fields=("extension_fields",),
    )
    model.fieldset(
        "signing",
        label="Signing",
        fields=("publication_mode", "signing_profile"),
    )

    contact = schema.List(
        title="Contact",
        description="Ordered contact URIs; the first is preferred.",
        value_type=schema.TextLine(title="Contact URI"),
        required=False,
    )
    expires = schema.TextLine(
        title="Expires",
        description="An exact timezone-aware ISO 8601 instant.",
        required=False,
    )
    preferred_languages = schema.List(
        title="Preferred languages",
        value_type=schema.TextLine(title="BCP 47 language tag"),
        required=False,
    )
    canonical = schema.List(
        title="Canonical",
        value_type=schema.TextLine(title="Canonical HTTPS URL"),
        required=False,
    )
    encryption = schema.List(
        title="Encryption",
        value_type=schema.TextLine(title="Encryption URI"),
        required=False,
    )
    acknowledgments = schema.List(
        title="Acknowledgments",
        value_type=schema.TextLine(title="Acknowledgments URI"),
        required=False,
    )
    policy = schema.List(
        title="Policy",
        value_type=schema.TextLine(title="Policy URI"),
        required=False,
    )
    hiring = schema.List(
        title="Hiring",
        value_type=schema.TextLine(title="Hiring URI"),
        required=False,
    )
    extension_fields = schema.List(
        title="Extension fields",
        description="Ordered Field-Name: value rows.",
        value_type=schema.TextLine(title="Extension field"),
        required=False,
    )
    publication_mode = schema.Choice(
        title="Publication mode",
        values=("unsigned", "signed"),
        default="unsigned",
        required=True,
    )
    signing_profile = schema.TextLine(
        title="Signing Profile",
        description="Deployment-owned profile identifier.",
        required=False,
    )

    directives.order_before(expires="preferred_languages")


class SecurityPolicyControlPanelForm(RegistryEditForm):
    """One guided form; no value is persisted through ``plone.registry``."""

    schema = ISecurityPolicySettings
    label = "Security Policy"
    description = "Manage the site-wide security.txt policy"
    control_panel_view = "@@overview-controlpanel"

    def update(self):
        self.application = SecurityPolicyApplication(self.context)
        self.management_state = self.application.inspect()
        self.preview = ""
        super().update()

    def getContent(self):
        state = getattr(self, "management_state", None)
        if state is None:
            self.application = SecurityPolicyApplication(self.context)
            state = self.application.inspect()
            self.management_state = state
        values = dict(state["values"])
        values["extension_fields"] = [
            f"{row['name']}: {row['value']}" for row in values.pop("extensions", [])
        ]
        return SimpleNamespace(**values)

    def _candidate(self, data):
        candidate = dict(data)
        rows = []
        for row in candidate.pop("extension_fields", []) or []:
            name, separator, value = row.partition(":")
            rows.append({"name": name.strip(), "value": value.strip() if separator else ""})
        candidate["extensions"] = rows
        return candidate

    def _extract_candidate(self):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return None
        return self._candidate(data)

    def _execute(self, command, candidate=None):
        try:
            state = self.application.execute(
                command,
                candidate,
                expected_revision=self.management_state["revision"],
            )
        except (PolicyCommandError, PolicyRevisionError) as exc:
            self.status = str(exc)
            IStatusMessage(self.request).addStatusMessage(str(exc), "error")
            return
        self.management_state = state
        IStatusMessage(self.request).addStatusMessage("Security Policy updated.", "info")
        self.request.response.redirect(self.request.getURL())

    @button.buttonAndHandler("Save draft", name="save")
    def handleSave(self, action):
        candidate = self._extract_candidate()
        if candidate is not None:
            self._execute("save", candidate)

    @button.buttonAndHandler("Validate", name="validate")
    def handleValidate(self, action):
        candidate = self._extract_candidate()
        if candidate is not None:
            result = self.application.evaluate(candidate, preview=False)
            self.status = self._diagnostic_summary(result)

    @button.buttonAndHandler("Preview", name="preview")
    def handlePreview(self, action):
        candidate = self._extract_candidate()
        if candidate is not None:
            result = self.application.evaluate(candidate, preview=True)
            self.preview = result["preview"]
            self.status = self._diagnostic_summary(result)
            self.request.response.setHeader("Cache-Control", "no-store")

    @button.buttonAndHandler("Publish", name="publish")
    def handlePublish(self, action):
        candidate = self._extract_candidate()
        if candidate is not None:
            # Publishing the current form values is still one atomic command.
            self._execute("publish", candidate)

    @button.buttonAndHandler("Disable publication", name="disable")
    def handleDisable(self, action):
        self._execute("disable")

    @button.buttonAndHandler("Test signing", name="test-signing")
    def handleTestSigning(self, action):
        self._execute("test-signing")

    @staticmethod
    def _diagnostic_summary(result):
        return (
            f"{len(result['errors'])} errors, "
            f"{len(result['blockers'])} publication blockers, "
            f"{len(result['warnings'])} warnings."
        )


class SecurityPolicyControlPanelView(ControlPanelFormWrapper):
    """Standard Plone control-panel layout wrapper."""

    form = SecurityPolicyControlPanelForm
