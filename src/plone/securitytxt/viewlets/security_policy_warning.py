"""Permission-gated Classic UI expiry warning."""

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component.hooks import getSite

from plone.app.layout.viewlets.common import ViewletBase
from plone.securitytxt.i18n import _
from plone.securitytxt.policy import PolicyPermissionError
from plone.securitytxt.policy import SecurityPolicyApplication


class SecurityPolicyWarning(ViewletBase):
    """Presentation-only adapter for approaching or passed expiry."""

    index = ViewPageTemplateFile("security_policy_warning.pt")

    def update(self):
        super().update()
        site = getSite()
        try:
            self.state = SecurityPolicyApplication(site).inspect()
        except PolicyPermissionError:
            self.available = False
            return
        self.available = self.state["show_expiry_warning"]
        seconds = self.state["expiry_seconds"]
        if seconds is None or seconds <= 0:
            self.message = _("The published Security Policy has expired.")
        else:
            days = max(0, seconds // (24 * 60 * 60))
            self.message = _(
                "The Security Policy expires in ${days} days.",
                mapping={"days": days},
            )
        self.review_url = f"{site.absolute_url()}/@@security-policy-controlpanel"
