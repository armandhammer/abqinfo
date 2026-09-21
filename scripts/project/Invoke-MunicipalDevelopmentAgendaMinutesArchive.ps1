[CmdletBinding()]
param(
  [string]$PreparationPath = 'project-state/discovery/municipaldevelopment-agenda-minutes-archive-preparation-2026-09-20.json',
  [string]$PrioritizationPath = 'project-state/discovery/approved-inventory-backlog-prioritization-2026-09-21.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/discovery/municipaldevelopment-agenda-minutes-archive-public-byte-verification-2026-09-21.json',
  [string]$SourceDirectory = 'research/staging/municipaldevelopment-agenda-minutes-archive-2026-09-21',
  [int64]$MaximumObjectBytes = 100000000,
  [int64]$MaximumProjectedR2Bytes = 10000000000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Artifact([object]$Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  [IO.File]::WriteAllText($temporaryPath, ($Value | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}

function Get-SafeError([System.Management.Automation.ErrorRecord]$ErrorRecord) {
  return [string]$ErrorRecord.Exception.Message
}

$preparation = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$prioritization = Get-Content -Raw -Encoding UTF8 -LiteralPath $PrioritizationPath | ConvertFrom-Json
$selected = @($prioritization.family_groups | Where-Object ranking -eq 1)
if ($selected.Count -ne 1) { throw 'Expected exactly one rank-1 selected backlog family.' }
$selectedIds = @($selected[0].candidate_ids)
$records = @($preparation.records)
if ($records.Count -ne 18 -or ((@($records.id | Sort-Object) -join ',') -ne (@($selectedIds | Sort-Object) -join ','))) {
  throw 'Archive-preparation records do not exactly match the selected 18-record backlog batch.'
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$preflight = @()
foreach ($record in $records) {
  $candidate = @($inventory.candidates | Where-Object id -eq $record.id)
  if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for $($record.id)." }
  $failure = $null
  $actualSize = $null
  $actualHash = $null
  $sourceAcquisition = 'existing saved local original'
  $sourcePath = $candidate[0].local_path
  try {
    if (-not $sourcePath -or -not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
      New-Item -ItemType Directory -Force -Path $SourceDirectory | Out-Null
      $sourcePath = Join-Path $SourceDirectory ($record.id + '.pdf')
      Invoke-WebRequest -Uri $record.direct_original_file_url -OutFile $sourcePath -UseBasicParsing -MaximumRedirection 10 -TimeoutSec 180 -Headers @{ 'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ABQInfo-Archive/1.0'; 'Cache-Control' = 'no-cache' }
      $sourceAcquisition = 'authoritative City source downloaded for exact-byte verification'
    }
    $file = Get-Item -LiteralPath $sourcePath
    $actualSize = [int64]$file.Length
    $actualHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualSize -ne [int64]$record.size_bytes) { throw "Saved source size mismatch: expected $($record.size_bytes); got $actualSize." }
    if ($actualHash -ne [string]$record.checksum_sha256) { throw "Saved source SHA-256 mismatch: expected $($record.checksum_sha256); got $actualHash." }
    if ($candidate[0].size_bytes -ne $record.size_bytes -or $candidate[0].checksum_sha256 -ne $record.checksum_sha256) { throw 'Inventory source metadata differs from the prepared record.' }
    $alreadyArchived = $candidate[0].status -eq 'placement assigned' -and $candidate[0].r2_key -eq $record.proposed_r2_key -and $candidate[0].r2_url -eq "https://files.abqinfo.com/$($record.proposed_r2_key)"
    if ($candidate[0].status -ne 'approved for addition' -and -not $alreadyArchived) { throw "Inventory status must be 'approved for addition' or this record's exact previously verified archive assignment; got '$($candidate[0].status)'." }
  } catch { $failure = Get-SafeError $_ }
  $preflight += [pscustomobject][ordered]@{
    id = $record.id; local_path = $sourcePath; source_acquisition = $sourceAcquisition; expected_size_bytes = [int64]$record.size_bytes
    expected_checksum_sha256 = $record.checksum_sha256; actual_size_bytes = $actualSize; actual_checksum_sha256 = $actualHash
    source_byte_verification = if ($failure) { 'failed' } else { 'passed' }; failure = $failure
  }
}

$artifact = [ordered]@{
  schema_version = 1
  artifact_type = 'municipal_development_agenda_minutes_archive_public_byte_verification'
  recorded_at = (Get-Date).ToUniversalTime().ToString('o')
  state = 'running'
  scope = [ordered]@{ preparation_artifact = $PreparationPath; prioritization_artifact = $PrioritizationPath; candidate_ids = $selectedIds; authorized_action = 'unchanged R2 upload and public byte verification only'; public_content_changed = $false; merge_or_deploy = $false }
  preflight = $preflight
  results = @()
  summary = [ordered]@{ selected_records = 18; source_byte_verified = @($preflight | Where-Object source_byte_verification -eq 'passed').Count; uploaded = 0; public_byte_verified = 0; failures = @($preflight | Where-Object source_byte_verification -eq 'failed').Count; added_bytes = 0 }
}
Write-Artifact $artifact $OutputPath

foreach ($record in $records) {
  $check = @($preflight | Where-Object id -eq $record.id)[0]
  $result = [ordered]@{
    id = $record.id; title = $record.accepted_title; date = $record.date; authoritative_source_url = $record.authoritative_source_url
    direct_original_file_url = $record.direct_original_file_url; r2_key = $record.proposed_r2_key; public_url = "https://files.abqinfo.com/$($record.proposed_r2_key)"
    expected_size_bytes = [int64]$record.size_bytes; expected_checksum_sha256 = $record.checksum_sha256
    missing_minutes_label = $record.missing_minutes_label; meeting_occurrence_caveat = $record.meeting_occurrence_caveat
    source_byte_verification = $check.source_byte_verification; upload = 'not_attempted'; public_byte_verification = 'not_attempted'; failure = $check.failure
  }
  if ($check.source_byte_verification -eq 'passed') {
    try {
      $public = $null
      $metadata = $null
      # Resume safely after an interrupted local inventory update: a public
      # byte-identical object is the same already-uploaded original, never an
      # invitation to overwrite the key.
      try {
        $public = & "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $check.local_path -PublicUrl ([uri]$result.public_url)
        $head = Invoke-WebRequest -Method Head -Uri $result.public_url -UseBasicParsing -Headers @{ 'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ABQInfo-Archive/1.0' }
        $metadata = [pscustomobject]@{ ETag = [string](@($head.Headers.ETag)[0]); LastModified = [string](@($head.Headers.'Last-Modified')[0]) }
        $result.upload = 'passed'
        $result.upload_provenance = 'existing public byte-identical object from the interrupted authorized archive run'
      } catch {
        $public = $null
      }
      if ($null -eq $public) {
        $uploadOutput = @(& "$PSScriptRoot/../upload-r2-document.ps1" -SourcePath $check.local_path -ObjectKey $record.proposed_r2_key -MaxObjectBytes $MaximumObjectBytes -MaxProjectedStorageBytes $MaximumProjectedR2Bytes)
        $upload = @($uploadOutput | Where-Object { $_.PSObject.Properties.Name -contains 'R2Metadata' } | Select-Object -Last 1)
        if ($upload.Count -ne 1) { throw 'Uploader did not return R2 metadata.' }
        $result.upload = 'passed'
        $result.upload_provenance = 'uploaded during this authorized archive run'
        $metadata = $upload[0].R2Metadata | ConvertFrom-Json
        $public = & "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $check.local_path -PublicUrl ([uri]$result.public_url)
      }
      if (-not $public.byte_identical -or $public.size_bytes -ne $record.size_bytes -or $public.checksum_sha256 -ne $record.checksum_sha256) { throw 'Public object did not match the prepared source bytes.' }
      $result.public_byte_verification = 'passed'
      $result.public_size_bytes = [int64]$public.size_bytes
      $result.public_checksum_sha256 = $public.checksum_sha256
      $result.public_verified_at = $public.verified_at
      & "$PSScriptRoot/Update-Candidate.ps1" -Id $record.id -Set @{
        status = 'placement assigned'; r2_key = $record.proposed_r2_key; r2_url = $result.public_url; r2_etag = ([string]$metadata.ETag).Trim('"'); r2_last_modified = [string]$metadata.LastModified
        validation_status = 'local source and public R2 size and SHA-256 passed; Hugo/public-content implementation remains separately authorized'
        processing_notes = @($record.remaining_gates) + @('Original source file uploaded unchanged; public R2 download matched the saved exact size and SHA-256.')
      } -InventoryPath $InventoryPath | Out-Null
    } catch {
      $result.failure = Get-SafeError $_
      if ($result.upload -eq 'not_attempted') { $result.upload = 'failed' } elseif ($result.public_byte_verification -eq 'not_attempted') { $result.public_byte_verification = 'failed' }
    }
  }
  $artifact.results += [pscustomobject]$result
  $artifact.summary.uploaded = @($artifact.results | Where-Object upload -eq 'passed').Count
  $artifact.summary.public_byte_verified = @($artifact.results | Where-Object public_byte_verification -eq 'passed').Count
  $artifact.summary.failures = @($artifact.results | Where-Object failure).Count
  [int64]$verifiedBytes = 0
  foreach ($verified in @($artifact.results | Where-Object public_byte_verification -eq 'passed')) { $verifiedBytes += [int64]$verified.expected_size_bytes }
  $artifact.summary.added_bytes = $verifiedBytes
  Write-Artifact $artifact $OutputPath
}
$artifact.state = if ($artifact.summary.failures -eq 0 -and $artifact.summary.public_byte_verified -eq 18) { 'complete_all_18_uploaded_and_public_byte_verified' } else { 'complete_with_failures_unadvanced_records_retained' }
$artifact.completed_at = (Get-Date).ToUniversalTime().ToString('o')
Write-Artifact $artifact $OutputPath
$artifact.summary | ConvertTo-Json -Compress
