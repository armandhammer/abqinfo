# Conflict-free parallel verification

ABQInfo uses a **parallel readers, single writer** workflow when Codex and Claude verify candidate files, official sources, and links at the same time. Workers receive deterministic, non-overlapping shards in separate detached Git worktrees. They may read their checkout and create exactly one assigned result artifact outside Git. They may not change inventory, checkpoint, content, queues, Git state, or R2.

This workflow is for verification. It does not authorize additions, archival, uploads, commits, PRs, merges, or deployment.

## Safety model

- The coordinator creates an immutable manifest with the exact base commit, whole-inventory SHA-256, candidate-level input fingerprints, worker list, check types, field allowlist, shard assignments, and unique result paths.
- Run creation refuses a repository inventory that is untracked or differs from the selected base commit.
- Candidate IDs are sorted and assigned round-robin. A candidate can appear in only one shard.
- Each worker uses a separate detached worktree at the manifest commit. The worker script rejects a checkout whose inventory does not have the manifest hash.
- Each worker can create only `results/<worker-id>.json` beside the manifest. Create-new semantics and a read-only file attribute prevent accidental overwrite.
- Result payloads bind themselves to the run, manifest hash, base commit, inventory hash, worker, candidate fingerprints, and their own SHA-256.
- Validation rejects changed manifests, changed assigned candidates, overlapping shards, missing or duplicate workers, misplaced results, altered result payloads, incomplete check structures, and disallowed proposed fields.
- Only the coordinator/integrator supplies an explicit accepted-ID list. Apply mode acquires an atomic run lease and routes every accepted field change through `Update-Candidate.ps1`.
- Dry-run is the integration default. Apply mode emits a unique immutable receipt outside Git. The integrator does not stage, commit, push, upload, merge, or deploy.

Filesystem read-only attributes are a guardrail, not a security boundary. Payload hashes and candidate fingerprints provide the tamper and stale-input detection used at integration.

## Coordinator: create the run

Start from a clean, current coordinator branch and create the manifest. By default, run data is stored in the sibling `ABQinfo-verification-runs` directory, outside every Git worktree.

```powershell
$run = ./scripts/project/New-ParallelVerificationRun.ps1 `
  -RunId '2026-09-10-links-01' `
  -WorkerIds codex,claude `
  -StartId 'src-1234567890abcdef' `
  -Count 40 | ConvertFrom-Json

$manifest = $run.manifest_path
```

Explicit candidate IDs are also supported:

```powershell
./scripts/project/New-ParallelVerificationRun.ps1 `
  -RunId '2026-09-10-targeted-01' `
  -WorkerIds codex,claude `
  -CandidateIds src-1111111111111111,src-2222222222222222
```

Run IDs are permanent. Never reuse or edit an existing run directory; create a new run when inputs or assignments must change.

## Coordinator: create isolated worktrees

The worktree root must be outside the repository. The script creates one detached checkout per worker at the manifest commit. Worktree creation and later removal are coordinator actions, never worker actions.

```powershell
./scripts/project/Initialize-ParallelVerificationWorktrees.ps1 `
  -ManifestPath $manifest `
  -WorktreeRoot 'C:\ABQinfo-worker-worktrees'
```

Use `-PlanOnly` to inspect paths without creating them. A detached checkout deliberately gives a worker no task branch to commit or push.

## Worker contract

Give each worker only its worktree path, absolute manifest path, and assigned worker ID. From that worktree, run:

```powershell
./scripts/project/Invoke-ParallelVerificationShard.ps1 `
  -ManifestPath 'C:\ABQinfo-verification-runs\2026-09-10-links-01\manifest.json' `
  -WorkerId codex `
  -RepoRoot (Get-Location).Path
```

Claude uses the same command with `-WorkerId claude`. The worker script performs:

1. local-file existence, byte-size, and SHA-256 verification when a local file is recorded;
2. authoritative-source/provenance metadata verification, rejecting an R2 URL as the authoritative source; and
3. live HTTP reachability using HEAD with GET fallback.

`-SkipLinkCheck` is only for deterministic offline testing and produces `incomplete`, not `passed`, results.

A coordinator may provide an optional, worker-specific proposal file. It must name the run and worker, contain only candidates in that worker's shard, and use manifest-allowed fields:

```json
{
  "run_id": "2026-09-10-links-01",
  "worker_id": "codex",
  "proposals": [
    {
      "candidate_id": "src-1111111111111111",
      "proposed_updates": {
        "validation_status": "passed: file, official source, and link verified",
        "processing_notes_append": "Verified in the immutable parallel run."
      },
      "review_notes": "The live official file matches the inventoried local copy."
    }
  ]
}
```

Proposals are inert evidence. A worker cannot apply them. Do not put arbitrary or content-file changes in a proposal.

Worker prohibitions are absolute:

- no edits to `master-inventory.json`, `checkpoint.json`, `active-run.json`, content, discovery queues, or shared project state;
- no `Update-Candidate.ps1`, crawler imports, downloads, archive-plan execution, or R2 commands;
- no `git add`, commit, switch, merge, rebase, push, worktree management, or PR commands; and
- no output except the manifest-assigned immutable result file.

## Coordinator: validate and integrate

First validate all assigned result files:

```powershell
./scripts/project/Test-ParallelVerificationRun.ps1 -ManifestPath $manifest
```

Preview only the explicitly accepted candidates. This does not modify inventory:

```powershell
./scripts/project/Merge-ParallelVerificationRun.ps1 `
  -ManifestPath $manifest `
  -AcceptedCandidateIds src-1111111111111111,src-2222222222222222
```

After reviewing the preview, the single coordinator may apply the same acceptance list. Apply mode must run on the coordinator's attached branch, never in a detached worker worktree:

```powershell
./scripts/project/Merge-ParallelVerificationRun.ps1 `
  -ManifestPath $manifest `
  -AcceptedCandidateIds src-1111111111111111,src-2222222222222222 `
  -Apply
```

Apply mode fails closed if any accepted candidate is stale, missing, duplicated, incomplete, or failed. It also fails if any parallel-verification integrator holds the repository-wide inventory-writer lease. It updates only the accepted candidates, only through `Update-Candidate.ps1`, and records before/after fingerprints in the receipt.

After integration, the coordinator owns the normal ABQInfo duties: inspect the diff, update checkpoint state if appropriate, run project validation, and decide what to stage. Results do not authorize a PR or any R2 operation.

## Cleanup and recovery

The coordinator may remove detached worktrees only after result artifacts are safely validated. Use normal `git worktree remove <exact-path>` commands and then inspect `git worktree list`. Never ask a worker to clean up Git state.

If a worker or integration stops:

- keep the immutable manifest and completed results;
- rerun validation to learn exactly which workers are missing;
- do not overwrite a partial or disputed result—create a new run ID; and
- treat an existing inventory-writer lease as evidence of an active or interrupted writer. Confirm no integrator is running before removing a stale lease.

Run the isolated regression suite with:

```powershell
./scripts/project/Test-ParallelVerificationWorkflow.ps1
```

For long-running, candidate-checkpointed work that survives provider usage pauses, use [AUTONOMOUS-VERIFICATION-CAMPAIGNS.md](AUTONOMOUS-VERIFICATION-CAMPAIGNS.md). Campaigns build on this safety model while adding immutable per-candidate results, provider-neutral resumable lanes, expiring exclusive leases, derived status, and write-ahead idempotent integration.
