[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/cabq-404-targeted-source-replacement-decisions-2026-09-11.json',
  [switch]$RepairTerminalReasons
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventoryFull = [IO.Path]::GetFullPath($InventoryPath)
$inventory = Get-Content -LiteralPath $inventoryFull -Raw -Encoding UTF8 | ConvertFrom-Json
$decisions = Get-Content -LiteralPath $DecisionPath -Raw -Encoding UTF8 | ConvertFrom-Json
$byId = @{}
foreach ($candidate in $inventory.candidates) { $byId[[string]$candidate.id] = $candidate }
$seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)

foreach ($decision in @($decisions.decisions)) {
  $id = [string]$decision.id
  if (-not $seen.Add($id)) { throw "Duplicate decision candidate ID: $id" }
  if (-not $byId.ContainsKey($id)) { throw "Decision candidate is not in the inventory: $id" }
  $candidate = $byId[$id]
  $expectedStatus = if ($RepairTerminalReasons) { 'superseded' } else { 'requires human review' }
  if ([string]$candidate.status -ne $expectedStatus) { throw "Unexpected candidate status: $id = $($candidate.status)" }
  $successor = [string]$decision.successor_url
  if ($successor -notmatch '^https://(www\.)?cabq\.gov/' -and $successor -notmatch '^https://documents\.cabq\.gov/' -and $successor -notmatch '^https://abq\.legistar\.com/' -and $successor -notmatch '^https://codelibrary\.amlegal\.com/') { throw "Unsupported authoritative successor host: $successor" }
  if (@($candidate.referring_urls) -notcontains $successor) { $candidate.referring_urls = @($candidate.referring_urls) + @($successor) }
  $candidate.direct_file_url = $successor
  $candidate.cited_successors = @($candidate.cited_successors) + @($successor) | Select-Object -Unique
  $note = "City HTTP-404 targeted source-replacement resolution 2026-09-11: $($decision.relation): $($decision.successor_title). $($decision.note)"
  if (@($candidate.processing_notes) -notcontains $note) { $candidate.processing_notes = @($candidate.processing_notes) + @($note) }
  $candidate.status = 'superseded'
  $candidate.validation_status = 'passed: exact authoritative successor or authoritative supersession recorded; completed failed verification result preserved in processing notes'
  $candidate.exclusion_reason = "Superseded by authoritative successor or authoritative supersession: $($decision.successor_title). $($decision.note)"
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

if ($seen.Count -ne 15) { throw "Unexpected targeted replacement count: $($seen.Count)" }
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object { [string]$_.status -eq $status }).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$temporary = "$inventoryFull.tmp-$PID"
try { [IO.File]::WriteAllText($temporary, ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $temporary -Destination $inventoryFull -Force } finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force } }
[pscustomobject][ordered]@{ resolved = $seen.Count; status = 'superseded'; counts = $inventory.counts } | ConvertTo-Json -Depth 5
