[CmdletBinding()]
param(
  [string]$ManifestPath,
  [string]$ActiveRunPath='project-state/active-run.json',
  [Parameter(Mandatory)][string[]]$AcceptedCandidateIds,
  [string]$DecisionPath,
  [string]$InventoryPath,
  [switch]$Apply,
  [switch]$TakeOverExpiredLease,
  [ValidateRange(1,60)][int]$LeaseMinutes=5,
  [string]$LeasePath,
  [string]$CoordinatorLeasePath,
  [string]$CoordinatorOwnerToken,
  [string]$UpdateCandidateScript=(Join-Path $PSScriptRoot 'Update-Candidate.ps1'),
  [Parameter(DontShow)][ValidateSet('','after-intent','after-update-before-receipt','after-receipt')][string]$TestInterruptAt=''
)

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/ParallelVerification.Campaign.Common.ps1"

function Test-ObjectValues($Candidate,$Updates){
  foreach($property in @($Updates.PSObject.Properties)){
    if($property.Name -eq 'processing_notes_append'){continue}
    if(($Candidate.($property.Name)|ConvertTo-Json -Compress -Depth 10)-ne($property.Value|ConvertTo-Json -Compress -Depth 10)){return $false}
  }
  return $true
}

$manifestFull=Resolve-ParallelVerificationCampaignManifest -ManifestPath $ManifestPath -ActiveRunPath $ActiveRunPath
$campaign=Read-ParallelVerificationJson $manifestFull;$manifestErrors=@(Test-ParallelVerificationCampaignObject $campaign);if($manifestErrors.Count){throw "Campaign validation failed: $($manifestErrors -join '; ')"}
$manifestDirectory=Split-Path -Parent $manifestFull
$acceptedInput=@($AcceptedCandidateIds|ForEach-Object{[string]$_});if(-not$acceptedInput.Count){throw 'Specify accepted candidate IDs.'};if(@($acceptedInput|Group-Object|Where-Object Count -gt 1).Count){throw 'AcceptedCandidateIds contains duplicates.'};$AcceptedCandidateIds=@($acceptedInput|Sort-Object)
if(-not $InventoryPath){$InventoryPath=[string]$campaign.inventory_path};if(-not[IO.Path]::IsPathRooted($InventoryPath)){$InventoryPath=Join-Path (Get-Location).Path $InventoryPath};$inventoryFull=[IO.Path]::GetFullPath($InventoryPath)
$entries=@(Get-ParallelVerificationCampaignEntries $campaign);$entryMap=@{};foreach($entry in $entries){$entryMap[[string]$entry.candidate_id]=$entry}
$decisionMap=@{}
if($DecisionPath){
  $decision=Read-ParallelVerificationJson ([IO.Path]::GetFullPath($DecisionPath));if([string]$decision.campaign_id-ne[string]$campaign.campaign_id -or [string]$decision.campaign_sha256-ne[string]$campaign.campaign_sha256){throw 'Decision file campaign binding is invalid.'}
  foreach($item in @($decision.decisions)){$id=[string]$item.candidate_id;if($decisionMap.ContainsKey($id)){throw "Duplicate decision: $id"};$decisionMap[$id]=$item}
}
$operations=[Collections.Generic.List[object]]::new()
foreach($id in $AcceptedCandidateIds){
  if(-not$entryMap.ContainsKey($id)){throw "Accepted candidate is not assigned: $id"};$entry=$entryMap[$id];$resultPath=Join-Path $manifestDirectory ([string]$entry.result_path)
  if(-not(Test-Path -LiteralPath $resultPath)){throw "Accepted candidate has no result: $id"};$result=Read-ParallelVerificationJson $resultPath;$resultErrors=@(Test-ParallelVerificationCandidateResultObject -Result $result -Campaign $campaign -Entry $entry -ResultPath $resultPath -ManifestDirectory $manifestDirectory);if($resultErrors.Count){throw "Invalid result for ${id}: $($resultErrors -join '; ')"}
  $updates=[ordered]@{};foreach($p in @($result.proposed_updates.PSObject.Properties)){$updates[$p.Name]=$p.Value}
  $decisionItem=$null
  if($decisionMap.ContainsKey($id)){
    $decisionItem=$decisionMap[$id];if(-not[bool]$decisionItem.accepted){throw "Decision file does not accept candidate: $id"}
    foreach($p in @($decisionItem.proposed_updates.PSObject.Properties)){$updates[$p.Name]=$p.Value}
  }
  if([string]$result.overall_status-ne'passed' -and ($null-eq$decisionItem -or [string]$updates.status-ne'requires human review' -or [string]::IsNullOrWhiteSpace([string]$decisionItem.decision_notes))){throw "Failed or incomplete candidate $id requires an explicit documented requires-human-review decision."}
  foreach($field in @($updates.Keys)){if($field -notin @($campaign.update_field_allowlist)){throw "Candidate $id proposes disallowed field: $field"}}
  if(-not$updates.Contains('validation_status')){$updates.validation_status=if([string]$result.overall_status-eq'passed'){"passed: autonomous campaign $($campaign.campaign_id)"}else{"requires human review: autonomous campaign $($campaign.campaign_id)"}}
  $operationPayload=[ordered]@{campaign_sha256=[string]$campaign.campaign_sha256;candidate_id=$id;result_sha256=[string]$result.result_sha256;updates=[pscustomobject]$updates}
  $operationId=Get-ParallelVerificationObjectHash $operationPayload
  $operations.Add([pscustomobject][ordered]@{candidate_id=$id;entry=$entry;result=$result;updates=[pscustomobject]$updates;operation_id=$operationId;marker="Parallel verification operation $operationId."})
}
if(-not$Apply){[pscustomobject][ordered]@{campaign_id=$campaign.campaign_id;mode='dry-run';candidates=$operations.Count;operations=@($operations|ForEach-Object{[pscustomobject]@{candidate_id=$_.candidate_id;operation_id=$_.operation_id;updates=$_.updates}})}|ConvertTo-Json -Depth 12;exit 0}
& git symbolic-ref --quiet HEAD|Out-Null;if($LASTEXITCODE){throw 'Apply mode must run from the coordinator branch.'}
if(-not$LeasePath -or -not$CoordinatorLeasePath){$gitCommon=(& git rev-parse --git-common-dir).Trim();if(-not[IO.Path]::IsPathRooted($gitCommon)){$gitCommon=Join-Path (Get-Location).Path $gitCommon}}
if(-not$LeasePath){$LeasePath=Join-Path $gitCommon 'abqinfo-verification-locks/inventory-writer.lock'}
if(-not$CoordinatorLeasePath){$CoordinatorLeasePath=Join-Path $gitCommon 'abqinfo-verification-locks/campaign-coordinator.lock'}
Assert-ParallelVerificationCoordinatorLeaseAccess -LeasePath ([IO.Path]::GetFullPath($CoordinatorLeasePath)) -OwnerToken $CoordinatorOwnerToken
$leaseFull=[IO.Path]::GetFullPath($LeasePath);$leaseParent=Split-Path -Parent $leaseFull;if(-not(Test-Path -LiteralPath $leaseParent)){New-Item -ItemType Directory -Path $leaseParent -Force|Out-Null}
$leaseStream=$null;$leaseOwned=$false
try{
  if(Test-Path -LiteralPath $leaseFull){
    try{$leaseStream=[IO.File]::Open($leaseFull,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}catch{throw "Inventory writer lease is active: $leaseFull"}
    $reader=[IO.StreamReader]::new($leaseStream,[Text.Encoding]::UTF8,$true,1024,$true);try{$text=$reader.ReadToEnd()}finally{$reader.Dispose()};$prior=$null;try{$prior=$text|ConvertFrom-Json -DateKind String}catch{}
    $expired=$prior -and [DateTimeOffset]::Parse([string]$prior.expires_at)-le[DateTimeOffset]::UtcNow
    if(-not$expired -or -not$TakeOverExpiredLease){throw 'Existing inventory writer lease is not eligible for stale takeover.'}
  }else{$leaseStream=[IO.File]::Open($leaseFull,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}
  $leaseOwned=$true;$now=(Get-Date).ToUniversalTime();$lease=[ordered]@{campaign_id=$campaign.campaign_id;pid=$PID;started_at=$now.ToString('o');expires_at=$now.AddMinutes($LeaseMinutes).ToString('o')};$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($lease|ConvertTo-Json -Compress));$leaseStream.Position=0;$leaseStream.SetLength(0);$leaseStream.Write($bytes,0,$bytes.Length);$leaseStream.Flush($true)
  $completed=[Collections.Generic.List[object]]::new()
  foreach($operation in $operations){
    $id=[string]$operation.candidate_id;$intentPath=Join-Path $manifestDirectory "integration/intents/$id.json";$receiptPath=Join-Path $manifestDirectory "integration/receipts/$id.json"
    $inventory=Read-ParallelVerificationJson $inventoryFull;$candidate=@($inventory.candidates|Where-Object id -eq $id);if($candidate.Count-ne1){throw "Expected one inventory candidate for $id"};$candidate=$candidate[0]
    $receiptRecovery=$false;$receipt=$null
    if(Test-Path -LiteralPath $receiptPath){
      if(-not(Test-Path -LiteralPath $intentPath)){throw "Integration receipt exists without intent: $id"};$intent=Read-ParallelVerificationJson $intentPath;$intentErrors=@(Test-ParallelVerificationIntegrationIntentObject -Intent $intent -Campaign $campaign -Entry $operation.entry -Result $operation.result -Path $intentPath);if($intentErrors.Count -or [string]$intent.operation_id-ne[string]$operation.operation_id){throw "Invalid integration intent for ${id}: $($intentErrors -join '; ')"};$receipt=Read-ParallelVerificationJson $receiptPath;$receiptErrors=@(Test-ParallelVerificationIntegrationReceiptObject -Receipt $receipt -Campaign $campaign -Entry $operation.entry -Result $operation.result -Intent $intent -Path $receiptPath);if($receiptErrors.Count){throw "Invalid integration receipt for ${id}: $($receiptErrors -join '; ')"};if($operation.marker -in @($candidate.processing_notes)){$completed.Add([pscustomobject]@{candidate_id=$id;operation_id=$operation.operation_id;state='already-integrated'});continue};if((Get-ParallelVerificationCandidateFingerprint $candidate)-ne[string]$receipt.before_fingerprint_sha256){throw "Receipt exists but inventory is neither the recorded input nor the completed operation: $id"};$receiptRecovery=$true
    }
    $inputFingerprint=Get-ParallelVerificationCandidateFingerprint $candidate;$markerPresent=$operation.marker -in @($candidate.processing_notes)
    if($markerPresent){if(-not(Test-ObjectValues $candidate $operation.updates)){throw "Operation marker exists but intended fields do not match: $id"};$recovery=$true}
    elseif($inputFingerprint-ne[string]$operation.entry.input_fingerprint_sha256){throw "Stale integration input: $id"}else{$recovery=$false}
    if(Test-Path -LiteralPath $intentPath){$intent=Read-ParallelVerificationJson $intentPath;$intentErrors=@(Test-ParallelVerificationIntegrationIntentObject -Intent $intent -Campaign $campaign -Entry $operation.entry -Result $operation.result -Path $intentPath);if($intentErrors.Count -or [string]$intent.operation_id-ne[string]$operation.operation_id){throw "Invalid integration intent for ${id}: $($intentErrors -join '; ')"}}
    else{
      $intentPayload=[ordered]@{schema_version=1;campaign_id=[string]$campaign.campaign_id;campaign_sha256=[string]$campaign.campaign_sha256;candidate_id=$id;result_sha256=[string]$operation.result.result_sha256;operation_id=[string]$operation.operation_id;created_at=(Get-Date).ToUniversalTime().ToString('o');before_fingerprint_sha256=[string]$operation.entry.input_fingerprint_sha256;set=$operation.updates}
      $intent=[ordered]@{};foreach($key in $intentPayload.Keys){$intent[$key]=$intentPayload[$key]};$intent.intent_sha256=Get-ParallelVerificationObjectHash $intentPayload;Write-ParallelVerificationJsonCreateNew $intent $intentPath -ReadOnly|Out-Null
    }
    if($TestInterruptAt-eq'after-intent'){throw "Test interruption after intent: $id"}
    if(-not$markerPresent){
      $set=@{};foreach($p in @($operation.updates.PSObject.Properties)){if($p.Name-ne'processing_notes_append'){$set[$p.Name]=$p.Value}}
      $notes=[Collections.Generic.List[string]]::new();foreach($note in @($candidate.processing_notes)){if(-not[string]::IsNullOrWhiteSpace([string]$note)){$notes.Add([string]$note)}}
      if($operation.updates.PSObject.Properties['processing_notes_append']){foreach($note in @($operation.updates.processing_notes_append)){if($note -and [string]$note -notin $notes){$notes.Add([string]$note)}}};if($operation.marker -notin $notes){$notes.Add($operation.marker)};$set.processing_notes=@($notes)
      & $UpdateCandidateScript -Id $id -Set $set -InventoryPath $inventoryFull|Out-Null;$recovery=$false
    }
    if($TestInterruptAt-eq'after-update-before-receipt'){throw "Test interruption after update: $id"}
    $updated=Read-ParallelVerificationJson $inventoryFull;$updatedCandidate=@($updated.candidates|Where-Object id -eq $id)[0]
    if($receiptRecovery){if(-not(Test-ObjectValues $updatedCandidate $operation.updates) -or $operation.marker -notin @($updatedCandidate.processing_notes)){throw "Replayed inventory operation does not match its immutable intent: $id"};$completed.Add([pscustomobject]@{candidate_id=$id;operation_id=$operation.operation_id;state='receipt-replayed'});continue}
    $receiptPayload=[ordered]@{schema_version=1;campaign_id=[string]$campaign.campaign_id;campaign_sha256=[string]$campaign.campaign_sha256;candidate_id=$id;result_sha256=[string]$operation.result.result_sha256;operation_id=[string]$operation.operation_id;completed_at=(Get-Date).ToUniversalTime().ToString('o');before_fingerprint_sha256=[string]$operation.entry.input_fingerprint_sha256;after_fingerprint_sha256=Get-ParallelVerificationCandidateFingerprint $updatedCandidate;recovery=[bool]$recovery}
    $receipt=[ordered]@{};foreach($key in $receiptPayload.Keys){$receipt[$key]=$receiptPayload[$key]};$receipt.receipt_sha256=Get-ParallelVerificationObjectHash $receiptPayload;Write-ParallelVerificationJsonCreateNew $receipt $receiptPath -ReadOnly|Out-Null
    $completed.Add([pscustomobject]@{candidate_id=$id;operation_id=$operation.operation_id;state=if($recovery){'receipt-recovered'}else{'integrated'}})
    if($TestInterruptAt-eq'after-receipt'){throw "Test interruption after receipt: $id"}
  }
  [pscustomobject][ordered]@{campaign_id=$campaign.campaign_id;mode='applied';candidates=$completed.Count;completed=@($completed)}|ConvertTo-Json -Depth 8
}finally{
  if($leaseStream){$leaseStream.Dispose()};if($leaseOwned -and(Test-Path -LiteralPath $leaseFull)){Remove-Item -LiteralPath $leaseFull -Force}
}
