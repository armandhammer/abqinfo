[CmdletBinding()]
param(
  [string]$ActiveRunPath = 'project-state/active-run.json',
  [string]$CampaignRoot,
  [string]$WorktreeRoot,
  [string]$SupervisorRoot,
  [string[]]$ManagedLaneIds = @('codex'),
  [ValidateRange(1,24)][double]$DurationHours = 9,
  [ValidateRange(5,300)][int]$PollSeconds = 20,
  [ValidateRange(1,20)][int]$WorkerSliceSize = 5,
  [ValidateRange(1,1000)][int]$SuccessorCandidateCount = 240,
  [ValidateRange(1,1000)][int]$MaxCandidatesPerLane = 120,
  [switch]$TakeOverExpiredLease,
  [ValidateRange(1,300)][int]$LinkTimeoutSeconds = 30,
  [Parameter(DontShow)][ValidateRange(0,100000)][int]$MaxCycles = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-SupervisorJsonAtomic([object]$Value,[string]$Path) {
  $parent = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
  $temporary = Join-Path $parent ('.' + [IO.Path]::GetFileName($Path) + '.' + [guid]::NewGuid().ToString('N') + '.tmp')
  try {
    [IO.File]::WriteAllText($temporary, ($Value | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporary -Destination $Path -Force
  } finally {
    if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
  }
}

function Write-SupervisorEvent([string]$Event,[object]$Data) {
  $record = [ordered]@{ recorded_at=(Get-Date).ToUniversalTime().ToString('o'); event=$Event; data=$Data }
  [IO.File]::AppendAllText($script:EventLogPath, (($record | ConvertTo-Json -Depth 12 -Compress) + [Environment]::NewLine), [Text.UTF8Encoding]::new($false))
}

function ConvertFrom-SupervisorCommandJson([object[]]$Lines,[string]$Operation) {
  $text = (@($Lines) -join [Environment]::NewLine).Trim()
  if (-not $text) { throw "$Operation returned no JSON." }
  try { $text | ConvertFrom-Json -DateKind String } catch { throw "$Operation returned invalid JSON: $($_.Exception.Message)" }
}

function Get-SupervisorActivePointer([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Active campaign pointer is missing: $Path" }
  $pointer = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -DateKind String
  if ([string]$pointer.type -ne 'parallel-verification-campaign') { throw 'The active-run pointer is not a parallel verification campaign.' }
  if (-not [IO.Path]::IsPathRooted([string]$pointer.manifest_path)) { throw 'The active campaign manifest path is not absolute.' }
  $pointer
}

function Get-SupervisorCampaignStatus([string]$ManifestPath) {
  $lines = @(& "$PSScriptRoot/Get-ParallelVerificationCampaignStatus.ps1" -ManifestPath $ManifestPath)
  if ($LASTEXITCODE) { throw "Campaign status command failed for $ManifestPath." }
  $status = ConvertFrom-SupervisorCommandJson $lines 'Campaign status'
  if (-not [bool]$status.valid) { throw "Campaign status is invalid: $(@($status.errors) -join '; ')" }
  $status
}

function Test-SupervisorSafeLease([string]$State) {
  [string]$State -in @('absent','released','expired')
}

$repo = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE) { throw 'Unable to resolve repository root.' }
$repo = [IO.Path]::GetFullPath($repo).TrimEnd('\','/')
& git symbolic-ref --quiet HEAD | Out-Null
if ($LASTEXITCODE) { throw 'The verification supervisor must run from the attached coordinator branch.' }

$activeFull = if ([IO.Path]::IsPathRooted($ActiveRunPath)) { [IO.Path]::GetFullPath($ActiveRunPath) } else { [IO.Path]::GetFullPath((Join-Path $repo $ActiveRunPath)) }
if (-not $CampaignRoot) { $CampaignRoot = Join-Path (Split-Path -Parent $repo) 'ABQinfo-verification-campaigns' }
if (-not $WorktreeRoot) { $WorktreeRoot = Join-Path (Split-Path -Parent $repo) 'ABQinfo-campaign-workers' }
if (-not $SupervisorRoot) { $SupervisorRoot = Join-Path (Split-Path -Parent $repo) 'ABQinfo-verification-supervisor' }
$campaignRootFull = [IO.Path]::GetFullPath($CampaignRoot)
$worktreeRootFull = [IO.Path]::GetFullPath($WorktreeRoot)
$supervisorRootFull = [IO.Path]::GetFullPath($SupervisorRoot)

$ManagedLaneIds = @($ManagedLaneIds | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ } | Select-Object -Unique)
if (-not $ManagedLaneIds.Count) { throw 'At least one managed lane is required.' }
if ($SuccessorCandidateCount -gt ($MaxCandidatesPerLane * 2)) { throw 'SuccessorCandidateCount exceeds the two-lane bounded campaign capacity.' }

$runId = 'supervisor-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$runRoot = Join-Path (Join-Path $supervisorRootFull 'runs') $runId
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
$script:EventLogPath = Join-Path $runRoot 'events.ndjson'
$statusPath = Join-Path $runRoot 'status.json'
$latestPath = Join-Path $supervisorRootFull 'latest.json'
$leasePath = Join-Path $supervisorRootFull 'supervisor.lock'
$leaseParent = Split-Path -Parent $leasePath
if (-not (Test-Path -LiteralPath $leaseParent)) { New-Item -ItemType Directory -Path $leaseParent -Force | Out-Null }

$leaseStream = $null
$startedAt = [DateTimeOffset]::UtcNow
$deadline = $startedAt.AddHours($DurationHours)
$state = 'starting'
$lastAction = 'initializing'
$lastError = $null
$campaignsCompleted = 0
$currentStatus = $null
$exitCode = 0

function Save-SupervisorStatus {
  $payload = [ordered]@{
    schema_version=1; run_id=$runId; pid=$PID; state=$state
    started_at=$startedAt.ToString('o'); deadline_at=$deadline.ToString('o'); heartbeat_at=[DateTimeOffset]::UtcNow.ToString('o')
    repo_root=$repo; active_run_path=$activeFull; campaign_root=$campaignRootFull; worktree_root=$worktreeRootFull
    managed_lanes=@($ManagedLaneIds); max_candidates_per_lane=$MaxCandidatesPerLane; successor_candidate_count=$SuccessorCandidateCount
    campaigns_completed=$campaignsCompleted; active_campaign_id=if($currentStatus){[string]$currentStatus.campaign_id}else{$null}
    active_campaign=if($currentStatus){[ordered]@{candidates=[int]$currentStatus.candidates;verified=[int]$currentStatus.verified;passed=[int]$currentStatus.passed;failed=[int]$currentStatus.failed;incomplete=[int]$currentStatus.incomplete;remaining=[int]$currentStatus.remaining;lanes=@($currentStatus.lanes)}}else{$null}
    last_action=$lastAction; last_error=$lastError
    event_log=$script:EventLogPath
    safeguards=@('verification only','non-passing only to requires human review','no R2','no merge','no deploy','no content or editorial changes')
  }
  Write-SupervisorJsonAtomic $payload $statusPath
  Write-SupervisorJsonAtomic ([ordered]@{run_id=$runId;pid=$PID;state=$state;status_path=$statusPath;event_log=$script:EventLogPath;heartbeat_at=[DateTimeOffset]::UtcNow.ToString('o')}) $latestPath
}

try {
  try { $leaseStream = [IO.File]::Open($leasePath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read) } catch { throw "Another verification supervisor owns the exclusive lease: $leasePath" }
  $lease = [ordered]@{schema_version=1;run_id=$runId;pid=$PID;started_at=$startedAt.ToString('o');deadline_at=$deadline.ToString('o');state='active'}
  $leaseBytes = [Text.UTF8Encoding]::new($false).GetBytes(($lease | ConvertTo-Json -Compress))
  $leaseStream.SetLength(0);$leaseStream.Write($leaseBytes,0,$leaseBytes.Length);$leaseStream.Flush($true)
  $state = 'running';$lastAction = 'supervisor lease acquired';Save-SupervisorStatus
  Write-SupervisorEvent 'supervisor-started' ([ordered]@{pid=$PID;deadline_at=$deadline.ToString('o');managed_lanes=@($ManagedLaneIds)})

  while ([DateTimeOffset]::UtcNow -lt $deadline) {
    $pointer = Get-SupervisorActivePointer $activeFull
    $currentStatus = Get-SupervisorCampaignStatus ([string]$pointer.manifest_path)
    if ([int]$currentStatus.candidates -gt $SuccessorCandidateCount) { throw "Active campaign exceeds the bounded candidate limit: $($currentStatus.candidates)." }
    foreach ($laneStatus in @($currentStatus.lanes)) {
      if ([int]$laneStatus.assigned -gt $MaxCandidatesPerLane) { throw "Lane $($laneStatus.lane_id) exceeds the bounded $MaxCandidatesPerLane-candidate limit." }
    }
    foreach ($managedLane in $ManagedLaneIds) {
      if ($managedLane -notin @($currentStatus.lanes | ForEach-Object { [string]$_.lane_id })) { throw "Managed lane is absent from active campaign: $managedLane" }
    }
    $lastAction = 'validated active campaign';Save-SupervisorStatus

    foreach ($managedLane in $ManagedLaneIds) {
      if ([DateTimeOffset]::UtcNow -ge $deadline) { break }
      $laneStatus = @($currentStatus.lanes | Where-Object { [string]$_.lane_id -eq $managedLane })[0]
      if ([int]$laneStatus.invalid_or_stale -gt 0) { throw "Lane $managedLane has invalid or stale assigned results." }
      if ([int]$laneStatus.remaining -eq 0) { continue }
      if (-not (Test-SupervisorSafeLease ([string]$laneStatus.lease_state))) {
        $lastAction = "waiting for lane $managedLane lease ($($laneStatus.lease_state))";Save-SupervisorStatus
        continue
      }
      $worktree = Join-Path (Join-Path $worktreeRootFull ([string]$currentStatus.campaign_id)) $managedLane
      if (-not (Test-Path -LiteralPath $worktree -PathType Container)) { throw "Managed lane worktree is missing: $worktree" }
      $lastAction = "processing $managedLane lane slice";Save-SupervisorStatus
      Write-SupervisorEvent 'lane-slice-started' ([ordered]@{campaign_id=[string]$currentStatus.campaign_id;lane_id=$managedLane;remaining=[int]$laneStatus.remaining})
      Push-Location $worktree
      try {
        $workerLines = @(& "$worktree/scripts/project/Invoke-ParallelVerificationCampaignWorker.ps1" -ManifestPath ([string]$pointer.manifest_path) -LaneId $managedLane -WorkerProvider "supervisor-$managedLane" -RepoRoot $worktree -TakeOverExpiredLease:$TakeOverExpiredLease -MaxCandidates $WorkerSliceSize -LinkTimeoutSeconds $LinkTimeoutSeconds)
        if ($LASTEXITCODE) { throw "Worker command failed for $managedLane lane." }
      } finally { Pop-Location }
      $workerResult = ConvertFrom-SupervisorCommandJson $workerLines "Worker $managedLane"
      Write-SupervisorEvent 'lane-slice-completed' $workerResult
      $currentStatus = Get-SupervisorCampaignStatus ([string]$pointer.manifest_path)
      $lastAction = "completed $managedLane lane slice";Save-SupervisorStatus
    }

    $currentStatus = Get-SupervisorCampaignStatus ([string]$pointer.manifest_path)
    if ([int]$currentStatus.remaining -eq 0) {
      $unsafe = @($currentStatus.lanes | Where-Object { -not (Test-SupervisorSafeLease ([string]$_.lease_state)) })
      if ($unsafe.Count) {
        $lastAction = 'waiting for completed campaign leases to release';Save-SupervisorStatus
      } else {
        $lastAction = 'coordinating completed campaign';Save-SupervisorStatus
        Write-SupervisorEvent 'rollover-started' ([ordered]@{campaign_id=[string]$currentStatus.campaign_id;passed=[int]$currentStatus.passed;non_passing=([int]$currentStatus.failed+[int]$currentStatus.incomplete)})
        $coordinatorLines = @(& "$PSScriptRoot/Invoke-ParallelVerificationCampaignCoordinator.ps1" -ManifestPath ([string]$pointer.manifest_path) -ActiveRunPath $activeFull -CampaignRoot $campaignRootFull -WorktreeRoot $worktreeRootFull -Count $SuccessorCandidateCount -Apply -TakeOverExpiredLease:$TakeOverExpiredLease)
        if ($LASTEXITCODE) { throw "Campaign coordinator failed for $($currentStatus.campaign_id)." }
        $rollover = ConvertFrom-SupervisorCommandJson $coordinatorLines 'Campaign coordinator'
        Write-SupervisorEvent 'rollover-completed' $rollover
        $campaignsCompleted++
        if (-not [bool]$rollover.successor_created) {
          $state = 'complete-queue-exhausted';$lastAction = [string]$rollover.reason;Save-SupervisorStatus
          break
        }
        $lastAction = "activated successor $($rollover.successor_campaign_id)";Save-SupervisorStatus
        if ($MaxCycles -gt 0 -and $campaignsCompleted -ge $MaxCycles) { $state='stopped-cycle-limit';break }
        continue
      }
    }

    foreach ($externalLane in @($currentStatus.lanes | Where-Object { [string]$_.lane_id -notin $ManagedLaneIds })) {
      $watcherLatestPath = Join-Path (Join-Path $supervisorRootFull 'watchers') "$($externalLane.lane_id)-latest.json"
      if (Test-Path -LiteralPath $watcherLatestPath -PathType Leaf) {
        $watcherLatest = Get-Content -LiteralPath $watcherLatestPath -Raw | ConvertFrom-Json -DateKind String
        if ([string]$watcherLatest.state -eq 'faulted-systemic') {
          $watcherStatus = Get-Content -LiteralPath ([string]$watcherLatest.status_path) -Raw | ConvertFrom-Json -DateKind String
          throw "External lane watcher $($externalLane.lane_id) faulted: $($watcherStatus.last_error)"
        }
      }
    }

    $remainingSeconds = [Math]::Floor(($deadline - [DateTimeOffset]::UtcNow).TotalSeconds)
    if ($remainingSeconds -le 0) { break }
    Start-Sleep -Seconds ([Math]::Min($PollSeconds,$remainingSeconds))
  }
  if ($state -eq 'running') { $state = 'stopped-deadline';$lastAction = 'nine-hour supervision window elapsed';Save-SupervisorStatus }
} catch {
  $exitCode = 1;$state = 'faulted-systemic';$lastError = $_.Exception.Message;$lastAction = 'stopped on systemic fault'
  try { Save-SupervisorStatus;Write-SupervisorEvent 'systemic-fault' ([ordered]@{message=$lastError;script_stack=$_.ScriptStackTrace}) } catch {}
} finally {
  if ($leaseStream) {
    try {
      $released = [ordered]@{schema_version=1;run_id=$runId;pid=$PID;started_at=$startedAt.ToString('o');deadline_at=$deadline.ToString('o');state=$state;released_at=[DateTimeOffset]::UtcNow.ToString('o')}
      $releasedBytes = [Text.UTF8Encoding]::new($false).GetBytes(($released | ConvertTo-Json -Compress))
      $leaseStream.Position=0;$leaseStream.SetLength(0);$leaseStream.Write($releasedBytes,0,$releasedBytes.Length);$leaseStream.Flush($true)
    } catch {}
    $leaseStream.Dispose()
  }
}

[pscustomobject][ordered]@{run_id=$runId;pid=$PID;state=$state;status_path=$statusPath;event_log=$script:EventLogPath;campaigns_completed=$campaignsCompleted;last_error=$lastError} | ConvertTo-Json -Depth 6
exit $exitCode
