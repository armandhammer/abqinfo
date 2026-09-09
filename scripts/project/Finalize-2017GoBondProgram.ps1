[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$PlanPath = 'project-state/discovery/2017-go-bond-program-r2-archive-plan-2026-09-09.json',
  [string]$PublicValidationPath = 'project-state/discovery/2017-go-bond-program-public-validation-2026-09-09.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$public = Get-Content -Raw -Encoding UTF8 -LiteralPath $PublicValidationPath | ConvertFrom-Json
$verified = @{}
foreach ($result in @($public.results)) { if ($result.byte_identical) { $verified[[string]$result.id] = $true } }

$unverified = @(@($plan.items) | Where-Object { -not $verified.ContainsKey([string]$_.id) } | ForEach-Object { $_.id })
if ($unverified.Count) { throw "Refusing to finalize: public byte-identical validation is missing for $($unverified -join ', ')." }

$landingId = 'src-afd33bcd74a06555'
$ids = @(@($plan.items | ForEach-Object { [string]$_.id }) + $landingId)

foreach ($id in $ids) {
  $inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
  $candidate = @($inventory.candidates | Where-Object id -eq $id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for '$id'." }
  $candidate = $candidate[0]
  if ($candidate.status -eq 'validated') { continue }

  $locations = @($candidate.implementation_locations | Where-Object { $_ })
  if (-not $locations.Count) { throw "Candidate '$id' has no implementation location." }

  $set = @{
    status = 'implemented'
    implementation_location = $locations[0]
    implementation_locations = $locations
    cross_listing_approved = ($locations.Count -gt 1)
  }
  if ($id -eq $landingId) {
    $set['validation_status'] = 'official City collection URL linked as the browsable source; no file archived'
  } else {
    $set['validation_status'] = 'public R2 download matched exact size and SHA-256; awaiting authoritative-source link check'
  }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -InventoryPath $InventoryPath -Set $set | Out-Null
  & "$PSScriptRoot/Test-Candidate.ps1" -Id $id -InventoryPath $InventoryPath -UpdateInventory | Out-Null
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$final = @($inventory.candidates | Where-Object { $_.id -in $ids })
[pscustomobject]@{
  finalized = $final.Count
  validated = @($final | Where-Object status -eq 'validated').Count
  not_validated = @($final | Where-Object status -ne 'validated' | ForEach-Object { "$($_.id)=$($_.status)" })
  next_pending_id = $inventory.next_pending_id
} | ConvertTo-Json -Depth 5
