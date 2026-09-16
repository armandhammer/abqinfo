[CmdletBinding()]
param(
  [string]$ActiveRunPath = 'project-state/active-run.json',
  [string]$CampaignRoot,
  [string]$WorktreeRoot,
  [string]$SupervisorRoot,
  [string[]]$ManagedLaneIds = @('codex','claude'),
  [ValidateRange(1,24)][double]$DurationHours = 9,
  [ValidateRange(5,300)][int]$PollSeconds = 20,
  [ValidateRange(1,20)][int]$WorkerSliceSize = 5,
  [ValidateRange(1,1000)][int]$SuccessorCandidateCount = 240,
  [ValidateRange(1,1000)][int]$MaxCandidatesPerLane = 120,
  [switch]$TakeOverExpiredLease,
  [ValidateRange(1,300)][int]$LinkTimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repo = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE) { throw 'Unable to resolve repository root.' }
$repo = [IO.Path]::GetFullPath($repo).TrimEnd('\','/')
if (-not $SupervisorRoot) { $SupervisorRoot = Join-Path (Split-Path -Parent $repo) 'ABQinfo-verification-supervisor' }
$supervisorRootFull = [IO.Path]::GetFullPath($SupervisorRoot)
New-Item -ItemType Directory -Path $supervisorRootFull -Force | Out-Null
$launchId = 'launch-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$stdoutPath = Join-Path $supervisorRootFull "$launchId.stdout.log"
$stderrPath = Join-Path $supervisorRootFull "$launchId.stderr.log"
$scriptPath = Join-Path $PSScriptRoot 'Invoke-ParallelVerificationCampaignSupervisor.ps1'
$arguments = @('-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$scriptPath,'-ActiveRunPath',$ActiveRunPath,'-DurationHours',[string]$DurationHours,'-PollSeconds',[string]$PollSeconds,'-WorkerSliceSize',[string]$WorkerSliceSize,'-SuccessorCandidateCount',[string]$SuccessorCandidateCount,'-MaxCandidatesPerLane',[string]$MaxCandidatesPerLane,'-LinkTimeoutSeconds',[string]$LinkTimeoutSeconds)
if ($CampaignRoot) { $arguments += @('-CampaignRoot',$CampaignRoot) }
if ($WorktreeRoot) { $arguments += @('-WorktreeRoot',$WorktreeRoot) }
$arguments += @('-SupervisorRoot',$supervisorRootFull)
$arguments += '-ManagedLaneIds'
$arguments += @($ManagedLaneIds)
if ($TakeOverExpiredLease) { $arguments += '-TakeOverExpiredLease' }
$process = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList $arguments -WorkingDirectory $repo -WindowStyle Hidden -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru
[pscustomobject][ordered]@{launch_id=$launchId;pid=$process.Id;started_at=[DateTimeOffset]::UtcNow.ToString('o');duration_hours=$DurationHours;managed_lanes=@($ManagedLaneIds);supervisor_root=$supervisorRootFull;latest_status=Join-Path $supervisorRootFull 'latest.json';stdout_log=$stdoutPath;stderr_log=$stderrPath;safeguards=@('verification only','no R2','no merge','no deploy','no content or editorial changes')} | ConvertTo-Json -Depth 6
