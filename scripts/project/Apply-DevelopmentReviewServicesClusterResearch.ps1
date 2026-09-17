[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/development-review-services-cluster-research-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$artifact = Get-Content -Raw -Encoding UTF8 -LiteralPath $DecisionPath | ConvertFrom-Json
$byId = @{}
foreach ($candidate in $inventory.candidates) { $byId[[string]$candidate.id] = $candidate }
$seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)

function Get-RowReason($Row) {
  foreach ($property in @('exclusion_reason','basis','why_retained','evidence','note')) {
    $value = $Row.PSObject.Properties[$property]
    if ($value -and $value.Value) { return [string]$value.Value }
  }
  return 'Reviewed in the dated Development Review Services research artifact.'
}

function Set-DrsCandidate($Row, [string]$Status) {
  $id = [string]$Row.id
  if (-not $seen.Add($id)) { throw "Duplicate decision for $id." }
  $candidate = $byId[$id]
  if (-not $candidate) { throw "Inventory candidate $id is missing." }
  if ([string]$candidate.status -ne 'pending review') { throw "Unexpected starting status for ${id}: $($candidate.status)." }

  $url = [string]$Row.authoritative_url
  $candidate.direct_file_url = $url
  if (@($candidate.referring_urls) -notcontains $url) { $candidate.referring_urls = @($candidate.referring_urls) + @($url) }
  if ($Row.PSObject.Properties['size_bytes'] -and $null -ne $Row.size_bytes) { $candidate.size_bytes = [int64]$Row.size_bytes }
  if ($Row.PSObject.Properties['checksum_sha256'] -and $Row.checksum_sha256) { $candidate.checksum_sha256 = [string]$Row.checksum_sha256 }
  $reason = Get-RowReason $Row

  if ($Status -eq 'approved for addition') {
    $candidate.title = [string]$Row.title
    $candidate.date = if ($Row.PSObject.Properties['date'] -and $Row.date) { [string]$Row.date } else { $null }
    $candidate.description = [string]$Row.description
    $candidate.description_word_count = [int]$Row.description_word_count
    $candidate.proposed_canonical_page = [string]$Row.proposed_canonical_page
    $locations = @([string]$Row.proposed_canonical_page) + @($Row.cross_listings | Where-Object { $_ })
    $candidate.implementation_locations = @($locations | Select-Object -Unique)
    $candidate.cross_listing_approved = [bool]($candidate.implementation_locations.Count -gt 1)
    $candidate.validation_status = 'passed: authoritative City file reviewed and HTTP 200 verified; awaiting archive-first editorial placement'
    $candidate.exclusion_reason = $null
  } elseif ($Status -in @('duplicate','superseded')) {
    $canonicalId = [string]$Row.canonical_id
    $canonical = $byId[$canonicalId]
    if (-not $canonical) { throw "Canonical inventory candidate $canonicalId for $id is missing." }
    $canonicalUrl = if ($canonical.direct_file_url) { [string]$canonical.direct_file_url } else { [string]$canonical.source_url }
    $candidate.cited_successors = @(@($candidate.cited_successors) + @($canonicalUrl) | Select-Object -Unique)
    $candidate.validation_status = "terminal research decision: $Status by exact, normalized-text, rendered-content, or authoritative version comparison"
    $candidate.exclusion_reason = "$Status in favor of canonical inventory record $canonicalId. $reason"
  } else {
    $candidate.validation_status = 'terminal research decision: excluded after content review'
    $candidate.exclusion_reason = $reason
  }

  $note = "$($artifact.batch_id) integration: $reason"
  if (@($candidate.processing_notes) -notcontains $note) { $candidate.processing_notes = @($candidate.processing_notes) + @($note) }
  $candidate.status = $Status
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

foreach ($row in @($artifact.approved_for_addition)) { Set-DrsCandidate $row 'approved for addition' }
foreach ($row in @($artifact.duplicate)) { Set-DrsCandidate $row 'duplicate' }
foreach ($row in @($artifact.superseded)) { Set-DrsCandidate $row 'superseded' }
foreach ($row in @($artifact.excluded)) { Set-DrsCandidate $row 'excluded' }

if ($seen.Count -ne [int]$artifact.counts.reviewed) { throw "Expected $($artifact.counts.reviewed) decisions; integrated $($seen.Count)." }
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$next = @($inventory.candidates | Where-Object {
  $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or
  ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed')
} | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { [string]$next[0].id } else { $null }
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
try {
  [IO.File]::WriteAllText($temporaryPath, ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
} finally {
  if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force }
}

[pscustomobject]@{ integrated = $seen.Count; counts = $inventory.counts; next_pending_id = $inventory.next_pending_id } | ConvertTo-Json -Depth 5
