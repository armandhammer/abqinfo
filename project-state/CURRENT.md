# ABQInfo Current Work

This is the compact resume file for normal ABQInfo work. Workflow and context optimization is complete; do not start another optimization project or load historical handoff ledgers during routine startup.

## Startup and workflow

- Read `AGENTS.md`, inspect the current branch and worktree, then use this file. Read `checkpoint.json` or task artifacts only when relevant.
- `project-state/master-inventory.json` is authoritative. Query it selectively unless full-inventory regeneration or validation is required.
- ABQInfo uses one logical Codex workflow. Legacy `codex` and `claude` verification lane IDs remain only for script/artifact compatibility.
- No verification campaign is active; `project-state/active-run.json` is absent. Campaign tooling recreates that pointer when explicitly started and requires PowerShell 7 or newer.
- Preserve unrelated local files. Generated build output, backups, temporary files, and the superseded local live-R2 verification intermediate are ignored.

## Current state

- Repository history preserves the later local archive-accounting work through a history-preserving reconciliation with `origin/main`.
- Master inventory: 7,130 unique records; status aggregates and `next_pending_id` are generated from the records.
- R2 inventory: 1,191 objects / 8,638,742,164 bytes. The saved 1,180-object / 8,614,076,524-byte live-R2 snapshot remains the immutable archive-reconciliation baseline; the current ledger additionally contains the later publicly verified Paseo del Volcan archive batch.
- Archive reconciliation is locally complete. EPC and WIZ use the later explicit editorial decisions; no live R2 mutation occurred.
- Corrected 2014-2018 DPM packets are local only. Their upload/content transition remains externally gated; the already-live annual packets remain unchanged.

## Ordinary work

The 44 `add_to_inventory` rows in `project-state/discovery/undiscovered-documents-research-2026-09-14.json` are now inventory candidates with exact saved sizes, SHA-256 hashes, descriptions, cautions, and proposed pages. The durable mapping is `project-state/discovery/undiscovered-documents-candidate-integration-2026-09-17.json`. All remain `pending review`; no content or R2 change occurred.

The official City DPM directory and 18 existing Bernalillo County project pages passed authoritative HTTP validation as a coherent live-service batch. Results are in `project-state/discovery/live-service-validation-batch-2026-09-17.json`. Five MRCOG DocumentCenter records encountered during selection are static PDFs and remain behind the normal archive-first gate.

Capital Spending consolidation is complete. The durable family status is `project-state/discovery/capital-spending-consolidation-status-2026-09-17.json`; the 2013 decision is `project-state/discovery/go2013-department-set-decision-2026-09-17.json`. The 2013-2022 book is an EPC-stage record, not an adopted-program record, so the materially distinct 2013 department editions and useful existing summary/scope records remain separate.

The normal queue resumed with the complete 2013-2014 Paseo del Volcan family, beginning at `src-05705d25113d3f2e` (not an MS4 record). Its complete research, publication decisions, and 11-object archive plan are `project-state/discovery/paseo-del-volcan-cluster-research-2026-09-11.json`, `project-state/discovery/paseo-del-volcan-publication-decisions-2026-09-17.json`, and `project-state/discovery/paseo-del-volcan-r2-archive-plan-2026-09-17.json`. All eleven originals were re-fetched and exact-byte verified; eight records are excluded and one delivery copy is duplicate. The interrupted archive invocation ultimately created all eleven planned new objects. Recovery verified every public R2 download as byte-identical and reconciled all eleven master records without overwriting or deleting any object. Content integration is now the next stage; after this family is integrated, resume the ordinary queue and review the 2014 MS4 family as a package when reached.

## External gates

- Do not upload the corrected DPM packets or the separate 17-PDF / 67,526,043-byte batch without explicit authorization.
- Do not delete the noncanonical `mrmppo` duplicate, modify live R2, deploy, or merge merely as cleanup.
