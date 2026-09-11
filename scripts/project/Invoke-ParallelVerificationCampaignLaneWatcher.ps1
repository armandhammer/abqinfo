[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$LaneId,
  [string]$WorkerProvider,
  [string]$ActiveRunPath = 'project-state/active-run.json',
  [string]$WorktreeRoot,
  [string]$WatcherRoot,
  [ValidateRange(1,24)][double]$DurationHours = 9,
  [ValidateRange(5,300)][int]$PollSeconds = 20,
  [ValidateRange(1,20)][int]$WorkerSliceSize = 5,
  [ValidateRange(1,1000)][int]$MaxCandidatesPerLane = 120,
  [switch]$TakeOverExpiredLease,
  [ValidateRange(1,300)][int]$LinkTimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$LaneId = $LaneId.Trim().ToLowerInvariant()
if (-not $LaneId) { throw 'LaneId is required.' }
if (-not $WorkerProvider) { $WorkerProvider = "$LaneId-watcher" }
$repo = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE) { throw 'Unable to resolve repository root.' }
$repo = [IO.Path]::GetFullPath($repo).TrimEnd('\','/')
$activeFull = if ([IO.Path]::IsPathRooted($ActiveRunPath)) { [IO.Path]::GetFullPath($ActiveRunPath) } else { [IO.Path]::GetFullPath((Join-Path $repo $ActiveRunPath)) }
if (-not $WorktreeRoot) { $WorktreeRoot = Join-Path (Split-Path -Parent $repo) 'ABQinfo-campaign-workers' }
if (-not $WatcherRoot) { $WatcherRoot = Join-Path (Split-Path -Parent $repo) 'ABQinfo-verification-supervisor/watchers' }
$worktreeRootFull = [IO.Path]::GetFullPath($WorktreeRoot)
$watcherRootFull = [IO.Path]::GetFullPath($WatcherRoot)
New-Item -ItemType Directory -Path $watcherRootFull -Force | Out-Null
$watcherId = "$LaneId-" + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$eventPath = Join-Path $watcherRootFull "$watcherId.ndjson"
$statusPath = Join-Path $watcherRootFull "$watcherId.status.json"
$latestPath = Join-Path $watcherRootFull "$LaneId-latest.json"
$leasePath = Join-Path $watcherRootFull "$LaneId-watcher.lock"
$leaseStream = $null
$startedAt = [DateTimeOffset]::UtcNow
$deadline = $startedAt.AddHours($DurationHours)
$state = 'starting';$lastAction='initializing';$lastError=$null;$currentCampaign=$null;$campaignsObserved=0;$exitCode=0

function Write-WatcherJsonAtomic([object]$Value,[string]$Path) {
  $temporary = Join-Path (Split-Path -Parent $Path) ('.' + [IO.Path]::GetFileName($Path) + '.' + [guid]::NewGuid().ToString('N') + '.tmp')
  try { [IO.File]::WriteAllText($temporary,($Value|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $temporary -Destination $Path -Force }
  finally { if(Test-Path -LiteralPath $temporary){Remove-Item -LiteralPath $temporary -Force} }
}
function Write-WatcherEvent([string]$Event,[object]$Data){$record=[ordered]@{recorded_at=[DateTimeOffset]::UtcNow.ToString('o');event=$Event;data=$Data};[IO.File]::AppendAllText($eventPath,(($record|ConvertTo-Json -Depth 10 -Compress)+[Environment]::NewLine),[Text.UTF8Encoding]::new($false))}
function Save-WatcherStatus{$payload=[ordered]@{schema_version=1;watcher_id=$watcherId;pid=$PID;state=$state;lane_id=$LaneId;worker_provider=$WorkerProvider;started_at=$startedAt.ToString('o');deadline_at=$deadline.ToString('o');heartbeat_at=[DateTimeOffset]::UtcNow.ToString('o');active_campaign_id=$currentCampaign;campaigns_observed=$campaignsObserved;last_action=$lastAction;last_error=$lastError;event_log=$eventPath;safeguards=@('assigned lane results only','no inventory or project-state writes','no Git changes','no R2','no merge','no deploy','no content or editorial changes')};Write-WatcherJsonAtomic $payload $statusPath;Write-WatcherJsonAtomic ([ordered]@{watcher_id=$watcherId;pid=$PID;state=$state;status_path=$statusPath;event_log=$eventPath;heartbeat_at=[DateTimeOffset]::UtcNow.ToString('o')}) $latestPath}
function Convert-WatcherJson([object[]]$Lines,[string]$Operation){$text=(@($Lines)-join[Environment]::NewLine).Trim();if(-not$text){throw "$Operation returned no JSON."};try{$text|ConvertFrom-Json -DateKind String}catch{throw "$Operation returned invalid JSON: $($_.Exception.Message)"}}

try {
  try{$leaseStream=[IO.File]::Open($leasePath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)}catch{throw "Another watcher owns lane ${LaneId}: $leasePath"}
  $bytes=[Text.UTF8Encoding]::new($false).GetBytes(([ordered]@{schema_version=1;watcher_id=$watcherId;pid=$PID;started_at=$startedAt.ToString('o');deadline_at=$deadline.ToString('o');state='active'}|ConvertTo-Json -Compress));$leaseStream.SetLength(0);$leaseStream.Write($bytes,0,$bytes.Length);$leaseStream.Flush($true)
  $state='running';$lastAction='watcher lease acquired';Save-WatcherStatus;Write-WatcherEvent 'watcher-started' ([ordered]@{lane_id=$LaneId;deadline_at=$deadline.ToString('o')})
  while([DateTimeOffset]::UtcNow -lt $deadline){
    if(-not(Test-Path -LiteralPath $activeFull -PathType Leaf)){throw "Active campaign pointer is missing: $activeFull"}
    $pointer=Get-Content -LiteralPath $activeFull -Raw|ConvertFrom-Json -DateKind String
    if([string]$pointer.type-ne'parallel-verification-campaign'){throw 'The active-run pointer is not a parallel verification campaign.'}
    $statusLines=@(& "$repo/scripts/project/Get-ParallelVerificationCampaignStatus.ps1" -ManifestPath ([string]$pointer.manifest_path));if($LASTEXITCODE){throw 'Campaign status command failed.'};$status=Convert-WatcherJson $statusLines 'Campaign status'
    if(-not[bool]$status.valid){throw "Campaign status is invalid: $(@($status.errors)-join'; ')"}
    if($currentCampaign-ne[string]$status.campaign_id){$currentCampaign=[string]$status.campaign_id;$campaignsObserved++;Write-WatcherEvent 'campaign-observed' ([ordered]@{campaign_id=$currentCampaign})}
    $lane=@($status.lanes|Where-Object{[string]$_.lane_id-eq$LaneId});if($lane.Count-ne1){throw "Lane $LaneId is not assigned exactly once in campaign $currentCampaign."};$laneStatus=$lane[0]
    if([int]$laneStatus.assigned-gt$MaxCandidatesPerLane){throw "Lane $LaneId exceeds the bounded $MaxCandidatesPerLane-candidate limit."}
    if([int]$laneStatus.invalid_or_stale-gt0){throw "Lane $LaneId has invalid or stale results."}
    if([int]$laneStatus.remaining-gt0 -and [string]$laneStatus.lease_state-in@('absent','released','expired')){
      $worktree=Join-Path (Join-Path $worktreeRootFull $currentCampaign) $LaneId;if(-not(Test-Path -LiteralPath $worktree -PathType Container)){throw "Lane worktree is missing: $worktree"}
      $lastAction="processing $LaneId lane slice";Save-WatcherStatus;Write-WatcherEvent 'lane-slice-started' ([ordered]@{campaign_id=$currentCampaign;remaining=[int]$laneStatus.remaining})
      Push-Location $worktree
      try{$workerLines=@(& "$worktree/scripts/project/Invoke-ParallelVerificationCampaignWorker.ps1" -ManifestPath ([string]$pointer.manifest_path) -LaneId $LaneId -WorkerProvider $WorkerProvider -RepoRoot $worktree -TakeOverExpiredLease:$TakeOverExpiredLease -MaxCandidates $WorkerSliceSize -LinkTimeoutSeconds $LinkTimeoutSeconds);if($LASTEXITCODE){throw "Worker command failed for lane $LaneId."}}
      finally{Pop-Location}
      $workerResult=Convert-WatcherJson $workerLines 'Campaign worker';Write-WatcherEvent 'lane-slice-completed' $workerResult;$lastAction="completed $LaneId lane slice";Save-WatcherStatus
      continue
    }
    if([int]$laneStatus.remaining-eq0){
      $supervisorLatestPath=Join-Path (Split-Path -Parent $watcherRootFull) 'latest.json'
      if(Test-Path -LiteralPath $supervisorLatestPath -PathType Leaf){
        $supervisorLatest=Get-Content -LiteralPath $supervisorLatestPath -Raw|ConvertFrom-Json -DateKind String
        if([string]$supervisorLatest.state-eq'complete-queue-exhausted'){$state='complete-queue-exhausted';$lastAction='coordinator reported no successor candidates';Save-WatcherStatus;break}
      }
      $lastAction="waiting for successor after completing $LaneId lane"
    }else{$lastAction="waiting for $LaneId lease ($($laneStatus.lease_state))"};Save-WatcherStatus
    $remainingSeconds=[Math]::Floor(($deadline-[DateTimeOffset]::UtcNow).TotalSeconds);if($remainingSeconds-le0){break};Start-Sleep -Seconds ([Math]::Min($PollSeconds,$remainingSeconds))
  }
  if($state-eq'running'){$state='stopped-deadline';$lastAction='watch window elapsed';Save-WatcherStatus}
} catch {
  $exitCode=1;$state='faulted-systemic';$lastError=$_.Exception.Message;$lastAction='stopped on systemic fault';try{Save-WatcherStatus;Write-WatcherEvent 'systemic-fault' ([ordered]@{message=$lastError;script_stack=$_.ScriptStackTrace})}catch{}
} finally {
  if($leaseStream){try{$released=[Text.UTF8Encoding]::new($false).GetBytes(([ordered]@{schema_version=1;watcher_id=$watcherId;pid=$PID;state=$state;released_at=[DateTimeOffset]::UtcNow.ToString('o')}|ConvertTo-Json -Compress));$leaseStream.Position=0;$leaseStream.SetLength(0);$leaseStream.Write($released,0,$released.Length);$leaseStream.Flush($true)}catch{};$leaseStream.Dispose()}
}
[pscustomobject][ordered]@{watcher_id=$watcherId;pid=$PID;state=$state;status_path=$statusPath;event_log=$eventPath;last_error=$lastError}|ConvertTo-Json -Depth 5
exit $exitCode
