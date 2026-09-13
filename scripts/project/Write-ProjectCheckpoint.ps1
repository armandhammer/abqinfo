[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/checkpoint.json',
  [string]$CompletedRange = '',
  [string]$NextPendingId = '',
  [string[]]$Blockers = @(),
  [string]$ResumeCommand = 'powershell -NoProfile -ExecutionPolicy Bypass -File scripts/project/Test-Candidate.ps1 -UpdateInventory'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$terminal = @('validated','excluded','duplicate','superseded','blocked','requires human review')
$remaining = @($inventory.candidates | Where-Object { $_.status -notin $terminal })
$prior = if (Test-Path -LiteralPath $OutputPath) {
  Get-Content -Raw -Encoding UTF8 -LiteralPath $OutputPath | ConvertFrom-Json
} else {
  $null
}
$history = @()
if ($null -ne $prior) {
  if ($prior.PSObject.Properties.Name -contains 'history') {
    $history = @($prior.history)
  }
  $history += [ordered]@{
    recorded_at = $prior.recorded_at
    completed_item_range = $prior.completed_item_range
    total_candidates = $prior.total_candidates
    counts_by_status = $prior.counts_by_status
    remaining_nonterminal = $prior.remaining_nonterminal
    next_pending_id = $prior.next_pending_id
    blockers = @($prior.blockers)
    resume_command = $prior.resume_command
    verification_campaign_totals = if ($prior.PSObject.Properties.Name -contains 'verification_campaign_totals') {
      $prior.verification_campaign_totals
    } else {
      $null
    }
  }
}
$checkpoint = [ordered]@{
  recorded_at = (Get-Date).ToUniversalTime().ToString('o')
  completed_item_range = $CompletedRange
  total_candidates = @($inventory.candidates).Count
  counts_by_status = $inventory.counts
  remaining_nonterminal = $remaining.Count
  next_pending_id = if ($NextPendingId) { $NextPendingId } else { $inventory.next_pending_id }
  blockers = $Blockers
  resume_command = $ResumeCommand
  verification_campaign_totals = if ($null -ne $prior -and $prior.PSObject.Properties.Name -contains 'verification_campaign_totals') {
    $prior.verification_campaign_totals
  } else {
    $null
  }
  history = $history
}
$checkpoint | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$checkpoint | ConvertTo-Json -Compress -Depth 8
