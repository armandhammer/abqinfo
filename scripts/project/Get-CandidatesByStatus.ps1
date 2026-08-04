[CmdletBinding()]
param(
  [ValidateSet('pending review','approved for addition','downloading','downloaded','parsed','description drafted','placement assigned','implemented','validated','excluded','duplicate','superseded','blocked','requires human review')][string]$Status = 'pending review',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
@($inventory.candidates | Where-Object { $_.status -eq $Status } | Sort-Object id) |
  Select-Object id,title,agency,date,file_type,size_bytes,source_url,direct_file_url,proposed_canonical_page,processing_notes |
  ConvertTo-Json -Depth 6
