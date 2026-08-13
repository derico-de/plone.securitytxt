# Task for reviewer

[Read from: /workspaces/plone.securitytxt/plan.md, /workspaces/plone.securitytxt/progress.md]

Review the implementation in /workspaces/plone.securitytxt.
Diff command: git diff df6a0a4...HEAD
Commits: 537c166 Implement security.txt policy control panel
Standards sources: AGENTS.md, .editorconfig, pyproject.toml, README.md. Run the diff and read these sources.
Smell baseline (judgement calls; repo rules override): Mysterious Name—names do not reveal intent; Duplicated Code—same logic shape repeats; Feature Envy—method reaches into another object more than its own; Data Clumps—same fields repeatedly travel together; Primitive Obsession—primitive stands in for a domain concept; Repeated Switches—same conditional dispatch recurs; Shotgun Surgery—one logical change forces scattered edits; Divergent Change—one module changes for unrelated reasons; Speculative Generality—abstractions/hooks not required; Message Chains—long navigation leaks structure; Middle Man—mostly delegates; Refused Bequest—subclass ignores inheritance.
Report per file/hunk: (a) every documented-standard violation, citing source/rule; (b) baseline smells, naming and quoting the hunk. Distinguish hard violations from judgement calls. Skip tooling-enforced issues. Under 400 words. Do not edit.

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