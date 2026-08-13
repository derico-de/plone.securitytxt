# Task for reviewer

[Read from: /workspaces/plone.securitytxt/plan.md, /workspaces/plone.securitytxt/progress.md]

Review the implementation in /workspaces/plone.securitytxt against the full originating specification.
Diff command: git diff df6a0a4...HEAD
Commits: 537c166 Implement security.txt policy control panel
Spec source: .scratch/securitytxt-control-panel/map.md and all .scratch/securitytxt-control-panel/issues/*.md. Read the relevant files and the diff.
Report: (a) missing/partial requirements; (b) scope creep; (c) requirements that look implemented incorrectly. Quote the spec line for each finding. Prioritize concrete release-blocking behavior, security, and data-integrity issues. Under 400 words. Do not edit.

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