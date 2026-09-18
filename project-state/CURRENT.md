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
- Project-state regeneration is deterministic and preserves durable checkpoint metadata. The checkpoint’s DPM packet state is regenerated from its manifest; do not hand-edit derived aggregate fields.

## Ordinary work

The 44 `add_to_inventory` rows in `project-state/discovery/undiscovered-documents-research-2026-09-14.json` are now inventory candidates with exact saved sizes, SHA-256 hashes, descriptions, cautions, and proposed pages. The durable mapping is `project-state/discovery/undiscovered-documents-candidate-integration-2026-09-17.json`. All remain `pending review`; no content or R2 change occurred.

The official City DPM directory and 18 existing Bernalillo County project pages passed authoritative HTTP validation as a coherent live-service batch. Results are in `project-state/discovery/live-service-validation-batch-2026-09-17.json`. Five MRCOG DocumentCenter records encountered during selection are static PDFs and remain behind the normal archive-first gate.

Capital Spending consolidation review is current. The durable family status is `project-state/discovery/capital-spending-consolidation-status-2026-09-17.json`; the 2013 decision is `project-state/discovery/go2013-department-set-decision-2026-09-17.json`. The 2013-2022 book is an EPC-stage record, not an adopted-program record, so the materially distinct 2013 department editions and useful existing summary/scope records remain separate. The 2011 preparation boundary is recorded in `project-state/discovery/2011-capital-spending-consolidation-manifest-2026-09-18.json`: two visually and structurally verified local-only compilations cover 21 preliminary/EPC and 46 published-program components (67 unique originals). Sixty-three originals are already byte-verified in R2; four distinct December 2010 City editions and both compilations remain behind future R2 authorization. The Capital Spending page, inventory, and R2 were not changed.

The 2013-2014 Paseo del Volcan family is complete: its 11 approved originals are publicly byte-identical in R2 and validated on Transportation Plans, Roadway Projects, and Parks and Recreation; eight records remain excluded and one delivery copy remains duplicate. Its durable research, decisions, plan, and validation artifact are `project-state/discovery/paseo-del-volcan-cluster-research-2026-09-11.json`, `project-state/discovery/paseo-del-volcan-publication-decisions-2026-09-17.json`, `project-state/discovery/paseo-del-volcan-r2-archive-plan-2026-09-17.json`, and `project-state/discovery/paseo-del-volcan-r2-public-validation-2026-09-17.json`.

`src-05b68a5758490499` is complete as `requires human review`: its saved City-source research records the unresolved choice to publish, redact, or summarize named residents' fiber-rulemaking correspondence. It has no R2 object or content placement. The 2014 MS4 Annual Report package decision is complete locally: exactly one main body and 27 attachments (28 records total), with saved exact-source hashes in `project-state/discovery/2014-ms4-package-decision-2026-09-18.json`. All 28 remain pending review behind explicit archive/publication and targeted contact/complaint-detail review gates; do not treat attachments as individual review items.

## External gates

- Do not upload the corrected DPM packets or the separate 17-PDF / 67,526,043-byte batch without explicit authorization.
- Do not delete the noncanonical `mrmppo` duplicate, modify live R2, deploy, or merge merely as cleanup.
