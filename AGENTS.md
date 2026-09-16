# ABQInfo Codex Instructions

## Durable Project State

- At the start of a task, inspect the current Git branch and working-tree state. Read `project-state/checkpoint.json` and `project-state/active-run.json` when they are relevant to the task.
- `project-state/master-inventory.json` is authoritative project state, but do not read it wholesale by default. Use the repository's deterministic scripts or targeted parsing to retrieve only the candidate records or fields needed for the task. Load the full inventory only when a task explicitly requires full-inventory validation, regeneration, or another operation that inherently needs the complete file.
- Do not pull, rebase, merge, or otherwise reconcile with `origin/main` merely as startup housekeeping. Compare with `origin/main` when needed for the task and preserve the current worktree and branch state.
- Use the repository's deterministic PowerShell and Python scripts for crawling, downloading, hashing, extraction, deduplication, inventory updates, link checks, and Hugo validation whenever possible.
- Treat Legistar attachments as versioned delivery wrappers, not automatically distinct documents: compare hashes and extracted/rendered substantive content with existing City-source copies. A Legistar copy may prepend only Council bill, enactment, routing, signature, or agenda pages to an otherwise identical underlying document; retain one canonical original and document the wrapper relationship rather than archiving both.
- Missing-minutes agenda policy: after a recorded exhaustive official-source review finds no approved minutes for a meeting, ABQInfo may preserve a verified original official agenda. Label it “Agenda (approved minutes not located)” or equivalent, link the official source, preserve the meeting date, and never present it as minutes or a substitute. Do not archive agendas for officially cancelled or no-quorum meetings, or when an approved-minutes original is available.
- Save inventory status changes immediately and checkpoint meaningful progress throughout a batch so an interrupted task can resume without reconstructing prior work.
- Preserve unrelated user files and changes, including the untracked `backups/` directory.

## Batch and Pull Request Expectations

- A normal content PR should be a substantial coherent batch, generally 15-30 visible additions across 3-8 appropriate pages. Do not stop after one small source cluster unless a genuine technical, authorization, storage, or usage boundary requires it.
- A static document must be archived to R2 and its public archive download verified (exact size and SHA-256, plus authoritative-source provenance) before it is added to any site page. Retain the official source link alongside the archive link. The only exception is content that cannot meaningfully be archived as a document, such as a live ArcGIS web map or another genuinely live official service; label and link those as live sources rather than treating them as archived records.
- Never open or describe a content PR as site-ready when it contains a direct-source-only static document. If archival is not authorized or cannot be completed, keep the item inventory-only and state that blocker.
- Every PR description must list each modified ABQInfo page with its direct `https://abqinfo.com/` URL and enumerate the exact visible additions, removals, moves, and cross-listings on that page.
- For an unmerged site-content PR, replace production page links with the verified temporary deployment URL for that PR. State the exact added or changed visible headings and document titles; do not use aggregate descriptions such as a count or category of records. Use production URLs only after the change is live.
- Distinguish inventory-only work from visible site changes. Report R2 uploads, exact added storage, size warnings, validation results, and unresolved items.
- The user has authorized autonomous merge and production deployment for routine ABQInfo content PRs that meet the archival and validation standards in this file. Before merging, confirm the PR is limited to the intended coherent batch, its temporary deployment is healthy, and all required checks pass. Do not autonomously merge or deploy a PR involving a novel content category, unresolved provenance/version conflict, failed check, destructive storage change, credential/permission change, or material site-architecture change; surface those for user direction.

## Required End-of-Task Handoff

Every substantive task-ending response must state the saved artifact paths, the concrete result, validation performed, and any remaining blocker. It must be self-contained: do not require the user to relay a prompt, create a new conversation, or manually coordinate a follow-up merely to receive or use the completed work.

Recommend a next task and model only when it would materially help the user decide what to do next. Do not include a copy-and-paste prompt unless the user explicitly asks for one.

Use this model-selection baseline:

- `GPT-5.6 Terra, Medium`: default for normal ABQInfo research, document review, editorial placement, archiving, validation, and PR preparation.
- `GPT-5.6 Terra, High`: large or unusually ambiguous batches involving conflicting versions, uncertain relevance, or complicated cross-listing.
- `GPT-5.6 Sol, High`: crawler or methodology redesign, diagnosis of missed benchmark documents, difficult state recovery or merge conflicts, major information-architecture changes, and unusually complex planning or engineering interpretation.
- `GPT-5.6 Luna, Medium`: deterministic formatting, metadata cleanup, inventory regeneration, and scripted link or build checks requiring little editorial judgment.

Do not recommend a higher model merely because a batch contains many files when local scripts handle the volume and the editorial decisions are straightforward.
