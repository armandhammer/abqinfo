# ABQInfo Current Work

This is the compact resume file for normal Codex work. Keep it current and concise.
Do not use historical handoff ledgers as routine startup context.

## Workflow

- ABQInfo uses one logical Codex workflow at a time.
- The Codex login/account may change when usage limits are reached; that does not create a separate agent or work lane.
- Do not create parallel-agent coordination state unless a task explicitly requires parallel execution.
- Use deterministic PowerShell or Python tooling for crawling, downloading, hashing, extraction, inventory queries, validation, and other mechanical work whenever possible.

## Current repository context

- Branch at creation: `codex/autonomous-campaign-coordinator`
- Inspect `git status` at the start of work; do not assume the working tree is clean.
- `project-state/master-inventory.json` remains authoritative but should be queried selectively rather than loaded wholesale.
- `project-state/active-run.json` is machine state for the verification-campaign tooling. Read it only when working with that tooling.
- Historical Claude/Codex coordination is preserved under `project-state/history/` and is not startup context.

## Current task

The archive-reconciliation provenance campaign is complete for all deterministic local work: 14 initial R2-inventory bookkeeping repairs and 24 provenance-backed master/R2 accounting repairs are complete. Three editorial or policy cases remain in `project-state/discovery/archive-reconciliation-unresolved-review-2026-09-17.json`: the 2003 EPC hearing-notification packet, the Water Master Plan Infrastructure Zone map, and the April 4, 2018 DPM agenda. One noncanonical duplicate R2 object remains only a future deletion candidate. No live R2 deletion or modification, publication, deployment, or further master-inventory repair is currently authorized.

Completed so far:

- repaired `.gitignore` and removed generated/local-only files from Git tracking;
- stopped routine startup loading of the full `master-inventory.json`;
- preserved the former dual-agent ledger verbatim at `project-state/history/AGENT-HANDOFF-legacy-2026-09-16.md`;
- adopted a single logical Codex workflow regardless of which ChatGPT/Codex account is currently logged in.

## Current workflow

Token/context optimization is complete.

- Use one logical Codex workflow regardless of which Codex account is logged in.
- Use `project-state/CURRENT.md` for compact cross-session continuity.
- Query `master-inventory.json` selectively; do not load it wholesale unless the task inherently requires it.
- `Get-CandidatesByStatus.ps1` returns 50 records by default; use `-Skip` and `-Limit` for paging or `-All` only when full output is explicitly required.
- The verification supervisor processes both legacy `codex` and `claude` lane IDs sequentially with deterministic PowerShell workers; those lane names do not represent separate AI agents.
- Verification campaign tooling requires PowerShell 7 or newer.
- Historical dual-agent handoff material is preserved under `project-state/history/` and is not normal startup context.

## Next action

Obtain an editorial or policy decision for the three isolated unresolved archive-reconciliation cases before any further local accounting, publication, or storage action. Do not perform live R2 deletion or modification, publication, deployment, or further master-inventory repair without explicit authorization.
