[CmdletBinding()]
param(
  [string]$ResearchPath = 'project-state/discovery/early-go-bond-cluster-research-2026-09-11.json',
  [string]$OutputPath = 'project-state/discovery/early-go-bond-archive-decisions-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$research = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath | ConvertFrom-Json
$keys = @{
  'src-cae140d675779242' = 'city-data/capital-spending/cabq-2003-capital-improvements-priorities-resolution-r-02-30.pdf'
  'src-93085b1bc76f4709' = 'city-data/capital-spending/cabq-2003-2012-decade-plan-capital-budget-resolution-r-03-215.pdf'
  'src-d86965da6d5d26f2' = 'city-data/capital-spending/cabq-2003-capital-budget-amendment-resolution-r-03-265.pdf'
  'src-57a1e412247c863d' = 'city-data/capital-spending/cabq-2003-go-bond-funding-allocation-chart.pdf'
  'src-3dfd629f27870dc1' = 'city-data/capital-spending/cabq-2003-go-bond-rehabilitation-maintenance-deficiency-summary.pdf'
  'src-6fc996f849849028' = 'city-data/capital-spending/cabq-2003-street-go-bond-project-scopes.pdf'
  'src-96e217080e84c14e' = 'city-data/capital-spending/cabq-2003-parks-recreation-go-bond-project-scopes.pdf'
  'src-321df68eff322421' = 'city-data/capital-spending/cabq-2003-senior-family-community-center-go-bond-project-scopes.pdf'
  'src-3c7653f64815b4ad' = 'city-data/capital-spending/cabq-2003-zoo-biological-park-museum-go-bond-project-scopes.pdf'
  'src-a24b9d451e022e8f' = 'city-data/capital-spending/cabq-2003-public-facilities-equipment-system-modernization-go-bond-project-scopes.pdf'
  'src-e7cd892adf805950' = 'city-data/capital-spending/cabq-2003-public-transportation-go-bond-project-scopes.pdf'
  'src-ea516f826e5da86a' = 'city-data/capital-spending/cabq-2003-police-go-bond-project-scopes.pdf'
  'src-724dd13839ecb166' = 'city-data/capital-spending/cabq-2003-fire-protection-go-bond-project-scopes.pdf'
  'src-888427a6abc5edf0' = 'city-data/capital-spending/cabq-2003-library-go-bond-project-scopes.pdf'
  'src-230753126ba3bbf7' = 'development-land-use/development-process/cabq-consultant-compensation-rules-2003.pdf'
  'src-8c5d2888cc22b991' = 'city-data/capital-spending/cabq-2004-street-go-bond-project-titles-amounts-scopes.pdf'
  'src-f1a9e4e7e1d84e9e' = 'city-data/capital-spending/cabq-2004-capital-programming-amendment-resolution-r-04-109.pdf'
  'src-6ebb9f0834bce393' = 'city-data/capital-spending/cabq-2004-street-bond-program-planning-process.pdf'
  'src-a58b458f5d0f5284' = 'city-data/capital-spending/cabq-2004-street-bond-ballot-question.pdf'
}

$decisions = foreach ($item in $research.approved_for_addition) {
  if (-not $keys.ContainsKey([string]$item.id)) { throw "Missing R2 key for $($item.id)." }
  $locations = @([string]$item.proposed_canonical_page) + @($item.proposed_cross_listings)
  [ordered]@{
    id = [string]$item.id
    title = [string]$item.title
    date = [string]$item.date
    source_page = ([string]$item.authoritative_url + '/view')
    direct_file_url = [string]$item.authoritative_url
    r2_key = [string]$keys[[string]$item.id]
    canonical_page = [string]$item.proposed_canonical_page
    implementation_locations = @($locations)
    cross_listing_approved = [bool](@($locations).Count -gt 1)
    description = [string]$item.description
    provenance_status = 'official City of Albuquerque PDF fetched directly; exact byte size and SHA-256 verified against the reviewed research artifact'
    processing_notes = @(
      [string]$item.evidence,
      'Original authoritative PDF selected for byte-identical archival without modification.'
    )
  }
}

if (@($decisions).Count -ne 19) { throw "Expected 19 archive decisions; found $(@($decisions).Count)." }
[ordered]@{
  schema_version = 1
  batch_id = 'early-go-bond-archive-2026-09-11'
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  source_research = $ResearchPath
  decisions = @($decisions)
} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{ Items = @($decisions).Count; OutputPath = $OutputPath } | ConvertTo-Json -Compress
