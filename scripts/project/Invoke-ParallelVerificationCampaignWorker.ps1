[CmdletBinding()]
param(
  [string]$ManifestPath,
  [string]$ActiveRunPath='project-state/active-run.json',
  [Parameter(Mandatory)][string]$LaneId,
  [string]$WorkerProvider='unspecified',
  [string]$RepoRoot=(Get-Location).Path,
  [ValidateRange(1,1440)][int]$LeaseMinutes=5,
  [switch]$TakeOverExpiredLease,
  [ValidateRange(0,100000)][int]$MaxCandidates=0,
  [switch]$SkipLinkCheck,
  [ValidateRange(1,300)][int]$LinkTimeoutSeconds=30,
  [Parameter(DontShow)][ValidateSet('','before-verification','after-verification-before-result','after-result','after-batch')][string]$TestInterruptAt=''
)

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/ParallelVerification.Campaign.Common.ps1"

function Write-LeaseStream([IO.FileStream]$Stream,[string]$CampaignId,[string]$Lane,[string]$Token,[string]$Provider,[int]$Minutes,[string]$State){
  $now=(Get-Date).ToUniversalTime()
  $lease=[ordered]@{schema_version=1;campaign_id=$CampaignId;lane_id=$Lane;owner_token=$Token;worker_provider=$Provider;pid=$PID;state=$State;heartbeat_at=$now.ToString('o');expires_at=$now.AddMinutes($Minutes).ToString('o')}
  $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($lease|ConvertTo-Json -Compress))
  $Stream.Position=0;$Stream.SetLength(0);$Stream.Write($bytes,0,$bytes.Length);$Stream.Flush($true)
}

$manifestFull=Resolve-ParallelVerificationCampaignManifest -ManifestPath $ManifestPath -ActiveRunPath $ActiveRunPath
$campaign=Read-ParallelVerificationJson $manifestFull
$errors=@(Test-ParallelVerificationCampaignObject $campaign);if($errors.Count){throw "Campaign validation failed: $($errors -join '; ')"}
if(((Get-Item -LiteralPath $manifestFull).Attributes -band [IO.FileAttributes]::ReadOnly)-eq 0){throw 'Campaign manifest is not read-only.'}
$LaneId=$LaneId.Trim().ToLowerInvariant();if($LaneId -notin @($campaign.lanes)){throw "Lane is not assigned to this campaign: $LaneId"}
$repoFull=[IO.Path]::GetFullPath($RepoRoot)
$inventoryPath=[string]$campaign.inventory_path;if(-not[IO.Path]::IsPathRooted($inventoryPath)){$inventoryPath=Join-Path $repoFull $inventoryPath}
$inventoryPath=[IO.Path]::GetFullPath($inventoryPath)
if((Get-ParallelVerificationFileHash $inventoryPath)-ne[string]$campaign.inventory_sha256){throw 'Worker inventory does not match the immutable campaign snapshot.'}
$inventory=Read-ParallelVerificationJson $inventoryPath;$map=@{};foreach($candidate in @($inventory.candidates)){$map[[string]$candidate.id]=$candidate}
$entries=@(Get-ParallelVerificationCampaignEntries $campaign|Where-Object lane_id -eq $LaneId|Sort-Object batch_ordinal,candidate_ordinal)
$manifestDirectory=Split-Path -Parent $manifestFull
$leasePath=Join-Path $manifestDirectory "leases/$LaneId.json";$leaseParent=Split-Path -Parent $leasePath;if(-not(Test-Path -LiteralPath $leaseParent)){New-Item -ItemType Directory -Path $leaseParent -Force|Out-Null}
$leaseStream=$null;$ownerToken=[guid]::NewGuid().ToString('N');$newResults=0;$skippedResults=0
try{
  try{$leaseStream=[IO.File]::Open($leasePath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}catch{throw "Lane lease is held by another worker: $leasePath"}
  if($leaseStream.Length -gt 0){
    $leaseStream.Position=0;$reader=[IO.StreamReader]::new($leaseStream,[Text.Encoding]::UTF8,$true,1024,$true)
    try{$existingText=$reader.ReadToEnd()}finally{$reader.Dispose()}
    try{$existing=$existingText|ConvertFrom-Json -DateKind String}catch{throw 'Existing lane lease is corrupt and requires coordinator review.'}
    $expired=[DateTimeOffset]::Parse([string]$existing.expires_at)-le[DateTimeOffset]::UtcNow
    if([string]$existing.state -ne 'released' -and (-not $expired -or -not $TakeOverExpiredLease)){throw "Orphaned lane lease is not eligible for takeover until $($existing.expires_at)."}
  }
  Write-LeaseStream $leaseStream $campaign.campaign_id $LaneId $ownerToken $WorkerProvider $LeaseMinutes 'active'

  for($index=0;$index -lt $entries.Count;$index++){
    $entry=$entries[$index];$id=[string]$entry.candidate_id;$resultPath=Join-Path $manifestDirectory ([string]$entry.result_path)
    if(Test-Path -LiteralPath $resultPath){
      $existingResult=Read-ParallelVerificationJson $resultPath
      $resultErrors=@(Test-ParallelVerificationCandidateResultObject -Result $existingResult -Campaign $campaign -Entry $entry -ResultPath $resultPath -ManifestDirectory $manifestDirectory)
      if($resultErrors.Count){throw "Existing result for $id is invalid: $($resultErrors -join '; ')"}
      $skippedResults++;continue
    }
    if(-not $map.ContainsKey($id)){throw "Assigned candidate is missing from inventory: $id"}
    $candidate=$map[$id];$fingerprint=Get-ParallelVerificationCandidateFingerprint $candidate
    if($fingerprint-ne[string]$entry.input_fingerprint_sha256){throw "Stale candidate input: $id"}
    Write-LeaseStream $leaseStream $campaign.campaign_id $LaneId $ownerToken $WorkerProvider $LeaseMinutes 'active'
    if($TestInterruptAt -eq 'before-verification'){throw "Test interruption before verification: $id"}
    $verification=Invoke-ParallelVerificationCandidateChecks -Candidate $candidate -RepoRoot $repoFull -SkipLinkCheck:$SkipLinkCheck -LinkTimeoutSeconds $LinkTimeoutSeconds
    if($TestInterruptAt -eq 'after-verification-before-result'){throw "Test interruption after verification before result: $id"}
    $payload=[ordered]@{schema_version=1;campaign_id=[string]$campaign.campaign_id;campaign_sha256=[string]$campaign.campaign_sha256;base_commit=[string]$campaign.base_commit;inventory_sha256=[string]$campaign.inventory_sha256;lane_id=$LaneId;batch_id=[string]$entry.batch_id;batch_ordinal=[int]$entry.batch_ordinal;candidate_ordinal=[int]$entry.candidate_ordinal;candidate_id=$id;input_fingerprint_sha256=$fingerprint;worker_provider=$WorkerProvider;generated_at=(Get-Date).ToUniversalTime().ToString('o');overall_status=[string]$verification.overall_status;checks=$verification.checks;proposed_updates=[pscustomobject]@{};review_notes=$null}
    $result=[ordered]@{};foreach($key in $payload.Keys){$result[$key]=$payload[$key]};$result.result_sha256=Get-ParallelVerificationObjectHash $payload
    Write-ParallelVerificationJsonCreateNew -Value $result -Path $resultPath -ReadOnly|Out-Null;$newResults++
    Write-LeaseStream $leaseStream $campaign.campaign_id $LaneId $ownerToken $WorkerProvider $LeaseMinutes 'active'
    if($TestInterruptAt -eq 'after-result'){throw "Test interruption after result creation: $id"}
    $nextEntry=if($index+1 -lt $entries.Count){$entries[$index+1]}else{$null}
    if($TestInterruptAt -eq 'after-batch' -and $nextEntry -and [string]$nextEntry.batch_id -ne [string]$entry.batch_id){throw "Test interruption after batch: $($entry.batch_id)"}
    if($MaxCandidates -gt 0 -and $newResults -ge $MaxCandidates){break}
  }
  [pscustomobject][ordered]@{campaign_id=$campaign.campaign_id;lane_id=$LaneId;worker_provider=$WorkerProvider;assigned=$entries.Count;created=$newResults;already_complete=$skippedResults;remaining=$entries.Count-$newResults-$skippedResults;status=if($entries.Count-$newResults-$skippedResults){'paused'}else{'complete'}}|ConvertTo-Json -Depth 5
}finally{
  if($leaseStream){
    try{Write-LeaseStream $leaseStream $campaign.campaign_id $LaneId $ownerToken $WorkerProvider 0 'released'}catch{}
    $leaseStream.Dispose()
  }
}
