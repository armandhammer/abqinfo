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

Archive reconciliation local work is complete. The 14 initial bookkeeping repairs, 24 provenance-backed repairs, and 116 final published-object accounting gaps remain complete; R2 inventory stays exactly aligned with saved live R2. The 2003 EPC recommendation/Notice of Decision and the standalone WIZ appendix map are validated and placed locally in Capital Spending with the required enacted-program and parent-document limitations. The corrected 2014-2018 DPM packets contain 5/9/9/15/6 components and 13/17/19/32/10 pages; their hashes and sizes are recorded in checkpoint.json and the external-action manifest. The April 4, 2018 component is explicitly Agenda - approved minutes not located and does not establish meeting occurrence. Their R2 uploads are externally gated, so no placeholder DPM packet links were added to content. Fifty-three current-branch links remain deployment lag, 111 published legacy objects remain intentionally unconverted to master records, and one noncanonical duplicate R2 object remains only a future deletion candidate. No live R2 deletion/modification, upload, deployment, merge, or publication action has occurred.

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

Maintain the completed local reconciliation state. The next external action, if separately authorized, is upload of the five generated DPM annual packets described in `project-state/discovery/archive-reconciliation-external-action-manifest-2026-09-17.json`, followed by the corresponding content/deployment workflow. The 53 deployment-lag links require deployment authorization; the one duplicate remains a future deletion candidate only. Do not perform live R2 deletion or modification, upload, deployment, or merge without explicit authorization.
