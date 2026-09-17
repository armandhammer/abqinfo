[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
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
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')

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

[pscustomobject]@{
  total_candidates = @($inventory.candidates).Count
  counts = $inventory.counts
  next_pending_id = $inventory.next_pending_id
} | ConvertTo-Json -Depth 5
