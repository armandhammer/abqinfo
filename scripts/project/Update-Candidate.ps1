[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Id,
  [Parameter(Mandatory)][hashtable]$Set,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw $InventoryPath | ConvertFrom-Json
$candidate = @($inventory.candidates | Where-Object id -eq $Id)
if ($candidate.Count -ne 1) { throw "Expected one candidate for '$Id'; found $($candidate.Count)." }
$candidate = $candidate[0]
foreach ($key in $Set.Keys) {
  if (-not $candidate.PSObject.Properties[$key]) { throw "Unknown inventory field '$key'." }
  $candidate.$key = $Set[$key]
}
if ($Set.ContainsKey('description')) {
  $candidate.description_word_count = if ([string]::IsNullOrWhiteSpace($candidate.description)) { 0 } else { @($candidate.description -split '\s+' | Where-Object { $_ }).Count }
}
$candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$nextCandidates = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($nextCandidates.Count) { $nextCandidates[0].id } else { $null }
$inventory | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $InventoryPath -Encoding utf8
$candidate | ConvertTo-Json -Depth 8
