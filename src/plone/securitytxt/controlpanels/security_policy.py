"""Classic UI control panel backed by the authoritative policy application."""

from __future__ import annotations

import json
from datetime import datetime
from html import escape
from types import SimpleNamespace
from urllib.parse import urlsplit

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from zope import schema
from zope.i18n import translate
from zope.interface import alsoProvides
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.autoform import directives
from plone.securitytxt.i18n import _
from plone.securitytxt.policy import PolicyCommandError
from plone.securitytxt.policy import PolicyRevisionError
from plone.securitytxt.policy import SecurityPolicyApplication
from plone.supermodel import model


PUBLICATION_MODES = SimpleVocabulary([
    SimpleTerm(value="unsigned", title=_("Unsigned")),
    SimpleTerm(value="signed", title=_("Signed")),
])
LIFECYCLE_LABELS = {
    "draft": _("Draft"),
    "published": _("Published"),
    "publication-blocked": _("Publication blocked"),
}
SIGNING_CAPABILITY_LABELS = {
    "unavailable": _("Unavailable"),
    "configured": _("Configured"),
    "verified": _("Verified"),
}


class ISecurityPolicySettings(model.Schema):
    """Structured Security Policy authoring fields."""

    model.fieldset(
        "contact-expiry",
        label=_("Contact & expiry"),
        fields=("contact", "expires", "preferred_languages", "canonical"),
    )
    model.fieldset(
        "disclosure",
        label=_("Disclosure"),
        fields=("encryption", "acknowledgments", "policy", "hiring"),
    )
    model.fieldset(
        "extensions",
        label=_("Extension fields"),
        fields=("extension_fields",),
    )
    model.fieldset(
        "signing",
        label=_("Signing"),
        fields=("publication_mode", "signing_profile"),
    )

    contact = schema.List(
        title=_("Contact"),
        description=_(
            "One contact URI per line, in preference order. Examples: "
            "mailto:security@example.com or https://example.com/security/contact"
        ),
        value_type=schema.TextLine(title=_("Contact URI")),
        required=False,
    )
    expires = schema.Datetime(
        title=_("Expires"),
        description=_(
            "Select the expiration date and time. Example: December 31, 2027 at 23:59 UTC"
        ),
        required=False,
    )
    preferred_languages = schema.TextLine(
        title=_("Preferred languages"),
        description=_(
            "Comma-separated BCP 47 language tags, in preference order. Common values: "
            "en (English), de (German), de-CH (German as used in Switzerland), "
            "or fr (French). Example: en, de-CH"
        ),
        required=False,
    )
    canonical = schema.List(
        title=_("Canonical"),
        description=_(
            "The official URL where this security.txt is published. Enter one HTTPS URL "
            "per line; each must end with /.well-known/security.txt and have no query or "
            "fragment. Usually use your site's own URL."
        ),
        value_type=schema.TextLine(title=_("Canonical HTTPS URL")),
        required=False,
    )
    encryption = schema.List(
        title=_("Encryption"),
        description=_("One encryption-key URI per line. Example: https://example.com/pgp-key.txt"),
        value_type=schema.TextLine(title=_("Encryption URI")),
        required=False,
    )
    acknowledgments = schema.List(
        title=_("Acknowledgments"),
        description=_(
            "One acknowledgments URI per line. Example: "
            "https://example.com/security/acknowledgments"
        ),
        value_type=schema.TextLine(title=_("Acknowledgments URI")),
        required=False,
    )
    policy = schema.List(
        title=_("Policy"),
        description=_(
            "One security-policy URI per line. Example: https://example.com/security/policy"
        ),
        value_type=schema.TextLine(title=_("Policy URI")),
        required=False,
    )
    hiring = schema.List(
        title=_("Hiring"),
        description=_("One security-jobs URI per line. Example: https://example.com/security/jobs"),
        value_type=schema.TextLine(title=_("Hiring URI")),
        required=False,
    )
    extension_fields = schema.List(
        title=_("Extension fields"),
        description=_(
            "One Field-Name: value row per line. Examples: Bug-Bounty: True or "
            "CSAF: https://example.com/.well-known/csaf/provider-metadata.json"
        ),
        value_type=schema.TextLine(title=_("Extension field")),
        required=False,
    )
    publication_mode = schema.Choice(
        title=_("Publication mode"),
        description=_("Choose unsigned output or output signed by a configured profile."),
        vocabulary=PUBLICATION_MODES,
        default="unsigned",
        required=True,
    )
    signing_profile = schema.TextLine(
        title=_("Signing Profile"),
        description=_("Deployment-owned profile identifier. Example: production-security-key"),
        required=False,
    )

    directives.widget("expires", default_timezone="UTC")
    directives.order_before(expires="preferred_languages")


class SecurityPolicyControlPanelForm(RegistryEditForm):
    """One guided form; no value is persisted through ``plone.registry``."""

    schema = ISecurityPolicySettings
    label = _("Security Policy")
    description = _("Manage the site-wide security.txt policy")
    control_panel_view = "@@overview-controlpanel"

    def update(self):
        self.publication_url = f"{self.context.absolute_url().rstrip('/')}/.well-known/security.txt"
        self.application = SecurityPolicyApplication(self.context)
        self.management_state = self.application.inspect()
        self.diagnostics = self.application.evaluate(self.management_state["values"], preview=True)
        self.preview = self.diagnostics["preview"]
        self.lifecycle_label = LIFECYCLE_LABELS[self.management_state["lifecycle"]]
        capability = self.management_state["signing"]["capability"]
        self.signing_capability_label = SIGNING_CAPABILITY_LABELS[capability]
        self.expiry_label = self.management_state["expiry_seconds"]
        if self.expiry_label is None:
            self.expiry_label = _("Not set")
        super().update()
        self._set_canonical_description()

    def _set_canonical_description(self):
        site_url = urlsplit(self.publication_url)
        if site_url.scheme.casefold() == "https":
            description = _(
                "The official URL where this security.txt is published. Enter one HTTPS "
                "URL per line; each must end with /.well-known/security.txt and have no "
                "query or fragment. Copy this site's URL: ${url}",
                mapping={"url": f"<code>{escape(self.publication_url)}</code>"},
            )
        else:
            description = _(
                "The official URL where this security.txt is published must use HTTPS. "
                "Canonical requires a public HTTPS URL, but this site is currently using "
                "HTTP: ${url}. Leave Canonical blank for unsigned local testing, or "
                "configure public HTTPS first.",
                mapping={"url": f"<code>{escape(self.publication_url)}</code>"},
            )
        for group in self.groups:
            if "canonical" in group.widgets:
                group.widgets["canonical"].description = description
                return

    def updateActions(self):
        super(RegistryEditForm, self).updateActions()
        enabled = self.management_state["publication_enabled"]
        self.actions["save"].title = _("Save changes") if enabled else _("Save draft")
        self.actions["save"].addClass("btn btn-primary")
        if enabled:
            del self.actions["publish"]
            message = translate(
                _("Disable publication and return 404 to anonymous clients?"),
                context=self.request,
            )
            self.actions["disable"].onclick = f"return window.confirm({json.dumps(message)})"
        else:
            del self.actions["disable"]
            mode = self.management_state["values"]["publication_mode"]
            expiry = self.management_state["values"]["expires"] or translate(
                _("the selected expiry"), context=self.request
            )
            mode_message = _("signed") if mode == "signed" else _("unsigned")
            message = translate(
                _(
                    "Publish at ${url} in ${mode} mode until ${expiry}?",
                    mapping={
                        "url": self.publication_url,
                        "mode": translate(mode_message, context=self.request),
                        "expiry": expiry,
                    },
                ),
                context=self.request,
            )
            self.actions["publish"].onclick = f"return window.confirm({json.dumps(message)})"

    def getContent(self):
        state = getattr(self, "management_state", None)
        if state is None:
            self.application = SecurityPolicyApplication(self.context)
            state = self.application.inspect()
            self.management_state = state
        values = dict(state["values"])
        if values["expires"]:
            values["expires"] = datetime.fromisoformat(values["expires"].replace("Z", "+00:00"))
        values["preferred_languages"] = ", ".join(values["preferred_languages"])
        values["extension_fields"] = [
            f"{row['name']}: {row['value']}" for row in values.pop("extensions", [])
        ]
        content = SimpleNamespace(**values)
        alsoProvides(content, ISecurityPolicySettings)
        return content

    def _candidate(self, data):
        candidate = dict(data)
        languages = candidate.get("preferred_languages", "") or ""
        candidate["preferred_languages"] = [
            language.strip() for language in languages.split(",") if language.strip()
        ]
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
            if isinstance(exc, PolicyCommandError) and exc.diagnostics:
                self.diagnostics = exc.diagnostics
            self.status = str(exc)
            IStatusMessage(self.request).addStatusMessage(str(exc), "error")
            return
        self.management_state = state
        IStatusMessage(self.request).addStatusMessage(_("Security Policy updated."), "info")
        self.request.response.redirect(self.request.getURL())

    @button.buttonAndHandler(_("Save draft"), name="save")
    def handleSave(self, action):
        candidate = self._extract_candidate()
        if candidate is not None:
            self._execute("save", candidate)

    @button.buttonAndHandler(_("Validate"), name="validate")
    def handleValidate(self, action):
        candidate = self._extract_candidate()
        if candidate is not None:
            result = self.application.evaluate(candidate, preview=False)
            self.diagnostics = result
            self.status = self._diagnostic_summary(result)

    @button.buttonAndHandler(_("Preview"), name="preview")
    def handlePreview(self, action):
        candidate = self._extract_candidate()
        if candidate is not None:
            result = self.application.evaluate(candidate, preview=True)
            self.diagnostics = result
            self.preview = result["preview"]
            self.status = self._diagnostic_summary(result)
            self.request.response.setHeader("Cache-Control", "no-store")

    @button.buttonAndHandler(_("Publish"), name="publish")
    def handlePublish(self, action):
        candidate = self._extract_candidate()
        if candidate is not None:
            # Publishing the current form values is still one atomic command.
            self._execute("publish", candidate)

    @button.buttonAndHandler(_("Disable publication"), name="disable")
    def handleDisable(self, action):
        self._execute("disable")

    @button.buttonAndHandler(_("Test signing"), name="test-signing")
    def handleTestSigning(self, action):
        candidate = self._extract_candidate()
        if candidate is not None:
            self._execute("test-signing", candidate)

    @staticmethod
    def _diagnostic_summary(result):
        return _(
            "${errors} errors, ${blockers} publication blockers, ${warnings} warnings.",
            mapping={
                "errors": len(result["errors"]),
                "blockers": len(result["blockers"]),
                "warnings": len(result["warnings"]),
            },
        )


class SecurityPolicyControlPanelView(ControlPanelFormWrapper):
    """Standard Plone control-panel layout with lifecycle and preview."""

    form = SecurityPolicyControlPanelForm
    index = ViewPageTemplateFile("security_policy.pt")
