# Security Policy administration

Install the `plone.securitytxt` GenericSetup profile, then open **Site Setup → Security Policy**. Management requires the dedicated **Manage Security Policy** permission, granted to Manager and Site Administrator by default.

The site has one language-independent policy. Drafts may be incomplete, but populated values must be valid. Saving does not publish. **Publish** validates the whole policy and atomically retains the exact public bytes. **Disable publication** returns the endpoint to `404`.

The form groups Contact and expiry, disclosure links, ordered extension fields, and signing. Contact order is preference order. Expiry is an exact timezone-aware instant. Extension rows use `Field-Name: value`; first-class names cannot be repeated as extensions. Preview is unsigned, non-public, `no-store`, and has no persistence or signing side effects.

A published policy enters **Publication Blocked** at expiry. Managers see a non-dismissible Classic UI warning beginning exactly 30 days before expiry. Setting a future expiry restores publication; there are no email or scheduled notifications.
