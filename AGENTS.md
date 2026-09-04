# ABQInfo Codex Instructions

## Durable Project State

- At the start of every task, reconcile Git state with `origin/main` and read `project-state/checkpoint.json`, `project-state/master-inventory.json`, and `project-state/active-run.json` when present.
- Use the repository's deterministic PowerShell and Python scripts for crawling, downloading, hashing, extraction, deduplication, inventory updates, link checks, and Hugo validation whenever possible.
- Save inventory status changes immediately and checkpoint meaningful progress throughout a batch so an interrupted task can resume without reconstructing prior work.
- Preserve unrelated user files and changes, including the untracked `backups/` directory.

## Batch and Pull Request Expectations

- A normal content PR should be a substantial coherent batch, generally 15-30 visible additions across 3-8 appropriate pages. Do not stop after one small source cluster unless a genuine technical, authorization, storage, or usage boundary requires it.
- Every PR description must list each modified ABQInfo page with its direct `https://abqinfo.com/` URL and enumerate the exact visible additions, removals, moves, and cross-listings on that page.
- Distinguish inventory-only work from visible site changes. Report R2 uploads, exact added storage, size warnings, validation results, and unresolved items.
- Do not merge or deploy without explicit user approval.

## Required End-of-Task Handoff

Every substantive task-ending response must conclude with all five fields below, even if the user does not ask for them:

**Next task:** A concrete description based on the saved checkpoint and queue.

**New conversation:** `Yes` after a merged PR, completed major batch, or material change of work type; otherwise `No` while fixing or completing the same PR or batch.

**Recommended model:** Give the exact model and reasoning level for the next task.

**Reason:** One sentence explaining the recommendation.

**Paste this:** A complete, concise prompt the user can paste into the next conversation.

Use this model-selection baseline:

- `GPT-5.6 Terra, Medium`: default for normal ABQInfo research, document review, editorial placement, archiving, validation, and PR preparation.
- `GPT-5.6 Terra, High`: large or unusually ambiguous batches involving conflicting versions, uncertain relevance, or complicated cross-listing.
- `GPT-5.6 Sol, High`: crawler or methodology redesign, diagnosis of missed benchmark documents, difficult state recovery or merge conflicts, major information-architecture changes, and unusually complex planning or engineering interpretation.
- `GPT-5.6 Luna, Medium`: deterministic formatting, metadata cleanup, inventory regeneration, and scripted link or build checks requiring little editorial judgment.

Do not recommend a higher model merely because a batch contains many files when local scripts handle the volume and the editorial decisions are straightforward.
