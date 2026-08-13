# Prototype the owner control-panel experience

Type: prototype
Status: resolved
Blocked by: 02 — [Define the Security Policy field model](02-define-policy-field-model.md); 03 — [Define publication and HTTP semantics](03-define-publication-http-semantics.md)

## Question

What should a website owner see and do when creating, validating, previewing, publishing, disabling, and maintaining a Security Policy? Build a low-fidelity prototype covering structured and repeated fields, Extension Fields, generated preview, validation errors and warnings, publication state, signing availability and state, expiry countdown, and the persistent site-wide administrative expiry warning. Include the REST-facing states a separate frontend would need, without designing a custom Volto UI.

## Comments

- Interactive prototype: [Security policy control panel — three UX directions](http://planetmobile:8228/p/0LLHNm_uyt0). Local source: [`../prototypes/control-panel.html`](../prototypes/control-panel.html). The scenario selector covers empty draft, publish-ready draft, approaching expiry, expired publication, and signing failure.

## Answer

The owner experience uses the prototype's **A — Guided form** direction, simplified into one standard `z3c.form` control panel rather than a wizard or custom workbench. The later architecture decision places persistence behind the application module rather than using registry-backed CRUD.

### Form structure

- Keep all settings on one page using four standard fieldsets: **Contact & expiry**, **Disclosure**, **Extension fields**, and **Signing**. Open **Contact & expiry** by default.
- Put a compact lifecycle summary above the form rather than in a sticky sidebar. It shows Draft, Published, or Publication Blocked; expiry/countdown; anonymous endpoint status; signing mode/status; and the latest validation result.
- Put the exact generated unsigned preview below the form in a read-only monospace region. It is explicitly labelled non-public and unsigned when Signed Publication Mode is selected.
- Repeatable standard values use add/remove/reorder rows. Extension Fields use ordered name/value rows with add, remove, and reorder controls. The real form should use standard widgets and fieldsets rather than reproduce the prototype's bespoke layout.

### Feedback and actions

- Show a validation summary above the form and inline feedback beside affected fields. Errors are labelled **Blocks publication**; warnings are clearly advisory.
- Keep **Save draft** (or **Save changes** for an enabled policy), **Validate**, **Preview**, and either **Publish** or **Disable publication** visible. Saving never enables publication implicitly.
- Preview validates and renders the current unsaved values without changing the saved Draft, retained artifact, or public endpoint. It may show publication blockers and warnings and never invokes signing.
- Confirm both Publish and Disable publication. Publish summarizes the public endpoint, expiry, and signing mode. Disable explains that anonymous requests will return `404`.
- While publication remains enabled, **Save changes** updates the public representation atomically only if the edit remains valid. A rejected validation or signing attempt leaves the previously committed public representation live, matching the already-decided lifecycle and signing contracts.

### Lifecycle and maintenance states

- **Draft:** incomplete values may be saved; endpoint `404`; Publish is available only after full validation.
- **Published:** endpoint `200`; routine valid changes can be saved; Disable publication is available.
- **Publication Blocked — expired:** owner intent remains enabled; endpoint `404`; the summary and persistent administrator warning explain that setting a future expiry restores publication.
- **Publication Blocked — operational/signing failure:** endpoint `503`; no unsigned fallback; authorized owners see the actionable failure category and operator-oriented guidance.
- From 30 days before expiry and after expiry, every standard Classic UI page rendering the selected global manager shows a non-dismissible, permission-gated warning with the countdown/state and a **Review policy** link. There is no email, job, or custom Volto component.
- The Signing fieldset remains present as status even when signing is unavailable. It distinguishes Unavailable, Configured, Verified, active, waiting, and error states and exposes only owner-selectable mode/profile controls plus deployment-owned public identity/status.

### Frontend-independent state

A permission-protected REST consumer needs the same conceptual state shown by the control panel: lifecycle state, publication intent, blockers, warnings, expiry instant/countdown, signing capability/mode/profile status, current public endpoint status, and permitted owner actions. Preview is a protected, `no-store`, side-effect-free operation over candidate values. The exact REST resource and write boundary remain decisions for [Choose the Plone integration architecture](08-choose-integration-architecture.md); this prototype does not imply a custom Volto UI.

The prototype answered the UX question without surfacing another independent decision ticket. The remaining integration choices already belong to [Choose the Plone integration architecture](08-choose-integration-architecture.md).
