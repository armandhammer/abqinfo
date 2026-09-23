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
    try { return Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json -DateKind String }
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

function ConvertTo-ComparableJson($Value) {
  if ($null -eq $Value) { return 'null' }
  return ($Value | ConvertTo-Json -Depth 20 -Compress)
}

$inventory = Read-InventoryWithRetry $InventoryPath
. "$PSScriptRoot/MissionScopePolicy.ps1"
$legacyScopeRegistry = Read-MissionScopeLegacyRegistry
$candidate = @($inventory.candidates | Where-Object id -eq $Id)
if ($candidate.Count -ne 1) { throw "Expected one candidate for '$Id'; found $($candidate.Count)." }
$candidate = $candidate[0]
$candidateChanged = $false
foreach ($key in $Set.Keys) {
  if (-not $candidate.PSObject.Properties[$key] -and $key -notin @('scope_assessment','review_reason')) { throw "Unknown inventory field '$key'." }
  if (-not $candidate.PSObject.Properties[$key]) { $candidate | Add-Member -NotePropertyName $key -NotePropertyValue $null }
  if ((ConvertTo-ComparableJson $candidate.$key) -ne (ConvertTo-ComparableJson $Set[$key])) {
    $candidate.$key = $Set[$key]
    $candidateChanged = $true
  }
}
if ($candidateChanged -and $Set.ContainsKey('description')) {
  $candidate.description_word_count = if ([string]::IsNullOrWhiteSpace($candidate.description)) { 0 } else { @($candidate.description -split '\s+' | Where-Object { $_ }).Count }
}
if ($candidateChanged) {
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  if (-not (Test-MissionScopeProgressEligible $candidate $legacyScopeRegistry)) {
    throw "Candidate '$Id' cannot enter or remain in '$($candidate.status)' after an update without a complete positive mission scope assessment."
  }
}
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$nextCandidates = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$expectedNext = if ($nextCandidates.Count) { $nextCandidates[0].id } else { $null }
$aggregateChanged =
  (ConvertTo-ComparableJson $inventory.counts) -ne (ConvertTo-ComparableJson ([pscustomobject]$counts)) -or
  $inventory.next_pending_id -ne $expectedNext
if ($candidateChanged -or $aggregateChanged) {
  $inventory.counts = [pscustomobject]$counts
  $inventory.next_pending_id = $expectedNext
  $inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
  Write-InventoryWithRetry $inventory $InventoryPath
}
$candidate | ConvertTo-Json -Depth 8
