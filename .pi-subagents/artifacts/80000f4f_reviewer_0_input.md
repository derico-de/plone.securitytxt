# Task for reviewer

[Read from: /workspaces/plone.securitytxt/plan.md, /workspaces/plone.securitytxt/progress.md]

Independently review the Wayfinder research asset .scratch/securitytxt-control-panel/research/plone-integration-seams.md against the question in .scratch/securitytxt-control-panel/issues/07-confirm-plone-integration-seams.md and the destination/notes in .scratch/securitytxt-control-panel/map.md. Read CONTEXT.md and the plonecli skill/relevant references. This is read-only: do not edit files. Check factual correctness for supported Plone 6.0+ mechanisms, whether platform constraints are clearly separated from architectural choices, whether every requested seam is covered, whether recommendations accidentally decide ticket 08, and whether citations are primary and plausibly support their claims. Return findings by severity with precise suggested corrections; state no blockers if none.

## Acceptance Contract
Acceptance level: attested
Completion is not accepted from prose alone. End with a structured acceptance report.

Criteria:
- criterion-1: Return concrete findings with file paths and severity when applicable

Required evidence: review-findings, residual-risks

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