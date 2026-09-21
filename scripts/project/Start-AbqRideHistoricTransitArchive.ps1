[CmdletBinding()]
param(
  [string]$PreparationPath = 'project-state/discovery/transit-openspace-nmdot-sustainability-archive-preparation-2026-09-20.json',
  [string]$VerificationPath = 'project-state/discovery/abq-ride-historic-transit-archive-public-byte-verification-2026-09-21.json',
  [string]$StagingDirectory = 'research/staging/abq-ride-historic-transit-archive-2026-09-21'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ids = @(
  'src-6220c942e21cbc67', 'src-cd76ed2642c5bc5b', 'src-e42bbc888a2b6931',
  'src-ee0aec5b78f6ec86', 'src-54391dbd27e5d212', 'src-4092005fa5d61b38',
  'src-e28e38dabfbdb2e2', 'src-2dbbf587fead4146', 'src-12207bd87008378c'
)

function Write-Utf8Json([object]$Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  [IO.File]::WriteAllText($temporaryPath, ($Value | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}

$preparation = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$records = @($preparation.records | Where-Object { $_.id -in $ids })
if ($records.Count -ne 9 -or ((@($records.id | Sort-Object) -join ',') -ne (@($ids | Sort-Object) -join ','))) { throw 'Preparation artifact does not contain exactly the authorized nine-record ABQ RIDE set.' }

New-Item -ItemType Directory -Force -Path $StagingDirectory | Out-Null
$preflight = @()
foreach ($record in $records) {
  $expectedSize = [int64]$record.source_evidence.size_bytes
  $expectedHash = [string]$record.source_evidence.sha256
  $fileName = [string]$record.archive_preparation.proposed_filename
  $localPath = Join-Path $StagingDirectory $fileName
  $failure = $null
  $actualSize = $null
  $actualHash = $null
  try {
    Invoke-WebRequest -Uri ([string]$record.source_evidence.verified_download_url) -OutFile $localPath -UseBasicParsing -TimeoutSec 180 -Headers @{ 'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ABQInfo-archive-verification/1.0' }
    $file = Get-Item -LiteralPath $localPath
    $actualSize = [int64]$file.Length
    $actualHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualSize -ne $expectedSize -or $actualHash -ne $expectedHash) { throw "Saved source evidence mismatch: expected $expectedSize/$expectedHash, got $actualSize/$actualHash." }
  } catch {
    $failure = $_.Exception.Message
  }
  $preflight += [pscustomobject][ordered]@{
    id = $record.id; title = $record.title; authoritative_source_url = $record.source_evidence.provenance_url
    direct_original_file_url = $record.source_evidence.verified_download_url; local_path = $localPath
    expected_size_bytes = $expectedSize; expected_checksum_sha256 = $expectedHash
    actual_size_bytes = $actualSize; actual_checksum_sha256 = $actualHash
    source_byte_verification = if ($failure) { 'failed' } else { 'passed' }; failure = $failure
  }
}

$legacyWordVisualStatus = 'passed'
$legacyWordVisualFailure = $null
try {
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.Quit()
  # This guard only establishes renderer availability.  A successful run must
  # still be accompanied by actual rendered-page review before upload.
  $legacyWordVisualStatus = 'renderer_available_manual_page_review_required'
} catch {
  $legacyWordVisualStatus = 'failed'
  $legacyWordVisualFailure = "Legacy Word visual rendering unavailable: $($_.Exception.Message)"
}

$results = foreach ($record in $records) {
  [pscustomobject][ordered]@{
    id = $record.id; title = $record.title; date = $record.inventory_update.date
    authoritative_source_url = $record.source_evidence.provenance_url; direct_original_file_url = $record.source_evidence.verified_download_url
    r2_key = $record.archive_preparation.proposed_r2_key; public_url = "https://files.abqinfo.com/$($record.archive_preparation.proposed_r2_key)"
    expected_size_bytes = [int64]$record.source_evidence.size_bytes; expected_checksum_sha256 = $record.source_evidence.sha256
    source_byte_verification = (@($preflight | Where-Object id -eq $record.id)[0]).source_byte_verification
    visual_render_inspection = if ($record.source_evidence.container -eq 'OLE2') { $legacyWordVisualStatus } else { 'not_required_by_current_stage_instruction' }
    upload = 'pending'; public_byte_verification = 'pending'; failure = if ($record.source_evidence.container -eq 'OLE2' -and $legacyWordVisualFailure) { $legacyWordVisualFailure } else { (@($preflight | Where-Object id -eq $record.id)[0]).failure }
  }
}

$artifact = [ordered]@{
  schema_version = 1; artifact_type = 'abq_ride_historic_transit_archive_public_byte_verification'; recorded_at = (Get-Date).ToUniversalTime().ToString('o')
  state = if ($legacyWordVisualStatus -eq 'failed') { 'blocked_legacy_word_visual_rendering_unavailable_no_r2_mutation' } else { 'preflight_complete_awaiting_legacy_word_visual_render_inspection' }; scope = [ordered]@{
    preparation_artifact = $PreparationPath; candidate_ids = $ids; authorized_action = 'unchanged R2 upload and public byte verification only'
    public_content_changed = $false; merge_or_deploy = $false
  }; preflight = $preflight; results = $results
  visual_render = [ordered]@{ legacy_word_records = @($records | Where-Object { $_.source_evidence.container -eq 'OLE2' }).Count; status = $legacyWordVisualStatus; failure = $legacyWordVisualFailure }
  summary = [ordered]@{ selected_records = 9; source_byte_verified = @($preflight | Where-Object source_byte_verification -eq 'passed').Count; uploaded = 0; public_byte_verified = 0; failures = @($results | Where-Object failure).Count }
}
Write-Utf8Json $artifact $VerificationPath
$artifact.summary | ConvertTo-Json -Compress
