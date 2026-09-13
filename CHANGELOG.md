# Changelog

## 1.0.0b2 (unreleased)


- Drop the `setuptools<81` upper bound inherited from the package template. The cap
  guarded against the removal of `pkg_resources` in setuptools 82, which this stack no
  longer needs: Plone 6.2 uses native PEP 420 namespace packages and the remaining
  `pkg_resources` imports in the dependency tree are guarded or test-only.


## 1.0.0b1 (2026-09-03)

- Add the site-wide Security Policy control panel, dedicated REST API, expiry warning,
  and RFC 9116 `/.well-known/security.txt` endpoint.
- Add deterministic retained publication artifacts and optional OpenPGP signing support.
- Translate validation diagnostics and command errors; complete the German catalog.
