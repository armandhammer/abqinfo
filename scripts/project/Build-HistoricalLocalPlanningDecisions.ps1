[CmdletBinding()]
param(
  [string]$OutputPath = 'project-state/discovery/historical-local-planning-decisions.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$bikePage = 'content/transportation/bicycling/bike-plans.md'
$studiesPage = 'content/transportation/roadway-projects/studies.md'
$projectsPage = 'content/development-land-use/projects.md'
$redevelopmentPage = 'content/development-land-use/redevelopment-plans.md'
$districtTwoDocuments = 'https://www.cabq.gov/council/documents/councilor-district-2-documents/'
$redevelopmentIndex = 'https://www.cabq.gov/mra/redevelopment-areas'

$decisions = @(
  [pscustomobject][ordered]@{
    id='src-4dd0d7313497ab4e'; title='Albuquerque Comprehensive On-Street Bicycle Plan Technical Appendices'; date='2000'
    r2_key='transportation/bicycling/bike-plans/cabq-comprehensive-on-street-bicycle-plan-technical-appendices-2000.pdf'; canonical_page=$bikePage
    source_page='https://www.cabq.gov/parksandrecreation/recreation/bike/documents'
    description="Preserves the plan's supporting bicycle counts, crash analysis, public survey, route evaluations, facility costs, implementation priorities, and technical data used to develop Albuquerque's 2000 on-street bicycle network."
  }
  [pscustomobject][ordered]@{
    id='src-ce3c9f54fa83aba9'; title='Downtown Neighborhood Area Traffic Study'; date='2014'
    r2_key='transportation/roadway-projects/studies/cabq-downtown-neighborhood-area-traffic-study-2014.pdf'; canonical_page=$studiesPage; source_page=$districtTwoDocuments
    description='Evaluates Downtown neighborhood traffic, crashes, speeds, intersections, midblock crossings, Mountain Road safety, and public concerns, then recommends short- and long-term circulation, parking, crossing, and traffic-calming improvements.'
  }
  [pscustomobject][ordered]@{
    id='src-66d6dd3f2f7408bb'; title='Downtown Neighborhood Area Traffic Study Appendices'; date='2014'
    r2_key='transportation/roadway-projects/studies/cabq-downtown-neighborhood-area-traffic-study-appendices-2014.pdf'; canonical_page=$studiesPage; source_page=$districtTwoDocuments
    description="Preserves the Downtown study's supporting speed and traffic counts, turning movements, cost estimates, public meeting records, resident comments, analysis worksheets, and other technical documentation."
  }
  [pscustomobject][ordered]@{
    id='src-d83c6c8206910d55'; title='Albuquerque Rail Yards Master Plan'; date='2014'
    r2_key='development-land-use/projects/cabq-rail-yards-master-plan-2014.pdf'; canonical_page=$projectsPage
    source_page='https://www.cabq.gov/council/council/projects/current-projects/albuquerque-rail-yards-redevelopment'
    description='Preserves the original Rail Yards redevelopment framework, including site history, building conditions, community goals, land use, transportation, preservation, public spaces, infrastructure, environmental constraints, development concepts, and implementation.'
    large_file_assessment='71.06 MiB PDF with 238 image-rich pages of historic photographs, maps, architectural drawings, existing conditions, and development concepts. This is the smaller of two authoritative City copies; it is preserved unchanged because further compression could reduce the usefulness of detailed graphics. The 102.14 MiB City variant remains withheld pending human review for potentially unique pages.'
  }
  [pscustomobject][ordered]@{
    id='src-917173b06523dda9'; title='North Corridor Metropolitan Redevelopment Plan'; date='2020'
    r2_key='development-land-use/redevelopment-plans/cabq-north-corridor-mra-plan-2020.pdf'; canonical_page=$redevelopmentPage
    source_page='https://www.cabq.gov/mra/redevelopment-areas/north-corridor'
    description="Sets revitalization strategies for Albuquerque's North Corridor along Second and Fourth Streets, addressing catalytic sites, infrastructure, trails, transportation, housing, business support, public safety, cultural identity, and redevelopment tools."
  }
  [pscustomobject][ordered]@{
    id='src-d6d3b671040d9c5c'; title='Los Candelarias Village Center and Metropolitan Redevelopment Plan'; date='2001'
    r2_key='development-land-use/redevelopment-plans/cabq-los-candelarias-village-center-mra-plan-2001.pdf'; canonical_page=$redevelopmentPage; source_page=$redevelopmentIndex
    description='Coordinates land use, transportation, pedestrian improvements, building design, drainage, cultural identity, economic revitalization, and implementation for a village center around Twelfth Street and Candelaria Road in the North Valley.'
  }
  [pscustomobject][ordered]@{
    id='src-f4d3bc242320a9a3'; title='Railroad Metropolitan Redevelopment Plan'; date='1986'
    r2_key='development-land-use/redevelopment-plans/cabq-railroad-mra-plan-1986.pdf'; canonical_page=$redevelopmentPage; source_page=$redevelopmentIndex
    description="Preserves Albuquerque's 1986 redevelopment framework for the Railroad area, documenting blight findings, property boundaries, acquisition and disposition authority, public improvements, financing, relocation obligations, and implementation provisions."
  }
)

foreach ($decision in $decisions) {
  $words = @($decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { throw "$($decision.id) description has $words words." }
  $decision | Add-Member -NotePropertyName provenance_status -NotePropertyValue 'official City source page and byte-identical official file recorded'
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative City of Albuquerque PDF preserved without modification.',
    'Description reviewed against extracted text and representative visual inspection.'
  )
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
foreach ($decision in $decisions) {
  $candidate = @($inventory.candidates | Where-Object id -eq $decision.id)
  if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for '$($decision.id)'; found $($candidate.Count)." }
  $candidate = $candidate[0]
  if (-not $candidate.local_path -or -not (Test-Path -LiteralPath $candidate.local_path)) { throw "Missing local file for '$($decision.id)'." }
  $candidate.status = 'parsed'
  $candidate.provenance_status = [string]$decision.provenance_status
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Representative first, midpoint, and final pages visually inspected; PDF rendered successfully.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$largeVariant = @($inventory.candidates | Where-Object id -eq 'src-16d851caed2d2c01')
if ($largeVariant.Count -ne 1) { throw 'Expected one large Rail Yards variant candidate.' }
$largeVariant = $largeVariant[0]
$largeVariant.status = 'requires human review'
$largeVariant.validation_status = 'withheld: exceeds 100 MB production threshold'
$largeVariant.exclusion_reason = $null
$largeVariant.processing_notes = @(@($largeVariant.processing_notes) + @(
  'Exact size: 107101361 bytes (102.14 MiB); PDF; SHA-256 7f73040955cc31e45f1d0f18b3a4048ab214da30cc8ea8dac357ca8a0575bd04.',
  'Not uploaded: exceeds the 100 MB production threshold and lacks explicit approval for this specific file.',
  'A smaller authoritative 74515734-byte City copy of the 2014 Rail Yards Master Plan is included in this batch; the larger copy may contain unique pages and remains available locally for later comparison.'
) | Sort-Object -Unique)
$largeVariant.updated_at = (Get-Date).ToUniversalTime().ToString('o')

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
$json = $inventory | ConvertTo-Json -Depth 12
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), $json, [Text.UTF8Encoding]::new($false))

[ordered]@{schema_version=1;batch_id='historical-local-planning-31';decisions=$decisions} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;Withheld='src-16d851caed2d2c01';OutputPath=$OutputPath}|ConvertTo-Json -Compress
