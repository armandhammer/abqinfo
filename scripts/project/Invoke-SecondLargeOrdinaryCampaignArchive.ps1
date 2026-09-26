[CmdletBinding()]
param([int]$Start=1,[int]$End=999)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$campaignPath='project-state/discovery/ordinary-queue-second-large-resolution-campaign-2026-09-26.json'
$selection=Get-Content 'project-state/discovery/ordinary-queue-second-large-campaign-selection-2026-09-26.json' -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
$familyPaths=@($selection.candidate_families | Where-Object { $_.order -ge $Start -and $_.order -le $End } | ForEach-Object { 'project-state/discovery/ordinary-second-large-campaign-'+$_.family_id+'-2026-09-26.json' } | Where-Object { Test-Path -LiteralPath $_ })
$guardPath='tmp/ordinary-second-large-campaign-live-2026-09-26.json'
$d=Get-Content $campaignPath -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
$allFamilyRecords=@(Get-ChildItem 'project-state/discovery/ordinary-second-large-campaign-family-*-2026-09-26.json' | Where-Object { $_.Name -notmatch 'application' } | ForEach-Object { (Get-Content $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String).records })
$baseline=Get-Content $d.baseline_r2_artifact -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
if ($d.project_storage_limit_bytes -ne 10000000000 -or $d.visitor_visible_content_changed) {throw 'Campaign boundary changed'}
function Field($o,$n,$v){$o|Add-Member -NotePropertyName $n -NotePropertyValue $v -Force}
function Save-State {
  foreach ($entry in @(@{path=$campaignPath;data=$d},@{path=$familyPath;data=$family})) {
    $temporary=$entry.path+'.archive.tmp'
    [IO.File]::WriteAllText([IO.Path]::GetFullPath($temporary),($entry.data|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporary -Destination $entry.path -Force
  }
}
function Guard {
  & "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath $guardPath | Out-Null
  $live=Get-Content $guardPath -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String
  $map=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
  foreach($o in $live.objects){$map.Add($o.key,$o)}
  foreach($o in $baseline.objects){if(-not $map.ContainsKey($o.key) -or $map[$o.key].size_bytes -ne $o.size_bytes -or $map[$o.key].etag -cne $o.etag){throw "Pre-campaign object missing or overwritten: $($o.key)"}}
  $oldKeys=@($baseline.objects.key)
  foreach($o in $live.objects){if($o.key -cnotin $oldKeys){
    $intents=@($allFamilyRecords|Where-Object { $_.PSObject.Properties['upload_intent'] -and $_.r2_key -ceq $o.key -and $_.fresh_source_qa.size_bytes -eq $o.size_bytes })
    if($intents.Count -ne 1){throw "Unexpected R2 object: $($o.key)"}
  }}
  if($live.total_bytes -gt 10000000000){throw 'Storage ceiling exceeded'}
  return $live
}
# The complete listing is refreshed immediately before the first mutation and
# every subsequent upload. Resume verifies existing intended bytes, never puts.
$live=Guard
foreach($familyPath in $familyPaths){
$family=Get-Content $familyPath -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
foreach($r in $family.records){
  if($r.disposition -ne 'approved for addition' -or -not $r.review_complete){continue}
  $qa=$r.fresh_source_qa
  if($r.PSObject.Properties['archive_complete'] -and $r.archive_complete){continue}
  try {
    if($r.mission_scope_assessment.final_scope_decision -ne 'passes_both_gates' -or -not $qa.source_exact_verified -or $qa.representative_visual_qa -ne 'passed_agent_inspection_opening_middle_ending'){throw 'Eligibility or QA gate failed'}
    if($qa.size_bytes -gt 150000000){Field $r 'archive_deferred_reason' 'Object exceeds 150000000-byte campaign authorization';Save-State;continue}
    $inv=Get-Content project-state/master-inventory.json -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String
    $row=@($inv.candidates|Where-Object id -eq $r.id)[0]
    if($row.status -notin @('approved for addition','placement assigned') -or $row.checksum_sha256 -cne $qa.checksum_sha256 -or $row.size_bytes -ne $qa.size_bytes){throw 'Inventory identity/state changed'}
    if(@($inv.candidates|Where-Object { $_.id -ne $r.id -and $_.checksum_sha256 -ceq $qa.checksum_sha256 }).Count){throw 'Unresolved exact inventory alias'}
    $file=Get-Item -LiteralPath $qa.staged_path
    if($file.Length -ne $qa.size_bytes -or (Get-FileHash $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $qa.checksum_sha256){throw 'Staged source bytes changed'}
    $live=Guard
    $existing=@($live.objects|Where-Object {$_.key.ToLowerInvariant() -eq $r.r2_key.ToLowerInvariant()})
    if($existing.Count){
      if($existing.Count -ne 1 -or $existing[0].key -cne $r.r2_key -or $existing[0].size_bytes -ne $qa.size_bytes -or -not $r.PSObject.Properties['upload_intent']){throw 'Exact/casefold collision; overwrite prohibited'}
    }else{
      if(@($live.objects|Where-Object size_bytes -eq $qa.size_bytes).Count){throw 'Unresolved same-size R2 candidate'}
      if($live.total_bytes+$qa.size_bytes -gt 10000000000){Field $r 'archive_deferred_reason' 'Fully prepared; only storage capacity prevents upload';Save-State;continue}
      Field $r 'upload_intent' ([pscustomobject]@{key=$r.r2_key;key_was_absent=$true;size_bytes=$qa.size_bytes;sha256=$qa.checksum_sha256;started_at=(Get-Date).ToUniversalTime().ToString('o')})
      Save-State
      $allFamilyRecords=@($allFamilyRecords|Where-Object id -ne $r.id)+@($r)
      $uploadArgs=@{SourcePath=$qa.staged_path;ObjectKey=$r.r2_key}
      if($qa.size_bytes -gt 100000000){$uploadArgs.MaxObjectBytes=150000000}
      & "$PSScriptRoot/../upload-r2-document.ps1" @uploadArgs | Out-Null
      Field $r 'uploaded_pending_public_verification' $true;Save-State
    }
    $verification=& "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $qa.staged_path -PublicUrl ([uri]('https://files.abqinfo.com/'+$r.r2_key))
    if(-not $verification.byte_identical -or $verification.size_bytes -ne $qa.size_bytes -or $verification.checksum_sha256 -cne $qa.checksum_sha256){throw 'Fresh public full GET did not match exact original'}
    Field $r 'public_verification' $verification;Save-State
    $live=Guard;$object=@($live.objects|Where-Object key -CEQ $r.r2_key)[0]
    Copy-Item $guardPath project-state/r2-inventory.json -Force
    $note='Second large ordinary campaign 2026-09-26: unchanged original exact-public-byte verified; background archival only. '+$familyPath
    $notes=@($row.processing_notes);if($note -notin $notes){$notes+=$note}
    & "$PSScriptRoot/Update-Candidate.ps1" -Id $r.id -Set @{status='placement assigned';r2_key=$r.r2_key;r2_url=$verification.public_url;r2_etag=$object.etag;r2_last_modified=$object.last_modified;proposed_canonical_page=$r.proposed_canonical_page;processing_notes=$notes;validation_status='exact authoritative source and fresh public R2 GET match size/SHA-256; archive complete; no implementation'} | Out-Null
    Field $r 'archive_complete' $true
    $d.archive_objects=@($d.archive_objects|Where-Object id -ne $r.id)+@([pscustomobject]@{id=$r.id;key=$r.r2_key;size_bytes=$qa.size_bytes;checksum_sha256=$qa.checksum_sha256;etag=$object.etag;public_verification=$verification;upload_intent=$r.upload_intent})
    foreach($resolved in $d.resolved_records){if($resolved.id -eq $r.id){$resolved.current_status='placement assigned'}}
    Save-State
    & "$PSScriptRoot/Update-ArchiveReconciliationCheckpointCounts.ps1" | Out-Null
    Write-Host "Archived and exact-public-byte verified: $($r.id), $($qa.size_bytes) bytes"
  } catch {
    if($_.Exception.Message -match 'Pre-campaign object|Unexpected R2 object|Storage ceiling exceeded'){throw}
    Field $r 'archive_operation_error' ([string]$_.Exception.Message);Save-State
    Write-Warning "Isolated archive failure: $($r.id) $($_.Exception.Message)"
  }
}
}
$live=Guard
Copy-Item $guardPath project-state/r2-inventory.json -Force
Field $d 'latest_r2' ([pscustomobject]@{object_count=$live.object_count;total_bytes=$live.total_bytes})
Save-State
