[CmdletBinding()]
param([int]$Start=1,[int]$End=999)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$writerLock=[IO.File]::Open([IO.Path]::GetFullPath('tmp/background-campaign-writer.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try {
$pointer=Get-Content 'project-state/active-campaign.json' -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String
$campaignPath=$pointer.campaign_artifact
$d=Get-Content $campaignPath -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String
if($d.state -eq 'complete_background_campaign'){throw 'Campaign sealed'}
$selection=Get-Content $d.selection_artifact -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String
$familyPaths=@($selection.candidate_families|Where-Object {$_.order -ge $Start -and $_.order -le $End}|ForEach-Object {$_.evidence_artifact})+@($d.archive_family_artifacts)
$familyPaths=@($familyPaths|Select-Object -Unique)
$guardPath=Join-Path (Split-Path $campaignPath) 'r2-live.json'
$allFamilyRecords=@($familyPaths|ForEach-Object {(Get-Content $_ -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String).records})
$baseline=Get-Content $d.baseline_r2_artifact -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String
$policy=Get-Content 'project-state/r2-storage-policy.json' -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String
if($d.project_storage_limit_bytes -ne $policy.maximum_projected_r2_bytes -or $d.maximum_object_bytes -ne 150000000 -or $d.visitor_visible_content_changed -or -not $d.authorization.eligible_original_r2_upload_and_exact_public_verification){throw 'Campaign boundary changed'}
function Field($o,$n,$v){$o|Add-Member -NotePropertyName $n -NotePropertyValue $v -Force}
$familyPath=$null
$family=$null
function Save-State {
  $entries=@(@{path=$campaignPath;data=$d})
  if($familyPath){$entries+=@{path=$familyPath;data=$family}}
  foreach ($entry in $entries) {
    $temporary=$entry.path+'.archive.tmp'
    [IO.File]::WriteAllText([IO.Path]::GetFullPath($temporary),($entry.data|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporary -Destination $entry.path -Force
  }
}
function Guard {
  & "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath $guardPath | Out-Null
  $live=Get-Content $guardPath -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String
  $map=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
  $foldKeys=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  foreach($o in $live.objects){
    if(-not $foldKeys.Add($o.key)){throw "Unexpected R2 object: casefold key collision $($o.key)"}
    $map.Add($o.key,$o)
  }
  foreach($o in $baseline.objects){if(-not $map.ContainsKey($o.key) -or $map[$o.key].size_bytes -ne $o.size_bytes -or $map[$o.key].etag -cne $o.etag){throw "Pre-campaign object missing or overwritten: $($o.key)"}}
  $oldKeys=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
  foreach($o in $baseline.objects){[void]$oldKeys.Add($o.key)}
  $intentIndex=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
  foreach($rr in $allFamilyRecords){if($rr.PSObject.Properties['upload_intent']){
    if($intentIndex.ContainsKey($rr.r2_key)){throw "Unexpected R2 object: duplicate saved intents for $($rr.r2_key)"}
    $intentIndex.Add($rr.r2_key,$rr)
  }}
  foreach($o in $live.objects){if(-not $oldKeys.Contains($o.key)){
    if(-not $intentIndex.ContainsKey($o.key) -or $intentIndex[$o.key].fresh_source_qa.size_bytes -ne $o.size_bytes){throw "Unexpected R2 object: $($o.key)"}
  }}
  if($live.total_bytes -gt $policy.maximum_projected_r2_bytes){throw 'Storage ceiling exceeded'}
  return $live
}
function Assert-SameSizeCandidates($objects,$record) {
  foreach($o in $objects){
    $receipts=if($record.PSObject.Properties['same_size_r2_disambiguation']){@($record.same_size_r2_disambiguation)}else{@()}
    $matched=@($receipts|Where-Object {$_.key -ceq $o.key -and $_.etag -ceq $o.etag -and $_.size_bytes -eq $o.size_bytes -and $_.source_sha256 -ceq $record.fresh_source_qa.checksum_sha256 -and $_.public_get_size_bytes -eq $o.size_bytes -and $_.public_get_sha256 -match '^[0-9a-f]{64}$' -and $_.public_get_sha256 -cne $_.source_sha256 -and $_.verified_at})
    if($matched.Count -ne 1){throw ('Unresolved same-size R2 candidate: '+$o.key)}
  }
}
# The complete listing is refreshed immediately before the first mutation and
# every subsequent upload. Resume verifies existing intended bytes, never puts.
$live=Guard
$tasks=@(foreach($path in $familyPaths){
 $ff=Get-Content $path -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String
 foreach($rr in $ff.records){if($rr.PSObject.Properties['review_complete'] -and $rr.review_complete -and $rr.disposition -eq 'approved for addition' -and (-not $rr.PSObject.Properties['archive_complete'] -or -not $rr.archive_complete)){
  $priority=5
  $title=if($rr.PSObject.Properties['reviewed_title']){$rr.reviewed_title}else{''}
  if($ff.family_id -match '^family-(139|137|123|142|290|295|296|297|298|294)$' -or $title -match 'Enacted|Signed|Final|Adopted|Ordinance|Resolution|Regulation'){$priority=1}
  elseif($ff.family_id -match '^family-(095|108|111|119|127|134|136|144|146|291)$' -or $title -match 'Albuquerque|Study|Master Plan|Design|Traffic|Parking|Construction|Greenhouse|Climate|Food'){$priority=2}
  elseif($ff.family_id -match '^family-152'){$priority=3}
  elseif($title -match 'Minutes|Meeting|Survey|Data|Report'){$priority=4}
  if($title -match 'Draft|Proposed|Recommended|Recommendation|Instruction|Agenda'){$priority=[Math]::Max($priority,4)}
  [pscustomobject]@{path=$path;id=$rr.id;priority=$priority;size=$rr.fresh_source_qa.size_bytes}
 }}
}) | Sort-Object priority,path,id
foreach($task in $tasks){
if(Test-Path -LiteralPath 'tmp/background-campaign-pause-archive'){Write-Host 'Paused at completed-object boundary';break}
$familyPath=$task.path
$family=Get-Content $familyPath -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
$r=@($family.records|Where-Object id -eq $task.id)[0]

  if($r.disposition -ne 'approved for addition' -or -not $r.PSObject.Properties['review_complete'] -or -not $r.review_complete){continue}
  $qa=$r.fresh_source_qa
  if($r.PSObject.Properties['archive_complete'] -and $r.archive_complete){continue}
  try {
    if($r.mission_scope_assessment.final_scope_decision -ne 'passes_both_gates' -or -not $qa.source_exact_verified -or $qa.representative_visual_qa -ne 'passed_agent_inspection_opening_middle_ending'){throw 'Eligibility or QA gate failed'}
    if($qa.size_bytes -gt 150000000){Field $r 'archive_deferred_reason' 'Object exceeds 150000000-byte campaign authorization';Save-State;continue}
    # A known capacity deferral performs no remote mutation. Avoid repeating a
    # full listing for it; Guard still runs immediately before every actual PUT,
    # after every completed upload and at the final closeout boundary.
    $present=@($live.objects|Where-Object {$_.key.ToLowerInvariant() -eq $r.r2_key.ToLowerInvariant()})
    if($present.Count -and ($present.Count -ne 1 -or $present[0].key -cne $r.r2_key -or $present[0].size_bytes -ne $qa.size_bytes -or -not $r.PSObject.Properties['upload_intent'])){throw 'Exact/casefold collision; overwrite prohibited'}
    if(-not $present.Count -and $live.total_bytes+$qa.size_bytes -gt $policy.maximum_projected_r2_bytes){Field $r 'archive_deferred_reason' 'Fully prepared; only storage capacity prevents upload';Save-State;continue}
    $inv=Get-Content project-state/master-inventory.json -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String
    $row=@($inv.candidates|Where-Object id -eq $r.id)[0]
    if($row.status -notin @('approved for addition','placement assigned') -or $row.checksum_sha256 -cne $qa.checksum_sha256 -or $row.size_bytes -ne $qa.size_bytes){throw 'Inventory identity/state changed'}
    $canonicalSource=if($row.direct_file_url){$row.direct_file_url}else{$row.source_url}
    $aliases=@($inv.candidates|Where-Object { $_.id -ne $r.id -and $_.checksum_sha256 -ceq $qa.checksum_sha256 })
    foreach($alias in $aliases){if($alias.status -ne 'duplicate' -or $canonicalSource -cnotin @($alias.cited_successors) -or ($alias.processing_notes -join ' ') -notmatch [regex]::Escape($r.id)){throw 'Unresolved exact inventory alias'}}
    $file=Get-Item -LiteralPath $qa.staged_path
    if($file.Length -ne $qa.size_bytes -or (Get-FileHash $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $qa.checksum_sha256){throw 'Staged source bytes changed'}
    $live=Guard
    $existing=@($live.objects|Where-Object {$_.key.ToLowerInvariant() -eq $r.r2_key.ToLowerInvariant()})
    if($existing.Count){
      if($existing.Count -ne 1 -or $existing[0].key -cne $r.r2_key -or $existing[0].size_bytes -ne $qa.size_bytes -or -not $r.PSObject.Properties['upload_intent']){throw 'Exact/casefold collision; overwrite prohibited'}
    }else{
      $sameSize=@($live.objects|Where-Object size_bytes -eq $qa.size_bytes)
      foreach($candidate in $sameSize){
        $receipts=if($r.PSObject.Properties['same_size_r2_disambiguation']){@($r.same_size_r2_disambiguation)}else{@()}
        $already=@($receipts|Where-Object {$_.key -ceq $candidate.key -and $_.etag -ceq $candidate.etag -and $_.source_sha256 -ceq $qa.checksum_sha256})
        if(-not $already.Count){
          $comparisonPath=Join-Path ([IO.Path]::GetTempPath()) ('abqinfo-size-comparison-'+[guid]::NewGuid().ToString('n'))
          try {
            Invoke-WebRequest -Uri ('https://files.abqinfo.com/'+$candidate.key) -OutFile $comparisonPath -UseBasicParsing -TimeoutSec 180 -Headers @{'Cache-Control'='no-cache'}
            $comparison=Get-Item -LiteralPath $comparisonPath
            $comparisonHash=(Get-FileHash -LiteralPath $comparisonPath -Algorithm SHA256).Hash.ToLowerInvariant()
            $receipts=@($receipts|Where-Object key -CNE $candidate.key)+@([pscustomobject]@{key=$candidate.key;etag=$candidate.etag;size_bytes=$candidate.size_bytes;source_sha256=$qa.checksum_sha256;public_get_size_bytes=$comparison.Length;public_get_sha256=$comparisonHash;public_url=('https://files.abqinfo.com/'+$candidate.key);verified_at=(Get-Date).ToUniversalTime().ToString('o')})
            Field $r 'same_size_r2_disambiguation' $receipts;Save-State
          } finally {if(Test-Path -LiteralPath $comparisonPath){Remove-Item -LiteralPath $comparisonPath}}
        }
      }
      # A byte-size coincidence is cleared only by saved full-GET negative hash
      # evidence tied to the current listing ETag and exact source identity.
      $live=Guard
      Assert-SameSizeCandidates @($live.objects|Where-Object size_bytes -eq $qa.size_bytes) $r
      if($live.total_bytes+$qa.size_bytes -gt $policy.maximum_projected_r2_bytes){Field $r 'archive_deferred_reason' 'Fully prepared; only storage capacity prevents upload';Save-State;continue}
      Field $r 'upload_intent' ([pscustomobject]@{key=$r.r2_key;key_was_absent=$true;size_bytes=$qa.size_bytes;sha256=$qa.checksum_sha256;started_at=(Get-Date).ToUniversalTime().ToString('o')})
      Save-State
      $allFamilyRecords=@($allFamilyRecords|Where-Object id -ne $r.id)+@($r)
      $uploadArgs=@{SourcePath=$qa.staged_path;ObjectKey=$r.r2_key}
      $uploadArgs.MaxObjectBytes=150000000
      $uploadArgs.MaxProjectedStorageBytes=$policy.maximum_projected_r2_bytes
      & "$PSScriptRoot/../upload-r2-document.ps1" @uploadArgs | Out-Null
      Field $r 'uploaded_pending_public_verification' $true;Save-State
    }
    $verification=& "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $qa.staged_path -PublicUrl ([uri]('https://files.abqinfo.com/'+$r.r2_key))
    if(-not $verification.byte_identical -or $verification.size_bytes -ne $qa.size_bytes -or $verification.checksum_sha256 -cne $qa.checksum_sha256){throw 'Non-identical collision: fresh public full GET did not match exact original'}
    Field $r 'public_verification' $verification;Save-State
    $live=Guard;$object=@($live.objects|Where-Object key -CEQ $r.r2_key)[0]
    Copy-Item $guardPath project-state/r2-inventory.json -Force
    $note=('Background campaign '+$d.campaign_id+': unchanged original exact-public-byte verified; background archival only. ')+$familyPath
    $notes=@($row.processing_notes);if($note -notin $notes){$notes+=$note}
    $placementRequest='tmp/background-campaign-placement-update.json'
    $updates=@([pscustomobject]@{id=$r.id;changes=@{status='placement assigned';r2_key=$r.r2_key;r2_url=$verification.public_url;r2_etag=$object.etag;r2_last_modified=$object.last_modified;proposed_canonical_page=$r.proposed_canonical_page;processing_notes=$notes;validation_status='exact authoritative source and fresh public R2 GET match size/SHA-256; archive complete; no implementation'}})
    [IO.File]::WriteAllText([IO.Path]::GetFullPath($placementRequest),(ConvertTo-Json -InputObject $updates -Depth 20),[Text.UTF8Encoding]::new($false))
    & python -B "$PSScriptRoot/Update-CandidatesBatch.py" --requests $placementRequest | Out-Null
    if($LASTEXITCODE){throw 'Exact-public placement update failed existing mission-scope policy'}
    Field $r 'archive_complete' $true
    $d.archive_objects=@($d.archive_objects|Where-Object id -ne $r.id)+@([pscustomobject]@{id=$r.id;key=$r.r2_key;size_bytes=$qa.size_bytes;checksum_sha256=$qa.checksum_sha256;etag=$object.etag;public_verification=$verification;upload_intent=$r.upload_intent})
    foreach($resolved in $d.resolved_records){if($resolved.id -eq $r.id){$resolved.current_status='placement assigned'}}
    Save-State
    & "$PSScriptRoot/Update-ArchiveReconciliationCheckpointCounts.ps1" | Out-Null
    Write-Host "Archived and exact-public-byte verified: $($r.id), $($qa.size_bytes) bytes"
  } catch {
    if($_.Exception.Message -match 'Pre-campaign object|Unexpected R2 object|Storage ceiling exceeded|collision|Unresolved same-size R2 candidate|Public object (size|checksum) mismatch'){throw}
    Field $r 'archive_operation_error' ([string]$_.Exception.Message);Save-State
    Write-Warning "Isolated archive failure: $($r.id) $($_.Exception.Message)"
  }
}
$live=Guard
Copy-Item $guardPath project-state/r2-inventory.json -Force
Field $d 'latest_r2' ([pscustomobject]@{object_count=$live.object_count;total_bytes=$live.total_bytes})
Save-State
} finally { $writerLock.Dispose() }
