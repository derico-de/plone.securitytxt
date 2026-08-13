# Define publication and HTTP semantics

Type: grilling
Status: resolved
Blocked by: 01 — [Establish the security.txt standards baseline](01-establish-standards-baseline.md)

## Question

What exact public contract should `<Plone site root>/.well-known/security.txt` implement? Decide behavior for draft, disabled, invalid, expired, and operational-error states; virtual-host and Canonical URL handling; response media type and encoding; deterministic serialization; redirects; cache headers, validators, and invalidation; anonymous access; and the documented reverse-proxy responsibility for sites mounted below the public origin root.

## Answer

### Route, methods, and access

The add-on exposes exactly `<Plone site root>/.well-known/security.txt`. It does not expose or redirect the legacy `<Plone site root>/security.txt` location, and acquisition must not create folder-relative variants. Deployments where the Plone site is not mounted at the public origin root must route the public origin's `/.well-known/security.txt` to this site-root endpoint.

The endpoint supports anonymous `GET` and `HEAD`. `HEAD` returns the same status and headers as `GET`, including the representation's `Content-Length` when known, but no body. Other methods return `405 Method Not Allowed` with `Allow: GET, HEAD`.

### State and status contract

The endpoint evaluates the current effective Security Policy state before conditional-request validators:

- Published returns `200 OK`, or `304 Not Modified` for a matching valid conditional request.
- Draft, explicitly disabled, expired, or Canonical-host mismatch returns `404 Not Found`.
- An enabled policy blocked by an operational failure, including signing failure, returns `503 Service Unavailable` and never falls back to stale or unsigned content.
- A persisted enabled state that is corrupt or invalid despite accepted-write validation also returns `503` rather than exposing malformed content.

Non-success responses have generic UTF-8 plain-text bodies that reveal no policy or operational details. `404`, `503`, and `405` use `Cache-Control: no-store`; `503` also includes `Retry-After: 300`. `HEAD` suppresses these bodies too.

### Deterministic representation

A successful response uses `Content-Type: text/plain; charset=utf-8`. The unsigned renderer emits UTF-8 without a byte-order mark, canonical field-name casing, exact `Field-Name: value` syntax, CRLF after every line including the final line, and the field/value order fixed by the Security Policy model. The signed representation is the complete OpenPGP clear-signed form of those canonical unsigned bytes and retains the same media type.

Repeated requests for unchanged policy and signing inputs must be byte-identical. Signed output must therefore be generated or cached so that per-request timestamps or signatures cannot alter the bytes. The response never varies by accepted media type, language, authenticated identity, request host, or other request metadata. The application emits no `Vary`, `Content-Language`, or `Content-Disposition` header. Infrastructure may negotiate transport compression and add `Vary: Accept-Encoding` where appropriate.

### Caching and invalidation

Every successful representation has a strong, content-derived ETag calculated from the exact served bytes. A matching `If-None-Match` returns `304` only after the policy still qualifies for a successful response and the request passes Canonical matching. The endpoint does not emit `Last-Modified` or an HTTP `Expires` header.

Successful responses use `Cache-Control: public, max-age=<n>, must-revalidate`, where `<n>` is the smaller of 300 seconds and the whole seconds remaining until the Security Policy's `Expires` instant. A cached representation can therefore never remain fresh beyond policy expiry. Changes to policy values or ordering, publication state, signing configuration, or signing key immediately invalidate any local rendered representation and produce new bytes and a new ETag. External caches may retain an earlier successful response only for the accepted freshness window.

### Virtual hosting and Canonical enforcement

The add-on relies exclusively on the externally visible URL already resolved by Plone/Zope virtual hosting. It does not independently parse or trust raw `Forwarded` or `X-Forwarded-*` headers. Trusted-proxy configuration, TLS termination, public-root routing, and HTTP-to-HTTPS redirection belong to deployment infrastructure; the add-on does not enforce or redirect the transport scheme itself.

When the Security Policy has Canonical values, the resolved request URL must match one or the endpoint returns `404`. Comparison normalizes only scheme and hostname case, IDNA hostname representation, and omission of default port `443`; the path and percent-encoding must match exactly. Credentials, query, and fragment are already forbidden by the field model. Multiple public hostnames must each have a Canonical entry. An unsigned policy without Canonical values may be served through any host correctly routed to the Plone site.

### Auxiliary headers

Successful responses include `X-Content-Type-Options: nosniff`. The application does not add CORS headers or application-specific security-policy headers. Standard server-managed headers such as `Date` remain unaffected.
