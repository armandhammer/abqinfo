[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
@($inventory.candidates | Where-Object {
  $_.status -eq 'implemented' -and (-not $_.description -or $_.description_word_count -lt 20 -or $_.description_word_count -gt 50)
} | Sort-Object implementation_location,title) |
  Select-Object id,title,implementation_location,description_word_count,direct_file_url,source_url |
  ConvertTo-Json -Depth 5
