# ABQInfo Codex Instructions

## Workflow Roles

- ChatGPT is the project lead and handles planning, stage sequencing, and continuation prompts.
- Codex is the implementation worker.

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

- Mission scope is a mandatory prerequisite to approval, archive preparation, backlog ranking, or any visible/static addition. An approved record must carry a structured `scope_assessment` that records: geographic/institutional scope; a specific, material Albuquerque connection; ABQInfo public-information value; an explicit exclusion test explaining why general context is insufficient; a final scope decision; and a substantive rationale. Provenance, authenticity, quality, family coherence, archive readiness, or a plausible page may not substitute for this determination.
- The positive scope gate also applies to `downloading`, `downloaded`, `parsed`, `description drafted`, `placement assigned`, `implemented`, and `validated`; a newly reviewed or changed record cannot enter or remain in any of these states without `final_scope_decision = passes_both_gates` and the complete assessment. The exact 2026-09-23 frozen legacy registry allows only unchanged historical `placement assigned`, `implemented`, and `validated` rows with their original status and update timestamp to validate without retrospective assessments. It is not a route for new review or state transitions; any change to one of those rows requires positive scope first.
- Apply two independent gates before approval: (1) the record must substantially concern Albuquerque, a City entity/service/project/facility/policy/expenditure/regulation/decision, or a regional/state/federal matter with a specific and material Albuquerque component; and (2) it must materially help a reader understand a core ABQInfo public-information subject. Statewide applicability, agency jurisdiction, an interstate passing through Albuquerque, incidental references/maps/statistics, or generic contextual usefulness do not satisfy the first gate. Geographic connection alone, peripheral technical-operational material, transactional paperwork, generic templates, or trivial material do not satisfy the second gate.
- Ask whether a reasonable ABQInfo user gains meaningful Albuquerque public-policy or infrastructure information here beyond what is naturally available from the originating agency. If the answer is not substantive, exclude the record or require human review. Backlog ranking begins only after a positive scope decision; archive readiness ranks eligible work and never establishes eligibility.
- Mission-scope review has exactly three outcomes: `passes_both_gates`; a definitive scope exclusion; or `requires_human_scope_review`. Use the last outcome only for a genuine borderline: a specific material Albuquerque connection and credible public-information value exist, but usefulness/significance is close enough that editorial judgment should control. Clearly irrelevant, generic, statewide, transactional, trivial, or merely contextual material must be excluded directly, not sent to human scope review.
- A borderline record must use inventory status `requires human review`, `review_reason = mission_scope_borderline`, and a structured scope assessment with title, publisher, date, geographic/institutional scope, specific Albuquerque connection, potential public-information value, why it does not confidently pass, why it does not clearly fail, proposed page/section if admitted, recommended default disposition, and substantive rationale. It cannot advance to an eligible publication state until a human disposition is durably applied.
- Maintain `project-state/discovery/mission-scope-borderline-human-review-queue.json` as the exclusive queue for unresolved `mission_scope_borderline` records. Do not mix privacy, provenance, version/finality, legal-status, source-recovery, or other human-review reasons. Continue ordinary work below 20 unresolved cases; at 20, stop adding scope-borderline cases and make that 20-record review batch the next user-facing decision task. Surface a smaller batch only when it resolves the active family or no other productive ungated work remains.
- Provenance, authenticity, successful parsing, archival verification, and a well-written description are necessary but do not establish that a document deserves a separate public-facing entry. Before any static document is approved for visible publication, record and validate a `quality_assessment` covering visual inspection, measured page/text content, standalone public value, information density, series/component relationships, intended publication form, and a substantive rationale.
- Do not publish administrative scraps, context-free requests, skeletal summaries, or serial fragments as standalone entries merely because they are authoritative. A one- or two-page text document with fewer than 250 extractable words requires an explicit limited-content exception; maps, forms, legal instruments, and dense visual or tabular records may qualify when their distinct use is documented.
- Review every component or serial document against its complete family before publication. Prefer one curated, chronological or program-level master historical record when several short official files are meaningful mainly together. Preserve the byte-identical originals and their individual provenance in R2 and inventory history even when the public site presents a consolidated master record.

- A normal content PR should be a substantial coherent batch, generally 15-30 visible additions across 3-8 appropriate pages. Do not stop after one small source cluster unless a genuine technical, authorization, storage, or usage boundary requires it.
- A static document must be archived to R2 and its public archive download verified (exact size and SHA-256, plus authoritative-source provenance) before it is added to any site page. Retain the official source link alongside the archive link. The only exception is content that cannot meaningfully be archived as a document, such as a live ArcGIS web map or another genuinely live official service; label and link those as live sources rather than treating them as archived records.
- Never open or describe a content PR as site-ready when it contains a direct-source-only static document. If archival is not authorized or cannot be completed, keep the item inventory-only and state that blocker.
- Any addition, removal, substantive rewrite, heading or section rename, move, canonical-page change, cross-listing change, or other change visible to a normal site visitor must be presented in a PR for the user's manual review and approval before merge. Codex must not autonomously merge or deploy a PR with visible site-content changes, even when checks and preview pass or the content category is routine. Historical autonomous-content-merge instructions do not override this rule. Background-only changes to agent instructions, project state, inventory, tracking, logs, scripts, or validation machinery do not require a user-facing content PR solely because those files changed.
- A site-content PR description is a manual editorial review aid, not a repository change log. In concise human-readable UTF-8 Markdown with actual newline characters, identify exactly what changed visibly, where, and why when useful. For each modified page, name the visible addition, removal, rewrite, rename, move, or cross-listing with its actual heading and document titles. Avoid generic counts or descriptions. Do not enumerate routine background files or metadata unless they materially explain a visible change; those remain available in Git history and the Files tab.
- For each modified public page in an unmerged content PR, give a direct link to the changed page on the verified non-production review deployment, preferably with a working changed-section anchor. The link must open the changed page rather than the preview homepage. Use a production `https://abqinfo.com/` page URL only after the change is live or when no functioning preview URL is available, and explain that limitation.
- Before creating or editing a PR, construct its description in a real Markdown file, validate it with `scripts/project/Test-PullRequestDescription.ps1`, and submit it with `gh pr create --body-file <file>` or `gh pr edit --body-file <file>`. Do not embed an escaped multi-line body in a command-line string.
- Distinguish inventory-only work from visible site changes. Report R2 uploads, exact added storage, size warnings, validation results, and unresolved items.
- After a visible site-content PR is prepared and its preview verified, stop for the user's manual PR review. Merge, deployment, and production verification require the user's subsequent approval. Background-only, non-visible work may follow its otherwise applicable workflow rules.

## Required End-of-Task Report

At the end of a substantive task, Codex should report what it completed, commits and artifacts created, validation performed, unresolved blockers or issues, and the recommended next type of work and model/reasoning level when useful. Codex should not generate a copy-and-paste continuation prompt.

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
