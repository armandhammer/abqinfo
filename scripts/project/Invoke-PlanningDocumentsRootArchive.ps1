[CmdletBinding()]
param(
  [string]$ManifestPath='project-state/discovery/planning-documents-root-r2-upload-preflight-2026-09-26.json',
  [string]$EvidencePath='project-state/discovery/planning-documents-root-archive-public-byte-verification-2026-09-26.json',
  [string]$PreLivePath='tmp/planning-documents-root-live-preupload-2026-09-26.json',
  [string]$PostLivePath='tmp/planning-documents-root-live-postupload-2026-09-26.json'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
function Save-Evidence($Value) {
  $full=[IO.Path]::GetFullPath($EvidencePath); $temp="$full.tmp-$PID"
  [IO.File]::WriteAllText($temp,($Value | ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temp -Destination $full -Force
}
function Get-ManifestHash($Objects) {
  $lines=@($Objects | Sort-Object key | ForEach-Object { "$($_.key)`t$($_.size_bytes)`t$($_.etag)" })
  $bytes=[Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))
  $hash=[Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() } finally { $hash.Dispose() }
}
$ids=@('src-16b33375ffbddc62','src-1fa6ae851ddf282d','src-513fe9056bf9b34c','src-c54e59cd5c25282d','src-7de0f5803d442e8f','src-8740362a1b751e26','src-99fe2201b73355c4','src-afac0cf84867a22f','src-c87775c045d8acc4','src-eb0f4b39798d29df','src-f528ec2e0e955690','src-fb6e95610a43c7a4')
$authorizedKeys=@('city-data/demographics/cabq-planning-impact-area-chapter-01-executive-summary.pdf','city-data/demographics/cabq-planning-impact-area-chapter-05.pdf','city-data/demographics/cabq-planning-impact-area-chapter-08.pdf','city-data/demographics/cabq-planning-impact-area-chapter-03.pdf','public-works/city-facilities/cabq-electric-system-transmission-generation-facility-plan-2010-2020.pdf','development-land-use/zoning-ido/cabq-planned-communities-criteria-policy-element-1991.pdf','development-land-use/area-sector-plans/cabq-barelas-sector-development-plan-2008.pdf','public-works/parks-recreation/cabq-bosque-action-plan-rio-grande-valley-state-park-1993.pdf','development-land-use/zoning-ido/cabq-h1-historic-old-town-zone-design-guidelines-1998.pdf','development-land-use/zoning-ido/cabq-unser-boulevard-overlay-zone-complete-legislation.pdf','development-land-use/area-sector-plans/cabq-volcano-trails-sector-development-plan-enacted-package-2011.pdf','public-works/parks-recreation/cabq-major-public-open-space-facility-plan-1999.pdf')
$manifest=Get-Content $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$inventory=Get-Content project-state/master-inventory.json -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
$records=@($manifest.records)
if ($records.Count -ne 12 -or @($records.id | Select-Object -Unique).Count -ne 12 -or @($records.id | Where-Object { $_ -notin $ids }).Count) { throw 'Manifest is outside the authorized 12 IDs.' }
if (@($records.proposed_r2_key | Select-Object -Unique).Count -ne 12 -or @($records.proposed_r2_key | Where-Object { $_ -cnotin $authorizedKeys }).Count) { throw 'Manifest is outside the exact authorized keys.' }
[int64]$bytes=0; [int]$pages=0
foreach ($record in $records) {
  $row=@($inventory.candidates | Where-Object id -eq $record.id)[0]
  if ($row.status -notin @('approved for addition','placement assigned') -or $row.scope_assessment.final_scope_decision -ne 'passes_both_gates') { throw "Ineligible inventory state: $($record.id)" }
  $file=Get-Item -LiteralPath $record.staged_path
  $sha=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($file.Length -ne $record.size_bytes -or $sha -ne $record.checksum_sha256 -or $row.size_bytes -ne $record.size_bytes -or $row.checksum_sha256 -ne $sha -or $row.direct_file_url -cne $record.direct_file_url) { throw "Source identity mismatch: $($record.id)" }
  if ($record.expected_public_archive_url -cne "https://files.abqinfo.com/$($record.proposed_r2_key)" -or $file.Length -gt 100000000) { throw 'URL or normal object limit mismatch.' }
  $otherHashes=@($inventory.candidates | Where-Object { $_.id -ne $record.id -and $_.checksum_sha256 -eq $sha })
  if ($otherHashes.Count) { throw "Cross-inventory exact-hash collision: $($record.id)" }
  $bytes += $file.Length; $pages += [int]$record.page_count
}
if ($bytes -ne 122249326 -or $pages -ne 928) { throw 'Authorized aggregate differs.' }
$duplicate=@($inventory.candidates | Where-Object id -eq 'src-d9bf34830a9467e2')[0]
if ($duplicate.status -ne 'duplicate') { throw 'Barelas alias reconciliation lost.' }
& "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath $PreLivePath | Out-Null
$before=Get-Content $PreLivePath -Raw -Encoding UTF8 | ConvertFrom-Json
$prior=$null
if (Test-Path $EvidencePath) { $prior=Get-Content $EvidencePath -Raw -Encoding UTF8 | ConvertFrom-Json }
if ($null -ne $prior -and $prior.state -like 'complete_all_12_*') { throw 'Completed Planning archive evidence already exists; no mutation rerun.' }
$keys=@($records.proposed_r2_key)
$initialBefore=if ($prior) { $prior.before_r2 } else { [pscustomobject]@{object_count=$before.object_count;total_bytes=$before.total_bytes;generated_at=$before.generated_at} }
$initialHash=if ($prior) { $prior.pre_existing_manifest_sha256 } else { Get-ManifestHash @($before.objects) }
$priorObjects=@($before.objects | Where-Object { $_.key -cnotin $keys })
if ((Get-ManifestHash $priorObjects) -cne $initialHash) { throw 'Initial R2 listing has an unexpected authorized key or pre-existing manifest change; reconcile before mutation.' }
if ([int64]$initialBefore.total_bytes + $bytes -gt 10000000000) { throw 'Batch exceeds normal projected-storage limit.' }
$saved=Get-Content project-state/r2-inventory.json -Raw -Encoding UTF8 | ConvertFrom-Json
$baselineReference=[ordered]@{repository_commit='6f2f181a81e75dd95faac1c0bf2283176964824c';path='project-state/r2-inventory.json';exact_match_to_saved=(Get-ManifestHash @($saved.objects)) -ceq $initialHash}
if (-not $baselineReference.exact_match_to_saved -and -not $prior) {
  $missingOrChanged=@($saved.objects | Where-Object { $old=$_; @($before.objects | Where-Object { $_.key -ceq $old.key -and $_.size_bytes -eq $old.size_bytes -and $_.etag -ceq $old.etag }).Count -ne 1 })
  if ($missingOrChanged.Count) { throw 'Pre-upload baseline contains unexplained removals or changes.' }
  $freshBaselinePath='project-state/discovery/planning-documents-root-refreshed-r2-baseline-2026-09-26.json'
  Copy-Item $PreLivePath $freshBaselinePath
  $baselineReference.path=$freshBaselinePath
  $baselineReference.repository_commit=$null
}
$evidence=if ($prior) { $prior } else { [pscustomobject][ordered]@{
  schema_version=1;artifact_type='planning_documents_root_archive_public_byte_verification';started_at=(Get-Date).ToUniversalTime().ToString('o');state='running'
  owner_authorization='Owner explicitly authorized exactly the 12 unchanged originals and exact destination keys in the finalized 2026-09-26 preflight, followed by full public-byte verification. No content edits, overwrite, deletion, or Barelas duplicate upload authorized.'
  manifest_path=$ManifestPath;candidate_ids=@($records.id);max_object_bytes=100000000;max_projected_storage_bytes=10000000000
  before_r2=$initialBefore;pre_existing_manifest_sha256=$initialHash;baseline_reference=$baselineReference
  initial_pre_upload_listing_local_path=$PreLivePath;source_guard=[ordered]@{all_12_staged_sizes_hashes_verified=$true;aggregate_bytes=$bytes;aggregate_pages=$pages;cross_inventory_same_hash_collisions=0;credentials_accessible=$true}
  excluded_barelas_duplicate=$manifest.excluded_exact_duplicate;planning_impact_area_family=$manifest.planning_impact_area_family
  upload_intents=@();results=@();summary=[ordered]@{intended=12;uploaded_now=0;already_completed=0;public_byte_verified=0;verified_bytes=0;verified_pages=0}
  visitor_visible_content_changed=$false;r2_mutation=$false
} }
Save-Evidence $evidence
try {
  foreach ($record in $records) {
    & "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath 'tmp/planning-documents-root-per-object-guard-2026-09-26.json' | Out-Null
    $guard=Get-Content tmp/planning-documents-root-per-object-guard-2026-09-26.json -Raw -Encoding UTF8 | ConvertFrom-Json
    if ((Get-ManifestHash @($guard.objects | Where-Object { $_.key -cnotin $keys })) -cne $initialHash) { throw 'An object outside the authorized set changed during the run.' }
    $existing=@($guard.objects | Where-Object { $_.key.ToLowerInvariant() -eq $record.proposed_r2_key.ToLowerInvariant() })
    $alreadyRecorded=@($evidence.results | Where-Object id -eq $record.id)
    $action='already_completed_after_interruption'
    if ($existing.Count) {
      if ($existing.Count -ne 1 -or $existing[0].key -cne $record.proposed_r2_key -or $existing[0].size_bytes -ne $record.size_bytes) { throw "Existing R2 object collision: $($record.id)" }
      $public=& "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $record.staged_path -PublicUrl ([uri]$record.expected_public_archive_url)
      if (@($evidence.upload_intents | Where-Object id -eq $record.id).Count -ne 1) { throw "Unexpected existing object is not attributable to this batch: $($record.id)" }
    } else {
      if ($alreadyRecorded.Count) { throw "Previously verified object disappeared: $($record.id)" }
      if (@($guard.objects | Where-Object { $_.size_bytes -eq $record.size_bytes }).Count) { throw "Unresolved same-size archive object: $($record.id)" }
      if (@($evidence.upload_intents | Where-Object id -eq $record.id).Count -eq 0) {
        $evidence.upload_intents += [pscustomobject]@{id=$record.id;r2_key=$record.proposed_r2_key;started_at=(Get-Date).ToUniversalTime().ToString('o');key_was_absent=$true}
      }
      $evidence.r2_mutation=$true; Save-Evidence $evidence
      $upload=@(& "$PSScriptRoot/../upload-r2-document.ps1" -SourcePath $record.staged_path -ObjectKey $record.proposed_r2_key -MaxObjectBytes 100000000 -MaxProjectedStorageBytes 10000000000)
      if (@($upload | Where-Object { $_.PSObject.Properties.Name -contains 'R2Metadata' }).Count -ne 1) { throw "Uploader did not return metadata: $($record.id)" }
      $action='uploaded_now'
      $public=& "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $record.staged_path -PublicUrl ([uri]$record.expected_public_archive_url)
    }
    if (-not $public.byte_identical -or $public.size_bytes -ne $record.size_bytes -or $public.checksum_sha256 -cne $record.checksum_sha256 -or $public.public_url -cne $record.expected_public_archive_url) { throw "Public exact-byte check failed: $($record.id)" }
    if ($alreadyRecorded.Count -eq 0) {
      $evidence.results += [pscustomobject][ordered]@{id=$record.id;staged_path=$record.staged_path;authoritative_source_url=$record.direct_file_url;official_source_page_url=$record.source_url;size_bytes=[int64]$record.size_bytes;checksum_sha256=$record.checksum_sha256;page_count=[int]$record.page_count;r2_key=$record.proposed_r2_key;public_url=$record.expected_public_archive_url;upload_action=$action;http_public_get='passed';public_size_bytes=[int64]$public.size_bytes;public_checksum_sha256=$public.checksum_sha256;byte_identical=$true;verified_at=$public.verified_at}
    }
    $evidence.summary=[pscustomobject][ordered]@{intended=12;uploaded_now=@($evidence.results | Where-Object upload_action -eq 'uploaded_now').Count;already_completed=@($evidence.results | Where-Object upload_action -ne 'uploaded_now').Count;public_byte_verified=@($evidence.results).Count;verified_bytes=[int64](@($evidence.results | Measure-Object size_bytes -Sum)[0].Sum);verified_pages=[int](@($evidence.results | Measure-Object page_count -Sum)[0].Sum)}
    Save-Evidence $evidence
    Write-Host "Planning public bytes verified: $($evidence.summary.public_byte_verified)/12 $($record.id)"
  }
  & "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath $PostLivePath | Out-Null
  $after=Get-Content $PostLivePath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($after.object_count -ne [int]$initialBefore.object_count+12 -or $after.total_bytes -ne [int64]$initialBefore.total_bytes+$bytes) { throw 'Final count/byte delta differs from the authorized 12 objects.' }
  foreach ($record in $records) {
    $obj=@($after.objects | Where-Object { $_.key -ceq $record.proposed_r2_key })
    if ($obj.Count -ne 1 -or $obj[0].size_bytes -ne $record.size_bytes) { throw "Final object missing/mis-sized: $($record.id)" }
  }
  $afterHash=Get-ManifestHash @($after.objects | Where-Object { $_.key -cnotin $keys })
  if ($afterHash -cne $initialHash) { throw 'A pre-existing object was added, overwritten or deleted outside authorization.' }
  $evidence | Add-Member -NotePropertyName after_r2 -NotePropertyValue ([pscustomobject]@{object_count=$after.object_count;total_bytes=$after.total_bytes;generated_at=$after.generated_at;listing_local_path=$PostLivePath}) -Force
  $evidence | Add-Member -NotePropertyName accounting -NotePropertyValue ([pscustomobject]@{added_objects=12;added_bytes=$bytes;pages=928;pre_existing_objects_unchanged=$true;pre_existing_manifest_sha256_before=$initialHash;pre_existing_manifest_sha256_after=$afterHash;unexpected_objects_added=$false;overwrite_or_deletion_performed=$false}) -Force
  $evidence | Add-Member -NotePropertyName completed_at -NotePropertyValue (Get-Date).ToUniversalTime().ToString('o') -Force
  $evidence.state='complete_all_12_public_byte_verified';Save-Evidence $evidence
  $evidence.summary | ConvertTo-Json -Compress
} catch {
  $evidence.state='blocked_incomplete'
  $evidence | Add-Member -NotePropertyName blocker -NotePropertyValue ([string]$_.Exception.Message) -Force
  Save-Evidence $evidence;throw
}
