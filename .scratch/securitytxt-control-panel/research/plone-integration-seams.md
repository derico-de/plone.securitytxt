# Plone 6 integration seams for `plone.securitytxt`

## Research question

Which supported Plone 6 mechanisms can implement the planned site-wide Security Policy control panel, REST contract, anonymous well-known resource, authorized expiry warning, cache invalidation, and install/upgrade lifecycle?

## Conclusion

Plone 6 provides a supported seam for every requested integration. The conventional foundation is a registry-backed `z3c.form` control panel, ordinary Zope permissions plus GenericSetup role mappings, a site-root traversal component for the two-segment well-known path, a Classic UI viewlet, `plone.restapi` control-panel or custom-service APIs, and versioned GenericSetup profiles and upgrade steps.

Those mechanisms do **not** decide the application architecture. In particular, Plone does not decide whether all policy state belongs in registry records, whether REST writes may use generic `@controlpanels` PATCH, which traversal hook should own `.well-known/security.txt`, or whether shared-cache purging is a required dependency. Those choices belong in [Choose the Plone integration architecture](../issues/08-choose-integration-architecture.md), with the proof points listed below.

## Established platform constraints

### 1. Classic UI control panel

- Classic UI uses `z3c.form`, integrated by `plone.z3cform`, `plone.app.z3cform`, and `plone.autoform`.[^plone-forms]
- `plone.app.registry` provides `RegistryEditForm` and `ControlPanelFormWrapper` for schema-backed control panels. Its documented registration targets the Plone site root and installs the configlet through `controlpanel.xml`.[^app-registry]
- The current plonecli catalogue includes a `controlpanel` subtemplate described as a registry-backed settings form. The implementation must begin with the scaffold rather than hand-writing the artifact:

  ```shell
  plonecli add controlpanel --defaults \
    -d controlpanel_name="SecurityPolicy" \
    -d controlpanel_title="Security Policy"
  ```

  The generated schema, form, ZCML, profile files, and tests may then be adapted.[^plonecli-templates]
- Standard field and widget validation is supported. Cross-field publication rules and effects such as artifact regeneration are application behavior, not something the generated form settles.

### 2. `plone.restapi` exposure

- `plone.restapi` exposes control panels through `GET /@controlpanels`, `GET /@controlpanels/{id}`, and `PATCH /@controlpanels/{id}`. Registry-backed panels expose their schema and data; non-registry panels can provide custom implementations.[^rest-controlpanels]
- Generic control-panel PATCH invokes field deserialization/validation and `IManagerValidator`, but it does not execute this add-on's Classic UI form button handlers.[^rest-controlpanel-source]
- In the `plone.restapi` version pinned by the Plone 6.0.0 baseline, generic `@controlpanels` methods are registered with the global `plone.app.controlpanel.Overview` permission. The panel serializer/deserializer does not automatically enforce the configlet or browser-page permission. A dedicated add-on permission therefore does **not** automatically protect the generic REST panel.[^rest-controlpanel-source]
- `@registry` can also mutate registry records, but it is a low-level settings API and must not become a path that bypasses the dedicated permission or publication invariants.[^rest-controlpanels]
- plonecli also provides `restapi_service`; it can scaffold a service registered for `IPloneSiteRoot` when a domain-specific API is needed.[^plonecli-templates]
- The later architecture must prove a REST boundary that preserves the dedicated permission, cross-field rules, publication effects, and atomic invalidation. Plone supports several component seams but does not select that boundary for this add-on.

### 3. Dedicated management permission

- Add-ons declare named permissions in ZCML; browser pages and viewlets have a `permission` registration attribute, and custom REST services remain subject to normal Plone/Zope authorization.[^plone-views][^plone-viewlets][^rest-auth][^zope-permissions]
- Initial role-to-permission mappings are installation data and belong in GenericSetup `rolemap.xml`.[^genericsetup-rolemap] The map's established product decision is to map the dedicated management permission to `Manager` and `Site Administrator` by default.
- The same server-side permission must protect the control panel, all management API operations, and the warning. Merely hiding UI is not authorization, and generic `@controlpanels` cannot be assumed to inherit the control panel's permission.
- The public `security.txt` representation is a separate anonymous-read surface; it must not inherit the management permission.

### 4. `/.well-known/security.txt` publication

- Zope publishes URLs by traversing path segments. `.well-known/security.txt` is therefore a `.well-known` segment followed by a `security.txt` segment, not one browser-view name containing a slash.[^zope-traversal]
- Publisher traversal can be extended with a traversal object/hook such as `IPublishTraverse`; browser pages are themselves normal supported traversal components.[^zope-traversal][^plone-views]
- The registration must be rooted at `IPloneSiteRoot`, not the Zope application root, so each Plone site owns one Security Policy and one endpoint.
- An add-on cannot make an internally mounted site appear automatically at the public origin-root path. Reverse-proxy routing remains deployment-owned.
- The exact `.well-known` traversal implementation is not prescribed by Plone and needs an integration proof for dotted names, rejected extra segments, acquisition hardening, anonymous access, and VirtualHostMonster URLs.

### 5. Site-scoped persistence

- `plone.registry` is the standard store for configurable, user-editable settings. In Plone it is a local utility, so each Plone site has site-local records.[^app-registry]
- `plone.app.registry` supplies GenericSetup integration and can create records from a schema interface in `registry.xml`.[^app-registry]
- Registry values are deliberately constrained: the registry is not an arbitrary object store and primarily accepts supported persistent primitive/collection field types.[^app-registry]
- The policy schema and simple lifecycle settings fit the registry seam. Whether repeatable Extension Fields and retained signed-artifact bytes should also be registry values, or instead live in one small dedicated persistent object, remains an architecture choice. Deployment secrets may not use either site-owned store.
- Registry writes emit add, remove, and modify events, providing a supported observation seam, but an event subscriber alone does not make a multi-record update atomic at the domain level.[^app-registry]

### 6. Persistent authorized expiry warning

- Classic UI viewlets are the supported conflict-free mechanism for adding HTML snippets to standard page chrome. Viewlets support `update()`/`render()`, conditional output, layers, viewlet managers, and a registration-level permission.[^plone-viewlets]
- plonecli provides a `viewlet` subtemplate. The warning should be scaffolded into a global manager rendered by standard Classic UI pages, then conditionally render only for a user with the dedicated permission when the 30-day/expired condition holds. Coverage must verify all supported Classic UI page templates that promise the warning.[^plonecli-templates]
- A Classic UI viewlet cannot display a warning in Volto or arbitrary frontends. A REST-readable status can preserve a frontend-independent contract, but a custom Volto component is outside this map.
- “Persistent” can be satisfied without jobs or email by evaluating the warning condition on each authorized Classic UI page request; permanent dismissal would contradict the current requirement while the condition remains true.

### 7. Cached-output invalidation

- `plone.app.caching` supplies Plone caching policy/configuration, while `plone.cachepurging` supports active proxy purge integration.[^app-caching][^cachepurging]
- `plone.cachepurging` initiates a purge with a `z3c.caching.purge.Purge` event and discovers affected paths through named `IPurgePaths` adapters. Purge paths can be virtual-host-relative or domain-root-absolute.[^cachepurging]
- Purges are queued only when purging is enabled/configured and are sent after a successful request transaction. An unmanaged external cache cannot be forcibly invalidated by the add-on.[^cachepurging]
- Strong ETags and bounded `max-age` remain necessary HTTP behavior even when active purging is available. Validators alone do not retract an already-fresh shared-cache response.
- The later architecture must decide whether active purging is required, optional, or merely documented. If used, the integration needs an explicit purge path for `.well-known/security.txt` and tests under VirtualHostMonster/proxy rewriting.

### 8. Profiles, upgrades, and compatibility

- Initial site installation data belongs in the add-on's GenericSetup default profile. Relevant import steps include registry records, control-panel registration, browser-layer activation, and `rolemap.xml`; Python/ZCML component registrations remain package configuration.[^genericsetup-rolemap]
- A profile XML change that must reach an already-installed site requires a registered upgrade step. Reinstalling the profile or only bumping `metadata.xml` is not a migration.[^plonecli-add]
- plonecli provides the supported scaffold:

  ```shell
  plonecli add upgrade_step --defaults \
    -d upgrade_step_title="<migration title>"
  ```

  The generated handler must reimport only the needed step and/or migrate values, with an upgrade test.[^plonecli-add]
- Registry schema changes, permission-role changes, control-panel registration changes, and retained-artifact format changes require explicit existing-site treatment. Uninstall retention/removal must also be decided rather than left implicit.
- The package currently declares `Plone>=6.0` and the Plone 6.0 classifier, while its generated development setup is constrained to Plone 6.2.1.[^local-pyproject] A current scaffold proves template compatibility only for its selected version; it does not prove the whole supported range. CI must test the oldest supported Plone 6.0 environment and selected current Plone 6 releases, with their supported Python versions.[^plone-upgrade-60][^plone-release-schedule]

## Architecture proof points carried forward

Before [Choose the Plone integration architecture](../issues/08-choose-integration-architecture.md) freezes the seams, implementation-oriented spikes or tests should answer:

1. **REST authorization and mutation:** On every supported `plone.restapi` version, which supported guard makes the dedicated add-on permission authoritative for both reads and writes, including direct `@registry` access? Can generic `@controlpanels/{id}` PATCH preserve cross-field validation, publication enablement checks, sign-then-verify generation, artifact replacement, and invalidation? If not, [Choose the Plone integration architecture](../issues/08-choose-integration-architecture.md) must select and prove an invariant-preserving write boundary; a custom site-root service is one option, not a decision made here.
2. **Traversal:** Which supported traversal component most narrowly accepts `.well-known/security.txt`, rejects every sibling/extra path, avoids acquisition surprises, and produces correct VirtualHostMonster URLs?
3. **Persistence:** Are all normalized fields and retained unsigned/signed artifacts safely representable within supported registry field/value limits, or does one site-local persistent policy object make the invariant deeper and upgrades safer?
4. **Purge:** Which relative and/or absolute paths does `IPurgePaths` emit for the endpoint under the supported proxy layouts, and what guarantee remains when active purging is absent?
5. **Compatibility:** What exact Plone/Python CI matrix defines “Plone 6.0+” for the first release?
6. **Uninstall:** Are Security Policy records and retained artifacts preserved or removed on uninstall?

## Supported scaffold inventory

| Concern | Start with plonecli | Follow-up that remains manual/domain-specific |
|---|---|---|
| Classic UI settings | `add controlpanel` | Policy schema, widgets, shared validation/application service |
| REST management | Existing `@controlpanels`, or `add restapi_service` after the architecture choice | Authorization and invariant-preserving write transaction |
| Warning banner | `add viewlet` | Expiry condition and dedicated permission |
| Existing-site migrations | `add upgrade_step` after relevant profile changes | Focused migration/reimport logic and tests |
| Well-known publisher | No specialized subtemplate identified | Narrow site-root traversal component and HTTP response tests |
| Permission declaration | No specialized subtemplate identified | Named ZCML permission plus `rolemap.xml` and upgrade coverage |
| Cache purge path | No specialized subtemplate identified | `Purge` event/`IPurgePaths` integration if chosen |

## Sources

[^plone-forms]: [Plone 6 documentation: Forms](https://6.docs.plone.org/classic-ui/forms.html).
[^app-registry]: [`plone.app.registry` README: registry, GenericSetup, events, and custom control panels](https://github.com/plone/plone.app.registry/blob/master/README.rst).
[^rest-controlpanels]: [`plone.restapi` documentation: Control Panels](https://plonerestapi.readthedocs.io/en/latest/endpoints/controlpanels.html).
[^rest-controlpanel-source]: [`plone.restapi` 8.32.6 generic control-panel service registration](https://github.com/plone/plone.restapi/blob/8.32.6/src/plone/restapi/services/controlpanels/configure.zcml) and [control-panel deserializer](https://github.com/plone/plone.restapi/blob/8.32.6/src/plone/restapi/deserializer/controlpanels/__init__.py), the version pinned by the Plone 6.0.0 release.
[^rest-auth]: [`plone.restapi` documentation: Authentication and authorization](https://plonerestapi.readthedocs.io/en/latest/usage/authentication.html).
[^plone-views]: [Plone 6 documentation: Views](https://6.docs.plone.org/classic-ui/views.html).
[^plone-viewlets]: [Plone 6 documentation: Viewlets](https://6.docs.plone.org/classic-ui/viewlets.html).
[^zope-traversal]: [Zope `ZPublisher.BaseRequest` traversal source](https://github.com/zopefoundation/Zope/blob/master/src/ZPublisher/BaseRequest.py) and [`zope.publisher.interfaces.IPublishTraverse`](https://github.com/zopefoundation/zope.publisher/blob/master/src/zope/publisher/interfaces/__init__.py).
[^app-caching]: [`plone.app.caching` source and documentation](https://github.com/plone/plone.app.caching).
[^cachepurging]: [`plone.cachepurging` README: purge events, `IPurgePaths`, and virtual hosting](https://github.com/plone/plone.cachepurging).
[^zope-permissions]: [`zope.security` permission configuration source](https://github.com/zopefoundation/zope.security/blob/master/src/zope/security/zcml.py).
[^genericsetup-rolemap]: [`Products.GenericSetup` role-map import/export handler](https://github.com/zopefoundation/Products.GenericSetup/blob/master/src/Products/GenericSetup/rolemap.py) and [profile/upgrade source](https://github.com/zopefoundation/Products.GenericSetup).
[^plonecli-templates]: [Plone copier templates source](https://github.com/plone/copier-templates) and the supplied plonecli template catalogue (`controlpanel`, `viewlet`, and `restapi_service`).
[^plonecli-add]: Supplied plonecli workflow, [Plone copier templates](https://github.com/plone/copier-templates), and [Plone 6 add-on upgrade guidance](https://6.docs.plone.org/backend/upgrading/add-on-upgrade.html).
[^local-pyproject]: Local package metadata in [`pyproject.toml`](../../../pyproject.toml).
[^plone-upgrade-60]: [Plone 6 documentation: Upgrade to Plone 6.0](https://6.docs.plone.org/backend/upgrading/version-specific-migration/upgrade-to-60.html).
[^plone-release-schedule]: [Plone release schedule](https://plone.org/download/release-schedule).
