[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$duplicateId = 'src-d9bf34830a9467e2'
$canonicalId = 'src-28418cab91a745a6'
$size = [int64]8719030
$sha = 'c2081c6cbc60b029c2b558a73ad975b429b03e89cc1837c393f8b5c30191ae19'
$artifactPath = 'project-state/discovery/planning-documents-root-barelas-duplicate-reconciliation-2026-09-26.json'
$inventory = Get-Content project-state/master-inventory.json -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
$duplicate = @($inventory.candidates | Where-Object id -eq $duplicateId)[0]
$canonical = @($inventory.candidates | Where-Object id -eq $canonicalId)[0]
if ($duplicate.status -notin @('approved for addition','duplicate') -or $canonical.status -ne 'validated') { throw 'Unexpected lifecycle state.' }
foreach ($row in @($duplicate,$canonical)) {
  if ($row.size_bytes -ne $size -or $row.checksum_sha256 -ne $sha) { throw 'Inventory exact identity mismatch.' }
}
$prep = Get-Content project-state/discovery/planning-documents-root-archive-preparation-2026-09-25.json -Raw -Encoding UTF8 | ConvertFrom-Json
$prepared = @($prep.records | Where-Object id -eq $duplicateId)[0]
if ($prepared.size_bytes -ne $size -or $prepared.sha256 -ne $sha -or $prepared.page_count -ne 150) { throw 'Preparation identity mismatch.' }
$staged = Get-Item -LiteralPath $prepared.staged_local_path
if ($staged.Length -ne $size -or (Get-FileHash -LiteralPath $staged.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sha) { throw 'Staged identity mismatch.' }
$publicArtifact = 'project-state/discovery/planning-udd-r2-public-validation-2026-09-12.json'
$public = Get-Content $publicArtifact -Raw -Encoding UTF8 | ConvertFrom-Json
$publicRecord = @($public.results | Where-Object id -eq $canonicalId)[0]
if (-not $publicRecord.byte_identical -or $publicRecord.error -or $publicRecord.size_bytes -ne $size -or $publicRecord.checksum_sha256 -ne $sha -or $publicRecord.public_url -ne $canonical.r2_url) { throw 'Canonical exact-public-byte evidence failed.' }
$saved = Get-Content project-state/r2-inventory.json -Raw -Encoding UTF8 | ConvertFrom-Json
$live = Get-Content tmp/planning-documents-root-live-r2-preflight-2026-09-26.json -Raw -Encoding UTF8 | ConvertFrom-Json
$savedObject = @($saved.objects | Where-Object key -eq $canonical.r2_key)
$liveObject = @($live.objects | Where-Object key -eq $canonical.r2_key)
if ($savedObject.Count -ne 1 -or $liveObject.Count -ne 1 -or $liveObject[0].size_bytes -ne $size -or $savedObject[0].etag -ne $liveObject[0].etag -or $canonical.r2_etag -ne $liveObject[0].etag) { throw 'Canonical live object identity failed.' }
$canonicalBefore = $canonical | ConvertTo-Json -Depth 30 -Compress
$note = "Planning documents-root exact-duplicate reconciliation 2026-09-26: this unchanged 8,719,030-byte / 150-page source delivery has SHA-256 $sha, identical to validated canonical $canonicalId and its exact-public-byte verified archive. Preserve the Planning-root URLs and historical review; no second archive object or standalone public entry is appropriate. Evidence: $artifactPath."
$evidence = [ordered]@{
  schema_version=1; artifact_type='planning_documents_root_exact_duplicate_reconciliation'; recorded_at=(Get-Date).ToUniversalTime().ToString('o'); date_basis='UTC execution date'; duplicate_id=$duplicateId; canonical_id=$canonicalId
  duplicate_source_url=$duplicate.source_url; duplicate_direct_file_url=$duplicate.direct_file_url; duplicate_source_title=$duplicate.title
  canonical_source_url=$canonical.source_url; canonical_direct_file_url=$canonical.direct_file_url; canonical_source_title=$canonical.title
  size_bytes=$size; checksum_sha256=$sha; page_count=150; staged_duplicate_path=$prepared.staged_local_path
  canonical_r2_key=$canonical.r2_key; canonical_r2_url=$canonical.r2_url; canonical_current_status=$canonical.status
  exact_public_byte_evidence=[ordered]@{artifact=$publicArtifact;record=$publicRecord;new_public_GET_performed=$false}
  live_object_evidence=[ordered]@{listing_generated_at=$live.generated_at;object=$liveObject[0];same_saved_and_live_etag=$true}
  same_substantive_identity='Exact size and SHA-256 establish one byte-identical 150-page original, including the same bound legislation; source-path provenance duplication, not distinct editions.'
  discovery_explanation='The historical directory-family decision did not capture this cross-cluster alias. Archive preparation compared exact source hashes across the current inventory and found the already validated UDD/MRA canonical row. The historical decision remains unchanged.'
  historical_decision='project-state/discovery/planning-documents-root-residual-decision-2026-09-20.json'
  prior_disposition='approved for addition'; resulting_disposition='duplicate'; canonical_record_changed=$false; no_new_r2_object_created=$true; r2_mutation=$false; visitor_visible_content_changed=$false
  state='exact_identity_verified_pending_inventory_transition'
}
if (Test-Path $artifactPath) {
  $existing = Get-Content $artifactPath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($duplicate.status -eq 'duplicate' -and $existing.state -eq 'reconciled_exact_duplicate') { Write-Output 'Already reconciled; no changes.'; return }
}
$evidence | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $artifactPath -Encoding utf8
$notes = @($duplicate.processing_notes)
if ($note -notin $notes) { $notes += $note }
$successors = @($duplicate.cited_successors)
if ($canonical.direct_file_url -notin $successors) { $successors += $canonical.direct_file_url }
& "$PSScriptRoot/Update-Candidate.ps1" -Id $duplicateId -Set @{
  status='duplicate'; cited_successors=$successors; processing_notes=$notes; local_path=[string]$prepared.staged_local_path
  exclusion_reason="Byte-identical source-path delivery of validated canonical $canonicalId; no second archive object or standalone public entry."
  validation_status="duplicate: exact saved/prepared size and SHA-256 match canonical $canonicalId; canonical R2 object remains exact-public-byte verified"
} | Out-Null
$after = Get-Content project-state/master-inventory.json -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
$canonicalAfter = @($after.candidates | Where-Object id -eq $canonicalId)[0] | ConvertTo-Json -Depth 30 -Compress
if ($canonicalAfter -ne $canonicalBefore) { throw 'Canonical row unexpectedly changed.' }
$evidence.state='reconciled_exact_duplicate'
$evidence.inventory_counts_after=$after.counts
$evidence | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $artifactPath -Encoding utf8
Write-Output "Reconciled $duplicateId to duplicate of $canonicalId; canonical row unchanged."
