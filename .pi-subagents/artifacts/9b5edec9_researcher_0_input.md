# Task for researcher

Research primary-source facts needed to decide release acceptance for plone.securitytxt in /workspaces/plone.securitytxt. Determine, as of 2026-08-10, the maintained Plone 6 minor lines and their supported Python versions; identify suitable oldest/current Plone and Python combinations for CI given the map promise Plone 6.0+; check authoritative Plone release schedules/configs and package metadata rather than secondary posts. Also identify primary-source interoperability tools or commands suitable for validating RFC 9116 output and OpenPGP clear-signatures, and supported minimum/current GnuPG test targets consistent with the already-decided GnuPG >=2.2.27 Linux contract. Separate facts from recommendations and note uncertainties. Read .scratch/securitytxt-control-panel/map.md, issues 01, 03, 06, 07, 08, pyproject.toml, and .github/workflows/ci.yml. Write one linked Markdown research asset at .scratch/securitytxt-control-panel/research/release-compatibility.md with source URLs. Do not modify any other project file. Return a concise summary and the file path. The parent owns all product decisions and tracker edits.

---
**Output:**
Write your findings to exactly this path: /workspaces/plone.securitytxt/.pi-subagents/artifacts/outputs/9b5edec9/research.md
This path is authoritative for this run.
Ignore any other output filename or output path mentioned elsewhere, including output destinations in the base agent prompt, system prompt, or task instructions.

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