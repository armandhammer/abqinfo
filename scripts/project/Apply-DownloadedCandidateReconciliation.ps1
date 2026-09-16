[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/downloaded-candidate-reconciliation-decisions-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventoryFull = [IO.Path]::GetFullPath($InventoryPath)
$inventory = Get-Content -LiteralPath $inventoryFull -Raw -Encoding UTF8 | ConvertFrom-Json
$artifact = Get-Content -LiteralPath $DecisionPath -Raw -Encoding UTF8 | ConvertFrom-Json
$byId = @{}
foreach ($candidate in $inventory.candidates) { $byId[[string]$candidate.id] = $candidate }
$seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)

foreach ($decision in @($artifact.decisions)) {
  $id = [string]$decision.id
  if (-not $seen.Add($id)) { throw "Duplicate decision ID: $id" }
  if (-not $byId.ContainsKey($id)) { throw "Candidate is not in the inventory: $id" }
  $candidate = $byId[$id]
  if ([string]$candidate.status -ne 'downloaded') { throw "Unexpected candidate status: $id = $($candidate.status)" }
  $status = [string]$decision.status
  if ($status -notin @('excluded', 'duplicate', 'requires human review')) { throw "Unsupported decision status: $status" }
  $directFileProperty = $decision.PSObject.Properties['direct_file_url']
  if ($directFileProperty -and $directFileProperty.Value) {
    $url = [string]$directFileProperty.Value
    $candidate.direct_file_url = $url
    if (@($candidate.referring_urls) -notcontains $url) { $candidate.referring_urls = @($candidate.referring_urls) + @($url) }
  }
  $sourceProperty = $decision.PSObject.Properties['source_url']
  if ($sourceProperty -and $sourceProperty.Value) {
    $url = [string]$sourceProperty.Value
    $candidate.source_url = $url
    if (@($candidate.referring_urls) -notcontains $url) { $candidate.referring_urls = @($candidate.referring_urls) + @($url) }
  }
  $canonicalProperty = $decision.PSObject.Properties['canonical_id']
  if ($canonicalProperty -and $canonicalProperty.Value) {
    $canonicalId = [string]$canonicalProperty.Value
    if (-not $byId.ContainsKey($canonicalId)) { throw "Canonical candidate is not in the inventory: $canonicalId" }
    $candidate.cited_successors = @($candidate.cited_successors) + @($canonicalId) | Select-Object -Unique
  }
  $note = "Downloaded-candidate reconciliation 2026-09-11: $($decision.reason)"
  if (@($candidate.processing_notes) -notcontains $note) { $candidate.processing_notes = @($candidate.processing_notes) + @($note) }
  $candidate.status = $status
  $candidate.validation_status = if ($status -eq 'requires human review') { 'requires human review: source provenance or distinct-document status remains unresolved' } else { "terminal review decision: $status" }
  $candidate.exclusion_reason = if ($status -eq 'requires human review') { $null } else { [string]$decision.reason }
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

if ($seen.Count -ne 9) { throw "Unexpected reconciliation count: $($seen.Count)" }
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object { [string]$_.status -eq $status }).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.next_pending_id = ($inventory.candidates | Where-Object { [string]$_.status -eq 'pending review' } | Select-Object -First 1 -ExpandProperty id)
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$temporary = "$inventoryFull.tmp-$PID"
try {
  [IO.File]::WriteAllText($temporary, ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporary -Destination $inventoryFull -Force
} finally {
  if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
}
[pscustomobject][ordered]@{ reconciled = $seen.Count; counts = $inventory.counts; next_pending_id = $inventory.next_pending_id } | ConvertTo-Json -Depth 5
