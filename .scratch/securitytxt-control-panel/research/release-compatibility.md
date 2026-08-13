# Research: release compatibility for `plone.securitytxt`

**Research date:** 2026-08-10
**Scope:** Primary-source facts for deciding release acceptance. Product choices remain with the parent.

## Summary

Plone 6.0, 6.1, and 6.2 are still security-supported on the research date, but only 6.2 is in maintenance; 6.0 and 6.1 are security-only lines. The useful CI boundary pairs are Plone 6.0.15 + Python 3.10 (oldest supported intersection with this package's declared Python floor) and Plone 6.2.1 + Python 3.14 (current Plone/current supported Python), with a 6.1-line job advisable because an unbounded `Plone>=6.0` job currently exercises only the newest resolver result.

The decided GnuPG floor, 2.2.27, is upstream-EOL but remains a defensible Linux vendor target through Ubuntu 22.04's patched package; upstream's current stable version is 2.5.21. RFC output should be checked both at the HTTP/byte level and through an independent RFC 9116 parser, while clear-signatures should be checked with GnuPG itself using machine-readable status output and recovered-cleartext comparison.

## Facts

### 1. Plone release lines and Python support

The authoritative [Plone release schedule](https://plone.org/download/release-schedule) reports:

| Plone line | State on 2026-08-10 | Current release | Official Python versions | Support horizon |
|---|---|---:|---|---|
| 6.0 | Security support only; regular maintenance ended | 6.0.15 | 3.9, 3.10, 3.11, 3.12, 3.13 | Security fixes through 2027-12-31 |
| 6.1 | Security support only; superseded for regular maintenance by 6.2 | 6.1.5 | 3.10, 3.11, 3.12, 3.13 | Security fixes through 2027-12-31 |
| 6.2 | Current maintenance line | 6.2.1 | 3.10, 3.11, 3.12, 3.13, 3.14 | Maintenance until 6.3.0 or 7.0.0; security through 2027-12-31 |

Release-page corroboration:

- [Plone 6.2.0 release notes](https://plone.org/download/releases/6.2.0) explicitly list Python 3.10–3.14.
- [Plone 6.1.5 release notes](https://plone.org/download/releases/6.1.5) record the line's current compatibility updates.
- [Plone 6.0.15 release notes](https://plone.org/download/releases/6.0.15) are the terminal/current 6.0 release named by the schedule.
- Plone publishes per-release resolver inputs under its official distribution host, for example [6.0.15](https://dist.plone.org/release/6.0.15/), [6.1.5](https://dist.plone.org/release/6.1.5/), and [6.2.1](https://dist.plone.org/release/6.2.1/). These constraints/requirements are the reproducible source for line-specific CI, rather than an unconstrained `pip install Plone>=6.0`.

“Maintained” is ambiguous unless qualified: all three lines receive security support, but only 6.2 receives routine maintenance releases.

### 2. Repository contract and actual CI coverage

- [`pyproject.toml`](/workspaces/plone.securitytxt/pyproject.toml) declares `requires-python = ">=3.10"` and `Plone>=6.0`. Its classifiers stop at Python 3.12 and Plone 6.0, while its development constraint pins only `Products.CMFPlone==6.2.1`.
- [`.github/workflows/ci.yml`](/workspaces/plone.securitytxt/.github/workflows/ci.yml) runs Python 3.10, 3.11, and 3.12, but does not constrain Plone by minor line. Each job therefore resolves the newest compatible Plone, not 6.0/6.1/6.2 independently. It does not test Python 3.13 or 3.14.
- The map's promise is Plone 6.0+ ([`map.md`](/workspaces/plone.securitytxt/.scratch/securitytxt-control-panel/map.md)); issue 06 fixes Linux signing with GnuPG >=2.2.27, while issues 03, 07, and 08 make exact artifact bytes, Plone traversal/integration, and retained publication behavior release-critical.

**Review finding — high:** current CI does not demonstrate the advertised Plone 6.0+ range. Three Python jobs against an unbounded dependency can all test the same newest Plone line.

**Review finding — medium:** current CI omits officially supported Python 3.13 and the current-line Python 3.14 boundary; metadata classifiers also under-report the intended range if those versions are accepted.

### 3. Suitable compatibility boundary combinations

These are arithmetic intersections of the primary-source support tables and the repository's declared Python floor:

- **Oldest supported boundary:** Plone **6.0.15** + Python **3.10**. Python 3.9 is supported by Plone 6.0 but excluded by this package's `>=3.10`. Using 6.0.15 represents the supported 6.0 line and includes its security fixes.
- **Current boundary:** Plone **6.2.1** + Python **3.14**. This exercises the current maintenance release and newest Python officially supported by that line on the research date.
- **Distinct retained line:** Plone **6.1.5** + at least Python **3.10** (optionally 3.13 as that line's upper boundary). Its security-supported status makes it part of the promise even though it is no longer routinely maintained.

There is a separate semantic question around “Plone 6.0+”: testing 6.0.15 proves compatibility with the supported 6.0 line, not necessarily with historical 6.0.0. If the promise literally includes every old patch release, add an exact 6.0.0 constraints job; otherwise document that compatibility means supported patch releases within each supported minor line.

### 4. Primary-source interoperability checks for RFC 9116

The normative source is [RFC 9116](https://www.rfc-editor.org/rfc/rfc9116.html), especially Sections 2–3. It supports deterministic acceptance checks without relying on an online service:

```sh
curl --fail-with-body --silent --show-error \
  --dump-header headers.txt \
  --output security.txt \
  https://example.test/.well-known/security.txt
```

Then assert status, `Content-Type: text/plain; charset=utf-8`, anonymous access, UTF-8/no BOM, required `Contact` and exactly one `Expires`, line grammar, endpoint location, and the product's stronger CRLF/final-CRLF contract. [`curl`'s official manual](https://curl.se/docs/manpage.html) documents `--dump-header`, `--output`, and `--fail-with-body`.

For independent parser interoperability, the Dutch government's Digital Trust Center maintains [`DigitalTrustCenter/sectxt`](https://github.com/DigitalTrustCenter/sectxt), an RFC 9116 parser/validator, with package and usage instructions in its README. [`spaze/security-txt`](https://github.com/spaze/security-txt) is a second independently implemented RFC 9116 parser/validator with an executable interface. Neither tool is normative; pin the chosen tool version and retain a direct RFC-derived test suite so a validator bug or release cannot redefine acceptance.

Online `securitytxt.org` is useful as a manual cross-check, but its generator/checker is not the standard and is unsuitable as the sole CI oracle.

### 5. OpenPGP clear-signature validation

RFC 9116 Section 2.3.2 recommends OpenPGP cleartext signatures and points to the OpenPGP cleartext-signature framework. GnuPG is the authoritative implementation already selected by issue 06. The [GnuPG operational command manual](https://www.gnupg.org/documentation/manuals/gnupg/Operational-GPG-Commands.html) documents `--clearsign` and `--verify`; the [GnuPG unattended-use guidance](https://www.gnupg.org/documentation/manuals/gnupg/GPG-Configuration-Options.html) says unattended verification should consume `--status-fd` rather than localized human output.

Suitable interoperability commands are:

```sh
# Verify and emit machine-readable status records.
gpg --batch --no-tty --status-fd 1 --verify security.txt

# Recover the cleartext only after successful verification, for byte comparison.
gpg --batch --no-tty --status-fd 2 --output recovered.txt --decrypt security.txt
cmp --silent recovered.txt expected-unsigned.txt
```

Acceptance should parse status records and require a valid signature from the exact configured signing-subkey fingerprint and the required digest, rather than grep stderr. It should also compare recovered cleartext with the canonical unsigned input, matching issue 06's already-decided sign-then-verify contract. Negative fixtures should cover altered cleartext, altered armor, wrong key, truncation, and an unexpected signing subkey.

### 6. GnuPG minimum and current targets

- The upstream [GnuPG download/EOL table](https://www.gnupg.org/download/) marks branch **2.2 EOL on 2024-12-31** and branch **2.4 EOL on 2026-06-30**. It identifies **2.5/2.6** as the maintained current branch family and publishes **2.5.21** (2026-07-02) as current on the research date. The [official source archive](https://gnupg.org/ftp/gcrypt/gnupg/) likewise identifies 2.5/2.6 as current stable.
- Ubuntu 22.04 LTS carries GnuPG **2.2.27** with Ubuntu security revisions ([Ubuntu package record](https://packages.ubuntu.com/jammy/gnupg)). Ubuntu's [release-cycle policy](https://ubuntu.com/about/release-cycle) gives 22.04 standard security maintenance through April 2027. Thus the exact minimum remains testable as a **vendor-maintained patched package**, despite upstream 2.2 EOL.
- A generic current Ubuntu runner is not an exact minimum test and can change underneath CI. An Ubuntu 22.04 container/runner with an asserted `gpg --version` is the appropriate minimum lane. A separately pinned upstream 2.5.21 build/container is the current lane.

**Review finding — medium:** wording must not imply that upstream supports 2.2.27. The decided contract is internally consistent only because it expressly requires a vendor-security-supported build; acceptance should record the complete vendor package version, not just `2.2.27`.

## Recommendations (not facts)

1. Make two required boundary jobs: **Plone 6.0.15/Python 3.10** using the official 6.0.15 constraints, and **Plone 6.2.1/Python 3.14** using the official 6.2.1 constraints.
2. Add a required **Plone 6.1.5** job (Python 3.10 is economical; 3.13 gives the line's upper boundary). A compact pairwise matrix is better evidence than testing every Python against only latest Plone.
3. Keep one unconstrained “dependency drift” job, but do not count it as line coverage. Assert/log `Plone`, `Products.CMFPlone`, Python, `python-gnupg`, and `gpg --version` in every acceptance run.
4. Decide and document whether “6.0+” means supported patch releases or literally 6.0.0 onward. Only in the latter case should 6.0.0 be a required compatibility fixture.
5. For signing, require Linux lanes for Ubuntu 22.04's patched 2.2.27 package and pinned upstream 2.5.21. Treat 2.4 as optional transitional coverage because it is already upstream-EOL on the research date.
6. Run direct RFC/HTTP assertions plus one pinned independent parser, and verify clear-signed output with `gpg --status-fd` plus recovered-byte comparison. Do not make an external web validator a required CI dependency.
7. If Python 3.13/3.14 acceptance succeeds, update classifiers to describe reality; classifiers should follow tested support rather than lead it.

## Uncertainties and residual risks

- Plone's schedule can change when 6.3 or 7.0 ships; re-read the live schedule immediately before release. The table above is a dated snapshot.
- The schedule gives line-level Python support, but third-party add-ons used by this project may narrow a combination. Only installation and tests with official per-release constraints settle the complete environment.
- Ubuntu may move 22.04's GnuPG security revision while retaining upstream version 2.2.27. Exact reproducibility requires recording or pinning the full Debian/Ubuntu package version; security acceptance may instead deliberately track the newest vendor revision.
- Upstream labels the 2.5/2.6 family current stable, but a production policy may prefer an LTS distribution's newer vendor-maintained branch. The parent must decide whether “current” means upstream current or current production-distribution package.
- Independent RFC validators can differ on RFC errata or stricter product invariants. They are interoperability signals, not normative authorities.

## Sources

### Kept

- [Plone release schedule and policy](https://plone.org/download/release-schedule) — authoritative supported lines, current releases, Python versions, and dates.
- [Plone 6.0.15 distribution directory](https://dist.plone.org/release/6.0.15/) — official reproducible resolver inputs for the oldest supported line.
- [Plone 6.1.5 distribution directory](https://dist.plone.org/release/6.1.5/) — official resolver inputs for the intermediate supported line.
- [Plone 6.2.1 distribution directory](https://dist.plone.org/release/6.2.1/) — official resolver inputs for the current line.
- [RFC 9116](https://www.rfc-editor.org/rfc/rfc9116.html) — normative security.txt protocol.
- [GnuPG download and EOL table](https://www.gnupg.org/download/) — authoritative current release and upstream branch lifecycle.
- [GnuPG manual](https://www.gnupg.org/documentation/manuals/gnupg/Operational-GPG-Commands.html) — authoritative clear-sign and verification commands.
- [Ubuntu 22.04 GnuPG package](https://packages.ubuntu.com/jammy/gnupg) and [Ubuntu lifecycle](https://ubuntu.com/about/release-cycle) — vendor-maintained realization of the 2.2.27 floor.
- [`DigitalTrustCenter/sectxt`](https://github.com/DigitalTrustCenter/sectxt) and [`spaze/security-txt`](https://github.com/spaze/security-txt) — independent primary repositories for interoperability validators.

### Dropped

- Search-engine summaries, blogs, and compatibility posts — secondary and unnecessary where Plone, RFC Editor, GnuPG, Ubuntu, and tool repositories provide direct evidence.
- Online-validator results — mutable, network-dependent observations rather than stable release evidence.

## Acceptance evidence

- **review-findings:** high — [`.github/workflows/ci.yml`](/workspaces/plone.securitytxt/.github/workflows/ci.yml) does not constrain Plone lines, so it does not attest the Plone 6.0+ promise; medium — Python 3.13/3.14 and exact GnuPG boundary lanes are absent; medium — upstream 2.2 is EOL and the minimum is valid only as a vendor-supported patched target.
- **residual-risks:** live schedules and vendor patch revisions can change; literal 6.0.0 compatibility versus supported 6.0.x compatibility remains a parent decision; third-party dependency solvability requires CI execution.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Concrete high/medium findings cite .github/workflows/ci.yml, pyproject.toml, map/issues, and primary Plone/GnuPG/RFC sources; residual risks are explicitly separated."
    }
  ],
  "changedFiles": [
    ".pi-subagents/artifacts/outputs/9b5edec9/research.md"
  ],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "Read requested map, issues 01/03/06/07/08, pyproject.toml, and .github/workflows/ci.yml",
      "result": "passed",
      "summary": "All requested repository inputs were reviewed."
    },
    {
      "command": "Primary-source web research: Plone schedule/releases, RFC 9116/tools, GnuPG lifecycle/manual, Ubuntu package lifecycle",
      "result": "passed",
      "summary": "Authoritative facts and dated uncertainties were collected and linked."
    }
  ],
  "validationOutput": [
    "Research separates facts from recommendations and identifies oldest/current Plone-Python and GnuPG targets.",
    "No project file was modified; only the authoritative runtime artifact was written."
  ],
  "residualRisks": [
    "Plone schedules and vendor package revisions are live and must be rechecked immediately before release.",
    "Whether the Plone 6.0+ promise includes historical 6.0.0 rather than supported 6.0.x remains a parent decision.",
    "Complete dependency compatibility requires executing the proposed constrained CI matrix."
  ],
  "noStagedFiles": true,
  "diffSummary": "Added one linked release-compatibility research artifact; no project sources or trackers changed.",
  "reviewFindings": [
    "high: .github/workflows/ci.yml - unconstrained Plone installation does not prove compatibility across supported Plone 6 minor lines.",
    "medium: .github/workflows/ci.yml - Python 3.13 and 3.14 boundary coverage is absent.",
    "medium: signing acceptance - GnuPG 2.2 is upstream-EOL, so 2.2.27 is acceptable only as a vendor-security-supported patched package such as Ubuntu 22.04's."
  ],
  "manualNotes": "The runtime output-path override prohibited writing the user-named .scratch research path; the complete asset is at the authoritative artifact path."
}
```
