[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Id,
  [Parameter(Mandatory)][ValidateSet('pending review','approved for addition','downloading','downloaded','parsed','description drafted','placement assigned','implemented','validated','excluded','duplicate','superseded','blocked','requires human review')][string]$Status,
  [string]$ValidationStatus,
  [string]$Note,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$set = @{ status = $Status }
if ($ValidationStatus) { $set.validation_status = $ValidationStatus }
if ($Note) {
  $inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
  $candidate = $inventory.candidates | Where-Object { $_.id -eq $Id } | Select-Object -First 1
  $set.processing_notes = @($candidate.processing_notes) + $Note
}
& "$PSScriptRoot/Update-Candidate.ps1" -Id $Id -Set $set -InventoryPath $InventoryPath
