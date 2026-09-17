[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$ResearchDirectory = 'project-state/discovery',
  [string]$CheckpointRoot = 'research/staging/claude-consolidation-checkpoints',
  [string]$DownloadDirectory = 'research/staging/queue',
  [string]$DecisionsPath = 'project-state/discovery/dpm-annual-original-components-decisions-2026-09-13.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-WordCount([string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { return 0 }
  return @($Value -split '\s+' | Where-Object { $_ }).Count
}

$decisions = [System.Collections.Generic.List[object]]::new()
$componentCount = 0
$alreadyArchivedCount = 0

foreach ($year in 2014..2018) {
  $researchPath = Join-Path $ResearchDirectory "claude-consolidation-dpm-$year-2026-09-13.json"
  if (-not (Test-Path -LiteralPath $researchPath)) { throw "Missing completed Claude research result for ${year}: $researchPath" }
  $research = Get-Content -Raw -Encoding UTF8 -LiteralPath $researchPath | ConvertFrom-Json
  if ([string]$research.slice_id -ne "dpm-$year") { throw "Unexpected slice ID in $researchPath." }
  if ([string]$research.recommended_publication_form.form -ne 'consolidated_master') { throw "Research does not approve a consolidated master for $year." }

  $members = @($research.ordered_members | Where-Object { -not $_.PSObject.Properties['role'] -or [string]$_.role -eq 'minutes' -or [string]$_.role -eq 'agenda (approved minutes not located)' } | Sort-Object date)
  foreach ($member in $members) {
    $componentCount++
    $id = [string]$member.candidate_id
    $isAgenda = $member.PSObject.Properties['role'] -and [string]$member.role -eq 'agenda (approved minutes not located)'
    $checkpointPath = Join-Path $CheckpointRoot "dpm-$year/items/$id.json"
    if (-not (Test-Path -LiteralPath $checkpointPath)) { throw "Missing per-document checkpoint for $id." }
    $checkpoint = Get-Content -Raw -Encoding UTF8 -LiteralPath $checkpointPath | ConvertFrom-Json
    if ([string]$checkpoint.candidate_id -ne $id -or -not [bool]$checkpoint.official_source_checked -or -not [bool]$checkpoint.visual_inspection_completed) {
      throw "Incomplete provenance or visual-review checkpoint for $id."
    }
    & "$PSScriptRoot/Test-ContentPublicationQuality.ps1" -Decision ([pscustomobject]@{ id=$id; quality_assessment=$checkpoint.quality_assessment }) -Context "DPM annual component '$id'" | Out-Null

    $inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
    $matches = @($inventory.candidates | Where-Object id -eq $id)
    if ($matches.Count -ne 1) { throw "Expected one inventory record for $id; found $($matches.Count)." }
    $candidate = $matches[0]
    if ($candidate.r2_url) {
      $alreadyArchivedCount++
      continue
    }

    $localIsValid = $false
    if ($candidate.local_path -and (Test-Path -LiteralPath ([string]$candidate.local_path))) {
      $file = Get-Item -LiteralPath ([string]$candidate.local_path)
      $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
      $localIsValid = $file.Length -eq [int64]$checkpoint.size_bytes -and $hash -eq [string]$checkpoint.checksum_sha256
    }
    if (-not $localIsValid) {
      & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -Set @{
        source_url = [string]$checkpoint.official_source_url
        direct_file_url = [string]$checkpoint.official_source_url
        status = 'pending review'
      } -InventoryPath $InventoryPath | Out-Null
      & "$PSScriptRoot/Download-Candidate.ps1" -Id $id -InventoryPath $InventoryPath -DownloadDirectory $DownloadDirectory | Out-Null
    }

    $inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
    $candidate = @($inventory.candidates | Where-Object id -eq $id)[0]
    $file = Get-Item -LiteralPath ([string]$candidate.local_path)
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($file.Length -ne [int64]$checkpoint.size_bytes -or $hash -ne [string]$checkpoint.checksum_sha256) {
      throw "Downloaded source does not match Claude's exact official-source checkpoint for $id."
    }

    $description = if ($isAgenda) {
      "Preserves the official $($checkpoint.page_count)-page agenda for the $($checkpoint.date_on_document) Development Process Manual Executive Committee meeting. Approved minutes were not located after exhaustive official-source review, so it is retained only as a clearly labeled component of the annual compilation."
    } else {
      "Preserves the official $($checkpoint.page_count)-page record of the $($checkpoint.date_on_document) Development Process Manual Executive Committee meeting. This sparse procedural record is retained as a source component of the complete annual compilation rather than as a standalone site entry."
    }
    $wordCount = Get-WordCount $description
    if ($wordCount -lt 20 -or $wordCount -gt 50) { throw "Generated description for $id has $wordCount words." }
    $notes = @($candidate.processing_notes) + @(
      "Reclassified from '$($member.inventory_status)' after exhaustive annual source-family review; archive as a preserved component only, not as a standalone site listing.",
      [string]$checkpoint.version_relationship,
      "Claude checkpoint: $($checkpointPath.Replace('\','/'))."
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | Select-Object -Unique
    & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -Set @{
      status = 'approved for addition'
      source_url = [string]$checkpoint.official_source_url
      direct_file_url = [string]$checkpoint.official_source_url
      agency = 'City of Albuquerque'
      title = [string]$member.title
      date = [string]$member.date
      proposed_canonical_page = 'content/development-land-use/development-process.md'
      description = $description
      provenance_status = 'official City source fetched and visually reviewed; exact size and SHA-256 match the immutable research checkpoint'
      validation_status = 'local exact size and SHA-256 match the official-source research checkpoint; R2 upload pending'
      processing_notes = @($notes)
      exclusion_reason = $null
    } -InventoryPath $InventoryPath | Out-Null

    $decisions.Add([pscustomobject][ordered]@{
      id = $id
      title = [string]$member.title
      date = [string]$member.date
      source_page = 'https://documents.cabq.gov/planning/development-process-manual/'
      direct_file_url = [string]$checkpoint.official_source_url
      agency = 'City of Albuquerque'
      canonical_page = 'content/development-land-use/development-process.md'
      description = $description
      r2_key = if ($isAgenda) { "development-land-use/development-process/cabq-dpm-executive-committee-agenda-$($member.date)-approved-minutes-not-located.pdf" } else { "development-land-use/development-process/cabq-dpm-executive-committee-minutes-$($member.date).pdf" }
      provenance_status = 'official City source fetched and visually reviewed; exact size and SHA-256 match the immutable research checkpoint'
      processing_notes = @($notes)
      implementation_locations = @()
      cross_listing_approved = $false
      quality_assessment = $checkpoint.quality_assessment
    })
  }
}

$artifact = [pscustomobject][ordered]@{
  schema_version = 1
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  batch_id = 'dpm-annual-original-components-2026-09-13'
  purpose = 'Archive the byte-identical original meeting records required by the approved 2014-2018 annual compilations; no component is approved as a standalone visible entry.'
  component_count = $componentCount
  already_archived_count = $alreadyArchivedCount
  decisions = @($decisions)
}
$artifact | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $DecisionsPath -Encoding utf8
$artifact | Select-Object component_count,already_archived_count,@{n='planned_original_archives';e={@($_.decisions).Count}},@{n='output_path';e={$DecisionsPath}} | ConvertTo-Json -Compress
