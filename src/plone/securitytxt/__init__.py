"""Plone security.txt."""

from plone.securitytxt.signing import initialize_profile_cache


# Load public profile metadata once per application process. This never imports
# python-gnupg and keeps anonymous publication free of configuration-file I/O.
initialize_profile_cache()
