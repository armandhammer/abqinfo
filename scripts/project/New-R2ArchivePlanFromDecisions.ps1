[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$DecisionsPath,
  [Parameter(Mandatory)][string]$OutputPath,
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json',
  [int64]$MaximumObjectBytes = 100000000,
  [int64]$MaximumProjectedR2Bytes = 8000000000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$decisions = Get-Content -Raw -LiteralPath $DecisionsPath | ConvertFrom-Json
$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$r2 = Get-Content -Raw -LiteralPath $R2InventoryPath | ConvertFrom-Json
$items = @()

foreach ($decision in @($decisions.decisions)) {
  $matches = @($inventory.candidates | Where-Object id -eq $decision.id)
  if ($matches.Count -ne 1) { throw "Expected one inventory candidate for '$($decision.id)'; found $($matches.Count)." }
  $candidate = $matches[0]
  $candidateType = ([string]$candidate.file_type).ToUpperInvariant()
  $readyStatuses = @('placement assigned','implemented','validated')
  $allowedStatuses = if ($candidateType -eq 'PDF') { @('parsed') + $readyStatuses } else { @('downloaded','parsed') + $readyStatuses }
  if ($candidate.status -notin $allowedStatuses) {
    throw "Candidate '$($decision.id)' must be locally inspected before planning; status is '$($candidate.status)'."
  }
  if (-not $candidate.local_path -or -not (Test-Path -LiteralPath $candidate.local_path)) { throw "Candidate '$($decision.id)' has no local source file." }

  $file = Get-Item -LiteralPath $candidate.local_path
  $checksum = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ([int64]$candidate.size_bytes -ne [int64]$file.Length) { throw "Candidate '$($decision.id)' size does not match its local source." }
  if ([string]$candidate.checksum_sha256 -ne $checksum) { throw "Candidate '$($decision.id)' checksum does not match its local source." }

  $wordCount = @([string]$decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($wordCount -lt 20 -or $wordCount -gt 50) { throw "Candidate '$($decision.id)' description has $wordCount words; expected 20-50." }

  $sourcePage = if ($decision.PSObject.Properties['source_page'] -and $decision.source_page) {
    [string]$decision.source_page
  } elseif ($candidate.source_url) {
    [string]$candidate.source_url
  } else {
    [string]$candidate.parent_url
  }

  $item = [ordered]@{
    id = [string]$decision.id
    source_url = $sourcePage
    direct_file_url = if ($decision.PSObject.Properties['direct_file_url'] -and $decision.direct_file_url) {
      [string]$decision.direct_file_url
    } elseif ($candidate.direct_file_url) {
      [string]$candidate.direct_file_url
    } elseif ($candidate.source_url -and [string]$candidate.source_url -ne $sourcePage) {
      [string]$candidate.source_url
    } else {
      ''
    }
    parent_url = $sourcePage
    agency = if ($decision.PSObject.Properties['agency'] -and $decision.agency) {
      [string]$decision.agency
    } elseif ($candidate.agency) {
      [string]$candidate.agency
    } else {
      'City of Albuquerque'
    }
    title = [string]$decision.title
    date = [string]$decision.date
    file_type = $candidateType
    size_bytes = [int64]$file.Length
    checksum_sha256 = $checksum
    r2_key = [string]$decision.r2_key
    proposed_canonical_page = [string]$decision.canonical_page
    description = [string]$decision.description
    provenance_status = if ($decision.PSObject.Properties['provenance_status'] -and $decision.provenance_status) {
      [string]$decision.provenance_status
    } else {
      'official government source page and byte-identical official file recorded'
    }
    processing_notes = if ($decision.PSObject.Properties['processing_notes'] -and @($decision.processing_notes).Count) {
      @($decision.processing_notes)
    } else {
      @("Original authoritative $candidateType preserved without modification; $wordCount-word description reviewed from extracted content or visual inspection.")
    }
    size_warning_over_25mb = [bool]($file.Length -gt 25MB)
  }
  if ($decision.PSObject.Properties['implementation_locations']) {
    $item.implementation_locations = @($decision.implementation_locations)
  }
  if ($decision.PSObject.Properties['cross_listing_approved']) {
    $item.cross_listing_approved = [bool]$decision.cross_listing_approved
  }
  if ($decision.PSObject.Properties['large_file_assessment']) {
    $item.large_file_assessment = [string]$decision.large_file_assessment
  }
  $items += [pscustomobject]$item
}

if (@($items.id | Group-Object | Where-Object Count -gt 1).Count) { throw 'Decision IDs are not unique.' }
if (@($items.r2_key | Group-Object | Where-Object Count -gt 1).Count) { throw 'R2 keys are not unique.' }
[int64]$batchBytes = ($items | Measure-Object size_bytes -Sum).Sum
[int64]$addedBytes = 0
foreach ($item in $items) {
  $existing = @($r2.objects | Where-Object key -eq $item.r2_key)
  if ($existing.Count -gt 1) { throw "R2 inventory contains duplicate key '$($item.r2_key)'." }
  if ($existing.Count -eq 1 -and [int64]$existing[0].size_bytes -ne [int64]$item.size_bytes) {
    throw "Existing R2 object '$($item.r2_key)' does not match the planned exact byte size."
  }
  $alreadyPresent = $existing.Count -eq 1
  $item | Add-Member -NotePropertyName already_present -NotePropertyValue $alreadyPresent
  if (-not $alreadyPresent) { $addedBytes += [int64]$item.size_bytes }
}
[int64]$projectedBytes = [int64]$r2.total_bytes + $addedBytes
if (@($items | Where-Object size_bytes -gt $MaximumObjectBytes).Count) { throw 'At least one file exceeds the production-upload approval threshold.' }
if ($projectedBytes -gt $MaximumProjectedR2Bytes) { throw 'The batch would exceed the project R2 storage stop point.' }

$plan = [ordered]@{
  schema_version = 1
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  batch_id = [string]$decisions.batch_id
  current_r2_bytes = [int64]$r2.total_bytes
  maximum_object_bytes = $MaximumObjectBytes
  maximum_projected_r2_bytes = $MaximumProjectedR2Bytes
  batch_bytes = $batchBytes
  added_bytes = $addedBytes
  projected_r2_bytes = $projectedBytes
  items = $items
}
$plan | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{
  Items = $items.Count
  AddedBytes = $addedBytes
  ProjectedR2Bytes = $projectedBytes
  Over25MB = @($items | Where-Object size_warning_over_25mb).Count
  OutputPath = $OutputPath
} | ConvertTo-Json -Compress
