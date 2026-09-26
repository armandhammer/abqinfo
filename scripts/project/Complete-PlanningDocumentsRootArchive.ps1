[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$manifestPath='project-state/discovery/planning-documents-root-r2-upload-preflight-2026-09-26.json'
$evidencePath='project-state/discovery/planning-documents-root-archive-public-byte-verification-2026-09-26.json'
$livePath='tmp/planning-documents-root-live-postupload-2026-09-26.json'
$manifest=Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$evidence=Get-Content $evidencePath -Raw -Encoding UTF8 | ConvertFrom-Json
$prepared=Get-Content project-state/discovery/planning-documents-root-archive-preparation-2026-09-25.json -Raw -Encoding UTF8 | ConvertFrom-Json
$live=Get-Content $livePath -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
function Save-Evidence {
  $temp="$evidencePath.tmp-$PID"
  [IO.File]::WriteAllText([IO.Path]::GetFullPath($temp),($evidence | ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temp -Destination $evidencePath -Force
}
if ($evidence.state -notin @('complete_all_12_public_byte_verified','complete_all_12_public_byte_verified_and_inventory_reconciled') -or $evidence.results.Count -ne 12 -or $evidence.summary.public_byte_verified -ne 12 -or $evidence.summary.verified_bytes -ne 122249326 -or $evidence.summary.verified_pages -ne 928) { throw 'All twelve exact-public-byte verifications are required before reconciliation.' }
if (-not $evidence.accounting.pre_existing_objects_unchanged -or $evidence.accounting.unexpected_objects_added -or $evidence.visitor_visible_content_changed) { throw 'Archive accounting or content safeguards failed.' }
if ($live.object_count -ne $evidence.after_r2.object_count -or $live.total_bytes -ne $evidence.after_r2.total_bytes) { throw 'Live R2 accounting differs from evidence.' }
foreach ($record in $manifest.records) {
  $result=@($evidence.results | Where-Object id -eq $record.id)
  $object=@($live.objects | Where-Object { $_.key -ceq $record.proposed_r2_key })
  if ($result.Count -ne 1 -or $object.Count -ne 1) { throw "Missing result or live object: $($record.id)" }
  $result=$result[0]; $object=$object[0]
  if (-not $result.byte_identical -or $result.public_size_bytes -ne $record.size_bytes -or $result.public_checksum_sha256 -cne $record.checksum_sha256 -or $result.r2_key -cne $record.proposed_r2_key -or $result.public_url -cne $record.expected_public_archive_url -or $object.size_bytes -ne $record.size_bytes) { throw "Exact archive identity failed: $($record.id)" }
}
Copy-Item -LiteralPath $livePath -Destination project-state/r2-inventory.json -Force
$saved=Get-Content project-state/r2-inventory.json -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
if (($saved.objects | ConvertTo-Json -Depth 8 -Compress) -cne ($live.objects | ConvertTo-Json -Depth 8 -Compress)) { throw 'Saved and live R2 objects do not agree exactly.' }
if (-not ($evidence.PSObject.Properties.Name -contains 'inventory_reconciled_ids')) { $evidence | Add-Member -NotePropertyName inventory_reconciled_ids -NotePropertyValue @() }
foreach ($record in $manifest.records) {
  $inventory=Get-Content project-state/master-inventory.json -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
  $row=@($inventory.candidates | Where-Object id -eq $record.id)[0]
  $object=@($live.objects | Where-Object { $_.key -ceq $record.proposed_r2_key })[0]
  $plan=@($prepared.records | Where-Object id -eq $record.id)[0]
  if ($row.status -notin @('approved for addition','placement assigned') -or $row.size_bytes -ne $record.size_bytes -or $row.checksum_sha256 -cne $record.checksum_sha256 -or $row.direct_file_url -cne $record.direct_file_url -or $row.proposed_canonical_page -cne $plan.proposed_canonical_page) { throw "Inventory identity or presentation plan changed: $($record.id)" }
  $note="Planning archive 2026-09-26: unchanged authoritative original uploaded to $($record.proposed_r2_key); fresh full public GET exactly matched $($record.size_bytes) bytes and SHA-256 $($record.checksum_sha256). Future canonical page $($plan.proposed_canonical_page), section $($plan.proposed_future_section). Presentation: $($plan.presentation_treatment). Caveat: $($plan.visitor_caveat). No Hugo implementation occurred; manual-review content PR remains a later stage. Evidence: $evidencePath."
  $notes=@($row.processing_notes); if ($note -notin $notes) { $notes += $note }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $record.id -Set @{
    status='placement assigned';r2_key=$record.proposed_r2_key;r2_url=$record.expected_public_archive_url;r2_etag=$object.etag;r2_last_modified=$object.last_modified
    local_path=$record.staged_path;proposed_canonical_page=$plan.proposed_canonical_page;processing_notes=$notes
    validation_status='authoritative source and public R2 bytes match exact size and SHA-256; placement planned; no visitor-visible implementation'
  } | Out-Null
  if ($record.id -notin $evidence.inventory_reconciled_ids) { $evidence.inventory_reconciled_ids += $record.id }
  Save-Evidence
}
$evidence | Add-Member -NotePropertyName r2_inventory_accounting -NotePropertyValue ([pscustomobject]@{saved_object_count=$saved.object_count;saved_total_bytes=$saved.total_bytes;live_object_count=$live.object_count;live_total_bytes=$live.total_bytes;saved_live_key_size_etag_match=$true;records_updated=12;inventory_status='placement assigned'}) -Force
$evidence.state='complete_all_12_public_byte_verified_and_inventory_reconciled'
$evidence | Add-Member -NotePropertyName completed_at -NotePropertyValue (Get-Date).ToUniversalTime().ToString('o') -Force
Save-Evidence
$evidence.r2_inventory_accounting | ConvertTo-Json -Compress
