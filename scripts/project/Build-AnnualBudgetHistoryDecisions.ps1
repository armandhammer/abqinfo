[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/annual-budget-history-decisions-2026-08-24.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$parentUrl = 'https://www.cabq.gov/dfa/budget/annual-budget'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$candidates = @($inventory.candidates | Where-Object {
  $_.parent_url -eq $parentUrl -and $_.status -eq 'parsed' -and $_.title -match 'Approved Budget|Performance Plan'
} | Sort-Object date,title)
if ($candidates.Count -ne 23) { throw "Expected 23 parsed historical documents; found $($candidates.Count)." }

$decisions = foreach ($candidate in $candidates) {
  $year = [regex]::Match([string]$candidate.date, '\d{4}').Value
  $isBudget = $candidate.title -match 'Approved Budget'
  $decision = [ordered]@{
    id = [string]$candidate.id
    title = [string]$candidate.title
    date = [string]$candidate.date
    canonical_page = 'content/city-data/budget-spending.md'
    source_page = $parentUrl
    direct_file_url = [string]$candidate.direct_file_url
    agency = 'City of Albuquerque'
    r2_key = if ($isBudget) { "city-data/budget-spending/cabq-approved-budget-fy$year.pdf" } else { "city-data/budget-spending/cabq-performance-plan-fy$year.pdf" }
    description = if ($isBudget) {
      "Preserves Albuquerque’s adopted Fiscal Year $year operating budget, including revenues, appropriations, department and program funding, staffing, performance measures, capital support, fund summaries, and financial assumptions for that budget cycle."
    } else {
      "Preserves Albuquerque’s Fiscal Year $year performance plan, documenting department missions, goals, services, workload measures, desired community conditions, and the performance framework used alongside that year’s approved budget."
    }
    processing_notes = @(
      'Original authoritative PDF preserved without modification after complete text extraction and representative-page visual review.'
    )
  }
  if ([int64]$candidate.size_bytes -gt 25MB) {
    $decision.large_file_assessment = 'The official PDF is unusually large because it contains roughly 400–470 pages of detailed budget tables, graphics, and departmental material. No smaller authoritative edition is linked from the City archive; optimization could reduce fidelity or alter the source, so the original should be preserved unchanged.'
  }
  $decision
}

$output = [ordered]@{batch_id='2026-08-24-annual-budget-history';decisions=@($decisions)}
$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
$output | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress
