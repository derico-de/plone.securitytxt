## Review

- **Correct:** All requested seams are addressed in dedicated sections: control panel, REST, permission, traversal, persistence, warning, cache invalidation, and lifecycle at `.scratch/securitytxt-control-panel/research/plone-integration-seams.md:15-88`.
- **Correct:** Platform mechanisms and unresolved architecture are generally separated clearly at `plone-integration-seams.md:7-13` and `:90-99`.
- **Correct:** The `controlpanel`, `viewlet`, `restapi_service`, and `upgrade_step` scaffolds were confirmed against the installed plonecli catalogue and templates.

### Blocker

- **Blocker:** `.scratch/securitytxt-control-panel/research/plone-integration-seams.md:32-41,94` does not expose a key authorization constraint of generic `@controlpanels`. In Plone 6.0.0’s pinned `plone.restapi==8.32.6`, all generic `@controlpanels` methods are registered with the global `plone.app.controlpanel.Overview` permission; the panel serializer/deserializer does not enforce the configlet/browser-page permission. Thus generic REST access is not automatically protected by this add-on’s dedicated management permission, contrary to the requirement at line 41.
  - **Suggested correction:** State this as an established platform constraint. Explain that the scaffold registers an `IControlpanel` adapter, but its Classic UI/configlet permission does not automatically become a panel-specific REST permission. Add a ticket-08 proof point requiring a supported dedicated-permission guard for GET and mutation, including direct `@registry` access. Do not yet prescribe which architecture supplies that guard.

### Major

- **Major:** The primary plonecli source links at `plone-integration-seams.md:124-125` point to the nonexistent `https://github.com/plone/plone-copier-templates` and return HTTP 404.
  - **Suggested correction:** Replace both with `https://github.com/plone/copier-templates`, preferably linking the relevant `controlpanel`, `viewlet`, `restapi_service`, and `upgrade_step` template paths or a pinned commit.

- **Major:** Ticket 07 does not yet link the research asset. `.scratch/securitytxt-control-panel/issues/07-confirm-plone-integration-seams.md:1-8` has no `## Answer`, unlike resolved research tickets.
  - **Suggested correction:** Before resolving ticket 07, add an answer linking `../research/plone-integration-seams.md` and summarize only confirmed seams and deferred choices.

### Medium

- **Medium:** `plone-integration-seams.md:35,94` understates a supported generic REST mechanism. `plone.restapi==8.32.6` invokes field deserializers, `field.validate()`, and `IManagerValidator` during control-panel PATCH. It does not invoke Classic UI button handlers.
  - **Suggested correction:** Record field and manager validation as an established mechanism, then narrowly defer publication effects, signing, artifact replacement, permission enforcement, and invalidation to ticket 08.

- **Medium:** `plone-integration-seams.md:94` says, “If not, use a custom site-root service,” prematurely selecting ticket 08’s fallback and excluding other possible guarded deserializer/service arrangements.
  - **Suggested correction:** Replace it with: “If generic PATCH cannot preserve every invariant and permission requirement, ticket 08 must select and prove an invariant-preserving write boundary.” Custom service can remain an example, not a decision.

- **Medium:** Permission and lifecycle claims at `plone-integration-seams.md:39-40,77-87` are only loosely supported by the cited views/authentication and broad upgrade references.
  - **Suggested correction:** Add primary references for ZCML permission declaration, GenericSetup `rolemap.xml`, profile import steps, and registered upgrade steps. Keep product role defaults explicitly attributed to `map.md:18`.

### Low

- **Low:** “Every-page manager” at `plone-integration-seams.md:63` implies a stronger guarantee than viewlets provide. A viewlet appears only where its chosen manager is rendered.
  - **Suggested correction:** Say “all standard Classic UI pages rendering the selected global manager,” identify the candidate manager, and carry tests for the relevant Classic UI templates. The Volto limitation at lines 64-65 is correctly separated.

- **Low:** Compatibility assertions at `plone-integration-seams.md:88` are correct from local `pyproject.toml`, but the cited upgrade page and release schedule do not establish the exact pinned Plone/restapi versions or Python matrix.
  - **Suggested correction:** Cite local `pyproject.toml:17-28,71-78` and official Plone release constraints/release notes. Keep the exact CI matrix deferred as already done at line 98.

## Residual risks

- Requested `/workspaces/plone.securitytxt/plan.md` and `progress.md` do not exist, so they could not be reviewed.
- Several GitHub citations target mutable `master`/`main`; pinning versions or commits would better attest Plone 6.0 compatibility.
- No runtime Plone instance was exercised; findings are based on Plone 6.0 constraints, primary source, documentation, and local templates.