[CmdletBinding()]
param(
  [string]$ManifestPath,
  [string]$ActiveRunPath = 'project-state/active-run.json',
  [string]$InventoryPath,
  [string]$CampaignRoot,
  [string]$WorktreeRoot,
  [string]$SuccessorCampaignId,
  [ValidateRange(0,100000)][int]$Count = 0,
  [string[]]$LaneIds,
  [ValidateRange(0,100)][int]$MicrobatchSize = 0,
  [switch]$Apply,
  [switch]$TakeOverExpiredLease,
  [ValidateRange(1,60)][int]$LeaseMinutes = 5,
  [string]$CoordinatorLeasePath,
  [string]$InventoryWriterLeasePath,
  [switch]$WorktreePlanOnly,
  [Parameter(DontShow)][ValidateSet('','after-integration','after-inventory-commit','after-successor','after-worktrees','after-pointer')][string]$TestInterruptAt = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/ParallelVerification.Campaign.Common.ps1"

function Get-SuccessorCampaignId([string]$CampaignId) {
  if ($CampaignId -match '^(?<prefix>.*?)(?<number>[0-9]+)$') {
    $width = $Matches.number.Length
    $next = ([int64]$Matches.number + 1).ToString("d$width")
    $value = "$($Matches.prefix)$next"
  } else {
    $value = "$CampaignId-next"
  }
  if ($value.Length -gt 64 -or $value -notmatch '^[a-z0-9][a-z0-9._-]{2,63}$') { throw 'Unable to derive a valid successor campaign ID; specify SuccessorCampaignId.' }
  $value
}

function Get-CampaignWorkerPrompt([string]$Lane,[string]$Worktree,[string]$Manifest,[string]$Pointer) {
  $manifestLiteral = $Manifest.Replace("'","''")
  @"
You are the read-only worker for lane $Lane in the active ABQInfo verification campaign.

Work only in this detached worktree:
$Worktree

Use this immutable campaign manifest:
$Manifest

The coordinator-owned active pointer is:
$Pointer

Read AGENTS.md, project-state/PARALLEL-VERIFICATION.md, and project-state/AUTONOMOUS-VERIFICATION-CAMPAIGNS.md. Do not fetch, switch branches, modify Git state, create a campaign, change the active pointer, or edit inventory, checkpoint, content, queues, or R2.

Run this command from the detached worktree and allow it to process the entire assigned lane:

./scripts/project/Invoke-ParallelVerificationCampaignWorker.ps1 -ManifestPath '$manifestLiteral' -LaneId $Lane -WorkerProvider $Lane -RepoRoot (Get-Location).Path -TakeOverExpiredLease

Ordinary candidate failures or ambiguity are durable results; continue processing later candidates. Stop only for a manifest/hash/assignment error, stale worker inventory, invalid existing result, active lane lease, or another systemic failure. If usage pauses, rerun the same command and resume from immutable results.

Your only persistent writes may be your lane lease and manifest-assigned candidate result artifacts. Do not integrate results, commit, push, open a PR, upload to R2, merge, or deploy.
"@
}

function Get-AssignedCandidateSet([string]$Root,[string]$IgnoreManifestPath) {
  $assigned = @{}
  if (Test-Path -LiteralPath $Root) {
    foreach ($path in @(Get-ChildItem -LiteralPath $Root -Filter campaign.json -File -Recurse -ErrorAction Stop | Select-Object -ExpandProperty FullName)) {
      if ($IgnoreManifestPath -and [IO.Path]::GetFullPath($path) -eq [IO.Path]::GetFullPath($IgnoreManifestPath)) { continue }
      $existing = Read-ParallelVerificationJson $path
      $existingErrors = @(Test-ParallelVerificationCampaignObject $existing)
      if ($existingErrors.Count) { throw "Existing campaign is invalid: $path :: $($existingErrors -join '; ')" }
      foreach ($entry in @(Get-ParallelVerificationCampaignEntries $existing)) { $assigned[[string]$entry.candidate_id] = [string]$existing.campaign_id }
    }
  }
  $assigned
}

function Get-NextCandidates($Inventory,$Predecessor,[string]$Root,[int]$RequestedCount,[string]$IgnoreManifestPath) {
  $assigned = Get-AssignedCandidateSet -Root $Root -IgnoreManifestPath $IgnoreManifestPath
  $lastId = @(Get-ParallelVerificationCampaignEntries $Predecessor | Sort-Object candidate_id | Select-Object -Last 1 -ExpandProperty candidate_id)[0]
  $available = @($Inventory.candidates |
    Where-Object { [string]$_.status -eq 'pending review' -and -not $assigned.ContainsKey([string]$_.id) } |
    Sort-Object id)
  $ordered = @(
    @($available | Where-Object { [string]$_.id -gt $lastId })
    @($available | Where-Object { [string]$_.id -le $lastId })
  )
  @($ordered | Select-Object -First $RequestedCount -ExpandProperty id)
}

$manifestFull = Resolve-ParallelVerificationCampaignManifest -ManifestPath $ManifestPath -ActiveRunPath $ActiveRunPath
$campaign = Read-ParallelVerificationJson $manifestFull
$campaignErrors = @(Test-ParallelVerificationCampaignObject $campaign)
if ($campaignErrors.Count) { throw "Campaign validation failed: $($campaignErrors -join '; ')" }
if (((Get-Item -LiteralPath $manifestFull).Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0) { throw 'Campaign manifest is not read-only.' }

$manifestDirectory = Split-Path -Parent $manifestFull
if (-not $CampaignRoot) { $CampaignRoot = Split-Path -Parent $manifestDirectory }
$campaignRootFull = [IO.Path]::GetFullPath($CampaignRoot)
if (-not $SuccessorCampaignId) { $SuccessorCampaignId = Get-SuccessorCampaignId ([string]$campaign.campaign_id) }
$successorPath = Join-Path (Join-Path $campaignRootFull $SuccessorCampaignId) 'campaign.json'

$activeFull = [IO.Path]::GetFullPath($ActiveRunPath)
$active = Read-ParallelVerificationJson $activeFull
$pointerAlreadyAdvanced = $false
if ([string]$active.type -ne 'parallel-verification-campaign') { throw 'The active-run pointer is not a parallel verification campaign.' }
if ([string]$active.campaign_id -ne [string]$campaign.campaign_id -or [string]$active.campaign_sha256 -ne [string]$campaign.campaign_sha256) {
  $advancedPath = [IO.Path]::GetFullPath([string]$active.manifest_path)
  $advanced = Read-ParallelVerificationJson $advancedPath
  $advancedErrors = @(Test-ParallelVerificationCampaignObject $advanced)
  if ($advancedErrors.Count -or [int]$advanced.schema_version -ne 2 -or [string]$advanced.campaign_id -ne [string]$active.campaign_id -or [string]$advanced.campaign_sha256 -ne [string]$active.campaign_sha256 -or [string]$advanced.predecessor_campaign_id -ne [string]$campaign.campaign_id -or [string]$advanced.predecessor_campaign_sha256 -ne [string]$campaign.campaign_sha256) { throw 'Only the coordinator may roll over the currently active campaign.' }
  $pointerAlreadyAdvanced = $true;$SuccessorCampaignId = [string]$advanced.campaign_id;$successorPath = $advancedPath
}

if (-not $InventoryPath) { $InventoryPath = [string]$campaign.inventory_path }
if (-not [IO.Path]::IsPathRooted($InventoryPath)) { $InventoryPath = Join-Path (Get-Location).Path $InventoryPath }
$inventoryFull = [IO.Path]::GetFullPath($InventoryPath)
$inventory = Read-ParallelVerificationJson $inventoryFull

$status = & "$PSScriptRoot/Get-ParallelVerificationCampaignStatus.ps1" -ManifestPath $manifestFull -InventoryPath $inventoryFull | ConvertFrom-Json -DateKind String
if (-not [bool]$status.valid) { throw "Completed campaign status is invalid: $(@($status.errors) -join '; ')" }
if ([int]$status.remaining -ne 0 -or [int]$status.verified -ne [int]$status.candidates) { throw 'The active campaign has not completed verification.' }
$unsafeLeases = @($status.lanes | Where-Object { [string]$_.lease_state -notin @('absent','released','expired') })
if ($unsafeLeases.Count) { throw "Campaign lanes are not safely released: $(@($unsafeLeases | ForEach-Object { "$($_.lane_id)=$($_.lease_state)" }) -join ', ')" }

$reviewOperations = [Collections.Generic.List[object]]::new()
foreach ($entry in @(Get-ParallelVerificationCampaignEntries $campaign)) {
  $resultPath = Join-Path $manifestDirectory ([string]$entry.result_path)
  $result = Read-ParallelVerificationJson $resultPath
  $resultErrors = @(Test-ParallelVerificationCandidateResultObject -Result $result -Campaign $campaign -Entry $entry -ResultPath $resultPath -ManifestDirectory $manifestDirectory)
  if ($resultErrors.Count) { throw "Invalid completed result for $($entry.candidate_id): $($resultErrors -join '; ')" }
  if ([string]$result.overall_status -eq 'passed') { continue }
  $failedChecks = @($result.checks.PSObject.Properties | Where-Object { [string]$_.Value.status -in @('failed','skipped') } | ForEach-Object { "$($_.Name)=$($_.Value.status)" })
  $summary = if ($failedChecks.Count) { $failedChecks -join ', ' } else { "overall_status=$($result.overall_status)" }
  $updates = [pscustomobject][ordered]@{
    status = 'requires human review'
    validation_status = "requires human review: autonomous campaign $($campaign.campaign_id) ($summary)"
    processing_notes_append = "Autonomous campaign $($campaign.campaign_id) did not pass verification ($summary); human review is required. Result SHA-256: $($result.result_sha256)."
  }
  $existingIntentPath = Join-Path $manifestDirectory "integration/intents/$($entry.candidate_id).json"
  if (Test-Path -LiteralPath $existingIntentPath) {
    $existingIntent = Read-ParallelVerificationJson $existingIntentPath
    $existingIntentErrors = @(Test-ParallelVerificationIntegrationIntentObject -Intent $existingIntent -Campaign $campaign -Entry $entry -Result $result -Path $existingIntentPath)
    if ($existingIntentErrors.Count) { throw "Existing failed-result integration intent is invalid for $($entry.candidate_id): $($existingIntentErrors -join '; ')" }
    $updates = [pscustomobject]$existingIntent.set
  }
  $operationPayload = [ordered]@{campaign_sha256=[string]$campaign.campaign_sha256;candidate_id=[string]$entry.candidate_id;result_sha256=[string]$result.result_sha256;updates=$updates}
  $operationId = Get-ParallelVerificationObjectHash $operationPayload
  $reviewOperations.Add([pscustomobject][ordered]@{
    candidate_id = [string]$entry.candidate_id
    result_sha256 = [string]$result.result_sha256
    proposed_updates = $updates
    operation_id = $operationId
    marker = "Parallel verification operation $operationId."
    decision_notes = "Deterministic coordinator escalation of a non-passing result ($summary); no publication, R2, merge, or deployment action is authorized."
  })
}

if (-not $LaneIds -or -not $LaneIds.Count) { $LaneIds = @($campaign.lanes | ForEach-Object { [string]$_ }) }
if ($MicrobatchSize -eq 0) { $MicrobatchSize = [int]$campaign.microbatch_size }
if ($Count -eq 0) { $Count = [int]$campaign.candidate_count }
$nextIds = Get-NextCandidates -Inventory $inventory -Predecessor $campaign -Root $campaignRootFull -RequestedCount $Count -IgnoreManifestPath $successorPath

if (-not $WorktreeRoot) {
  $repoForDefault = (& git rev-parse --show-toplevel).Trim();if ($LASTEXITCODE) { throw 'Unable to resolve repository root.' }
  $WorktreeRoot = Join-Path (Split-Path -Parent $repoForDefault) 'ABQinfo-campaign-workers'
}
$worktreeRootFull = [IO.Path]::GetFullPath($WorktreeRoot)
$plannedWorktrees = @($LaneIds | ForEach-Object { [pscustomobject][ordered]@{lane_id=$_;path=Join-Path (Join-Path $worktreeRootFull $SuccessorCampaignId) $_} })

if (-not $Apply) {
  [pscustomobject][ordered]@{
    mode = 'dry-run'; predecessor_campaign_id = [string]$campaign.campaign_id; predecessor_complete = $true
    review_required = $reviewOperations.Count; review_candidates = @($reviewOperations.candidate_id)
    successor_campaign_id = if ($nextIds.Count) { $SuccessorCampaignId } else { $null }
    successor_candidates = $nextIds.Count; successor_candidate_ids = @($nextIds); worktrees = $plannedWorktrees
    safeguards = @('coordinator-only active pointer','exclusive coordinator lease','exclusive inventory-writer lease','no R2','no merge','no deploy')
  } | ConvertTo-Json -Depth 10
  exit 0
}

& git symbolic-ref --quiet HEAD | Out-Null
if ($LASTEXITCODE) { throw 'Apply mode must run from the coordinator branch.' }
$repo = (& git rev-parse --show-toplevel).Trim();if ($LASTEXITCODE) { throw 'Unable to resolve repository root.' };$repo = [IO.Path]::GetFullPath($repo).TrimEnd('\','/')
if (-not $CoordinatorLeasePath) {
  $gitCommon = (& git rev-parse --git-common-dir).Trim();if (-not [IO.Path]::IsPathRooted($gitCommon)) { $gitCommon = Join-Path $repo $gitCommon }
  $CoordinatorLeasePath = Join-Path $gitCommon 'abqinfo-verification-locks/campaign-coordinator.lock'
}
$coordinatorLeaseFull = [IO.Path]::GetFullPath($CoordinatorLeasePath)
$leaseParent = Split-Path -Parent $coordinatorLeaseFull;if (-not (Test-Path -LiteralPath $leaseParent)) { New-Item -ItemType Directory -Path $leaseParent -Force | Out-Null }
$leaseStream = $null;$leaseOwned = $false;$decisionPath = $null;$coordinatorOwnerToken=[guid]::NewGuid().ToString('N')
try {
  if (Test-Path -LiteralPath $coordinatorLeaseFull) {
    try { $leaseStream = [IO.File]::Open($coordinatorLeaseFull,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read) } catch { throw "Campaign coordinator lease is active: $coordinatorLeaseFull" }
    $reader = [IO.StreamReader]::new($leaseStream,[Text.Encoding]::UTF8,$true,1024,$true);try { $priorText = $reader.ReadToEnd() } finally { $reader.Dispose() }
    $prior = $null;try { $prior = $priorText | ConvertFrom-Json -DateKind String } catch {}
    $expiresProperty = if ($prior) { $prior.PSObject.Properties['expires_at'] } else { $null }
    $releasedProperty = if ($prior) { $prior.PSObject.Properties['released_at'] } else { $null }
    $released = $releasedProperty -and -not [string]::IsNullOrWhiteSpace([string]$releasedProperty.Value)
    $expired = $expiresProperty -and [DateTimeOffset]::Parse([string]$expiresProperty.Value) -le [DateTimeOffset]::UtcNow
    if (-not $released -and (-not $expired -or -not $TakeOverExpiredLease)) { throw 'Existing campaign coordinator lease is not eligible for stale takeover.' }
  } else { $leaseStream = [IO.File]::Open($coordinatorLeaseFull,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read) }
  $leaseOwned = $true;$now = (Get-Date).ToUniversalTime();$lease = [ordered]@{campaign_id=[string]$campaign.campaign_id;owner_token=$coordinatorOwnerToken;pid=$PID;started_at=$now.ToString('o');expires_at=$now.AddMinutes($LeaseMinutes).ToString('o')};$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($lease|ConvertTo-Json -Compress));$leaseStream.Position=0;$leaseStream.SetLength(0);$leaseStream.Write($bytes,0,$bytes.Length);$leaseStream.Flush($true)

  $currentActive = Read-ParallelVerificationJson $activeFull
  $activeStillPredecessor = [string]$currentActive.campaign_id -eq [string]$campaign.campaign_id -and [string]$currentActive.campaign_sha256 -eq [string]$campaign.campaign_sha256
  $activeStillSuccessor = $pointerAlreadyAdvanced -and [string]$currentActive.campaign_id -eq $SuccessorCampaignId -and [IO.Path]::GetFullPath([string]$currentActive.manifest_path) -eq [IO.Path]::GetFullPath($successorPath)
  if (-not $activeStillPredecessor -and -not $activeStillSuccessor) { throw 'The active campaign changed after coordinator validation.' }

  $inventoryInsideRepo = $inventoryFull -eq $repo -or $inventoryFull.StartsWith("$repo\",[StringComparison]::OrdinalIgnoreCase)
  $inventoryRelative = $null
  if ($inventoryInsideRepo) {
    $inventoryRelative = [IO.Path]::GetRelativePath($repo,$inventoryFull).Replace('\','/')
    & git ls-files --error-unmatch -- $inventoryRelative | Out-Null;if ($LASTEXITCODE) { throw 'The coordinator inventory must be tracked by Git.' }
    & git diff --quiet HEAD -- $inventoryRelative
    if ($LASTEXITCODE -eq 1) {
      $baselineText = @(& git show "HEAD:$inventoryRelative") -join "`n";if ($LASTEXITCODE) { throw 'Unable to read the committed inventory baseline.' }
      $baseline = $baselineText | ConvertFrom-Json -DateKind String;$current = Read-ParallelVerificationJson $inventoryFull
      $stableTopLevel=@($baseline.PSObject.Properties|Where-Object Name -notin @('generated_at','counts','next_pending_id','candidates'))
      $currentStableNames=@($current.PSObject.Properties|Where-Object Name -notin @('generated_at','counts','next_pending_id','candidates')|ForEach-Object Name)
      if((@($stableTopLevel|ForEach-Object Name)-join "`n")-ne($currentStableNames-join "`n")){throw 'The inventory has unrelated top-level structural changes before rollover.'}
      foreach($property in $stableTopLevel){if((Get-ParallelVerificationObjectHash $property.Value)-ne(Get-ParallelVerificationObjectHash $current.($property.Name))){throw "The inventory has an unrelated top-level change before rollover: $($property.Name)"}}
      foreach($allowedStatus in @($current.allowed_statuses)){$countProperty=$current.counts.PSObject.Properties[[string]$allowedStatus];$actualCount=@($current.candidates|Where-Object status -eq $allowedStatus).Count;if(-not$countProperty -or [int]$countProperty.Value-ne$actualCount){throw "The inventory has inconsistent status counts before rollover: $allowedStatus"}}
      $baselineMap=@{};foreach($candidate in @($baseline.candidates)){$baselineMap[[string]$candidate.id]=$candidate};$currentMap=@{};foreach($candidate in @($current.candidates)){$currentMap[[string]$candidate.id]=$candidate}
      if($baselineMap.Count-ne$currentMap.Count){throw 'The inventory has non-recoverable candidate additions or removals before rollover.'}
      $reviewMap=@{};foreach($operation in $reviewOperations){$reviewMap[[string]$operation.candidate_id]=$operation}
      $changedIds=@($currentMap.Keys|Where-Object{-not$baselineMap.ContainsKey($_) -or (Get-ParallelVerificationCandidateFingerprint $currentMap[$_])-ne(Get-ParallelVerificationCandidateFingerprint $baselineMap[$_])})
      if(-not$changedIds.Count){throw 'The inventory has unrelated uncommitted top-level changes before rollover.'}
      foreach($changedId in $changedIds){
        if(-not$reviewMap.ContainsKey($changedId)){throw "The inventory has an uncommitted change outside recoverable failed-result integration: $changedId"}
        $operation=$reviewMap[$changedId];$candidate=$currentMap[$changedId];$intentPath=Join-Path $manifestDirectory "integration/intents/$changedId.json"
        if(-not(Test-Path -LiteralPath $intentPath)){throw "Recoverable inventory integration is missing its write-ahead intent: $changedId"}
        $intent=Read-ParallelVerificationJson $intentPath
        if([string]$intent.operation_id-ne[string]$operation.operation_id -or [string]$intent.intent_sha256-ne(Get-ParallelVerificationObjectHash (Get-ParallelVerificationIntegrationIntentPayload $intent))){throw "Recoverable inventory integration has an invalid intent: $changedId"}
        foreach($property in @($operation.proposed_updates.PSObject.Properties|Where-Object Name -ne 'processing_notes_append')){if(($candidate.($property.Name)|ConvertTo-Json -Compress -Depth 10)-ne($property.Value|ConvertTo-Json -Compress -Depth 10)){throw "Recoverable inventory integration does not match its intent: $changedId"}}
        if([string]$operation.proposed_updates.processing_notes_append -notin @($candidate.processing_notes) -or [string]$operation.marker -notin @($candidate.processing_notes)){throw "Recoverable inventory integration notes are incomplete: $changedId"}
        $receiptPath=Join-Path $manifestDirectory "integration/receipts/$changedId.json"
        if(Test-Path -LiteralPath $receiptPath){$receipt=Read-ParallelVerificationJson $receiptPath;if([string]$receipt.operation_id-ne[string]$operation.operation_id -or [string]$receipt.after_fingerprint_sha256-ne(Get-ParallelVerificationCandidateFingerprint $candidate)){throw "Recoverable inventory integration has an invalid receipt: $changedId"}}
      }
    } elseif ($LASTEXITCODE -ne 0) { throw 'Unable to verify the coordinator inventory state.' }
  }

  if ($reviewOperations.Count) {
    $decisionPath = Join-Path ([IO.Path]::GetTempPath()) ("abqinfo-campaign-decision-$PID-$([guid]::NewGuid().ToString('N')).json")
    $decision = [ordered]@{campaign_id=[string]$campaign.campaign_id;campaign_sha256=[string]$campaign.campaign_sha256;decisions=@($reviewOperations | ForEach-Object { [ordered]@{candidate_id=$_.candidate_id;accepted=$true;proposed_updates=$_.proposed_updates;decision_notes=$_.decision_notes} })}
    [IO.File]::WriteAllText($decisionPath,($decision|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
    $mergeArguments = @{ManifestPath=$manifestFull;InventoryPath=$inventoryFull;AcceptedCandidateIds=@($reviewOperations.candidate_id);DecisionPath=$decisionPath;Apply=$true;TakeOverExpiredLease=$TakeOverExpiredLease;CoordinatorLeasePath=$coordinatorLeaseFull;CoordinatorOwnerToken=$coordinatorOwnerToken}
    if ($InventoryWriterLeasePath) { $mergeArguments.LeasePath = $InventoryWriterLeasePath }
    & "$PSScriptRoot/Merge-ParallelVerificationCampaign.ps1" @mergeArguments | Out-Null
  }
  if ($TestInterruptAt -eq 'after-integration') { throw 'Test interruption after failed-result integration.' }

  if ($inventoryInsideRepo) {
    & git diff --quiet HEAD -- $inventoryRelative
    if ($LASTEXITCODE -eq 1) {
      & git commit --only -m "Escalate $($campaign.campaign_id) verification failures" -- $inventoryRelative | Out-Null
      if ($LASTEXITCODE) { throw 'Unable to commit the coordinator-owned inventory transition.' }
    } elseif ($LASTEXITCODE -ne 0) { throw 'Unable to inspect the post-integration inventory.' }
  }
  if ($TestInterruptAt -eq 'after-inventory-commit') { throw 'Test interruption after inventory commit.' }

  $baseCommit = (& git rev-parse 'HEAD^{commit}').Trim();if ($LASTEXITCODE) { throw 'Unable to resolve the successor base commit.' }
  $inventory = Read-ParallelVerificationJson $inventoryFull
  $successor = $null
  if (Test-Path -LiteralPath $successorPath) {
    $successor = Read-ParallelVerificationJson $successorPath;$successorErrors=@(Test-ParallelVerificationCampaignObject $successor)
    if ($successorErrors.Count -or [int]$successor.schema_version -ne 2 -or [string]$successor.predecessor_campaign_id -ne [string]$campaign.campaign_id -or [string]$successor.predecessor_campaign_sha256 -ne [string]$campaign.campaign_sha256) { throw 'Existing successor manifest is invalid or belongs to a different transition.' }
    $currentInventoryHash=Get-ParallelVerificationFileHash $inventoryFull
    if ([string]$successor.base_commit -ne $baseCommit -or [string]$successor.inventory_sha256 -ne $currentInventoryHash) { throw "Existing successor manifest does not match the committed inventory transition (base $($successor.base_commit) vs $baseCommit; inventory $($successor.inventory_sha256) vs $currentInventoryHash)." }
    $nextIds = @(Get-ParallelVerificationCampaignEntries $successor | Sort-Object batch_ordinal,candidate_ordinal | ForEach-Object { [string]$_.candidate_id })
  } else {
    $nextIds = Get-NextCandidates -Inventory $inventory -Predecessor $campaign -Root $campaignRootFull -RequestedCount $Count -IgnoreManifestPath $null
    if (-not $nextIds.Count) {
      [pscustomobject][ordered]@{mode='applied';predecessor_campaign_id=[string]$campaign.campaign_id;review_required=$reviewOperations.Count;successor_created=$false;reason='No later non-overlapping pending-review candidates remain.';safeguards=@('no R2','no merge','no deploy')} | ConvertTo-Json -Depth 8
      exit 0
    }
    $created = & "$PSScriptRoot/New-ParallelVerificationCampaign.ps1" -CampaignId $SuccessorCampaignId -LaneIds $LaneIds -CandidateIds $nextIds -MicrobatchSize $MicrobatchSize -InventoryPath $inventoryFull -CampaignRoot $campaignRootFull -BaseCommit $baseCommit -PredecessorManifestPath $manifestFull -CoordinatorLeasePath $coordinatorLeaseFull -CoordinatorOwnerToken $coordinatorOwnerToken | ConvertFrom-Json -DateKind String
    $successorPath = [string]$created.manifest_path;$successor = Read-ParallelVerificationJson $successorPath
  }
  if ($TestInterruptAt -eq 'after-successor') { throw 'Test interruption after successor creation.' }

  $worktreePlan = & "$PSScriptRoot/Initialize-ParallelVerificationCampaignWorktrees.ps1" -ManifestPath $successorPath -WorktreeRoot $worktreeRootFull -PlanOnly:$WorktreePlanOnly -ResumeExisting | ConvertFrom-Json -DateKind String
  if ($TestInterruptAt -eq 'after-worktrees') { throw 'Test interruption after worktree provisioning.' }

  if(-not$pointerAlreadyAdvanced){& "$PSScriptRoot/Set-ActiveParallelVerificationCampaign.ps1" -ManifestPath $successorPath -ActiveRunPath $activeFull -Replace -CoordinatorLeasePath $coordinatorLeaseFull -CoordinatorOwnerToken $coordinatorOwnerToken | Out-Null}
  if ($TestInterruptAt -eq 'after-pointer') { throw 'Test interruption after active-pointer replacement.' }

  $prompts = @($worktreePlan.worktrees | ForEach-Object { [pscustomobject][ordered]@{lane_id=[string]$_.lane_id;worktree_path=[string]$_.path;prompt=Get-CampaignWorkerPrompt -Lane ([string]$_.lane_id) -Worktree ([string]$_.path) -Manifest $successorPath -Pointer $activeFull} })
  [pscustomobject][ordered]@{
    mode='applied';predecessor_campaign_id=[string]$campaign.campaign_id;review_required=$reviewOperations.Count;review_candidates=@($reviewOperations.candidate_id)
    successor_created=$true;successor_campaign_id=[string]$successor.campaign_id;successor_manifest=$successorPath;successor_campaign_sha256=[string]$successor.campaign_sha256
    successor_candidates=$nextIds.Count;active_run_path=$activeFull;worktree_plan_only=[bool]$WorktreePlanOnly;worktrees=@($worktreePlan.worktrees);worker_prompts=$prompts
    safeguards=@('coordinator-only active pointer','exclusive coordinator lease','exclusive inventory-writer lease','no R2','no merge','no deploy')
  } | ConvertTo-Json -Depth 12
} finally {
  if ($decisionPath -and (Test-Path -LiteralPath $decisionPath)) { Remove-Item -LiteralPath $decisionPath -Force }
  if ($leaseOwned -and $leaseStream) {
    $releasedAt = (Get-Date).ToUniversalTime().ToString('o')
    $releasedLease = [ordered]@{campaign_id=[string]$campaign.campaign_id;owner_token=$coordinatorOwnerToken;pid=$PID;started_at=$lease.started_at;expires_at=$releasedAt;released_at=$releasedAt}
    $releasedBytes = [Text.UTF8Encoding]::new($false).GetBytes(($releasedLease | ConvertTo-Json -Compress))
    $leaseStream.Position=0;$leaseStream.SetLength(0);$leaseStream.Write($releasedBytes,0,$releasedBytes.Length);$leaseStream.Flush($true)
  }
  if ($leaseStream) { $leaseStream.Dispose() }
}
