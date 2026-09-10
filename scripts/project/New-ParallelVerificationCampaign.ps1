[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$CampaignId,
  [string[]]$LaneIds = @('codex','claude'),
  [string[]]$CandidateIds,
  [string]$StartId,
  [int]$Count = 0,
  [ValidateRange(1,100)][int]$MicrobatchSize = 10,
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$CampaignRoot,
  [string]$BaseCommit
)

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/ParallelVerification.Campaign.Common.ps1"

if($CampaignId -notmatch '^[a-z0-9][a-z0-9._-]{2,63}$'){throw 'CampaignId is invalid.'}
$LaneIds=@($LaneIds|ForEach-Object{$_.Trim().ToLowerInvariant()})
if(-not $LaneIds.Count -or @($LaneIds|Group-Object|Where-Object Count -gt 1).Count){throw 'LaneIds must be non-empty and unique.'}
foreach($lane in $LaneIds){if($lane -notmatch '^[a-z0-9][a-z0-9._-]{1,31}$'){throw "Invalid lane ID: $lane"}}

$repo=(& git rev-parse --show-toplevel).Trim(); if($LASTEXITCODE){throw 'Unable to resolve repository root.'}
$repo=[IO.Path]::GetFullPath($repo).TrimEnd('\','/')
if(-not $CampaignRoot){$CampaignRoot=Join-Path (Split-Path -Parent $repo) 'ABQinfo-verification-campaigns'}
$inventoryFull=[IO.Path]::GetFullPath($InventoryPath)
$inventory=Read-ParallelVerificationJson $inventoryFull
if($CandidateIds -and ($StartId -or $Count)){throw 'Use CandidateIds or StartId/Count, not both.'}
if(-not $CandidateIds){
  if(-not $StartId -or $Count -lt 1){throw 'Specify CandidateIds, or StartId with a positive Count.'}
  $CandidateIds=@($inventory.candidates|Where-Object{[string]$_.id -ge $StartId -and $_.status -eq 'pending review'}|Sort-Object id|Select-Object -First $Count -ExpandProperty id)
  if($CandidateIds.Count -ne $Count){throw "Requested $Count pending candidates but found $($CandidateIds.Count) at or after $StartId."}
}
$CandidateIds=@($CandidateIds|ForEach-Object{[string]$_}|Sort-Object -Unique)
if(-not $CandidateIds.Count){throw 'Campaign contains no candidates.'}
$map=@{}; foreach($candidate in @($inventory.candidates)){$map[[string]$candidate.id]=$candidate}
foreach($id in $CandidateIds){if(-not $map.ContainsKey($id)){throw "Candidate not found: $id"}}

if(-not $BaseCommit){$BaseCommit='HEAD'}
$BaseCommit=(& git rev-parse "$BaseCommit^{commit}").Trim(); if($LASTEXITCODE){throw 'Unable to resolve campaign base commit.'}
$inside=$inventoryFull -eq $repo -or $inventoryFull.StartsWith("$repo\",[StringComparison]::OrdinalIgnoreCase)
if($inside){
  $relative=[IO.Path]::GetRelativePath($repo,$inventoryFull).Replace('\','/')
  & git ls-files --error-unmatch -- $relative|Out-Null; if($LASTEXITCODE){throw 'A repository-local inventory must be tracked by Git.'}
  & git diff --quiet $BaseCommit -- $relative
  if($LASTEXITCODE -eq 1){throw 'Inventory content does not match the selected campaign base commit.'}
  if($LASTEXITCODE -ne 0){throw 'Unable to compare inventory with campaign base commit.'}
  $manifestInventoryPath=$relative
}else{$manifestInventoryPath=$inventoryFull.Replace('\','/')}

$rootFull=[IO.Path]::GetFullPath($CampaignRoot)
if($rootFull -eq $repo -or $rootFull.StartsWith("$repo\",[StringComparison]::OrdinalIgnoreCase)){throw 'CampaignRoot must be outside the repository so worker artifacts cannot modify Git working state.'}
$campaignPath=Join-Path (Join-Path $rootFull $CampaignId) 'campaign.json'
if(Test-Path -LiteralPath (Split-Path -Parent $campaignPath)){throw "Campaign directory already exists: $(Split-Path -Parent $campaignPath)"}
if(Test-Path -LiteralPath $rootFull){
  $requested=@{}; foreach($id in $CandidateIds){$requested[$id]=$true}
  foreach($existingPath in @(Get-ChildItem -LiteralPath $rootFull -Filter campaign.json -File -Recurse -ErrorAction SilentlyContinue|Select-Object -ExpandProperty FullName)){
    $existing=Read-ParallelVerificationJson $existingPath
    $existingErrors=@(Test-ParallelVerificationCampaignObject $existing)
    if($existingErrors.Count){throw "Existing campaign is invalid: $existingPath :: $($existingErrors -join '; ')"}
    foreach($entry in @(Get-ParallelVerificationCampaignEntries $existing)){
      if($requested.ContainsKey([string]$entry.candidate_id)){throw "Candidate overlaps existing campaign $($existing.campaign_id): $($entry.candidate_id)"}
    }
  }
}

$batches=[Collections.Generic.List[object]]::new()
$batchCount=[int][Math]::Ceiling([double]$CandidateIds.Count/$MicrobatchSize)
for($batchIndex=0;$batchIndex -lt $batchCount;$batchIndex++){
  $ordinal=$batchIndex+1; $batchId='batch-{0:d4}' -f $ordinal; $lane=$LaneIds[$batchIndex%$LaneIds.Count]
  $start=$batchIndex*$MicrobatchSize; $length=[Math]::Min($MicrobatchSize,$CandidateIds.Count-$start)
  $items=[Collections.Generic.List[object]]::new()
  for($candidateIndex=0;$candidateIndex -lt $length;$candidateIndex++){
    $id=$CandidateIds[$start+$candidateIndex]
    $items.Add([pscustomobject][ordered]@{ordinal=$candidateIndex+1;candidate_id=$id;input_fingerprint_sha256=Get-ParallelVerificationCandidateFingerprint $map[$id];result_path="results/$lane/$batchId/$id.json"})
  }
  $batches.Add([pscustomobject][ordered]@{ordinal=$ordinal;batch_id=$batchId;lane_id=$lane;candidates=@($items)})
}
$payload=[ordered]@{
  schema_version=1;campaign_id=$CampaignId;created_at=(Get-Date).ToUniversalTime().ToString('o');base_commit=$BaseCommit
  inventory_path=$manifestInventoryPath;inventory_sha256=Get-ParallelVerificationFileHash $inventoryFull;start_id=$CandidateIds[0]
  candidate_count=$CandidateIds.Count;microbatch_size=$MicrobatchSize
  sharding='sorted candidate IDs chunked into microbatches and batches assigned round-robin to lanes'
  check_types=@('file_integrity','source_provenance','link_reachability')
  update_field_allowlist=@('status','title','date','description','proposed_canonical_page','exclusion_reason','validation_status','provenance_status','processing_notes_append')
  lanes=$LaneIds;batches=@($batches)
}
$campaign=[ordered]@{};foreach($key in $payload.Keys){$campaign[$key]=$payload[$key]};$campaign.campaign_sha256=Get-ParallelVerificationObjectHash $payload
Write-ParallelVerificationJsonCreateNew -Value $campaign -Path $campaignPath -ReadOnly|Out-Null
[pscustomobject][ordered]@{campaign_id=$CampaignId;manifest_path=$campaignPath;campaign_sha256=$campaign.campaign_sha256;base_commit=$BaseCommit;candidates=$CandidateIds.Count;microbatches=$batchCount;lanes=@($LaneIds|ForEach-Object{$lane=$_;[pscustomobject]@{lane_id=$lane;batches=@($batches|Where-Object lane_id -eq $lane).Count;candidates=@($batches|Where-Object lane_id -eq $lane|ForEach-Object{$_.candidates}).Count}})}|ConvertTo-Json -Depth 6
