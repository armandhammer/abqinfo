[CmdletBinding()]
param(
  [int]$Limit = 10,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'
$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$candidates = @($inventory.candidates | Where-Object {
  $_.status -eq 'implemented' -and
  $_.description_word_count -ge 20 -and $_.description_word_count -le 50
} | Sort-Object id | Select-Object -First $Limit)

$results = foreach ($candidate in $candidates) {
  try {
    & "$PSScriptRoot/Test-Candidate.ps1" -Id $candidate.id -InventoryPath $InventoryPath -UpdateInventory | ConvertFrom-Json
  } catch {
    [pscustomobject]@{ id = $candidate.id; title = $candidate.title; error = $_.Exception.Message }
  }
}
@($results) | ConvertTo-Json -Depth 5
