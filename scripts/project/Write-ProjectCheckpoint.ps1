[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/checkpoint.json',
  [string]$CompletedRange = '',
  [string[]]$Blockers = @(),
  [string]$ResumeCommand = 'powershell -NoProfile -ExecutionPolicy Bypass -File scripts/project/Test-Candidate.ps1 -UpdateInventory'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$terminal = @('validated','excluded','duplicate','superseded','blocked','requires human review')
$remaining = @($inventory.candidates | Where-Object { $_.status -notin $terminal })
$checkpoint = [ordered]@{
  recorded_at = (Get-Date).ToUniversalTime().ToString('o')
  completed_item_range = $CompletedRange
  total_candidates = @($inventory.candidates).Count
  counts_by_status = $inventory.counts
  remaining_nonterminal = $remaining.Count
  next_pending_id = $inventory.next_pending_id
  blockers = $Blockers
  resume_command = $ResumeCommand
}
$checkpoint | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$checkpoint | ConvertTo-Json -Compress -Depth 8
