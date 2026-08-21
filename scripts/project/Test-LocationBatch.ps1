[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Location,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$ids = @($inventory.candidates | Where-Object {
  $_.status -eq 'implemented' -and
  $_.implementation_locations -contains $Location -and
  $_.description_word_count -ge 20 -and $_.description_word_count -le 50
} | Sort-Object id | Select-Object -ExpandProperty id)

$results = foreach ($candidateId in $ids) {
  & "$PSScriptRoot/Test-Candidate.ps1" -Id $candidateId -InventoryPath $InventoryPath -UpdateInventory | ConvertFrom-Json
}
@($results) | ConvertTo-Json -Depth 5
