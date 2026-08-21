[CmdletBinding()]
param(
  [string]$Id,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
if (-not $Id) { $Id = $inventory.next_pending_id }
$candidate = $inventory.candidates | Where-Object { $_.id -eq $Id } | Select-Object -First 1
if (-not $candidate) { throw "Candidate not found: $Id" }
$candidate | ConvertTo-Json -Depth 8
