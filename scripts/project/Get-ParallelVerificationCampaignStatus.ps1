[CmdletBinding()]
param(
  [string]$ManifestPath,
  [string]$ActiveRunPath='project-state/active-run.json',
  [string]$InventoryPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/ParallelVerification.Campaign.Common.ps1"

$manifestFull=Resolve-ParallelVerificationCampaignManifest -ManifestPath $ManifestPath -ActiveRunPath $ActiveRunPath
$campaign=Read-ParallelVerificationJson $manifestFull
$errors=[Collections.Generic.List[string]]::new();foreach($errorText in @(Test-ParallelVerificationCampaignObject $campaign)){$errors.Add($errorText)}
if(((Get-Item -LiteralPath $manifestFull).Attributes -band [IO.FileAttributes]::ReadOnly)-eq 0){$errors.Add('Campaign manifest is not read-only.')}
$root=Split-Path -Parent $manifestFull
if(-not $InventoryPath){$InventoryPath=[string]$campaign.inventory_path}
if(-not[IO.Path]::IsPathRooted($InventoryPath)){$InventoryPath=Join-Path (Get-Location).Path $InventoryPath}
$inventory=Read-ParallelVerificationJson ([IO.Path]::GetFullPath($InventoryPath));$map=@{};foreach($candidate in @($inventory.candidates)){$map[[string]$candidate.id]=$candidate}
$entries=@(Get-ParallelVerificationCampaignEntries $campaign)
$records=[Collections.Generic.List[object]]::new()
foreach($entry in $entries){
  $path=Join-Path $root ([string]$entry.result_path);$state='pending';$overall=$null;$resultHash=$null
  if(Test-Path -LiteralPath $path){
    try{$result=Read-ParallelVerificationJson $path;$resultErrors=@(Test-ParallelVerificationCandidateResultObject -Result $result -Campaign $campaign -Entry $entry -ResultPath $path -ManifestDirectory $root);if($resultErrors.Count){foreach($e in $resultErrors){$errors.Add("$($entry.candidate_id): $e")};$state='invalid'}else{$state='complete';$overall=[string]$result.overall_status;$resultHash=[string]$result.result_sha256}}catch{$errors.Add("$($entry.candidate_id): $($_.Exception.Message)");$state='invalid'}
  }elseif(-not $map.ContainsKey([string]$entry.candidate_id)){$state='stale';$errors.Add("Missing inventory candidate: $($entry.candidate_id)")}
  elseif((Get-ParallelVerificationCandidateFingerprint $map[[string]$entry.candidate_id])-ne[string]$entry.input_fingerprint_sha256){$state='stale';$errors.Add("Stale pending candidate: $($entry.candidate_id)")}
  $ambiguous=$false;if($state-eq'complete'){$ambiguous=[string]$result.checks.source_provenance.status-ne'passed'}
  $intentPath=Join-Path $root "integration/intents/$($entry.candidate_id).json";$receiptPath=Join-Path $root "integration/receipts/$($entry.candidate_id).json";$accepted=$false;$integrated=$false
  if(Test-Path -LiteralPath $intentPath){if($state-ne'complete'){$errors.Add("Integration intent exists without a valid result: $($entry.candidate_id)")}else{$intent=Read-ParallelVerificationJson $intentPath;$intentErrors=@(Test-ParallelVerificationIntegrationIntentObject -Intent $intent -Campaign $campaign -Entry $entry -Result $result -Path $intentPath);if($intentErrors.Count){foreach($e in $intentErrors){$errors.Add("$($entry.candidate_id): $e")}}else{$accepted=$true}}}
  if(Test-Path -LiteralPath $receiptPath){if(-not$accepted){$errors.Add("Integration receipt exists without a valid intent: $($entry.candidate_id)")}else{$receipt=Read-ParallelVerificationJson $receiptPath;$receiptErrors=@(Test-ParallelVerificationIntegrationReceiptObject -Receipt $receipt -Campaign $campaign -Entry $entry -Result $result -Intent $intent -Path $receiptPath);if($receiptErrors.Count){foreach($e in $receiptErrors){$errors.Add("$($entry.candidate_id): $e")}}else{$integrated=$true}}}
  $records.Add([pscustomobject][ordered]@{lane_id=$entry.lane_id;batch_id=$entry.batch_id;candidate_id=$entry.candidate_id;verification_state=$state;overall_status=$overall;ambiguous=$ambiguous;result_sha256=$resultHash;accepted=$accepted;integrated=$integrated})
}
$laneStatus=foreach($lane in @($campaign.lanes)){
  $laneRecords=@($records|Where-Object lane_id -eq $lane);$leasePath=Join-Path $root "leases/$lane.json";$leaseState='absent';$lease=$null
  if(Test-Path -LiteralPath $leasePath){
    try{$stream=[IO.File]::Open($leasePath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite);try{$reader=[IO.StreamReader]::new($stream);try{$lease=$reader.ReadToEnd()|ConvertFrom-Json -DateKind String}finally{$reader.Dispose()}}finally{$stream.Dispose()};$leaseState=if([string]$lease.state -eq 'released'){'released'}elseif([DateTimeOffset]::Parse([string]$lease.expires_at)-le[DateTimeOffset]::UtcNow){'expired'}else{'orphaned-unlocked'}}catch{$leaseState='active-locked'}
  }
  [pscustomobject][ordered]@{lane_id=$lane;lease_state=$leaseState;assigned=$laneRecords.Count;complete=@($laneRecords|Where-Object verification_state -eq 'complete').Count;passed=@($laneRecords|Where-Object overall_status -eq 'passed').Count;failed=@($laneRecords|Where-Object overall_status -eq 'failed').Count;incomplete=@($laneRecords|Where-Object overall_status -eq 'incomplete').Count;ambiguous=@($laneRecords|Where-Object ambiguous).Count;remaining=@($laneRecords|Where-Object verification_state -eq 'pending').Count;invalid_or_stale=@($laneRecords|Where-Object verification_state -in @('invalid','stale')).Count}
}
$batchStatus=foreach($batch in @($campaign.batches|Sort-Object ordinal)){$batchRecords=@($records|Where-Object batch_id -eq $batch.batch_id);[pscustomobject][ordered]@{batch_id=$batch.batch_id;ordinal=$batch.ordinal;lane_id=$batch.lane_id;assigned=$batchRecords.Count;complete=@($batchRecords|Where-Object verification_state -eq 'complete').Count;remaining=@($batchRecords|Where-Object verification_state -eq 'pending').Count;failed=@($batchRecords|Where-Object overall_status -eq 'failed').Count;ambiguous=@($batchRecords|Where-Object ambiguous).Count}}
[pscustomobject][ordered]@{valid=$errors.Count-eq 0;campaign_id=$campaign.campaign_id;manifest_path=$manifestFull;campaign_sha256=$campaign.campaign_sha256;candidates=$entries.Count;verified=@($records|Where-Object verification_state -eq 'complete').Count;passed=@($records|Where-Object overall_status -eq 'passed').Count;failed=@($records|Where-Object overall_status -eq 'failed').Count;incomplete=@($records|Where-Object overall_status -eq 'incomplete').Count;ambiguous=@($records|Where-Object ambiguous).Count;remaining=@($records|Where-Object verification_state -eq 'pending').Count;accepted=@($records|Where-Object accepted).Count;integrated=@($records|Where-Object integrated).Count;errors=@($errors);lanes=@($laneStatus);batches=@($batchStatus)}|ConvertTo-Json -Depth 10
