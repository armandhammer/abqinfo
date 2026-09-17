# Legacy lane watcher reference (`claude` compatibility lane)

Use this reference only when an active campaign intentionally needs a persistent watcher. A Codex session may watch the legacy lane ID `claude`; the lane name is a compatibility identifier, not a separate agent or provider. Read `AGENTS.md`, `project-state/PARALLEL-VERIFICATION.md`, and `project-state/AUTONOMOUS-VERIFICATION-CAMPAIGNS.md` before acting. Preserve all unrelated files and changes.

From the attached ABQInfo coordinator checkout, start this command once and leave it running for the full watch window:

```powershell
./scripts/project/Invoke-ParallelVerificationCampaignLaneWatcher.ps1 `
  -LaneId claude `
  -DurationHours 9 `
  -TakeOverExpiredLease
```

The watcher must derive the active immutable manifest from `project-state/active-run.json`, process only the manifest-assigned `claude` lane in its detached worktree, skip valid existing results, continue after ordinary candidate failures or ambiguity, wait for the coordinator to activate successors, and then process the successor's `claude` lane. Do not ask for new campaign IDs, candidate ranges, worktree paths, or continuation prompts.

Your only durable work product may be the assigned immutable candidate result artifacts, the lane lease, and the watcher's external status/event log. Do not integrate results or edit inventory, checkpoint, active-run, queues, content, R2 state, or Git state. Do not fetch, switch, commit, push, open or merge a PR, upload to R2, deploy, or make content/editorial changes.

Ordinary non-passing verification is a durable result and is not a reason to stop. Stop only when the nine-hour watcher deadline elapses, the pending-review queue is exhausted and no successor appears, or the watcher reports a systemic fault such as an invalid manifest/hash/assignment, stale inventory/result, oversized lane, missing detached worktree, corrupt state, or irreconcilable lease conflict. If the command exits with `faulted-systemic`, report the exact status path, event log, and error without trying to repair shared state.
