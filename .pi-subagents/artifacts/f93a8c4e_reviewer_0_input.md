# Task for reviewer

[Read from: /workspaces/plone.securitytxt/plan.md, /workspaces/plone.securitytxt/progress.md]

Review the resolved wayfinder architecture decision in /workspaces/plone.securitytxt for internal consistency and completeness. Read .scratch/securitytxt-control-panel/issues/08-choose-integration-architecture.md, map.md, issues 02, 03, 04, 06, 07, research/plone-integration-seams.md, CONTEXT.md, and docs/adr/0001-*.md plus 0002-*.md. Check specifically for contradictions with established lifecycle/HTTP/signing decisions, violations of Plone 6 supported seams, unclear module interfaces, missing GenericSetup/upgrade responsibilities, or map bookkeeping errors. Do not modify any files. Return only evidence-backed blockers or fixes worth doing now with exact file/section references; say clean if none. The parent retains architecture authority.

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