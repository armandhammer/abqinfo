[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/dpm-draft-and-agenda-research-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$artifact = Get-Content -LiteralPath $DecisionPath -Raw -Encoding UTF8 | ConvertFrom-Json
$inventory = Get-Content -LiteralPath $InventoryPath -Raw -Encoding UTF8 | ConvertFrom-Json
$index = @{}
foreach ($candidate in @($inventory.candidates)) { $index[[string]$candidate.id] = $candidate }
$seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)

foreach ($row in @($artifact.recommendations)) {
  $id = [string]$row.id
  if (-not $seen.Add($id)) { throw "Duplicate decision ID: $id" }
  if (-not $index.ContainsKey($id)) { throw "Missing candidate: $id" }
  $candidate = $index[$id]
  $status = [string]$row.recommended_status
  if ($status -notin @('superseded', 'excluded', 'requires human review')) { throw "Unsupported decision status: $status" }
  if ([string]$candidate.status -notin @('pending review', $status)) { throw "Unexpected candidate status: $id = $($candidate.status)" }
  $note = "DPM draft-and-agenda integration 2026-09-11: $($row.rationale)"
  $notes = @($candidate.processing_notes)
  if ($notes -notcontains $note) { $notes += $note }
  $set = @{ status = $status; processing_notes = $notes }
  if ($status -eq 'requires human review') {
    $set.validation_status = 'requires human review: adoption status or missing-minutes policy evidence remains unresolved'
    $set.exclusion_reason = $null
  } else {
    $set.validation_status = "terminal research decision: $status"
    $set.exclusion_reason = [string]$row.rationale
  }
  $canonicalId = [string]$row.canonical_id
  if ($canonicalId) {
    if (-not $index.ContainsKey($canonicalId)) { throw "Missing canonical record $canonicalId for $id" }
    $canonical = $index[$canonicalId]
    $canonicalUrl = if ($canonical.direct_file_url) { [string]$canonical.direct_file_url } else { [string]$canonical.source_url }
    if ($canonicalUrl) { $set.cited_successors = @($candidate.cited_successors) + @($canonicalUrl) | Select-Object -Unique }
  }
  foreach ($key in $set.Keys) { $candidate.$key = $set[$key] }
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

if ($seen.Count -ne 57) { throw "Unexpected integrated decision count: $($seen.Count)" }
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object { [string]$_.status -eq $status }).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.next_pending_id = ($inventory.candidates | Where-Object { [string]$_.status -eq 'pending review' } | Select-Object -First 1 -ExpandProperty id)
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$full = [IO.Path]::GetFullPath($InventoryPath)
$temporary = "$full.tmp-$PID"
try {
  [IO.File]::WriteAllText($temporary, ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporary -Destination $full -Force
} finally {
  if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
}
[pscustomobject][ordered]@{ integrated = $seen.Count; counts = $inventory.counts; next_pending_id = $inventory.next_pending_id } | ConvertTo-Json -Depth 5
