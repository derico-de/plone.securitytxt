# Changelog

## 1.0.0b3 (unreleased)


- Fix signing against real GnuPG. The helper passed `digest_algo="SHA256"` to
  `python-gnupg`, which has no such parameter, so every signing attempt raised a
  `TypeError` inside the helper and surfaced as a generic signing failure. The digest is
  now selected with `--digest-algo SHA256`; verified end to end against GnuPG 2.4.7 and
  python-gnupg 0.5.6, including the `VALIDSIG` SHA-256 check.
- Rewrite the signing guide as a step-by-step procedure for site administrators: key
  creation commands, configuration file walkthrough, control-panel steps, outside
  verification, rotation and renewal, and a troubleshooting table.


## 1.0.0b2 (2026-09-13)

- Drop the `setuptools<81` upper bound inherited from the package template. The cap
  guarded against the removal of `pkg_resources` in setuptools 82, which this stack no
  longer needs: Plone 6.2 uses native PEP 420 namespace packages and the remaining
  `pkg_resources` imports in the dependency tree are guarded or test-only.
- Stop shipping internal working files in the sdist. The default hatchling file
  selection swept in agent transcripts, scratch notes, copier answers and the local
  Zope instance config; the sdist is now an explicit allow-list and drops from 1.8 MB
  to 44 KB.
- Ship the compiled translation catalogs. `.gitignore` excludes `*.mo` and hatchling
  honours it, so the German catalog was missing from every release so far and the
  translations never took effect in an installed site.


## 1.0.0b1 (2026-09-03)

- Add the site-wide Security Policy control panel, dedicated REST API, expiry warning,
  and RFC 9116 `/.well-known/security.txt` endpoint.
- Add deterministic retained publication artifacts and optional OpenPGP signing support.
- Translate validation diagnostics and command errors; complete the German catalog.
