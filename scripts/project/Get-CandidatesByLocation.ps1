[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Location,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
@($inventory.candidates | Where-Object { $_.implementation_locations -contains $Location } | Sort-Object title) |
  Select-Object id,status,title,size_bytes,description_word_count,validation_status,direct_file_url |
  ConvertTo-Json -Depth 5
