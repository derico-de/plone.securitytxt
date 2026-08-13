# Task for researcher

Research and resolve the evidence-gathering portion of .scratch/securitytxt-control-panel/issues/05-evaluate-openpgp-approaches.md in /workspaces/plone.securitytxt. Write exactly one durable research asset at .scratch/securitytxt-control-panel/research/openpgp-signing-approaches.md. Do not edit the ticket, map, CONTEXT.md, source code, or any other project file.

Goal: determine which maintained OpenPGP approach is suitable for optional RFC 9116-compliant clear-signing in this Plone add-on. Compare viable Python libraries and direct/external gpg integration for Plone 6.0+ and the repository's Python support (inspect pyproject.toml). Cover maintenance/release recency, license compatibility, supported Python/platforms, packaging and native/subprocess weight, subprocess and sandbox/container implications, secret key selection, passphrase/agent handling, clear-sign mechanics and deterministic-output limits, RFC 4880/9580 and real gpg interoperability, structured error reporting, concurrency, and unit/integration testability. Recommend the dependency arrangement for the signing extra and a deployment-secret contract that stores neither keys nor passphrases in Plone.

Use high-trust primary sources only: RFCs, official project documentation, release metadata, source repositories/code, and upstream issue trackers where needed. Date the research 2026-08-08. Distinguish verified facts from product recommendations, cite important claims inline, and end with a linked Sources section. Inspect .scratch/securitytxt-control-panel/research/securitytxt-standards-baseline.md and issue 03's Answer for settled local constraints. Stop after enough evidence to make a recommendation; explicitly note evidence gaps and residual risks. Return a concise summary and the artifact path.

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