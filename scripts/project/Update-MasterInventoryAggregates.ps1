[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
$priorCounts = if ($inventory.PSObject.Properties.Name -contains 'counts') { $inventory.counts | ConvertTo-Json -Depth 12 -Compress } else { $null }
$priorNext = $inventory.next_pending_id
$counts = [ordered]@{}
foreach ($status in @($inventory.allowed_statuses)) {
  $counts[[string]$status] = @($inventory.candidates | Where-Object { [string]$_.status -eq [string]$status }).Count
}

$pendingStatuses = @(
  'pending review',
  'approved for addition',
  'downloaded',
  'parsed',
  'description drafted',
  'placement assigned'
)
$next = @(
  $inventory.candidates |
    Where-Object {
      $_.status -in $pendingStatuses -or
      ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed')
    } |
    Sort-Object id |
    Select-Object -First 1
)

$inventory.counts = [pscustomobject]$counts
$inventory.next_pending_id = if ($next.Count) { [string]$next[0].id } else { $null }

$changed =
  $priorCounts -ne ($inventory.counts | ConvertTo-Json -Depth 12 -Compress) -or
  $priorNext -ne $inventory.next_pending_id
if ($changed) { $inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o') }

if ($changed) {
  $fullPath = [IO.Path]::GetFullPath($InventoryPath)
  $temporaryPath = "$fullPath.tmp-$PID"
  try {
    [IO.File]::WriteAllText(
      $temporaryPath,
      ($inventory | ConvertTo-Json -Depth 12),
      [Text.UTF8Encoding]::new($false)
    )
    Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
  }
  finally {
    if (Test-Path -LiteralPath $temporaryPath) {
      Remove-Item -LiteralPath $temporaryPath -Force
    }
  }
}

[pscustomobject]@{
  total_candidates = @($inventory.candidates).Count
  counts = $inventory.counts
  next_pending_id = $inventory.next_pending_id
  changed = $changed
} | ConvertTo-Json -Depth 5
