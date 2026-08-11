# Deployment

The anonymous endpoint is `<Plone site root>/.well-known/security.txt`. It supports `GET` and `HEAD`; no legacy `/security.txt` redirect is installed. If Plone is mounted below the public origin root, configure the reverse proxy to route the origin-root `/.well-known/security.txt` to this site-root path.

TLS termination, HTTP-to-HTTPS redirection, trusted proxy headers, and VirtualHostMonster configuration belong to deployment infrastructure. The add-on trusts only the externally resolved URL supplied by Zope; it does not parse `Forwarded` or `X-Forwarded-*` itself. Add every public hostname as an explicit Canonical URL when Canonical enforcement is wanted.

Successful responses are public for at most five minutes and never beyond policy expiry. Exact retained bytes receive a strong ETag. Correctness does not depend on active proxy purging. Ensure caches honor `must-revalidate`; non-success responses are `no-store`.

Uninstall deletes the site annotation and retained artifacts. It never changes deployment-owned GnuPG homes or signing configuration.
