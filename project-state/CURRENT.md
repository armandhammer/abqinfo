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

Reduce Codex context and token overhead while preserving ABQInfo project state, research history, validation rules, and automation.

Completed so far:

- repaired `.gitignore` and removed generated/local-only files from Git tracking;
- stopped routine startup loading of the full `master-inventory.json`;
- preserved the former dual-agent ledger verbatim at `project-state/history/AGENT-HANDOFF-legacy-2026-09-16.md`;
- adopted a single logical Codex workflow regardless of which ChatGPT/Codex account is currently logged in.

## Next action

Verify and commit the migration from the active dual-agent handoff to this compact resume model, then continue reducing unnecessary context loads in inventory-query and campaign workflows.
