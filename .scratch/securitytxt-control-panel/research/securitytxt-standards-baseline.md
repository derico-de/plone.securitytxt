# security.txt standards baseline

Research date: 2026-08-08

## Answer in brief

The protocol baseline is [RFC 9116](https://www.rfc-editor.org/rfc/rfc9116.html), plus the live [IANA security.txt Fields registry](https://www.iana.org/assignments/security-txt-fields/security-txt-fields.xhtml). A current web publication needs at least one `Contact`, exactly one non-stale `Expires`, UTF-8 plain text at the HTTPS `/.well-known/security.txt` location, and field-level validation. OpenPGP clear-signing is recommended by the RFC but not mandatory; `Canonical` is also recommended—not required—when signing is used.

The live securitytxt.org generator is a useful UX reference, not a second standard. It currently exposes the eight RFC 9116 fields plus `CSAF`, validates structured values, supports repeated controls, generates text, and copies it to the clipboard. The Plone product's optional server-side signing, draft/publication lifecycle, permissions, persistent expiry warnings, REST exposure, and forward-compatible Extension Fields go beyond that generator.

## 1. Normative format

RFC 9116 defines a line-oriented, case-insensitive field-name format. Every field has a name, colon, single space, and value and appears on its own line. Blank lines are allowed; a line beginning with `#` is a comment. Lines end in either CRLF or LF. The entire file is `text/plain`, UTF-8 in Net-Unicode form. See [RFC 9116 §§2, 2.1, 2.2, and 4](https://www.rfc-editor.org/rfc/rfc9116.html#section-2).

Unless a field definition says otherwise, a field may appear repeatedly, but multiple values must not be chained into one occurrence. Field order is generally non-semantic, with one important exception: repeated `Contact` occurrences are ordered by preference. `Preferred-Languages` values explicitly have equal priority, regardless of their order. See [RFC 9116 §§2, 2.5.3, and 2.5.8](https://www.rfc-editor.org/rfc/rfc9116.html#section-2.5.3).

### RFC 9116 fields

| Field | Presence | Multiplicity | Relevant constraints |
| --- | --- | --- | --- |
| `Contact` | Required | One or more | URI syntax. Web URIs must use HTTPS; email and telephone contacts use `mailto:` and `tel:`. Repeated occurrences are in preference order. |
| `Expires` | Required | Exactly one | RFC 3339 date-time. A file is stale after this time. Less than one year into the future is recommended. |
| `Acknowledgments` | Optional | Repeated | URI; a web URI must use HTTPS. |
| `Canonical` | Optional | Repeated | URI; a web URI must use HTTPS. If present and the retrieval URI is absent from all Canonical values, the file should not be trusted. |
| `Encryption` | Optional | Repeated | URI pointing to key material or key information; never the key bytes themselves. A web URI must use HTTPS. |
| `Hiring` | Optional | Repeated | URI; a web URI must use HTTPS. |
| `Policy` | Optional | Repeated | URI; a web URI must use HTTPS. |
| `Preferred-Languages` | Optional | At most one | One or more comma-separated BCP 47 language tags of equal priority. |

The field definitions and multiplicities are normative in [RFC 9116 §2.5](https://www.rfc-editor.org/rfc/rfc9116.html#section-2.5) and reflected in the [IANA registry](https://www.iana.org/assignments/security-txt-fields/security-txt-fields.xhtml).

### Expiry details

`Expires` uses RFC 3339 syntax. RFC 9116 does not require a UTC `Z` representation; choosing UTC and uppercase `Z` is a deterministic product policy. The RFC recommends, but does not require, a value less than one year ahead. Clients should not use stale contents, and RFC 9116 says no file may be preferable to stale information. See [RFC 9116 §§2.5.5 and 5.3](https://www.rfc-editor.org/rfc/rfc9116.html#section-2.5.5).

The errata page currently lists a **reported**, not verified, technical erratum proposing uppercase `Z` in the example. It does not amend the published RFC unless its status changes. See [Erratum 7264](https://www.rfc-editor.org/errata/eid7264).

### Extensibility and the live registry

RFC 9116 establishes an Expert Review IANA registry. All later registered fields are optional, and consumers must ignore unsupported fields. Its ABNF also has an `ext-field` production using a syntactically valid field name and unstructured value. See [RFC 9116 §§2.4, 4, and 6.2](https://www.rfc-editor.org/rfc/rfc9116.html#section-2.4).

As of this research, the live IANA registry was last updated 2026-03-07 and contains two current fields beyond RFC 9116's initial eight:

| Field | Multiplicity | Registered meaning |
| --- | --- | --- |
| `CSAF` | Repeated | Link to a CSAF `provider-metadata.json` resource. |
| `Bug-Bounty` | At most one | `True` or `False` indication of whether a financial bug-bounty reward may be offered. |

Source: [IANA security.txt Fields registry](https://www.iana.org/assignments/security-txt-fields/security-txt-fields.xhtml).

Forward compatibility does not require a raw editor. Structured standard controls plus repeatable name/value Extension Fields can represent new registry entries, provided the product validates field-name syntax, prevents collisions with its first-class fields, preserves multiplicity/order, and warns when a name is not registered. Whether to hard-code first-class controls for `CSAF` and `Bug-Bounty` remains a product decision.

## 2. Discovery and HTTP behavior

For a web service, RFC 9116 requires publication under `/.well-known/security.txt` for the domain name or IP address, retrieval over HTTPS using HTTP/1.0 or later, and `Content-Type: text/plain` with charset `utf-8`. A legacy top-level `/security.txt` may additionally exist or redirect to the well-known location; if both exist, the well-known file wins. See [RFC 9116 §3](https://www.rfc-editor.org/rfc/rfc9116.html#section-3).

A file applies only to the domain or IP address from which it was retrieved, not automatically to parent or child domains. `Canonical` does not override that scope rule. Redirects are allowed, but RFC 9116 warns researchers to inspect them because an attacker can redirect to a resource they control. Directly serving a `200` representation at the well-known path is therefore the simplest product behavior, but the RFC does not forbid an HTTPS redirect. See [RFC 9116 §§3.1 and 5.2](https://www.rfc-editor.org/rfc/rfc9116.html#section-3.1).

RFC 9116 permits LF or CRLF line separators. Its errata page has one **reported**, not verified, technical erratum about a CRLF inconsistency in the signed-document ABNF. A deterministic generator should use one line-ending convention consistently and test signed output independently. See [RFC 9116 §2.2](https://www.rfc-editor.org/rfc/rfc9116.html#section-2.2) and [Erratum 7743](https://www.rfc-editor.org/errata/eid7743).

RFC 9116 does not define `Cache-Control`, `ETag`, or `Last-Modified` policy; ordinary HTTP caching rules apply under [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html). Bounding freshness so cached bytes do not outlive `Expires`, providing validators, and invalidating on Security Policy changes are sensible Plone product requirements, not RFC 9116 mandates.

RFC 9116's security considerations suggest parser limits of 32 KB per file, 2,048 characters per field, and 1,000 lines as optional defensive choices. These are client/parser suggestions rather than publisher maxima, but a generator can adopt them to maximize interoperability. See [RFC 9116 §5.4](https://www.rfc-editor.org/rfc/rfc9116.html#section-5.4).

## 3. OpenPGP clear-signing

RFC 9116 says OpenPGP cleartext signing is **RECOMMENDED**, not required. When signing is used, including `Canonical` is also **RECOMMENDED**, not required. The product may choose a stronger invariant—such as refusing to sign without a matching Canonical URI—but should label that as product policy rather than RFC compliance. See [RFC 9116 §2.3](https://www.rfc-editor.org/rfc/rfc9116.html#section-2.3).

The signed representation is the complete clear-signed document, not an extra `Signature` field. RFC 9116's signed ABNF expects the OpenPGP cleartext header, hash header, cleartext Security Policy, and armored signature. OpenPGP cleartext signing canonicalizes text for hashing and applies dash escaping; this should be delegated to a conforming implementation and verified independently. See [RFC 9116 §§2.3, 2.7, and 4](https://www.rfc-editor.org/rfc/rfc9116.html#section-2.7) and [RFC 4880 §7](https://www.rfc-editor.org/rfc/rfc4880.html#section-7).

RFC 4880 has since been obsoleted by [RFC 9580](https://www.rfc-editor.org/rfc/rfc9580.html), while RFC 9116 still normatively names RFC 4880's cleartext framework. Dependency selection must therefore balance current OpenPGP security guidance with deployed security.txt verifier compatibility; that belongs to [Evaluate OpenPGP signing approaches](../issues/05-evaluate-openpgp-approaches.md).

## 4. securitytxt.org generator parity

The live [securitytxt.org generator](https://securitytxt.org/) currently provides:

- structured authoring rather than arbitrary raw-file editing;
- required `Contact` and `Expires` controls;
- optional `Encryption`, `Acknowledgments`, `Preferred-Languages`, `Canonical`, `Policy`, `Hiring`, and `CSAF` controls;
- repeat/add-another affordances, while marking `Expires` and `Preferred-Languages` as singleton fields;
- inline format guidance and links to the relevant specification sections;
- generated text and a copy-to-clipboard action; and
- advice to publish under `/.well-known/security.txt` and consider OpenPGP signing.

The deployed page does not currently expose a `Bug-Bounty` control despite that field appearing in the live IANA registry, nor does it perform server-side signing. These observations are a dated UX snapshot, not normative requirements. The source is the first-party [securitytxt.org repository](https://github.com/securitytxt/securitytxt.org), whose GitHub metadata identifies it as the static website for securitytxt.org.

The Plone scope deliberately excludes checking arbitrary external sites. Format validation of the locally configured Security Policy remains necessary; network validation of referenced URIs would be a separate feature with SSRF, privacy, timeout, and availability implications.

## 5. Product choices left to later tickets

The following are sharp decisions not settled by the standards:

1. Whether `CSAF` and `Bug-Bounty` receive first-class controls or flow through Extension Fields.
2. Whether Extension Fields accept any syntactically valid name, require current IANA registration, or accept unknown names with a warning.
3. Which URI schemes are accepted per field beyond the RFC's explicit HTTPS rule for web URIs.
4. Whether Plone normalizes `Expires` to UTC/uppercase `Z`, caps it at one year, and refuses publication after expiry.
5. Whether Canonical values are manual, derived, or both across virtual hosts and proxy headers.
6. Whether signing requires a matching Canonical value as a stronger product invariant.
7. Whether to publish the optional legacy `/security.txt` path.
8. Whether any redirects are supported; direct publication is safer and simpler.
9. Canonical field ordering, comment support, final newline, and LF-versus-CRLF output policy.
10. Cache lifetime, validators, emergency invalidation, and CDN guidance.
11. Publisher size/field/line limits based on RFC 9116's defensive parser guidance.
12. How a release updates first-class controls as the IANA registry evolves without making live-network registry access part of every request.

These decisions are already assigned to [Define the Security Policy field model](../issues/02-define-policy-field-model.md), [Define publication and HTTP semantics](../issues/03-define-publication-http-semantics.md), and the signing tickets.

## Sources

- [RFC 9116 — A File Format to Aid in Security Vulnerability Disclosure](https://www.rfc-editor.org/rfc/rfc9116.html)
- [RFC 9116 errata](https://www.rfc-editor.org/errata/rfc9116)
- [Erratum 6946 — verified editorial cross-reference correction](https://www.rfc-editor.org/errata/eid6946)
- [Erratum 7264 — reported uppercase-`Z` correction](https://www.rfc-editor.org/errata/eid7264)
- [Erratum 7743 — reported line-ending/ABNF correction](https://www.rfc-editor.org/errata/eid7743)
- [IANA security.txt Fields registry](https://www.iana.org/assignments/security-txt-fields/security-txt-fields.xhtml)
- [securitytxt.org live generator](https://securitytxt.org/)
- [securitytxt.org first-party source repository](https://github.com/securitytxt/securitytxt.org)
- [RFC 8615 — Well-Known Uniform Resource Identifiers](https://www.rfc-editor.org/rfc/rfc8615.html)
- [RFC 9111 — HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html)
- [RFC 4880 §7 — OpenPGP Cleartext Signature Framework](https://www.rfc-editor.org/rfc/rfc4880.html#section-7)
- [RFC 9580 — OpenPGP](https://www.rfc-editor.org/rfc/rfc9580.html)
