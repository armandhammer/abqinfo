[CmdletBinding()]
param(
  [Parameter(Mandatory)][string[]]$Urls,
  [Parameter(Mandatory)][ValidateSet('pending review','approved for addition','downloading','downloaded','parsed','description drafted','placement assigned','implemented','validated','excluded','duplicate','superseded','blocked','requires human review')][string]$Status,
  [string]$ValidationStatus,
  [string]$Note,
  [string]$ExclusionReason,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$normalized = @($Urls | ForEach-Object { $_.Trim().TrimEnd('/') } | Sort-Object -Unique)
$changed = @()
foreach ($candidate in $inventory.candidates) {
  $candidateUrls = @($candidate.source_url,$candidate.direct_file_url,$candidate.r2_url) |
    Where-Object { $_ } | ForEach-Object { ([string]$_).Trim().TrimEnd('/') }
  if (-not @($candidateUrls | Where-Object { $_ -in $normalized }).Count) { continue }
  $candidate.status = $Status
  if ($ValidationStatus) { $candidate.validation_status = $ValidationStatus }
  if ($ExclusionReason) { $candidate.exclusion_reason = $ExclusionReason }
  if ($Note) { $candidate.processing_notes = @($candidate.processing_notes) + $Note }
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  $changed += $candidate
}
$missing = @($normalized | Where-Object { $url=$_; -not @($inventory.candidates | Where-Object { @($_.source_url,$_.direct_file_url,$_.r2_url) | Where-Object { $_ -and ([string]$_).Trim().TrimEnd('/') -eq $url } }).Count })
if ($missing.Count) { throw "Candidate URLs not found: $($missing -join ', ')" }
$counts = [ordered]@{}
foreach ($allowed in $inventory.allowed_statuses) { $counts[$allowed] = @($inventory.candidates | Where-Object status -eq $allowed).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($inventory.candidates | Where-Object status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned','implemented') | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
$inventory | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $InventoryPath -Encoding utf8
[pscustomobject]@{Changed=$changed.Count;Status=$Status;Counts=$counts} | ConvertTo-Json -Depth 5
