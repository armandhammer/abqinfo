[CmdletBinding()]
param(
  [ValidateSet('pending review','approved for addition','downloading','downloaded','parsed','description drafted','placement assigned','implemented','validated','excluded','duplicate','superseded','blocked','requires human review')]
  [string]$Status = 'pending review',

  [string]$InventoryPath = 'project-state/master-inventory.json',

  [ValidateRange(1,2147483647)]
  [int]$Limit = 50,

  [ValidateRange(0,2147483647)]
  [int]$Skip = 0,

  [switch]$All
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json

$matches = @(
  $inventory.candidates |
    Where-Object { $_.status -eq $Status } |
    Sort-Object id
)

if ($All) {
  $selected = $matches
}
else {
  $selected = @(
    $matches |
      Select-Object -Skip $Skip -First $Limit
  )
}

Write-Verbose (
  'Status "{0}" matched {1} candidates; returning {2}{3}.' -f
    $Status,
    $matches.Count,
    $selected.Count,
    $(if ($All) { ' (-All)' } else { " (Skip=$Skip, Limit=$Limit)" })
)

$selected |
  Select-Object id,title,agency,date,file_type,size_bytes,source_url,direct_file_url,proposed_canonical_page,processing_notes |
  ConvertTo-Json -Depth 6
