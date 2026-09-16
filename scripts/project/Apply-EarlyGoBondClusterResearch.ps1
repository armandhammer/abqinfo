[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/early-go-bond-cluster-research-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -LiteralPath $InventoryPath -Raw -Encoding UTF8 | ConvertFrom-Json
$artifact = Get-Content -LiteralPath $DecisionPath -Raw -Encoding UTF8 | ConvertFrom-Json
$index = @{}
foreach ($candidate in @($inventory.candidates)) { $index[[string]$candidate.id] = $candidate }
$seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)

function Apply-Decision($row, [string]$status) {
  $id = [string]$row.id
  if (-not $seen.Add($id)) { throw "Duplicate decision ID: $id" }
  if (-not $index.ContainsKey($id)) { throw "Missing candidate: $id" }
  $candidate = $index[$id]
  if ([string]$candidate.status -ne 'pending review') { throw "Unexpected candidate status: $id = $($candidate.status)" }
  $url = [string]$row.authoritative_url
  if ($url) {
    $candidate.direct_file_url = $url
    if (@($candidate.referring_urls) -notcontains $url) { $candidate.referring_urls = @($candidate.referring_urls) + @($url) }
  }
  $reasonProperty = $row.PSObject.Properties['reason']
  $evidenceProperty = $row.PSObject.Properties['evidence']
  $reason = if ($reasonProperty -and $reasonProperty.Value) { [string]$reasonProperty.Value } elseif ($evidenceProperty) { [string]$evidenceProperty.Value } else { 'Reviewed in the dated early 2003/2004 GO-bond research artifact.' }
  if ($status -eq 'approved for addition') {
    $candidate.proposed_canonical_page = [string]$row.proposed_canonical_page
    $candidate.description = [string]$row.description
    $candidate.description_word_count = [int]$row.description_word_count
    $candidate.size_bytes = [int64]$row.size_bytes
    $candidate.checksum_sha256 = [string]$row.checksum_sha256
    $candidate.implementation_locations = @($row.proposed_canonical_page) + @($row.proposed_cross_listings) | Select-Object -Unique
    $candidate.cross_listing_approved = @($row.proposed_cross_listings).Count -gt 0
    $candidate.validation_status = 'passed: authoritative City PDF reviewed and HTTP 200 verified; awaiting authorized editorial placement'
    $candidate.exclusion_reason = $null
  } elseif ($status -eq 'requires human review') {
    $candidate.validation_status = 'requires human review: editorial or parent-document decision remains unresolved'
    $candidate.exclusion_reason = $null
  } else {
    $candidate.validation_status = 'terminal research decision: excluded'
    $candidate.exclusion_reason = $reason
  }
  $note = "Early 2003/2004 GO-bond integration 2026-09-11: $reason"
  if (@($candidate.processing_notes) -notcontains $note) { $candidate.processing_notes = @($candidate.processing_notes) + @($note) }
  $candidate.status = $status
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

foreach ($row in @($artifact.approved_for_addition)) { Apply-Decision $row 'approved for addition' }
foreach ($row in @($artifact.excluded)) { Apply-Decision $row 'excluded' }
foreach ($row in @($artifact.requires_human_review)) { Apply-Decision $row 'requires human review' }
if ($seen.Count -ne 25) { throw "Unexpected integration count: $($seen.Count)" }

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object { [string]$_.status -eq $status }).Count }
$inventory.counts = [pscustomobject]$counts
$next = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$full = [IO.Path]::GetFullPath($InventoryPath)
$temporary = "$full.tmp-$PID"
try {
  [IO.File]::WriteAllText($temporary, ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporary -Destination $full -Force
} finally {
  if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
}
[pscustomobject][ordered]@{integrated=$seen.Count;counts=$inventory.counts;next_pending_id=$inventory.next_pending_id}|ConvertTo-Json -Depth 5
