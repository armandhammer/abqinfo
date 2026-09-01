[CmdletBinding()]
param(
  [string]$OutputPath = 'project-state/discovery/recent-high-value-decisions.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$decisions = @(
  [pscustomobject][ordered]@{
    id = 'src-c7b23be6a9c2dae9'
    title = 'MRCOG 2025 Annual Report'
    date = '2025'
    r2_key = 'city-data/regional-programs/mrcog-annual-report-2025.pdf'
    canonical_page = 'content/transportation/transportation-plans.md'
    source_page = 'https://www.mrcog-nm.gov/626/2025-Annual-Report'
    direct_file_url = 'https://www.mrcog-nm.gov/DocumentCenter/View/6879/2025-Annual-Report-PDF'
    description = "Summarizes MRCOG's 2025 work on regional growth, the Transitions 2045 plan, transportation safety, data management, bicycle and pedestrian counts, traffic management, Rio Metro service, Rail Runner facilities, and economic development."
  }
  [pscustomobject][ordered]@{
    id = 'src-56302a72a506fb36'
    title = 'MRMPO Performance Measures Target Assessment (2026)'
    date = '2026'
    r2_key = 'transportation/transportation-plans/mrmpo-performance-measures-target-assessment-2026.pdf'
    canonical_page = 'content/transportation/transportation-plans.md'
    source_page = 'https://www.mrcog-nm.gov/676/Performance-Based-Planning'
    direct_file_url = 'https://www.mrcog-nm.gov/DocumentCenter/View/7028/MPO-Performance-Measures-Appendix-Table_2026'
    description = "Compares the Albuquerque metropolitan area's latest federal transportation results with adopted targets for safety, pavement and bridge condition, travel reliability, freight, transit asset management, and public-transportation agency safety."
  }
  [pscustomobject][ordered]@{
    id = 'src-48b873837f28d1f8'
    title = 'Albuquerque 2025 General Obligation Bond Program by Purpose'
    date = '2025'
    r2_key = 'city-data/capital-spending/cabq-2025-go-bond-program-by-purpose.pdf'
    canonical_page = 'content/city-data/capital-spending.md'
    source_page = 'https://www.cabq.gov/municipaldevelopment/documents/2025-bond-program-by-purpose.pdf/view'
    direct_file_url = 'https://www.cabq.gov/municipaldevelopment/documents/2025-bond-program-by-purpose.pdf'
    description = "Compiles Albuquerque's voter-approved 2025 General Obligation Bond program by purpose, listing election questions, project scopes, and funding for streets, transit, drainage, parks, housing, redevelopment, public facilities, and other capital priorities."
  }
)

foreach ($decision in $decisions) {
  $wordCount = @($decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($wordCount -lt 20 -or $wordCount -gt 50) { throw "$($decision.id) description has $wordCount words." }
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative PDF preserved without modification.',
    'Description reviewed against complete extracted text and representative visual inspection.',
    'Selected under the recent-first, high-value review policy.'
  )
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$superseded = @(
  'src-315132875ee931d5',
  'src-679c1e001f4016c4',
  'src-4d2ff11d056e0122',
  'src-659fe7f2a2cb758d',
  'src-1081ee78bd665f71'
)
foreach ($id in $superseded) {
  $matches = @($inventory.candidates | Where-Object id -eq $id)
  if ($matches.Count -ne 1) { throw "Expected one inventory candidate for '$id'; found $($matches.Count)." }
  $candidate = $matches[0]
  $candidate.status = 'superseded'
  $candidate.validation_status = 'reconciled to comprehensive current program'
  $candidate.exclusion_reason = 'Separate purpose excerpt is contained in the archived 2025 General Obligation Bond Program by Purpose and the more detailed approved program book; publishing it separately would duplicate the same project list.'
  $candidate.cited_successors = @('src-48b873837f28d1f8','src-982cc018b0b8fc01')
  $candidate.processing_notes = @(
    @($candidate.processing_notes) +
    'Reviewed locally and reconciled as a purpose-specific excerpt of the comprehensive 2025 bond-program records.'
    | Sort-Object -Unique
  )
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) {
  $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count
}
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
[IO.File]::WriteAllText(
  [IO.Path]::GetFullPath($InventoryPath),
  ($inventory | ConvertTo-Json -Depth 12),
  [Text.UTF8Encoding]::new($false)
)

[ordered]@{
  schema_version = 1
  batch_id = 'recent-high-value-31'
  decisions = $decisions
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{
  Decisions = $decisions.Count
  SupersededExcerpts = $superseded.Count
  OutputPath = $OutputPath
} | ConvertTo-Json -Compress
