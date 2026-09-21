[CmdletBinding()]
param(
  [string]$PreparationPath = 'project-state/discovery/transit-openspace-nmdot-sustainability-archive-preparation-2026-09-20.json',
  [string]$VerificationPath = 'project-state/discovery/abq-ride-historic-transit-archive-public-byte-verification-2026-09-21.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ids = @('src-6220c942e21cbc67','src-cd76ed2642c5bc5b','src-e42bbc888a2b6931','src-ee0aec5b78f6ec86','src-54391dbd27e5d212','src-4092005fa5d61b38','src-e28e38dabfbdb2e2','src-2dbbf587fead4146','src-12207bd87008378c')

function Write-Utf8Json([object]$Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  [IO.File]::WriteAllText($temporaryPath, ($Value | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}

$preparation = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$verification = Get-Content -Raw -Encoding UTF8 -LiteralPath $VerificationPath | ConvertFrom-Json
$r2 = Get-Content -Raw -Encoding UTF8 -LiteralPath $R2InventoryPath | ConvertFrom-Json
$records = @($preparation.records | Where-Object { $_.id -in $ids })
if ($records.Count -ne 9) { throw 'Preparation artifact does not contain exactly the authorized nine records.' }

$preflightById = @{}
foreach ($preflight in @($verification.preflight)) { $preflightById[[string]$preflight.id] = $preflight }
$resultById = @{}
foreach ($result in @($verification.results)) { $resultById[[string]$result.id] = $result }
$publicResults = @()

foreach ($record in $records) {
  $id = [string]$record.id
  $preflight = $preflightById[$id]
  $result = $resultById[$id]
  if ($null -eq $preflight -or $null -eq $result) { throw "Missing preflight or result for $id." }
  $file = Get-Item -LiteralPath $preflight.local_path
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($file.Length -ne [int64]$record.source_evidence.size_bytes -or $hash -ne [string]$record.source_evidence.sha256) { throw "Staged source bytes no longer match saved evidence for $id." }
  $object = @($r2.objects | Where-Object key -eq $record.archive_preparation.proposed_r2_key)
  if ($object.Count -ne 1 -or [int64]$object[0].size_bytes -ne $file.Length) { throw "Reconciled R2 inventory does not contain the expected object for $id." }
  $public = & "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $file.FullName -PublicUrl ([uri]$result.public_url)
  if (-not $public.byte_identical) { throw "Public byte verification failed for $id." }
  $publicResults += $public
  $result.source_byte_verification = 'passed'
  $result.upload = 'passed'
  $result.public_byte_verification = 'passed'
  $result.failure = $null
  $result | Add-Member -NotePropertyName upload_provenance -NotePropertyValue 'Manual host-session upload using the normal abqinfo-r2-upload Windows credential; exact staged original preserved unchanged.' -Force
  $result | Add-Member -NotePropertyName public_size_bytes -NotePropertyValue ([int64]$public.size_bytes) -Force
  $result | Add-Member -NotePropertyName public_checksum_sha256 -NotePropertyValue ([string]$public.checksum_sha256) -Force
  $result | Add-Member -NotePropertyName public_verified_at -NotePropertyValue ([string]$public.verified_at) -Force
  if ($record.source_evidence.container -eq 'OLE2') {
    $result.visual_render_inspection = 'passed: rendered with Microsoft Word COM in the normal interactive host session; human visual inspection confirmed readable complete pages with no obvious corruption, missing content, or malformed layout.'
  }
}

$verification.state = 'complete_all_9_uploaded_public_byte_verified_and_r2_inventory_reconciled'
$verification.recorded_at = (Get-Date).ToUniversalTime().ToString('o')
$verification | Add-Member -NotePropertyName completed_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
$verification.visual_render.status = 'passed_all_three_human_inspected'
$verification.visual_render.failure = $null
$verification | Add-Member -NotePropertyName manual_host_operations -NotePropertyValue ([pscustomobject][ordered]@{
  legacy_word_rendering = 'All three unchanged Word originals rendered with Word COM and were visually inspected by the user in the normal interactive host session.'
  r2_upload_and_initial_public_check = 'All nine unchanged staged originals were uploaded through the normal credential path and verified in the normal interactive host session.'
}) -Force
$verification.summary.source_byte_verified = 9
$verification.summary.uploaded = 9
$verification.summary.public_byte_verified = 9
$verification.summary.failures = 0
$verification | Add-Member -NotePropertyName r2_inventory_accounting -NotePropertyValue ([pscustomobject][ordered]@{object_count=[int]$r2.object_count;total_bytes=[int64]$r2.total_bytes;added_or_reconciled=9;inventory_path=$R2InventoryPath}) -Force
$verification.r2_reconciliation = [pscustomobject][ordered]@{state='complete_live_inventory_reconciled';generated_at=$r2.generated_at;object_count=[int]$r2.object_count;total_bytes=[int64]$r2.total_bytes;added_objects=9;added_bytes=[int64](($records | Measure-Object { [int64]$_.source_evidence.size_bytes } -Sum).Sum)}
Write-Utf8Json $verification $VerificationPath

foreach ($record in $records) {
  $id = [string]$record.id
  $r2Object = @($r2.objects | Where-Object key -eq $record.archive_preparation.proposed_r2_key)[0]
  $current = (Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json).candidates | Where-Object id -eq $id
  if (@($current).Count -ne 1) { throw "Expected one inventory candidate for $id." }
  $notes = @($current.processing_notes) + @('ABQ RIDE historic-transit archive stage: unchanged authoritative original uploaded to prepared R2 key and independently verified by exact public size and SHA-256.') | Sort-Object -Unique
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -InventoryPath $InventoryPath -Set @{
    status = 'placement assigned'; r2_key = [string]$record.archive_preparation.proposed_r2_key; r2_url = "https://files.abqinfo.com/$($record.archive_preparation.proposed_r2_key)"
    r2_etag = [string]$r2Object.etag; r2_last_modified = [string]$r2Object.last_modified
    source_url = [string]$record.source_evidence.provenance_url; direct_file_url = [string]$record.source_evidence.verified_download_url
    proposed_canonical_page = [string]$record.archive_preparation.canonical_page
    validation_status = 'passed: authoritative source and unchanged local original matched saved size/SHA-256; prepared R2 object and exact public-byte download verified; public-content implementation remains separately authorized'
    provenance_status = 'authoritative City source URL retained; unchanged original R2 archive and exact public byte verification completed'
    processing_notes = $notes
  } | Out-Null
}

[pscustomobject]@{source_byte_verified=9;uploaded=9;public_byte_verified=9;object_count=$r2.object_count;total_bytes=$r2.total_bytes}|ConvertTo-Json -Compress
