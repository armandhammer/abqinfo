[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Id,
  [Parameter(Mandatory)][hashtable]$Set,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-InventoryWithRetry([string]$Path) {
  for ($attempt = 1; $attempt -le 8; $attempt++) {
    try { return Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json }
    catch {
      $retryable = $_.Exception -is [System.IO.IOException] -or $_.Exception -is [System.UnauthorizedAccessException] -or $_.Exception.InnerException -is [System.IO.IOException] -or $_.Exception.InnerException -is [System.UnauthorizedAccessException]
      if (-not $retryable -or $attempt -eq 8) { throw }
      Start-Sleep -Milliseconds (100 * $attempt)
    }
  }
}

function Write-InventoryWithRetry($Value, [string]$Path) {
  $json = $Value | ConvertTo-Json -Depth 12
  for ($attempt = 1; $attempt -le 8; $attempt++) {
    $fullPath = [IO.Path]::GetFullPath($Path)
    $temporaryPath = "$fullPath.tmp-$PID-$attempt"
    try {
      [IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
      Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
      return
    }
    catch {
      $retryable = $_.Exception -is [System.IO.IOException] -or $_.Exception -is [System.UnauthorizedAccessException] -or $_.Exception.InnerException -is [System.IO.IOException] -or $_.Exception.InnerException -is [System.UnauthorizedAccessException]
      if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force }
      if (-not $retryable -or $attempt -eq 8) { throw }
      Start-Sleep -Milliseconds (100 * $attempt)
    }
  }
}

$inventory = Read-InventoryWithRetry $InventoryPath
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
Write-InventoryWithRetry $inventory $InventoryPath
$candidate | ConvertTo-Json -Depth 8
