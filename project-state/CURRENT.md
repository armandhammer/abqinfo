# Current project state

PR #198 implementation is complete on `codex/go-capital-quality-remediation`, with manual editorial review pending. The PR remains open and unmerged: https://github.com/armandhammer/abqinfo/pull/198 . Its visitor-visible content is not integrated into main.

`main` and `chatgpt/planning-snapshot` remain synchronized at `de48a74d8522806a0d68ce247eb1d5d6a309c0ca`. The reviewed content revision is `555385b32a08ac1cffa7fefcf6a15d90c2c9fe4a`, content-tree SHA `833e473021f9fa58d6c361e6ea7a5e3f2b47fb1e`. Subsequent commits record validation and handoff metadata; the current PR head is the live remote branch reference.

The exact 32-record negative-review boundary is preserved. The complete 2009 master contains 24 originals in 87 pages; the separate 2011 preliminary/EPC and published-directory masters contain 21 originals in 56 pages and 46 originals in 130 pages. The owner-kept community-center authorization remains independently visible outside the 2009 master. Original bytes, independent instruments and historical negative findings are preserved.

The explicit owner archive/publication approval is registered in `governance/pr198-approved-2026-09-27/owner-approval.json`. The exact new 2009 master upload added 1,303,860 bytes. The two existing 2011 masters were reused; all three full public downloads match their pinned hashes. No R2 overwrite or deletion occurred. Archive receipts and complete listings are in `governance/pr198-archive-authorized-2026-09-27`.

Separate frozen tasks govern supporting records, derived-master closeout, the 32-record implementation and final review preparation. Final population, immutable contract, governance accounting and normal-suite results are in `governance/pr198-review-ready-2026-09-27`. Earlier contracts and evidence remain immutable. The original remediation witness remains sealed; current actual output accounting is separate.

Verified nonproduction review pages: https://e89de4d4.abqinfo.pages.dev/city-data/capital-spending/ . Every changed page has a direct link in the PR description, and all six rendered article texts, links and anchors match the local Hugo build. Browser UI inspection was unavailable. The full normal suite and actual-record/output-form regressions passed; final handoff validation is recorded in the review-ready folder.

The remaining gate is manual PR editorial review and subsequent merge/production authorization. No architecture or archival owner question remains pending.

Governance navigation: [workflow](governance-workflow.md), [registry](governance-registry.json), [active task](governance/active-task.json). CURRENT is resume evidence, not governing authority. Future substantive work uses a new frozen population and exhaustive resolver contract; a completed task supplies no new authorization.

Queue and campaign navigation: `ordinary-queue-current.json`, `active-campaign.json`, `campaign-workflow.md`. Prior stage evidence remains sealed by `workflow-stage-lifecycle.json`.
