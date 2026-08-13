# Task for researcher

Resolve the claimed Wayfinder research ticket “Confirm the Plone integration seams” for /workspaces/plone.securitytxt. Read .scratch/securitytxt-control-panel/issues/07-confirm-plone-integration-seams.md, .scratch/securitytxt-control-panel/map.md, CONTEXT.md, docs/agents/issue-tracker.md, the provided plonecli skill at /home/dev/.agents/skills/plonecli/SKILL.md and its relevant references. Research primary sources only (official Plone/plone.restapi/plonecli docs and authoritative source code as needed). Confirm supported Plone 6 mechanisms for: Classic UI z3c.form control panel scaffolding; plone.restapi exposure; dedicated permission; .well-known/security.txt traversal at site root; site-scoped settings; persistent permission-gated every-page warning; cached-output invalidation; GenericSetup profiles/upgrades and Plone 6.0+ compatibility. Explicitly separate established platform constraints from architectural choices. Write one linked Markdown research asset at .scratch/securitytxt-control-panel/research/plone-integration-seams.md, with citations attached to claims. Do NOT edit the ticket, map, CONTEXT.md, or any other files. Return a concise summary and residual uncertainties. This is research/planning only, not implementation.

---
**Output:**
Write your findings to exactly this path: /workspaces/plone.securitytxt/.pi-subagents/artifacts/outputs/62ce02df/.scratch/securitytxt-control-panel/research-agent-output.md
This path is authoritative for this run.
Ignore any other output filename or output path mentioned elsewhere, including output destinations in the base agent prompt, system prompt, or task instructions.

## Acceptance Contract
Acceptance level: checked
Completion is not accepted from prose alone. End with a structured acceptance report.

Criteria:
- criterion-1: Return concrete findings with file paths and severity when applicable

Required evidence: changed-files, tests-added, commands-run, residual-risks, no-staged-files, validation-output

Finish with a fenced JSON block tagged `acceptance-report` in this shape:
Use empty arrays when no items apply; array fields contain strings unless object entries are shown.
`criteriaSatisfied[].status` must be exactly one of: satisfied, not-satisfied, not-applicable.
`commandsRun[].result` must be exactly one of: passed, failed, not-run.
`manualNotes` and `notes` are optional strings; an empty string means no note and does not satisfy `manual-notes` evidence.
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "specific proof"
    }
  ],
  "changedFiles": [
    "src/file.ts"
  ],
  "testsAddedOrUpdated": [
    "test/file.test.ts"
  ],
  "commandsRun": [
    {
      "command": "command",
      "result": "passed",
      "summary": "short result"
    }
  ],
  "validationOutput": [
    "validation output or concise summary"
  ],
  "residualRisks": [
    "none"
  ],
  "noStagedFiles": true,
  "diffSummary": "short description of the diff",
  "reviewFindings": [
    "blocker: file.ts:12 - issue found, or no blockers"
  ],
  "manualNotes": "anything else the parent should know"
}
```