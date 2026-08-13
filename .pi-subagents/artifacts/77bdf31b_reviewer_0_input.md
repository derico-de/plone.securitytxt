# Task for reviewer

[Read from: /workspaces/plone.securitytxt/plan.md, /workspaces/plone.securitytxt/progress.md]

Review the just-resolved wayfinder decision in /workspaces/plone.securitytxt. Read .scratch/securitytxt-control-panel/issues/09-define-release-acceptance.md, map.md, research/release-compatibility.md, issues 01 through 08 as needed, pyproject.toml, and .github/workflows/ci.yml. Check for contradictions with established field/lifecycle/HTTP/signing/architecture decisions; unsupported or internally inconsistent compatibility claims; missing acceptance areas requested by the ticket; CI-versus-manual-release contradictions; and incorrect wayfinder map bookkeeping. Do not modify files. Return only evidence-backed blockers or fixes worth doing now with exact file/section references; say clean if none. Respect that open tickets do not belong in Not yet specified and that this is a specification, not implementation.

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