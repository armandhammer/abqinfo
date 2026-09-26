[CmdletBinding()]
param([string]$Phase='originals')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$campaignPath='project-state/discovery/approved-backlog-background-archive-campaign-2026-09-26.json'
$guardPath='tmp/background-campaign-current-live-2026-09-26.json'
$d=Get-Content $campaignPath -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String
if ($d.state -eq 'complete_background_campaign') { throw 'Completed campaign: preserve evidence, no upload rerun.' }
$baseline=Get-Content $d.baseline_r2_artifact -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String
$baselineMap=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach ($obj in $baseline.objects) { $baselineMap.Add($obj.key,$obj) }
function Save-Campaign {
  $d.updated_at=(Get-Date).ToUniversalTime().ToString('o')
  $tmp="$campaignPath.tmp-$PID"
  [IO.File]::WriteAllText([IO.Path]::GetFullPath($tmp),($d | ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $campaignPath -Force
}
function Set-Field($Object,[string]$Name,$Value) { $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force }
function Read-Guard {
  & "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath $guardPath | Out-Null
  $live=Get-Content $guardPath -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String
  $liveMap=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
  foreach ($obj in $live.objects) { $liveMap.Add($obj.key,$obj) }
  foreach ($old in $baseline.objects) {
    if (-not $liveMap.ContainsKey($old.key) -or $liveMap[$old.key].size_bytes -ne $old.size_bytes -or $liveMap[$old.key].etag -cne $old.etag) { throw "Baseline object changed: $($old.key)" }
  }
  $intended=@(@($d.records)+@($d.generated_packages) | Where-Object { $_.PSObject.Properties['upload_intent'] })
  foreach ($obj in $live.objects) {
    if ($baselineMap.ContainsKey($obj.key)) { continue }
    if (@($intended | Where-Object { $_.r2_key -ceq $obj.key -and $_.size_bytes -eq $obj.size_bytes }).Count -ne 1) { throw "Unexpected new object: $($obj.key)" }
  }
  return $live
}
function Update-Inventory($r,$object) {
  if ($r.classification -ne 'unchanged_City_original') { return }
  $inv=Get-Content project-state/master-inventory.json -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String
  $row=@($inv.candidates | Where-Object id -eq $r.id)[0]
  if ($row.status -notin @('approved for addition','placement assigned') -or $row.size_bytes -ne $r.size_bytes -or $row.checksum_sha256 -cne $r.expected_sha256 -or $row.scope_assessment.final_scope_decision -ne 'passes_both_gates') { throw "Inventory source/state changed: $($r.id)" }
  $note="Background campaign 2026-09-26: unchanged authoritative original exact-source staged and public-byte verified at $($r.r2_key); $($r.size_bytes) bytes / SHA-256 $($r.expected_sha256). No visitor-visible implementation. Governing campaign evidence: $campaignPath."
  $notes=@($row.processing_notes); if ($note -notin $notes) {$notes+=$note}
  $changes=@{r2_key=$r.r2_key;r2_url=$r.public_verification.public_url;r2_etag=$object.etag;r2_last_modified=$object.last_modified;local_path=$r.staged_path;file_type=$r.container_type;processing_notes=$notes;validation_status='authoritative source and fresh full public R2 GET match exact size and SHA-256; archival complete; no visitor-visible implementation'}
  if ($r.canonical_page) { $changes.status='placement assigned';$changes.proposed_canonical_page=$r.canonical_page }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $r.id -Set $changes | Out-Null
  Set-Field $r 'inventory_status_after' $(if($r.canonical_page){'placement assigned'}else{'approved for addition'})
  Set-Field $r 'inventory_reconciled' $true
}
if ($d.records.Count -ne 27 -or $d.visitor_visible_content_changed -or $d.project_storage_limit_bytes -ne 10000000000) { throw 'Campaign scope/guardrails invalid.' }
if ($Phase -eq 'originals') { $selected=@($d.records) }
elseif ($Phase -eq 'capital') {
  if (@($d.records | Where-Object outcome -eq 'ready_for_guarded_upload').Count) { throw 'Process all original attempts first.' }
  $selected=@($d.generated_packages | Where-Object family -eq 'Capital Spending 2011 historical compilations')
} elseif ($Phase -eq 'dpm') { $selected=@($d.generated_packages | Where-Object family -eq 'DPM corrected annual packets') }
else { throw 'Unknown bounded phase' }
$live=Read-Guard
foreach ($r in $selected) {
  if ($r.outcome -notin @('ready_for_guarded_upload','uploaded_pending_public_verification','upload_or_public_verification_failed','archive_complete')) { continue }
  try {
    if (-not $r.archival_authorized -or $r.human_review_requirement -or -not $r.source_exact_verified -or -not $r.r2_key -or $r.size_bytes -gt 150000000) { throw 'Object eligibility gate failed' }
    if ($r.container_type -eq 'PDF' -and $r.qa.representative_visual_qa -ne 'passed_agent_visual_inspection_opening_middle_final') { throw 'Visual QA missing' }
    $file=Get-Item -LiteralPath $r.staged_path
    if ($file.Length -ne $r.size_bytes -or (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $r.expected_sha256) { throw 'Staged identity changed' }
    $live=Read-Guard
    $existing=@($live.objects | Where-Object { $_.key.ToLowerInvariant() -eq $r.r2_key.ToLowerInvariant() })
    $action='already_completed_after_interruption'
    if ($existing.Count) {
      if ($existing.Count -ne 1 -or $existing[0].key -cne $r.r2_key -or $existing[0].size_bytes -ne $r.size_bytes -or -not $r.PSObject.Properties['upload_intent']) { throw 'Existing-object collision; no overwrite allowed' }
      if ($r.outcome -eq 'archive_complete' -and ($r.classification -ne 'unchanged_City_original' -or $r.PSObject.Properties['inventory_reconciled'])) {continue}
    } else {
      if ($r.outcome -eq 'archive_complete') { throw 'Previously verified object disappeared' }
      if (@($live.objects | Where-Object size_bytes -eq $r.size_bytes).Count) { throw 'Unresolved same-size live object' }
      if ($live.total_bytes+$r.size_bytes -gt 10000000000) {throw 'Storage ceiling reached'}
      Set-Field $r 'upload_intent' ([pscustomobject]@{id=$r.id;r2_key=$r.r2_key;key_was_absent=$true;started_at=(Get-Date).ToUniversalTime().ToString('o')})
      Save-Campaign
      $args=@{SourcePath=$r.staged_path;ObjectKey=$r.r2_key}
      if ($r.size_bytes -gt 100000000) { $args.MaxObjectBytes=150000000 }
      $upload=@(& "$PSScriptRoot/../upload-r2-document.ps1" @args)
      if (@($upload | Where-Object { $_.PSObject.Properties['R2Metadata'] }).Count -ne 1) {throw 'Uploader metadata missing'}
      $action='uploaded_now';Set-Field $r 'upload_action' $action
      $r.outcome='uploaded_pending_public_verification';Save-Campaign
    }
    $public=& "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $r.staged_path -PublicUrl ([uri]('https://files.abqinfo.com/'+$r.r2_key))
    if (-not $public.byte_identical -or $public.size_bytes -ne $r.size_bytes -or $public.checksum_sha256 -cne $r.expected_sha256) { throw 'Exact public-byte mismatch' }
    Set-Field $r 'public_verification' $public
    Set-Field $r 'upload_action' $action
    $r.outcome='archive_complete';Save-Campaign
    $live=Read-Guard; $object=@($live.objects | Where-Object { $_.key -ceq $r.r2_key })[0]
    Set-Field $r 'r2_etag' $object.etag;Set-Field $r 'r2_last_modified' $object.last_modified
    Copy-Item -LiteralPath $guardPath -Destination project-state/r2-inventory.json -Force
    Update-Inventory $r $object
    Save-Campaign
    Write-Host "Verified and saved: $($r.id) $($r.size_bytes) bytes"
  } catch {
    Set-Field $r 'operation_error' ([string]$_.Exception.Message)
    if ($r.outcome -ne 'archive_complete') { $r.outcome='upload_or_public_verification_failed' }
    Save-Campaign; Write-Warning "Isolated record failure $($r.id): $($_.Exception.Message)"
  }
}
$live=Read-Guard
Set-Field $d 'latest_r2' ([pscustomobject]@{object_count=$live.object_count;total_bytes=$live.total_bytes;verified_at=$live.generated_at})
$d.state='campaign_phase_'+$Phase+'_attempted';Save-Campaign
