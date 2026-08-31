[CmdletBinding()]
param(
  [string]$OutputPath = 'project-state/discovery/local-planning-transit-history-decisions.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$areaPlans = 'content/development-land-use/area-sector-plans.md'
$studies = 'content/transportation/roadway-projects/studies.md'
$speed = 'content/transportation/roadway-projects/speed-management.md'
$abqRide = 'content/transportation/transit/abq-ride.md'
$maps = 'content/maps/maps.md'

$decisions = @(
  [pscustomobject][ordered]@{
    id='src-e8d18ebb99858984'; title='Volcano Trails Environmental Planning Commission Official Notice of Decision'; date='2011'
    r2_key='development-land-use/area-sector-plans/cabq-volcano-trails-epc-notice-of-decision-2011.pdf'; canonical_page=$areaPlans
    source_page='https://www.cabq.gov/council/projects/completed-projects/2011/volcano-trails-sector-development-plan'
    description="Records the Environmental Planning Commission's recommendation to approve the Volcano Trails plan, including findings, zoning analysis, agency comments, public testimony, and detailed conditions forwarded to City Council."
  }
  [pscustomobject][ordered]@{
    id='src-d25ae9b6c27b4b2c'; title='Rio Grande Boulevard Corridor Plan'; date='1989'
    r2_key='transportation/roadway-projects/studies/cabq-rio-grande-boulevard-corridor-plan-1989.pdf'; canonical_page=$studies
    source_page='https://www.cabq.gov/council/documents/rio-grande-corridor-documents'
    description="Preserves the 1989 framework for Rio Grande Boulevard, covering land use, traffic, bicycle and pedestrian conditions, landscaping, drainage, intersections, neighborhood concerns, design alternatives, implementation priorities, and estimated costs."
  }
  [pscustomobject][ordered]@{
    id='src-4f52cc9a9cc25828'; title='Manzano/Four Hills Open Space Trail Map'; date='2021'
    r2_key='maps/cabq-manzano-four-hills-open-space-trail-map-2021.pdf'; canonical_page=$maps
    source_page='https://www.cabq.gov/parksandrecreation/open-space/facilities-map'
    description="Maps official trails, Open Space boundaries, access points, surrounding streets, and aerial context for the Manzano/Four Hills property beside Tijeras Arroyo in southeast Albuquerque."
  }
  [pscustomobject][ordered]@{
    id='src-6104954a4bb9d83f'; title='NTMP Adoption Resolution R-14-99 Floor Amendment 1'; date='2015'
    r2_key='transportation/roadway-projects/speed-management/cabq-ntmp-r-14-99-floor-amendment-1-2015.pdf'; canonical_page=$speed
    source_page='https://www.cabq.gov/council/projects/completed-projects/2015/neighborhood-traffic-management-program-policy-manual'
    description="Requires Municipal Development to report to City Council on NTMP effectiveness, applications, qualifying requests, funding availability, and anticipated implementation schedules two years after adoption."
  }
  [pscustomobject][ordered]@{
    id='src-9608715e6616b5ca'; title='NTMP Adoption Resolution R-14-99 Floor Amendment 2'; date='2015'
    r2_key='transportation/roadway-projects/speed-management/cabq-ntmp-r-14-99-floor-amendment-2-2015.pdf'; canonical_page=$speed
    source_page='https://www.cabq.gov/council/projects/completed-projects/2015/neighborhood-traffic-management-program-policy-manual'
    description="Clarifies the NTMP definition of cut-through traffic as travel through a residential neighborhood without an origin or destination on the street and specifies license-plate sampling for volume analysis."
  }
  [pscustomobject][ordered]@{
    id='src-36aeae26d4bb7572'; title='Summit Park and North Campus Neighborhood Transportation Management Plan'; date='2009'
    r2_key='transportation/roadway-projects/speed-management/cabq-summit-park-north-campus-neighborhood-transportation-management-plan-2009.pdf'; canonical_page=$speed
    source_page='https://www.cabq.gov/council/projects/completed-projects/2012/summit-park-north-campus-neighborhood-traffic-management-plan'
    description="Documents neighborhood traffic, speed, parking, walking, bicycling, school-access, and cut-through concerns, then maps short- and long-term traffic-calming, crossing, sidewalk, bicycle, enforcement, and circulation recommendations."
  }
  [pscustomobject][ordered]@{
    id='src-01a8eebf280d76a6'; title='ABQ RIDE 2009 General Obligation Bond Capital Scope'; date='2009'
    r2_key='transportation/transit/abq-ride/cabq-abq-ride-general-obligation-bond-capital-scope-2009.pdf'; canonical_page=$abqRide
    source_page='https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2009-go-bond-documents'
    description="Allocates 7.75 million dollars in 2009 City bond funding for buses, park-and-ride facilities, shelters, transit technology, facility rehabilitation, maintenance equipment, and security improvements."
  }
)

foreach ($decision in $decisions) {
  $words = @($decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { throw "$($decision.id) description has $words words." }
  $decision | Add-Member -NotePropertyName provenance_status -NotePropertyValue 'official government source page and authoritative file URL recorded'
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative government PDF preserved without modification.',
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

$duplicates = @(
  [pscustomobject]@{id='src-5f452be402579a19'; canonical='src-cb3254288f19ff4a'; reason='Byte-identical duplicate of the validated Rio Metro Budget and Capital Plan, FY2027-FY2031 already archived and implemented on the Rail Runner page.'}
  [pscustomobject]@{id='src-067da2bf9c878174'; canonical='src-d50cd2863da4f4be'; reason='Byte-identical duplicate of the validated 2023 Rail Runner system map already archived and cross-listed on the Rail Runner and Maps pages.'}
  [pscustomobject]@{id='src-b4b080417eadd7ed'; canonical='src-81cd99e1578af090'; reason='Byte-identical duplicate of the validated Rio Metro FY2012-FY2017 short-range plan already archived and implemented on the Rail Runner page.'}
  [pscustomobject]@{id='src-f9fcc0f8b0cba13e'; canonical='src-175afc4f0e4b8e24'; reason='Byte-identical duplicate of the validated 2013 draft Girard Boulevard Complete Street Master Plan already archived on the roadway studies page.'}
  [pscustomobject]@{id='src-6b9fccdac6a4fc63'; canonical='src-01a8eebf280d76a6'; reason='Near-identical duplicate of the 2009 ABQ RIDE bond scope: extracted text and rendered content match; the three-byte difference is non-substantive PDF metadata.'}
)

foreach ($duplicate in $duplicates) {
  $candidate = @($inventory.candidates | Where-Object id -eq $duplicate.id)[0]
  $candidate.status = 'duplicate'
  $candidate.exclusion_reason = "$($duplicate.reason) Canonical inventory record: $($duplicate.canonical)."
  $candidate.validation_status = 'duplicate reconciled by checksum or rendered-content comparison'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Reviewed in the local planning and transit-history batch; duplicate content will not be uploaded again.' | Sort-Object -Unique)
  if ($duplicate.id -eq 'src-f9fcc0f8b0cba13e') {
    $candidate.processing_notes = @(@($candidate.processing_notes) + 'File-size review: 33167254 bytes (31.63 MiB), PDF, unusually large because its 59 illustrated pages contain corridor maps, photographs, cross-sections, and design concepts. No smaller authoritative version was identified. Optimization could reduce image fidelity and is unnecessary because the unchanged authoritative file is already archived; projected R2 storage added for this duplicate is zero bytes.' | Sort-Object -Unique)
  }
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$exclusions = @(
  [pscustomobject]@{id='src-9bb008484007e933'; reason='Expired one-week construction traffic report from August 2025; the maintained live traffic map provides current information and this snapshot has no durable planning value.'}
  [pscustomobject]@{id='src-aef0ad3451266b39'; reason='Generic example lane-closure sheet for contractor traffic-control submissions; it is an administrative template rather than an Albuquerque plan, project record, or adopted standard.'}
  [pscustomobject]@{id='src-465eff5cac222168'; reason='Temporary construction traffic-control sheet for the Goff Boulevard project; the substantive project plan and public information are more useful than this staging diagram.'}
  [pscustomobject]@{id='src-84a4ef1b023a9002'; reason='Temporary detour and traffic-control sheet associated with construction; it does not add durable planning, design, or project-history information.'}
)

foreach ($exclusion in $exclusions) {
  $candidate = @($inventory.candidates | Where-Object id -eq $exclusion.id)[0]
  $candidate.status = 'excluded'
  $candidate.exclusion_reason = $exclusion.reason
  $candidate.validation_status = 'excluded after relevance and durability review'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Reviewed in the local planning and transit-history batch; excluded under ABQInfo relevance and durability criteria.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

[ordered]@{schema_version=1;batch_id='local-planning-transit-history-34';decisions=$decisions} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;Duplicates=$duplicates.Count;Exclusions=$exclusions.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress
