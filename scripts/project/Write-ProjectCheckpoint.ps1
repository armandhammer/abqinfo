[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/checkpoint.json',
  [string]$DpmManifestPath = 'project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json',
  [string]$CompletedRange = '',
  [string]$NextPendingId = '',
  [string[]]$Blockers = @(),
  [string]$ResumeCommand = 'powershell -NoProfile -ExecutionPolicy Bypass -File scripts/project/Test-Candidate.ps1 -UpdateInventory'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ConvertTo-ComparableJson {
  param([object]$Value)
  if ($null -eq $Value) { return 'null' }
  return ($Value | ConvertTo-Json -Depth 30 -Compress)
}

function Get-DpmAnnualConsolidationState {
  param([string]$ManifestPath)
  $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $ManifestPath | ConvertFrom-Json
  return [pscustomobject][ordered]@{
    state = 'corrected_local_packets_generated_upload_externally_gated'
    manifest = $ManifestPath
    component_count = [int](@($manifest.annual_packets | ForEach-Object { $_.component_count }) | Measure-Object -Sum).Sum
    packets = @($manifest.annual_packets | ForEach-Object {
      [pscustomobject][ordered]@{
        year = $_.year
        component_count = $_.component_count
        page_count = $_.resulting_page_count
        size_bytes = $_.resulting_size_bytes
        sha256 = $_.resulting_sha256
        local_output_path = $_.local_output_path
        proposed_r2_key = $_.proposed_r2_key
      }
    })
  }
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$terminal = @('validated','excluded','duplicate','superseded','blocked','requires human review')
$remaining = @($inventory.candidates | Where-Object { $_.status -notin $terminal })
$priorText = if (Test-Path -LiteralPath $OutputPath) { Get-Content -Raw -Encoding UTF8 -LiteralPath $OutputPath } else { $null }
$prior = if ($null -ne $priorText) { $priorText | ConvertFrom-Json -DateKind String } else { $null }

# Only these values are derived at checkpoint-refresh time. All other current
# top-level properties are durable metadata and must survive regeneration.
$derivedFields = @(
  'recorded_at', 'completed_item_range', 'total_candidates', 'counts_by_status',
  'remaining_nonterminal', 'next_pending_id', 'blockers', 'resume_command',
  'verification_campaign_totals', 'history', 'dpm_annual_consolidation'
)
$preservedMetadata = [ordered]@{}
if ($null -ne $prior) {
  foreach ($property in $prior.PSObject.Properties) {
    if ($property.Name -notin $derivedFields) { $preservedMetadata[$property.Name] = $property.Value }
  }
}

$dpmState = Get-DpmAnnualConsolidationState -ManifestPath $DpmManifestPath
$verificationTotals = if ($null -ne $prior -and $prior.PSObject.Properties.Name -contains 'verification_campaign_totals') { $prior.verification_campaign_totals } else { $null }
$nextId = if ($NextPendingId) { $NextPendingId } else { $inventory.next_pending_id }
$stateForComparison = [ordered]@{
  completed_item_range = $CompletedRange
  total_candidates = @($inventory.candidates).Count
  counts_by_status = $inventory.counts
  remaining_nonterminal = $remaining.Count
  next_pending_id = $nextId
  blockers = @($Blockers)
  resume_command = $ResumeCommand
  verification_campaign_totals = $verificationTotals
  dpm_annual_consolidation = $dpmState
  durable_metadata = $preservedMetadata
}
$priorStateForComparison = if ($null -ne $prior) {
  $priorDpm = if ($prior.PSObject.Properties.Name -contains 'dpm_annual_consolidation') { $prior.dpm_annual_consolidation } else { $null }
  [ordered]@{
    completed_item_range = $prior.completed_item_range
    total_candidates = $prior.total_candidates
    counts_by_status = $prior.counts_by_status
    remaining_nonterminal = $prior.remaining_nonterminal
    next_pending_id = $prior.next_pending_id
    blockers = @($prior.blockers)
    resume_command = $prior.resume_command
    verification_campaign_totals = $verificationTotals
    dpm_annual_consolidation = $priorDpm
    durable_metadata = $preservedMetadata
  }
} else { $null }
$stateChanged = $null -eq $prior -or (ConvertTo-ComparableJson $stateForComparison) -ne (ConvertTo-ComparableJson $priorStateForComparison)

$history = if ($null -ne $prior -and $prior.PSObject.Properties.Name -contains 'history') { @($prior.history) } else { @() }
# A valid checkpoint never stores shell-placeholder values (for example,
# ".next_pending_id") in history. Exclude only those malformed transient
# entries; preserve all ordinary historical checkpoints verbatim.
$history = @($history | Where-Object {
  -not ([string]$_.completed_item_range).StartsWith('.') -and
  -not ([string]$_.next_pending_id).StartsWith('.') -and
  -not ([string]$_.resume_command).StartsWith('.')
})
$priorIsMalformed = $null -ne $prior -and (
  ([string]$prior.completed_item_range).StartsWith('.') -or
  ([string]$prior.next_pending_id).StartsWith('.') -or
  ([string]$prior.resume_command).StartsWith('.')
)
if ($stateChanged -and $null -ne $prior -and -not $priorIsMalformed) {
  $historicalMetadata = [ordered]@{}
  foreach ($property in $prior.PSObject.Properties) {
    if ($property.Name -notin @('recorded_at', 'completed_item_range', 'total_candidates', 'counts_by_status', 'remaining_nonterminal', 'next_pending_id', 'blockers', 'resume_command', 'verification_campaign_totals', 'history')) {
      $historicalMetadata[$property.Name] = $property.Value
    }
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
    verification_campaign_totals = $verificationTotals
    durable_metadata = [pscustomobject]$historicalMetadata
  }
}

$checkpoint = [ordered]@{
  recorded_at = if ($stateChanged) { (Get-Date).ToUniversalTime().ToString('o') } else { $prior.recorded_at }
  completed_item_range = $CompletedRange
  total_candidates = @($inventory.candidates).Count
  counts_by_status = $inventory.counts
  remaining_nonterminal = $remaining.Count
  next_pending_id = $nextId
  blockers = @($Blockers)
  resume_command = $ResumeCommand
  verification_campaign_totals = $verificationTotals
  dpm_annual_consolidation = $dpmState
}
foreach ($name in $preservedMetadata.Keys) { $checkpoint[$name] = $preservedMetadata[$name] }
$checkpoint.history = $history

$json = $checkpoint | ConvertTo-Json -Depth 30
$desiredText = "$json`r`n"
if ($priorText -ne $desiredText) {
  [System.IO.File]::WriteAllText([System.IO.Path]::GetFullPath($OutputPath), $desiredText, [System.Text.UTF8Encoding]::new($false))
}
$checkpoint | ConvertTo-Json -Compress -Depth 30
