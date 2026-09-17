# Usage-paused-proof verification campaigns

ABQInfo verification campaigns extend the bounded parallel-run workflow with candidate-level durability. A Codex session may stop at any point because of a five-hour window, weekly usage limit, or terminal interruption. Re-running the same lane command reconstructs progress from immutable artifacts and continues at the first missing candidate.

The campaign system does not run work in the background after a session stops. It guarantees that completed verification and integration work is neither lost nor duplicated when the user later says **Continue**.

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

- `campaign.json` is an immutable, hashed assignment of sorted candidate IDs to fixed microbatches and legacy-compatible lanes.
- Every candidate result is written atomically with create-new semantics and then made read-only. There is no mutable progress cursor.
- Status is derived by validating the manifest and scanning expected candidate results, intents, and receipts.
- Lane leases use an exclusive operating-system file handle. An active worker therefore cannot share ownership. An abandoned lease can be taken over only after expiration and only after the replacement obtains the exclusive handle.
- A lane name is an assignment, not an identity. Any resumed Codex session may work either legacy lane ID when the coordinator explicitly gives it that lane.
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

## One-prompt legacy-lane worker

Fill the three bracketed values from coordinator output, then run this once:

```text
You are the read-only worker for the legacy lane ID `claude` in the active ABQInfo verification campaign. The lane ID is a compatibility identifier, not a separate agent or provider.

Work only in this detached worktree:
<LANE_WORKTREE>

Use this immutable campaign manifest:
<CAMPAIGN_MANIFEST>

The coordinator-owned active pointer is:
<ACTIVE_RUN_POINTER>

Read AGENTS.md, project-state/PARALLEL-VERIFICATION.md, and project-state/AUTONOMOUS-VERIFICATION-CAMPAIGNS.md. Do not fetch, switch branches, modify Git state, create a campaign, change the active pointer, or edit inventory, checkpoint, content, queues, or R2.

Run the following from the detached worktree and allow it to process the entire assigned lane:

./scripts/project/Invoke-ParallelVerificationCampaignWorker.ps1 `
  -ManifestPath '<CAMPAIGN_MANIFEST>' `
  -LaneId claude `
  -RepoRoot (Get-Location).Path `
  -TakeOverExpiredLease

Ordinary candidate failures or ambiguity are durable results; continue processing later candidates. Stop only for a manifest/hash/assignment error, stale worker inventory, invalid existing result, active lane lease, or another systemic failure.

If usage pauses and I later say “Continue,” do not ask for a new batch prompt. Re-read the same three project instructions and active pointer, validate the same campaign, run the same command, skip every valid existing result, and resume at the first missing candidate. Report derived campaign status when the lane completes or stops.

Your only persistent writes may be your lane lease and manifest-assigned candidate result artifacts. Do not integrate results, commit, push, open a PR, upload, merge, or deploy.
```

If the prior process was terminated while holding a lease, wait until its recorded expiration before using `-TakeOverExpiredLease`. An exclusive handle still held by a live process always blocks takeover.

## Coordinator working a lane

The coordinator can work an assigned lane in bounded slices, inspect the derived status of every lane between slices, and make editorial decisions without allowing any worker to write shared project state:

```powershell
./scripts/project/Invoke-ParallelVerificationCampaignWorker.ps1 `
  -ManifestPath $manifest `
  -LaneId codex `
  -RepoRoot '<LANE_WORKTREE>' `
  -TakeOverExpiredLease `
  -MaxCandidates 10

./scripts/project/Get-ParallelVerificationCampaignStatus.ps1 `
  -ManifestPath $manifest
```

Repeat the worker command until the assigned lane is complete. `MaxCandidates` counts newly created results, not valid results skipped during resumption.

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

## Autonomous campaign rollover

When every assigned candidate has a valid immutable result and all lane leases are released or expired, preview the coordinator transition:

```powershell
./scripts/project/Invoke-ParallelVerificationCampaignCoordinator.ps1 `
  -ManifestPath $manifest `
  -WorktreeRoot 'C:\ABQinfo-campaign-worktrees'
```

The preview identifies non-passing results that must be escalated and selects the next sorted pending-review range, excluding every candidate reserved by any valid manifest in the campaign root. Selection continues after the completed campaign's highest candidate ID and wraps to the earliest still-unassigned pending record, so earlier gaps cannot be stranded. By default the successor inherits the predecessor's candidate count, microbatch size, and lanes. `-Count`, `-MicrobatchSize`, `-LaneIds`, and `-SuccessorCampaignId` may override those values.

Apply the reviewed transition with:

```powershell
./scripts/project/Invoke-ParallelVerificationCampaignCoordinator.ps1 `
  -ManifestPath $manifest `
  -WorktreeRoot 'C:\ABQinfo-campaign-worktrees' `
  -Apply `
  -TakeOverExpiredLease
```

Apply mode holds a coordinator-wide exclusive lease. It converts only valid failed or incomplete results to `requires human review` through `Merge-ParallelVerificationCampaign.ps1` and its separate inventory-writer lease. On a clean exit, it durably marks that lease released before closing it, so a later coordinator can safely reacquire the same path without a delete/recreate race. Invalid or stale results, unfinished verification, and active or orphaned-unexpired lane leases stop the transition. For a repository-local inventory, the coordinator refuses pre-existing unrelated inventory changes and commits only the coordinator-owned inventory path so the successor has an exact immutable Git snapshot.

The successor uses schema version 2 to hash-bind its predecessor ID and SHA-256. Creating a successor requires the live coordinator lease owner token, closing the race between global non-overlap selection and manifest publication. Its manifest remains create-new and read-only. Exact clean detached worktrees may be reused after an interrupted provisioning pass; conflicting, attached, dirty, or wrong-commit directories are rejected. The active pointer changes atomically only after all lanes are provisioned. The final JSON includes one complete prompt per lane, with the no-integration, no-R2, no-merge, and no-deploy restrictions.

Rerunning the same coordinator command after interruption is idempotent. Existing integration intents and receipts are reconciled, including a safe replay only when a receipt-bearing candidate is exactly back at that receipt's immutable input fingerprint, a matching immutable successor is reused, exact worktrees are resumed, and an already-advanced pointer is accepted only when it names that predecessor-bound successor.

## Continue and takeover protocol

When the user says **Continue**, any resumed Codex session must:

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

The suite covers immutable deterministic assignment, overlap across campaigns and batches, active-pointer recovery, detached worktree planning, interruption before and during verification, post-result restart, batch-transition restart, stale input, result tampering, lease contention and expiry, lane-neutral takeover, integration dry-run, write-ahead interruption, post-inventory/pre-receipt recovery, post-receipt restart, and duplicate-application prevention.

## Unattended supervisor and persistent lane watchers

The unattended supervisor continuously validates the active pointer, processes only its explicitly managed lanes in small resumable slices, and waits for other lanes. When all lane results are valid and leases are safely released, it invokes the crash-safe coordinator. The coordinator escalates only non-passing results to `requires human review`, commits only that inventory transition, provisions a predecessor-bound successor with no more than 120 candidates per lane, and atomically advances the pointer. The supervisor stops normally at its deadline or when no pending-review candidates remain; malformed, stale, oversized, or structurally invalid state is a systemic fault.

Start the nine-hour coordinator supervisor in a hidden process from the attached coordinator branch:

```powershell
./scripts/project/Start-ParallelVerificationCampaignSupervisor.ps1 `
  -DurationHours 9 `
  -SuccessorCandidateCount 240 `
  -MaxCandidatesPerLane 120 `
  -TakeOverExpiredLease
```

By default, the supervisor manages both legacy campaign lane IDs, `codex` and `claude`, sequentially with the deterministic PowerShell worker. The lane names are identifiers retained for campaign compatibility; they do not require separate AI agents or accounts. Use `-ManagedLaneIds` only when deliberately limiting supervision to a subset of lanes.

By default, process output and persistent state are written under the sibling `ABQinfo-verification-supervisor` directory. `latest.json` points to the active run's atomic `status.json` and append-only `events.ndjson`. The hidden process also has separate stdout and stderr logs. A supervisor-wide exclusive file lease prevents concurrent coordinators.

A Codex session can watch one assigned lane across every pointer rollover with:

```powershell
./scripts/project/Invoke-ParallelVerificationCampaignLaneWatcher.ps1 `
  -LaneId claude `
  -DurationHours 9 `
  -TakeOverExpiredLease
```

The watcher never coordinates, integrates, changes Git, or writes repository state. It derives the current campaign from `active-run.json`, enters that campaign's detached lane worktree, writes only assigned immutable candidate results and its external watcher status/log, waits after lane completion, and automatically follows the next active campaign. An exclusive per-lane watcher lease prevents duplicate persistent watchers.
