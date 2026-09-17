# ABQInfo Current Work

This is the compact resume file for normal ABQInfo work. Workflow and context optimization is complete; do not start another optimization project or load historical handoff ledgers during routine startup.

## Startup and workflow

- Read `AGENTS.md`, inspect the current branch and worktree, then use this file. Read `checkpoint.json` or task artifacts only when relevant.
- `project-state/master-inventory.json` is authoritative. Query it selectively unless full-inventory regeneration or validation is required.
- ABQInfo uses one logical Codex workflow. Legacy `codex` and `claude` verification lane IDs remain only for script/artifact compatibility.
- No verification campaign is active; `project-state/active-run.json` is absent. Campaign tooling recreates that pointer when explicitly started and requires PowerShell 7 or newer.
- Preserve unrelated local files. Generated build output, backups, temporary files, and the superseded local live-R2 verification intermediate are ignored.

## Current state

- Branch: `codex/autonomous-campaign-coordinator`, reconciled with current `origin/main` while preserving the later local archive-accounting work.
- Master inventory: 7,086 unique records; status aggregates and `next_pending_id` are generated from the records.
- R2 inventory: 1,180 objects / 8,614,076,524 bytes, with exact six-field equality to the saved live-R2 inventory.
- Archive reconciliation is locally complete. EPC and WIZ use the later explicit editorial decisions; no live R2 mutation occurred.
- Corrected 2014-2018 DPM packets are local only. Their upload/content transition remains externally gated; the already-live annual packets remain unchanged.

## Ordinary work

Resume from saved discovery artifacts and the authoritative inventory. The next coherent inventory-only research integration is the 44 `add_to_inventory` rows in `project-state/discovery/undiscovered-documents-research-2026-09-14.json`; recheck current URL and checksum collisions before creating candidates. Do not publish those records until the normal archive gate is complete.

## External gates

- Do not upload the corrected DPM packets or the separate 17-PDF / 67,526,043-byte batch without explicit authorization.
- Do not delete the noncanonical `mrmppo` duplicate, modify live R2, deploy, or merge merely as cleanup.
