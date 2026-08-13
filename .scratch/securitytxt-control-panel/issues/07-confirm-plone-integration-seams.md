# Confirm the Plone integration seams

Type: research
Status: resolved

## Question

Which supported Plone 6 integration mechanisms should the later architecture decision use? Produce a linked Markdown research asset, consulting `/plonecli` and primary Plone documentation, that confirms how to scaffold a Classic UI control panel, expose it through `plone.restapi`, register a dedicated permission, publish the `.well-known/security.txt` traversal path, store site-scoped settings, render a persistent permission-gated warning on every page, invalidate cached output after changes, and package profiles and upgrades across supported Plone versions. Separate established platform constraints from architectural choices.

## Answer

Resolved in [Plone 6 integration seams for `plone.securitytxt`](../research/plone-integration-seams.md).

Plone 6 provides supported seams for every requested concern: a plonecli-scaffolded registry-backed `z3c.form` control panel, ordinary Zope permissions plus GenericSetup role mappings, site-root traversal, site-local registry settings, a permission-gated Classic UI viewlet, `plone.restapi` control-panel or custom-service APIs, cache-purge events and paths, and versioned profiles with scaffolded upgrade steps.

The key constraint is that generic `@controlpanels` authorization does not automatically inherit the control panel's dedicated permission in the Plone 6.0 baseline. Generic PATCH does perform field and manager validation, but it does not run Classic UI form handlers; direct `@registry` access is another potential bypass. [Choose the Plone integration architecture](08-choose-integration-architecture.md) must therefore prove an invariant-preserving and permission-correct REST boundary rather than assuming the generated control panel supplies one.

The exact REST boundary, `.well-known` traversal hook, registry-versus-dedicated persistence split, optional purge guarantee, supported Plone/Python matrix, and uninstall retention policy remain architectural choices already covered by [Choose the Plone integration architecture](08-choose-integration-architecture.md). No additional ticket is needed.
