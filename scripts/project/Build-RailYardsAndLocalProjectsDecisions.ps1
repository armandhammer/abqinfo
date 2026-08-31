[CmdletBinding()]
param(
  [string]$OutputPath = 'project-state/discovery/rail-yards-local-projects-decisions.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$railYardsPage = 'content/development-land-use/projects.md'
$speedPage = 'content/transportation/roadway-projects/speed-management.md'
$parksPage = 'content/public-works/parks-recreation.md'
$ranchoPage = 'https://www.cabq.gov/council/find-your-councilor/district-5/district-5-projects/district-5-traffic-projects/rancho-sereno-las-terrezas-traffic-calming-study'
$tijerasPage = 'https://www.cabq.gov/parksandrecreation/open-space/lands/tijeras-cultural-corridor'

$decisions = @(
  [pscustomobject][ordered]@{
    id='src-16d851caed2d2c01'; title='Rail Yards Master Plan Retained City Copy With Adoption and Amendments'; date='2018'
    r2_key='development-land-use/projects/cabq-rail-yards-master-plan-retained-2018.pdf'; canonical_page=$railYardsPage
    source_page='https://www.cabq.gov/council/council/projects/current-projects/albuquerque-rail-yards-redevelopment'
    description="Preserves the City's July 2018 retained-plan compilation: the adopted 2014 Rail Yards master plan, its formal adoption history, and appended resolutions recording the original approval and subsequent zoning and plan-type amendments."
    large_file_assessment='102.14 MiB PDF with 265 image-rich pages of historic photographs, maps, architectural drawings, technical appendices, and legislation. It is unusually large because it combines the full illustrated plan with adoption and amendment records. A smaller 71.06 MiB authoritative 2014 plan-only copy exists and remains separately archived. The original is preserved unchanged; recompression could reduce the usefulness of detailed graphics. Upload explicitly approved by the user on 2026-08-30. Projected R2 storage after the full batch is 7281384128 bytes.'
  }
  [pscustomobject][ordered]@{
    id='src-7d61498dd115170d'; title='Rancho Sereno/Las Terrezas Traffic-Calming Study Public Meeting 1'; date='2021'
    r2_key='transportation/roadway-projects/speed-management/cabq-rancho-sereno-las-terrezas-public-meeting-1-2021.pdf'; canonical_page=$speedPage; source_page=$ranchoPage
    description="Documents the study area, emergency routes, crash history, speed and volume data, NTMP process, and traffic-calming options presented for Rancho Sereno, Butterfield Trail, Las Terrezas, Calle Norteña, and Rancho Milagro."
  }
  [pscustomobject][ordered]@{
    id='src-ca1359ac633453a9'; title='Rancho Sereno/Las Terrezas Traffic-Calming Study Public Meeting 2'; date='2022'
    r2_key='transportation/roadway-projects/speed-management/cabq-rancho-sereno-las-terrezas-public-meeting-2-2022.pdf'; canonical_page=$speedPage; source_page=$ranchoPage
    description="Records the refined traffic-calming concepts and recommendations following the first meeting, including speed cushions, lane narrowing, median treatments, intersection changes, pedestrian improvements, public feedback, and preferred options."
  }
  [pscustomobject][ordered]@{
    id='src-94437ce17eaa523c'; title='Tijeras Bio-Zone Education Center Proposed Site Plan'; date='2024'
    r2_key='public-works/parks-recreation/cabq-tijeras-bio-zone-education-center-proposed-site-plan-2024.pdf'; canonical_page=$parksPage; source_page=$tijerasPage
    description="Provides a readable one-sheet design concept for the education center, locating accessible paths, parking, campsites, restrooms, shelters, outdoor learning areas, sensory-trail features, landscape restoration, event space, and caretaker facilities."
  }
  [pscustomobject][ordered]@{
    id='src-a61566721d63d9e1'; title='Route 66 Open Space Trailhead Draft Construction Drawings'; date='2023'
    r2_key='public-works/parks-recreation/cabq-route-66-open-space-trailhead-construction-drawings-2023.pdf'; canonical_page=$parksPage; source_page=$tijerasPage
    description="Preserves the seven-sheet draft construction set for the Route 66 Open Space trailhead, including parking, equestrian access, accessible paths, trail connections, signage, shade, restroom facilities, grading, dimensions, and site details."
  }
  [pscustomobject][ordered]@{
    id='src-efd20a6e9d1b0fd8'; title='Tijeras Bio-Zone Education Center Existing Conditions and Site Analysis'; date='2023'
    r2_key='public-works/parks-recreation/cabq-tijeras-bio-zone-education-center-existing-conditions-site-analysis-2023.pdf'; canonical_page=$parksPage; source_page=$tijerasPage
    description="Documents the site's cultural timeline, creek and aquifer context, vegetation, historic uses, disturbed areas, access, drainage, existing facilities, photographs, and cross-sections used to inform the education-center design."
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

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

[ordered]@{schema_version=1;batch_id='rail-yards-local-projects-32';decisions=$decisions} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress
