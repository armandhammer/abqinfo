# Current project state

PR #198 on `codex/go-capital-quality-remediation` contains the completed 32-record implementation and is being reconciled with the authoritative `main` background snapshot at `90c78020d7d7cc2fc3eaee8b1baa7689966ed7b9`. It remains open and unmerged: https://github.com/armandhammer/abqinfo/pull/198 . The reviewed visitor-visible content tree is `833e473021f9fa58d6c361e6ea7a5e3f2b47fb1e`; branch reconciliation preserves those page bytes and the candidate inventory.

`main` and `chatgpt/planning-snapshot` are synchronized at the background snapshot commit above. They contain no PR #198 visitor-visible content. The owner authorization and exact R2 receipt are recorded there and on this branch. One 1,303,860-byte 2009 historical master was uploaded and verified; the 2011 masters were reused. No overwrite or deletion occurred, and reconciliation performs no R2 mutation.

The settled 2009 master contains 24 originals in 87 pages. The separate 2011 preliminary/EPC and published-directory masters contain 21 originals in 56 pages and 46 originals in 130 pages. The owner-kept `src-7567c5f27fceba0a` remains independently visible outside the 2009 master, with its historical negative finding and explicit owner reversal preserved.

The current reconciliation task and immutable contract are identified by [active-task.json](governance/active-task.json); its evidence is in [pr198-main-reconcile-2026-09-27](governance/pr198-main-reconcile-2026-09-27). Earlier PR implementation and main background-snapshot tasks are complete historical evidence and grant no new authority. The active branch lifecycle preserves both histories. [Governance workflow](governance-workflow.md) and [registry](governance-registry.json) remain authoritative; this page is resume evidence.

The remaining gate is owner manual editorial PR review. Merge and production deployment require the owner's later approval. The PR description provides direct links to all six changed pages on the verified nonproduction preview.
