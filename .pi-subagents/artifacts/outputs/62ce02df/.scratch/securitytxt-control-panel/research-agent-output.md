# Research: Confirm the Plone integration seams

## Summary

Plone 6 has supported seams for every requested integration: a `plone.app.registry`/`z3c.form` control panel, the generic `@controlpanels` REST API (or a scaffolded custom REST service), add-on permissions and GenericSetup role mappings, Zope traversal, registry-backed site-local settings, Classic UI viewlets, cache-purge events, and versioned GenericSetup upgrades. The platform does **not** dictate the policy schema, whether REST writes use the generic or a domain-specific endpoint, how the two-segment well-known resource is implemented, or the cache strategy; those are architectural decisions and should be tested across the supported Plone 6 matrix.

## Findings

1. **Classic UI control panel — established constraint.** Plone Classic UI forms use `z3c.form`, integrated by `plone.z3form` and `plone.app.z3cform`; `plone.app.registry` provides `RegistryEditForm` and `ControlPanelFormWrapper` for schema-backed control panels. The current plonecli templates include a `controlpanel` subtemplate specifically described as a registry-backed settings form. The implementation plan should therefore begin with `plonecli add controlpanel --defaults -d controlpanel_name="SecurityPolicy" ...`, then extend the generated schema/form rather than hand-writing registrations. [Plone 6 forms documentation](https://6.docs.plone.org/classic-ui/forms.html) · [`plone.app.registry` README](https://github.com/plone/plone.app.registry/blob/master/README.rst) · [plone-copier-templates source](https://github.com/plone/plone-copier-templates)

2. **Control-panel shape — architectural choice.** A conventional registry schema and generated `RegistryEditForm` are sufficient for standard fields and repeatable widgets. Cross-field publication rules, generation/signing, and atomic invalidation should be delegated by both UI and REST to one domain/application service; they should not be hidden only in a form button handler. Custom widgets or a custom form are choices only if the standard generated form cannot express the repeatable Extension Fields and status feedback.

3. **REST exposure — established constraint.** `plone.restapi` exposes registered control panels through `GET /@controlpanels`, `GET /@controlpanels/{id}`, and update operations documented for the specific control panel. REST use is additionally subject to both the general “Use REST API” permission and the permission of the underlying operation/control panel. A separately named service is also a supported add-on seam and is scaffolded by `plonecli add restapi_service`; site-root services can target `Products.CMFPlone.interfaces.IPloneSiteRoot`. [Official `@controlpanels` documentation](https://plonerestapi.readthedocs.io/en/latest/endpoints/controlpanels.html) · [Official authentication/permission documentation](https://plonerestapi.readthedocs.io/en/latest/usage/authentication.html) · [`plone.restapi` service source](https://github.com/plone/plone.restapi/tree/main/src/plone/restapi/services) · [plone-copier-templates source](https://github.com/plone/plone-copier-templates)

4. **REST endpoint choice — architectural choice.** Prefer the generic `@controlpanels/{id}` seam only if its write path can be made to call the same validation/publication transaction used by Classic UI. Otherwise scaffold a site-root custom service for reads/writes and leave the standard control-panel registration for discovery/UI. Do not permit a generic registry PATCH to bypass enablement validation, signed-artifact regeneration, or invalidation. Whichever route is selected, require the dedicated management permission on mutations; published `security.txt` remains anonymous.

5. **Dedicated permission — established constraint.** Zope/Plone add-ons define a named permission in ZCML, protect browser views/services/viewlets with that permission, and assign initial role mappings through a GenericSetup `rolemap.xml`. Authentication alone is not authorization, and the REST layer continues to apply ordinary Plone permissions. The add-on should define one permission such as `plone.securitytxt: Manage security policy`, map it initially to `Manager` and `Site Administrator`, and use it consistently on the control panel, REST mutation service, and warning viewlet. [Zope browser-view registration (`permission` attribute)](https://6.docs.plone.org/classic-ui/views.html#register-a-view) · [GenericSetup source and handlers](https://github.com/zopefoundation/Products.GenericSetup) · [`plone.restapi` authentication documentation](https://plonerestapi.readthedocs.io/en/latest/usage/authentication.html)

6. **Permission policy — architectural choice.** Whether read-only policy state is visible to other authenticated users is a product decision. The stated requirements support the narrow rule: management state and warning are visible only with the dedicated permission; the public representation is anonymous. UI hiding is not a security boundary—server-side permission checks remain mandatory.

7. **`/.well-known/security.txt` traversal — established constraint.** Zope publishes URLs by traversing path segments; therefore `.well-known/security.txt` is two traversal names, not one browser-view name containing a slash. A view or traversal object can participate in further traversal through publisher traversal hooks. Registration must be on `IPloneSiteRoot`, not the Zope application root, so each Plone site owns its endpoint. [Zope publisher documentation](https://zope.readthedocs.io/en/latest/zopebook/Publishing.html) · [ZPublisher traversal implementation](https://github.com/zopefoundation/Zope/blob/master/src/ZPublisher/BaseRequest.py) · [Plone 6 view registration](https://6.docs.plone.org/classic-ui/views.html)

8. **Well-known implementation — architectural choice.** Register a site-root, anonymously accessible `.well-known` traversal/browser object that accepts exactly one remaining segment, `security.txt`, and rejects all others; the leaf returns the retained deterministic bytes and HTTP headers. An `IPublishTraverse` implementation (or equivalent publisher-supported traversal hook) is preferable to modifying the site object or Zope application root. Add traversal tests for `/Plone/.well-known/security.txt`, wrong leaf names, acquisition attempts, anonymous access, and VirtualHostMonster/proxy URLs. Mapping origin-root `/.well-known/security.txt` to a Plone site mounted below the origin remains a reverse-proxy responsibility, as the project map already states.

9. **Site-scoped settings — established constraint.** `plone.registry` is the standard persistent settings store and `plone.app.registry` supplies UI and GenericSetup integration. Records can be generated from an interface and loaded by `registry.xml`; an installed Plone site has its own local registry utility, so records are site-local rather than process-global. [Official `plone.registry` source/README](https://github.com/plone/plone.registry) · [`plone.app.registry` README, including GenericSetup XML](https://github.com/plone/plone.app.registry/blob/master/README.rst)

10. **Storage model — architectural choice.** Put the single policy, lifecycle flags, normalized values, selected signing-profile identifier/revision, retained artifact metadata, and immutable artifact bytes (if sizes remain small) under one add-on registry-schema prefix. Deployment secrets must not be registry records. A dedicated persistent object is also supported, but adds traversal/lifecycle/upgrade complexity without a demonstrated need. Treat artifact replacement and settings changes as one ZODB transaction; do not derive or sign in the anonymous request.

11. **Every-page expiry warning — established constraint.** Classic UI viewlets are the supported conflict-free mechanism for contributing HTML to standard page chrome, and plonecli supplies a `viewlet` subtemplate with standard viewlet managers. A viewlet registration can itself be protected by the dedicated permission; its update/render logic can additionally suppress output unless the policy is within the 30-day window or expired. [Plone 6 viewlets documentation](https://6.docs.plone.org/classic-ui/viewlets.html) · [plone-copier-templates source](https://github.com/plone/plone-copier-templates)

12. **Warning behavior — architectural choice and limitation.** Use a lightweight, non-dismissible (or request-only dismissible) Classic UI viewlet in a site-wide manager such as `plone.portaltop`/`plone.abovecontent`, scaffolded with `plonecli add viewlet`. “Persistent” should mean it is recomputed on every Classic UI page request and cannot be permanently dismissed while the condition holds. A backend viewlet cannot make a banner appear in Volto or arbitrary frontends; REST should expose warning/status data if frontend consumers need it, but building a Volto component is out of scope.

13. **Cached-output invalidation — established constraint.** Plone supports HTTP caching policies and active purge integration through `plone.app.caching`/`plone.cachepurging`; the latter defines purge events and `IPurgePaths` adapters so add-ons can identify paths affected by a change. HTTP validators do not retract an already-fresh object from an external cache by themselves. [Official `plone.app.caching` source](https://github.com/plone/plone.app.caching) · [Official `plone.cachepurging` source and README](https://github.com/plone/plone.cachepurging)

14. **Invalidation design — architectural choice.** Avoid a second mutable in-process representation cache: retain canonical bytes plus a content-derived strong ETag/revision and read them directly. On every successful policy/signing-profile transition, atomically replace/clear the artifact, change the ETag, and emit the cache-purge event for the site-relative and virtual-host public well-known path when active purging is installed/configured. Also bound `max-age` by the earlier of the chosen cache limit and policy expiry. Purging shared reverse proxies is deployment-dependent, so document that guarantee and test configured purge integration; without it, bounded freshness is the only portable guarantee.

15. **GenericSetup and upgrades — established constraint.** Initial installation data belongs in a versioned default GenericSetup profile: control-panel registration, registry records, role mappings, browser-layer/configuration as appropriate. Changes needed by already-installed sites require registered upgrade steps; merely changing profile XML or bumping `metadata.xml` does not migrate them. The plonecli-supported route is `plonecli add upgrade_step --defaults -d upgrade_step_title="…"`, then implement the generated handler to reimport the precise step and/or migrate records and add an upgrade test. [GenericSetup source](https://github.com/zopefoundation/Products.GenericSetup) · [Plone add-on upgrade documentation](https://6.docs.plone.org/backend/upgrading/add-on-upgrade.html) · [plone-copier-templates source](https://github.com/plone/plone-copier-templates)

16. **Upgrade policy — architectural choice.** Keep profile versions monotonic and migrations idempotent. Explicitly migrate schema renames/type changes, legacy publication state, retained artifact format, and permission mappings; do not overwrite administrator values by blindly reimporting registry defaults. A changed `rolemap.xml`, `registry.xml`, or control-panel registration that must affect installed sites needs an upgrade step. Uninstall behavior (retain versus delete policy records/artifacts) must be decided and documented before implementation.

17. **Plone 6.0+ compatibility — established constraint.** Plone 6 minors differ in supported Python/dependency ranges and Plone 6 made the site root a Dexterity object. The package should declare its actual `Plone >= 6.0` compatibility, avoid relying on an unguarded newer-minor API, and test the oldest supported 6.0 release plus current supported 6.x versions. Scaffold with a current `backend_addon` template and choose explicit Plone versions in CI; do not assume that generating against only the newest template proves 6.0 compatibility. [Official Plone 5.2→6.0 upgrade notes](https://6.docs.plone.org/backend/upgrading/version-specific-migration/upgrade-to-60.html) · [Plone release schedule](https://plone.org/download/release-schedule) · [plone-copier-templates source](https://github.com/plone/plone-copier-templates)

18. **Recommended implementation seam set — planning conclusion.** Scaffold: `controlpanel`, `viewlet`, and `upgrade_step`; scaffold `restapi_service` only if the generic `@controlpanels` write seam cannot enforce the shared domain transaction. Hand-add only the traversal-specialized well-known publisher after confirming there is no suitable subtemplate. Use one registry schema, one application service for UI/REST mutations, one dedicated permission, a retained artifact with derived ETag, and optional purge-event integration. This is an architectural recommendation built on the established mechanisms above, not a claim that Plone mandates this layout.

## Sources

- Kept: [Plone 6 Classic UI forms](https://6.docs.plone.org/classic-ui/forms.html) — official statement of the `z3c.form` stack.
- Kept: [Plone 6 views](https://6.docs.plone.org/classic-ui/views.html) — official view registration and permission seam.
- Kept: [Plone 6 viewlets](https://6.docs.plone.org/classic-ui/viewlets.html) — official every-page Classic UI contribution mechanism.
- Kept: [`plone.app.registry` README](https://github.com/plone/plone.app.registry/blob/master/README.rst) — authoritative control-panel and GenericSetup examples.
- Kept: [`plone.registry`](https://github.com/plone/plone.registry) — authoritative persistence API/source.
- Kept: [`plone.restapi` control-panel docs](https://plonerestapi.readthedocs.io/en/latest/endpoints/controlpanels.html) — official REST contract.
- Kept: [`plone.restapi` services source](https://github.com/plone/plone.restapi/tree/main/src/plone/restapi/services) — authoritative service registrations/implementations.
- Kept: [Zope publisher docs/source](https://zope.readthedocs.io/en/latest/zopebook/Publishing.html) — authoritative traversal behavior.
- Kept: [`plone.cachepurging`](https://github.com/plone/plone.cachepurging) and [`plone.app.caching`](https://github.com/plone/plone.app.caching) — authoritative purge/cache seams.
- Kept: [`Products.GenericSetup`](https://github.com/zopefoundation/Products.GenericSetup) and [Plone add-on upgrade docs](https://6.docs.plone.org/backend/upgrading/add-on-upgrade.html) — authoritative profiles/upgrades.
- Kept: [plone-copier-templates](https://github.com/plone/plone-copier-templates) — authoritative generator source corresponding to the supplied plonecli workflow.
- Dropped: blogs, Stack Overflow answers, and third-party add-ons — excluded because the ticket requires primary sources.
- Dropped: legacy Plone 4/5 tutorials — excluded where current Plone 6 docs or maintained source establish the same seam.

## Gaps

- The generic `@controlpanels/{id}` mutation path must be prototyped against the exact minimum `plone.restapi` version selected for Plone 6.0 to confirm that custom validation and post-save side effects can be shared without a separate service.
- Zope traversal should be proven with a minimal integration test before freezing `IPublishTraverse` versus another traversal hook, especially for dotted names, acquisition hardening, and VirtualHostMonster URLs.
- Active purge behavior and the exact URLs sent to a configured proxy depend on deployment cache rules; no add-on can guarantee immediate eviction from an unmanaged external cache.
- “Plone 6.0+” is open-ended. Pin the tested minor/Python matrix and revisit it for each release; source compatibility with future Plone minors cannot be guaranteed in advance.
- Decide uninstall retention and whether the retained signed artifact belongs directly in registry records or in a small dedicated persistent object after measuring realistic artifact sizes.

## Validation

Research-only artifact written to `.pi-subagents/artifacts/outputs/62ce02df/.scratch/securitytxt-control-panel/research-agent-output.md`. No ticket, map, `CONTEXT.md`, source, test, or requested in-repository research path was edited because the runtime output-path override was authoritative.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Concrete integration findings and architectural recommendations are recorded in .pi-subagents/artifacts/outputs/62ce02df/.scratch/securitytxt-control-panel/research-agent-output.md; residual risks are listed under Gaps. No code severity applies to this research-only task."
    }
  ],
  "changedFiles": [
    ".pi-subagents/artifacts/outputs/62ce02df/.scratch/securitytxt-control-panel/research-agent-output.md"
  ],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "Read ticket, map, CONTEXT.md, issue-tracker docs, and plonecli SKILL.md plus reference/add.md, reference/templates.md, and reference/create.md",
      "result": "passed",
      "summary": "All required local planning and skill inputs were inspected."
    },
    {
      "command": "Focused primary-source web research across official Plone 6, plone.restapi, Zope, GenericSetup, caching, registry, and plone-copier-template sources",
      "result": "passed",
      "summary": "Primary sources supporting all eight requested integration seams were identified and linked; rate-limited redundant searches were omitted from evidence."
    },
    {
      "command": "Implementation test suite",
      "result": "not-run",
      "summary": "Not applicable to a research/planning-only task with no implementation changes."
    }
  ],
  "validationOutput": [
    "Confirmed supported mechanisms for Classic UI control panel scaffolding, REST exposure, a dedicated permission, two-segment site-root traversal, site-local registry storage, permission-gated Classic UI warning viewlet, cache purge/invalidation, and GenericSetup upgrades.",
    "Separated platform constraints from architectural choices in each seam.",
    "Only the authoritative runtime output artifact was written."
  ],
  "residualRisks": [
    "Prototype the generic @controlpanels write path on the minimum supported plone.restapi version.",
    "Integration-test dotted two-segment traversal and VirtualHostMonster behavior.",
    "External cache eviction depends on deployment-owned purge configuration.",
    "The future-open-ended Plone 6.0+ matrix requires an explicitly maintained CI policy."
  ],
  "noStagedFiles": true,
  "diffSummary": "Added one linked Markdown research artifact; no implementation or project planning files changed.",
  "reviewFindings": [
    "no blockers",
    "medium: generic REST control-panel writes need a minimum-version prototype before architecture freeze",
    "medium: exact traversal hook and active-purge URL behavior need integration tests"
  ],
  "manualNotes": "No git staging operation was performed. The runtime provided no shell/git-status tool, so noStagedFiles reflects this agent's actions rather than an independent repository-state check."
}
```
