[CmdletBinding()]
param(
  [string]$ResearchPath = 'project-state/discovery/go2011-bond-cluster-research-2026-09-11.json',
  [string]$OutputPath = 'project-state/discovery/go2011-bond-archive-decisions-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$research = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath | ConvertFrom-Json
$keys = @{
  'src-2746069f062780cf' = 'city-data/capital-spending/cabq-2011-2019-go-bond-summary-totals.pdf'
  'src-75f032fd59799df5' = 'city-data/capital-spending/cabq-2011-council-neighborhood-set-aside-project-scopes.pdf'
  'src-d30fe509d51eec50' = 'transportation/transportation-plans/cabq-2011-streets-go-bond-project-scopes-published.pdf'
  'src-be70a79a59ae0915' = 'transportation/transportation-plans/cabq-2011-streets-go-bond-project-scopes-initial.pdf'
  'src-2663fc607177e07d' = 'public-works/stormwater/cabq-2011-storm-drainage-go-bond-project-scopes-published.pdf'
  'src-2daae0eb6e136555' = 'city-data/capital-spending/cabq-2011-finance-administrative-services-go-bond-project-scopes-published.pdf'
  'src-b7f0628556085641' = 'development-land-use/redevelopment/cabq-2011-planning-go-bond-project-scopes-published.pdf'
  'src-89b36d5577443f99' = 'development-land-use/redevelopment/cabq-2011-planning-go-bond-project-scopes-initial.pdf'
  'src-352694313c3e5710' = 'city-data/capital-spending/cabq-2011-family-community-services-go-bond-project-scopes-published.pdf'
  'src-b08cdbd2624ad1a0' = 'city-data/capital-spending/cabq-2011-family-community-services-go-bond-project-scopes-initial.pdf'
  'src-2ed981e6df5e99d2' = 'public-works/city-facilities/cabq-2011-city-facilities-cip-parking-go-bond-project-scopes-published.pdf'
  'src-4bafa6f452f2f586' = 'city-data/capital-spending/cabq-2011-environmental-health-go-bond-project-scopes-published.pdf'
  'src-afc7fa6f1c4ac06f' = 'city-data/capital-spending/cabq-2011-cultural-services-go-bond-project-scopes-published.pdf'
  'src-27d391d187280ced' = 'public-works/parks-recreation/cabq-2011-parks-recreation-go-bond-project-scopes-published.pdf'
  'src-b37593a011f57fae' = 'transportation/transit/cabq-2011-abq-ride-go-bond-project-scopes-published.pdf'
  'src-f74d655ffb05fd08' = 'city-data/public-safety/cabq-2011-police-go-bond-project-scopes-published.pdf'
  'src-db9fefd23083da69' = 'city-data/public-safety/cabq-2011-fire-go-bond-project-scopes-published.pdf'
  'src-e6ca25d4cfa80752' = 'city-data/public-safety/cabq-2011-fire-go-bond-project-scopes-initial.pdf'
  'src-b90b07ac62c4f7fd' = 'city-data/capital-spending/cabq-2011-senior-affairs-go-bond-project-scopes-published.pdf'
  'src-54665bf864159096' = 'city-data/capital-spending/cabq-2011-affordable-housing-go-bond-project-scope-published.pdf'
  'src-25501032bfbfa682' = 'city-data/capital-spending/cabq-2011-affordable-housing-go-bond-project-scope-initial.pdf'
  'src-4cd84ecef3756fb0' = 'city-data/capital-spending/cabq-2011-2019-senior-affairs-go-bond-schedule.pdf'
  'src-542056c326cf2578' = 'city-data/capital-spending/cabq-2011-2019-finance-administrative-services-go-bond-schedule-initial.pdf'
  'src-a547a0278fb86fb9' = 'city-data/public-safety/cabq-2011-2019-fire-go-bond-schedule-initial.pdf'
  'src-c9af414f77032660' = 'development-land-use/redevelopment/cabq-2011-2019-planning-go-bond-schedule-initial.pdf'
  'src-a31943aca401c7f0' = 'transportation/transportation-plans/cabq-2011-2019-streets-go-bond-schedule-initial.pdf'
}

$crossListings = @{
  'src-d30fe509d51eec50' = 'content/transportation/transportation-plans.md'
  'src-2663fc607177e07d' = 'content/public-works/stormwater-drainage.md'
  'src-b7f0628556085641' = 'content/development-land-use/redevelopment-plans.md'
  'src-2ed981e6df5e99d2' = 'content/public-works/city-facilities.md'
  'src-27d391d187280ced' = 'content/public-works/parks-recreation.md'
  'src-b37593a011f57fae' = 'content/transportation/transit/abq-ride.md'
  'src-f74d655ffb05fd08' = 'content/city-data/public-safety-data.md'
  'src-db9fefd23083da69' = 'content/city-data/public-safety-data.md'
}

$decisions = foreach ($item in $research.approved_for_addition) {
  $id = [string]$item.id
  if (-not $keys.ContainsKey($id)) { throw "Missing R2 key for $id." }
  $locations = @([string]$item.proposed_canonical_page)
  if ($crossListings.ContainsKey($id)) { $locations += [string]$crossListings[$id] }
  [ordered]@{
    id = $id
    title = [string]$item.title
    date = '2011'
    source_page = ([string]$item.authoritative_url + '/view')
    direct_file_url = [string]$item.authoritative_url
    r2_key = [string]$keys[$id]
    canonical_page = [string]$item.proposed_canonical_page
    implementation_locations = @($locations)
    cross_listing_approved = [bool]($locations.Count -gt 1)
    description = [string]$item.description
    provenance_status = 'official City of Albuquerque PDF fetched directly; exact byte size and SHA-256 verified against the reviewed research artifact'
    processing_notes = @(
      [string]$item.evidence,
      'Original authoritative PDF selected for byte-identical archival without modification.'
    )
  }
}

if (@($decisions).Count -ne 26) { throw "Expected 26 archive decisions; found $(@($decisions).Count)." }
[ordered]@{
  schema_version = 1
  batch_id = 'go2011-bond-archive-2026-09-11'
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  source_research = $ResearchPath
  decisions = @($decisions)
} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{ Items = @($decisions).Count; OutputPath = $OutputPath } | ConvertTo-Json -Compress
