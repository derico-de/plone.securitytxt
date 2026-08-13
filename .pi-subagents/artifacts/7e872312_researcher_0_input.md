# Task for researcher

Research and write the answer for the claimed wayfinder ticket “Establish the security.txt standards baseline” in repository /workspaces/plone.securitytxt. Use only high-trust primary sources: the current RFC defining security.txt (and any official errata or registries), securitytxt.org itself and its first-party source repository if discoverable, plus authoritative HTTP/OpenPGP specifications where needed. Distinguish normative RFC requirements from securitytxt.org generator conveniences. Cover: field syntax and multiplicity; required and optional fields; expiry; Canonical; extension fields; comments and ordering; endpoint discovery; media type/charset/line endings; redirects/status behavior; caching considerations; and OpenPGP clear-signing requirements. Inventory authoring/generation features exposed by securitytxt.org, but do not treat its validator for arbitrary sites as in scope. Identify concrete compatibility/product choices that remain for the owner. Write one cited Markdown research asset at .scratch/securitytxt-control-panel/research/securitytxt-standards-baseline.md. You may create that parent research directory and this file only; do not edit the ticket, map, CONTEXT.md, source code, or other repo files. Cite every substantive claim with inline links and include a Sources section. Return a concise handoff naming the file, strongest conclusions, source gaps, and residual uncertainty. Do not run subagents; the parent owns orchestration.

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