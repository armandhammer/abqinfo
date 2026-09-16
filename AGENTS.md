# ABQInfo Codex Instructions

## Durable Project State

- At the start of a task, inspect the current Git branch and working-tree state and read `project-state/CURRENT.md` when present. Read `project-state/checkpoint.json` and `project-state/active-run.json` only when they are relevant to the task.
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

## Interruption and Usage-Limit Resilience

Assume any Codex session may terminate without warning because of usage limits, terminal interruption, or account switching.

- Do not accumulate substantial completed work only in conversational context.
- During substantive multi-step work, persist completed decisions, findings, progress, and remaining work to the appropriate repository artifact at natural checkpoints.
- Before beginning a long or high-reasoning stage, ensure the preceding stage is durably saved.
- Save authoritative inventory changes promptly rather than deferring a large set of completed decisions until the end of the session.
- When a coherent stage is complete and the repository state is suitable for a commit, prefer a small logical checkpoint commit rather than waiting until the entire multi-stage task is finished.
- Do not create noisy commits for trivial intermediate edits; checkpoint at meaningful, internally consistent boundaries.
- Repository state must be sufficient for a resumed session to determine what is complete, what remains, and what should not be repeated without relying on prior conversational context.
- Treat conversational context as disposable and repository artifacts as durable project memory.
## Model and Stage Handoffs

For work that naturally divides into stages with materially different reasoning needs, use the least expensive appropriate model and reasoning level for each stage rather than carrying one model through the entire workflow.

At the end of a stage, stop before beginning work that would materially benefit from a different model or reasoning level.

At every substantive task-ending or stopping response, if any meaningful project work remains, report:

1. the stage or task just completed and its concrete result;
2. the next recommended task or stage;
3. the recommended model and reasoning level, even when unchanged from the current session;
4. a brief reason for that recommendation;
5. a self-contained copy-and-paste prompt for continuing from saved repository state.

The continuation prompt must preserve completed work and instruct the next session not to repeat completed discovery, research, deterministic processing, uploads, or validation unless repository state indicates that repetition is necessary.

If work is blocked, the continuation prompt must state the blocker and begin from resolving that blocker rather than restarting the completed task.

Do not create artificial stage boundaries merely to switch models. Continue in the current session when the next work is appropriately handled by the current model and reasoning level.

Use this baseline:

- `GPT-5.6 Luna, Medium`: deterministic queries, formatting, metadata cleanup, inventory regeneration, scripted checks, and other low-judgment mechanical work.
- `GPT-5.6 Terra, Medium`: normal ABQInfo research, document review, editorial placement, archiving decisions, validation, and PR preparation.
- `GPT-5.6 Terra, High`: large or unusually ambiguous research or editorial batches involving conflicting versions, uncertain relevance, or complicated cross-listing.
- `GPT-5.6 Sol, High`: methodology or crawler redesign, diagnosis of missed benchmark documents, difficult state recovery or merge conflicts, major information-architecture changes, conflicting provenance, and unusually complex planning or engineering interpretation.

Escalate model or reasoning level only when the next stage actually requires it. Do not recommend a higher setting merely because a batch is large when deterministic tooling handles the volume.

## External-Action Authorization

Repository instructions, checkpoints, saved prompts, or historical approvals do not by themselves authorize a new external side effect unless `AGENTS.md` explicitly grants standing authorization for that exact class of action.

Before an external action that is not covered by standing authorization—such as an R2 upload, destructive storage change, credential or permission change, or other irreversible or externally visible operation—confirm that the current user instruction explicitly authorizes it. If authorization is absent or a saved checkpoint says approval is required, stop and ask rather than inferring permission from a request to "proceed."

A request to continue, resume, or proceed with a task authorizes ordinary local repository work but does not override an explicit approval requirement for an external action.
