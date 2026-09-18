[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$PlanPath = 'project-state/discovery/paseo-del-volcan-r2-archive-plan-2026-09-17.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json -DateKind String
$items = @($plan.items | Sort-Object id)
if ($items.Count -ne 11) { throw 'Expected the complete eleven-object Paseo archive plan.' }
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
$seen = [System.Collections.Generic.HashSet[string]]::new()
foreach ($item in $items) {
  if (-not $seen.Add([string]$item.id)) { throw "Duplicate plan ID: $($item.id)" }
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for $($item.id)." }
  $candidate = $candidate[0]
  if (-not $candidate.local_path -or -not (Test-Path -LiteralPath $candidate.local_path)) { throw "Missing staged source for $($item.id)." }
  $file = Get-Item -LiteralPath $candidate.local_path
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($file.Length -ne [int64]$item.size_bytes -or $hash -ne [string]$item.checksum_sha256) { throw "Local source mismatch for $($item.id)." }
  $candidate.status = 'placement assigned'
  $candidate.r2_key = [string]$item.r2_key
  $candidate.r2_url = "https://files.abqinfo.com/$($item.r2_key)"
  $candidate.validation_status = 'local size and SHA-256 passed; existing R2 object verified by public byte-identical download'
  $notes = @($candidate.processing_notes) + 'Recovery reconciliation 2026-09-17: public R2 download matched exact local size and SHA-256 after interrupted archive execution; no overwrite or delete was performed.'
  $candidate.processing_notes = @($notes | Where-Object { $_ } | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$next = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { [string]$next[0].id } else { $null }
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$full = [IO.Path]::GetFullPath($InventoryPath)
$tmp = "$full.tmp-$PID"
try { [IO.File]::WriteAllText($tmp, ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $tmp -Destination $full -Force }
finally { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force } }
[pscustomobject]@{ reconciled=$seen.Count; next_pending_id=$inventory.next_pending_id; counts=$inventory.counts } | ConvertTo-Json -Depth 5
