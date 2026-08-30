[CmdletBinding()]
param([string]$OutputPath = 'project-state/discovery/north-fourth-historical-review-26-decisions.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$page = 'content/development-land-use/area-sector-plans.md'
$sourcePage = 'https://www.cabq.gov/council/projects/completed-projects/2010/north-4th-street-rank-iii-corridor-plan'
$decisions = @(
  [pscustomobject][ordered]@{
    id = 'src-6479e8efc5bcc2b6'
    title = 'North Fourth Street Rank III Corridor Plan - City Council Draft'
    date = '2010'
    r2_key = 'development-land-use/area-sector-plans/cabq-north-fourth-street-rank-iii-corridor-plan-city-council-draft-2010.pdf'
    canonical_page = $page
    source_page = $sourcePage
    description = 'Preserves the 133-page City Council draft combining corridor history, form-based zoning, building and frontage standards, transportation and street design, and redevelopment strategies for North Fourth Street from Mountain Road to the Los Ranchos boundary.'
  }
  [pscustomobject][ordered]@{
    id = 'src-925265ba30c142c1'
    title = 'North Fourth Street Background and Resources Materials'
    date = '2009'
    r2_key = 'development-land-use/area-sector-plans/cabq-north-fourth-street-background-resources-2009.pdf'
    canonical_page = $page
    source_page = $sourcePage
    description = 'Preserves the plan''s companion research volume, including negotiated community recommendations, demographics, land use, real-estate and business conditions, traffic and transit analysis, urban-design studies, streetscape cost estimates, and historic-preservation material.'
  }
  [pscustomobject][ordered]@{
    id = 'src-7ef6d021d2326e49'
    title = 'North Fourth Street Existing Zoning Map'
    date = '2009-12-15'
    r2_key = 'development-land-use/area-sector-plans/cabq-north-fourth-street-existing-zoning-map-2009.pdf'
    canonical_page = $page
    source_page = $sourcePage
    description = 'Maps the zoning districts in effect along the North Fourth Street study corridor in December 2009, providing a historical baseline for interpreting the plan''s proposed form-based overlay and redevelopment recommendations.'
    implementation_locations = @($page, 'content/maps/maps.md')
    cross_listing_approved = $true
  }
  [pscustomobject][ordered]@{
    id = 'src-5cdd997502c0d388'
    title = 'North Fourth Street Form-Based Overlay Zone Map'
    date = '2009-12-15'
    r2_key = 'development-land-use/area-sector-plans/cabq-north-fourth-street-form-based-overlay-zone-map-2009.pdf'
    canonical_page = $page
    source_page = $sourcePage
    description = 'Maps the North Fourth Street plan''s proposed transit-oriented, mixed-use, and infill-development overlay districts in December 2009, showing the corridor and study boundaries used during the City Council draft process.'
    implementation_locations = @($page, 'content/maps/maps.md')
    cross_listing_approved = $true
  }
)

foreach ($decision in $decisions) {
  $words = @($decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { throw "$($decision.id) description has $words words." }
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative City PDF preserved without modification.',
    'Official City page identifies the plan files as City Council drafts; ABQInfo labels them accordingly.',
    'Description reviewed against extracted text and representative visual inspection.'
  )
}

[ordered]@{
  schema_version = 1
  batch_id = 'north-fourth-historical-review-26'
  decisions = $decisions
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{ Decisions = $decisions.Count; OutputPath = $OutputPath } | ConvertTo-Json -Compress
