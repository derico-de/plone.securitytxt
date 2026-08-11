"""GenericSetup handlers for plone.securitytxt."""

from zope.annotation.interfaces import IAnnotations
from zope.component.hooks import getSite
from zope.interface import implementer

from plone.base.interfaces import INonInstallable
from plone.securitytxt.policy import ANNOTATION_KEY
from plone.securitytxt.policy import new_record


@implementer(INonInstallable)
class HiddenProfiles:
    """Hide the destructive uninstall profile from the add-ons list."""

    def getNonInstallableProfiles(self):
        return ["plone.securitytxt:uninstall"]


def install(context):
    """Create the site record once; reinstall must preserve existing state."""
    site = getSite()
    annotations = IAnnotations(site)
    if ANNOTATION_KEY not in annotations:
        annotations[ANNOTATION_KEY] = new_record()


def uninstall(context):
    """Remove site-owned policy values and retained public artifacts."""
    site = getSite()
    IAnnotations(site).pop(ANNOTATION_KEY, None)
