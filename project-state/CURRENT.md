# ABQInfo Current Work

This is the compact resume file for normal ABQInfo work. Workflow and context optimization is complete; do not start another optimization project or load historical handoff ledgers during routine startup.

## Startup and workflow

- Read `AGENTS.md`, inspect the current branch and worktree, then use this file. Read `checkpoint.json` or task artifacts only when relevant.
- `project-state/master-inventory.json` is authoritative. Query it selectively unless full-inventory regeneration or validation is required.
- No verification campaign is active; preserve unrelated local files and ignored build output, backups, and temporary files.

## Current state

- Master inventory has 7,130 unique records; status aggregates and `next_pending_id` are generated. R2 contains 1,191 objects / 8,638,742,164 bytes; the 1,180-object live-R2 snapshot remains the immutable archive-reconciliation baseline.
- Archive reconciliation is locally complete without live-R2 mutation. Corrected 2014-2018 DPM packets are local only and externally gated.
- Capital Spending consolidation research is closed by `project-state/discovery/capital-spending-consolidation-closeout-status-2026-09-18.json`; future build, archive/public verification, page edit, merge, or deployment is separately externally gated.

## Ordinary work

The saved terminal City web-page batches, the 34-record Prescription Trails human-review package, the 2014 MS4 package, the code-enforcement Notices and Orders, and the LGCC agenda family remain outside ordinary review unless a new task explicitly scopes them. `src-06d0fc4cd0abdef6` and the seven Administration answers to Council questions records are approved inventory-only and separately archive/publication gated.

The accepted 18-record NMDOT grant-administration-and-application decision is `project-state/discovery/nmdot-grant-administration-and-application-decision-2026-09-19.json`. All 18 are approved inventory-only, placement-unresolved, and behind R2/public-byte-verification and future information-architecture gates. Do not repeat their research or describe any member as the next ordinary review merely because its status is nonterminal.

The seven-part NMDOT statewide truck parking study is approved inventory-only under `project-state/discovery/nmdot-statewide-truck-parking-study-decision-2026-09-19.json`. It is a complete numbered study series; five DOCX originals and two PDFs retain their original containers. Its proposed Roadway Studies placement fits the state-highway-studies scope, but R2 archival, public-byte verification, implementation, validation, and public-content work remain separately gated.

The next genuinely actionable ordinary candidate is `src-0880f378bceeef60`, `sac rfp 7703 92 bellamah extension.pdf`: a pending-review City PDF not covered by the completed or externally gated families above. Review it only with a new task instruction and first determine whether it belongs to a coherent procurement family rather than merits a standalone record.

## External gates

- Do not upload corrected DPM packets, the separate 17-PDF / 67,526,043-byte batch, or any inventory-only NMDOT study originals without explicit authorization.
- Do not modify live R2, delete the noncanonical `mrmppo` duplicate, merge, or deploy merely as cleanup.
