[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$PlanPath = 'project-state/discovery/early-go-bond-r2-archive-plan-2026-09-11.json',
  [string]$PublicValidationPath = 'project-state/discovery/early-go-bond-r2-public-validation-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$public = Get-Content -Raw -Encoding UTF8 -LiteralPath $PublicValidationPath | ConvertFrom-Json
$verified = @{}
foreach ($result in @($public.results)) {
  if ($result.byte_identical) { $verified[[string]$result.id] = $true }
}

$unverified = @($plan.items | Where-Object { -not $verified.ContainsKey([string]$_.id) } | ForEach-Object id)
if ($unverified.Count) { throw "Refusing to finalize: public byte-identical validation is missing for $($unverified -join ', ')." }

foreach ($item in @($plan.items)) {
  $locations = @($item.implementation_locations | Where-Object { $_ })
  if (-not $locations.Count) { $locations = @([string]$item.proposed_canonical_page) }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $item.id -InventoryPath $InventoryPath -Set @{
    status = 'implemented'
    implementation_location = [string]$locations[0]
    implementation_locations = @($locations)
    cross_listing_approved = [bool]($locations.Count -gt 1)
    validation_status = 'public R2 download matched exact size and SHA-256; authoritative City source and site placement awaiting final candidate validation'
  } | Out-Null
  & "$PSScriptRoot/Test-Candidate.ps1" -Id $item.id -InventoryPath $InventoryPath -UpdateInventory | Out-Null
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$final = @($inventory.candidates | Where-Object { $_.id -in @($plan.items.id) })
[pscustomobject]@{
  finalized = $final.Count
  validated = @($final | Where-Object status -eq 'validated').Count
  not_validated = @($final | Where-Object status -ne 'validated' | ForEach-Object { "$($_.id)=$($_.status)" })
} | ConvertTo-Json -Depth 5
