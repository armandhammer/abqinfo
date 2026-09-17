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
- R2 inventory: 1,180 objects / 8,614,076,524 bytes, with exact six-field equality to the saved live-R2 inventory.
- Archive reconciliation is locally complete. EPC and WIZ use the later explicit editorial decisions; no live R2 mutation occurred.
- Corrected 2014-2018 DPM packets are local only. Their upload/content transition remains externally gated; the already-live annual packets remain unchanged.

## Ordinary work

The 44 `add_to_inventory` rows in `project-state/discovery/undiscovered-documents-research-2026-09-14.json` are now inventory candidates with exact saved sizes, SHA-256 hashes, descriptions, cautions, and proposed pages. The durable mapping is `project-state/discovery/undiscovered-documents-candidate-integration-2026-09-17.json`. All remain `pending review`; no content or R2 change occurred.

The official City DPM directory and 18 existing Bernalillo County project pages passed authoritative HTTP validation as a coherent live-service batch. Results are in `project-state/discovery/live-service-validation-batch-2026-09-17.json`. Five MRCOG DocumentCenter records encountered during selection are static PDFs and remain behind the normal archive-first gate.

Capital Spending consolidation is the next ordinary-work priority, before the generic `src-05705d25113d3f2e` queue. The 2004 street-bond family review is complete: its distinct program, ballot, process, and enacted-resolution records remain separately visible and its transportation-specific records remain cross-listed; no synthetic master is warranted. The saved 2009, 2011, and 2013 GO-bond family research must be resumed from their artifacts, not restarted. Do not make a master record while their documented competing-version relationships remain unresolved.

After the Capital Spending consolidation queue reaches a defensible family boundary, resume ordinary review from `src-05705d25113d3f2e`. The newly integrated 2014 MS4 family should be reviewed as a package rather than as isolated attachments, and must pass the normal archive gate before publication.

## External gates

- Do not upload the corrected DPM packets or the separate 17-PDF / 67,526,043-byte batch without explicit authorization.
- Do not delete the noncanonical `mrmppo` duplicate, modify live R2, deploy, or merge merely as cleanup.
