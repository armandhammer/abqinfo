# Usage-paused-proof verification campaigns

ABQInfo verification campaigns extend the bounded parallel-run workflow with candidate-level durability. A Codex or Claude task may stop at any point because of a five-hour window, weekly usage limit, terminal interruption, or provider handoff. Re-running the same lane command reconstructs progress from immutable artifacts and continues at the first missing candidate.

The campaign system does not run work in the background after a provider stops. It guarantees that completed verification and integration work is neither lost nor duplicated when the user later says **Continue**.

## State model

The campaign directory is outside Git and contains:

```text
campaign.json
leases/
  codex.json
  claude.json
results/
  codex/batch-0001/src-....json
  claude/batch-0002/src-....json
integration/
  intents/src-....json
  receipts/src-....json
```

- `campaign.json` is an immutable, hashed assignment of sorted candidate IDs to fixed microbatches and provider-neutral lanes.
- Every candidate result is written atomically with create-new semantics and then made read-only. There is no mutable progress cursor.
- Status is derived by validating the manifest and scanning expected candidate results, intents, and receipts.
- Lane leases use an exclusive operating-system file handle. An active worker therefore cannot share ownership. An abandoned lease can be taken over only after expiration and only after the replacement obtains the exclusive handle.
- A lane name is an assignment, not an identity. Codex may resume `claude`, or Claude may resume `codex`, when the coordinator explicitly gives it that lane.
- Integration writes an immutable intent before calling `Update-Candidate.ps1`. The inventory update includes a deterministic operation marker, followed by an immutable receipt. If execution stops between those writes, a rerun recognizes the marker and completes the receipt without applying the operation twice.

Workers never modify `master-inventory.json`, checkpoint, the active-run pointer, content, queues, Git state, or R2. Only the coordinator creates campaigns, sets the active pointer, creates/removes worktrees, accepts results, and integrates inventory decisions.

## Create a campaign

From a fresh coordinator branch at `origin/main`:

```powershell
$campaign = ./scripts/project/New-ParallelVerificationCampaign.ps1 `
  -CampaignId '2026-09-10-pending-01' `
  -LaneIds codex,claude `
  -StartId 'src-10d16d79d48b3ed3' `
  -Count 240 `
  -MicrobatchSize 10 | ConvertFrom-Json

$manifest = $campaign.manifest_path
```

Campaign creation requires the tracked inventory to match the selected Git commit. It scans existing immutable manifests under the campaign root and refuses any candidate assigned by another campaign. Candidate IDs are sorted, divided into consecutive microbatches, and batches are assigned round-robin to lanes.

The default campaign root is the sibling `ABQinfo-verification-campaigns` directory, outside the repository.

Create a coordinator-owned active pointer:

```powershell
./scripts/project/Set-ActiveParallelVerificationCampaign.ps1 `
  -ManifestPath $manifest
```

The pointer records the absolute manifest and artifact paths. Workers may read it but cannot modify it. `-Replace` is intentionally required when an active pointer already exists.

Create detached lane worktrees outside the repository:

```powershell
./scripts/project/Initialize-ParallelVerificationCampaignWorktrees.ps1 `
  -ManifestPath $manifest `
  -WorktreeRoot 'C:\ABQinfo-campaign-worktrees'
```

## One-prompt Claude worker

Replace the three bracketed values with coordinator output and send this once:

```text
You are the read-only worker for lane `claude` in the active ABQInfo verification campaign.

Work only in this detached worktree:
<CLAUDE_WORKTREE>

Use this immutable campaign manifest:
<CAMPAIGN_MANIFEST>

The coordinator-owned active pointer is:
<ACTIVE_RUN_POINTER>

Read AGENTS.md, project-state/PARALLEL-VERIFICATION.md, and project-state/AUTONOMOUS-VERIFICATION-CAMPAIGNS.md. Do not fetch, switch branches, modify Git state, create a campaign, change the active pointer, or edit inventory, checkpoint, content, queues, or R2.

Run the following from the detached worktree and allow it to process the entire assigned lane:

./scripts/project/Invoke-ParallelVerificationCampaignWorker.ps1 `
  -ManifestPath '<CAMPAIGN_MANIFEST>' `
  -LaneId claude `
  -WorkerProvider claude `
  -RepoRoot (Get-Location).Path `
  -TakeOverExpiredLease

Ordinary candidate failures or ambiguity are durable results; continue processing later candidates. Stop only for a manifest/hash/assignment error, stale worker inventory, invalid existing result, active lane lease, or another systemic failure.

If usage pauses and I later say “Continue,” do not ask for a new batch prompt. Re-read the same three project instructions and active pointer, validate the same campaign, run the same command, skip every valid existing result, and resume at the first missing candidate. Report derived campaign status when the lane completes or stops.

Your only persistent writes may be your lane lease and manifest-assigned candidate result artifacts. Do not integrate results, commit, push, open a PR, upload, merge, or deploy.
```

If the prior process was terminated while holding a lease, wait until its recorded expiration before using `-TakeOverExpiredLease`. An exclusive handle still held by a live process always blocks takeover.

## Codex master-decider and parallel worker

The coordinator can work its own lane in bounded slices, inspect Claude's progress between slices, and make editorial decisions without allowing either worker to write shared project state:

```powershell
./scripts/project/Invoke-ParallelVerificationCampaignWorker.ps1 `
  -ManifestPath $manifest `
  -LaneId codex `
  -WorkerProvider codex `
  -RepoRoot '<CODEX_WORKTREE>' `
  -TakeOverExpiredLease `
  -MaxCandidates 10

./scripts/project/Get-ParallelVerificationCampaignStatus.ps1 `
  -ManifestPath $manifest
```

Repeat the worker command until the Codex lane is complete. `MaxCandidates` counts newly created results, not valid results skipped during resumption.

Status reports campaign-, lane-, and batch-level assigned, completed, remaining, passed, failed, ambiguous, accepted, and integrated counts. It also reports whether each lease is absent, released, expired, unlocked/orphaned, or actively locked.

The coordinator reviews completed results and explicitly names accepted candidates. Preview is the default:

```powershell
./scripts/project/Merge-ParallelVerificationCampaign.ps1 `
  -ManifestPath $manifest `
  -AcceptedCandidateIds src-1111111111111111,src-2222222222222222
```

Apply only after reviewing the preview:

```powershell
./scripts/project/Merge-ParallelVerificationCampaign.ps1 `
  -ManifestPath $manifest `
  -AcceptedCandidateIds src-1111111111111111,src-2222222222222222 `
  -Apply `
  -TakeOverExpiredLease
```

An optional coordinator-owned decision JSON may add allowed inventory updates:

```json
{
  "campaign_id": "2026-09-10-pending-01",
  "campaign_sha256": "<CAMPAIGN_SHA256>",
  "decisions": [
    {
      "candidate_id": "src-1111111111111111",
      "accepted": true,
      "proposed_updates": {
        "status": "requires human review",
        "validation_status": "official source is ambiguous",
        "processing_notes_append": "Master review retained this candidate for human adjudication."
      },
      "decision_notes": "The source conflict is genuine and needs a person to choose the canonical record."
    }
  ]
}
```

Pass it with `-DecisionPath`. The command-line acceptance list remains mandatory. A failed or incomplete worker result can only be integrated when the decision explicitly sets `status` to `requires human review` and supplies non-empty `decision_notes`; it can never be silently treated as passed. Integration never edits content, creates a commit or PR, or performs an R2 operation.

After inventory decisions, the master coordinator performs ordinary ABQInfo editorial work in coherent 15–30-visible-addition PRs. Candidate verification does not itself authorize publication.

## Continue and takeover protocol

When the user says **Continue**, either provider must:

1. Read project instructions, checkpoint, and the active-run pointer.
2. Resolve and hash-validate the immutable campaign.
3. Run campaign status; never trust a remembered cursor.
4. Resume the explicitly assigned lane. Existing valid candidate results are skipped.
5. Take over only a released or expired, exclusively obtainable lane lease.
6. If acting as coordinator, inspect intents and receipts before integration. Existing receipts are skipped; intent-only operations are reconciled against the deterministic inventory marker.
7. Continue until the lane/campaign completes, usage pauses again, or a systemic safety check fails.

A worker should not ask the user for another candidate range, batch ID, or cursor. Those assignments are already immutable.

## Validation and forced-interruption tests

Run:

```powershell
./scripts/project/Test-ParallelVerificationCampaignWorkflow.ps1
```

The suite covers immutable deterministic assignment, overlap across campaigns and batches, active-pointer recovery, detached worktree planning, interruption before and during verification, post-result restart, batch-transition restart, stale input, result tampering, lease contention and expiry, provider-neutral takeover, integration dry-run, write-ahead interruption, post-inventory/pre-receipt recovery, post-receipt restart, and duplicate-application prevention.
