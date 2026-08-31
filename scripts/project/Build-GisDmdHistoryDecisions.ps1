[CmdletBinding()]
param(
  [string]$OutputPath = 'project-state/discovery/gis-dmd-history-decisions.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$development = 'content/development-land-use/development-process.md'
$transportPlans = 'content/transportation/transportation-plans.md'
$design = 'content/transportation/design-references.md'
$parks = 'content/public-works/parks-recreation.md'
$facilities = 'content/public-works/city-facilities.md'
$redevelopment = 'content/development-land-use/redevelopment-plans.md'
$stormwater = 'content/public-works/stormwater-drainage.md'

$decisions = @(
  [pscustomobject][ordered]@{
    id='src-0b9dc46fbf32cfb7'; title='Development Process Manual'; date='2020'
    r2_key='housing/development-process/development-process-manual-2020-06-02.pdf'; canonical_page=$development
    source_page='https://documents.cabq.gov/planning/development-process-manual/'
    description='Consolidates Albuquerque requirements for development review, transportation and drainage infrastructure, streets, sidewalks, bikeways, utilities, landscaping, construction, inspections, and acceptance of public improvements in the manual effective June 8, 2020.'
    implementation_locations=@($development,$transportPlans); cross_listing_approved=$true
  }
  [pscustomobject][ordered]@{
    id='src-40193914b85bdf2c'; title='Wells Park NeighborWoods Final Report'; date='2020-06'
    r2_key='public-works/parks-recreation/cabq-wells-park-neighborwoods-final-report-2020.pdf'; canonical_page=$parks
    source_page='https://www.cabq.gov/council/albuquerque-neighborwoods/district-2-neighborwoods'
    description="Evaluates Albuquerque's first NeighborWoods planting in Wells Park, documenting 109 street trees, three-year survivability, canopy and environmental benefits, species performance, watering challenges, volunteer practices, and lessons used to improve later neighborhood plantings."
  }
  [pscustomobject][ordered]@{
    id='src-2cf447cc8b453482'; title='Double Eagle II Airport Master Plan'; date='2019; amended 2024'
    r2_key='transportation/transportation-plans/cabq-double-eagle-ii-airport-master-plan-2019-amended-2024.pdf'; canonical_page=$transportPlans
    source_page='https://www.cabq.gov/planning/plans-publications'
    description='Guides long-term development of Double Eagle II Airport through aviation forecasts, runway and taxiway requirements, compatible land use, airside and landside alternatives, environmental review, recommended facilities, funding strategies, and a phased capital improvement program.'
    implementation_locations=@($transportPlans,$facilities); cross_listing_approved=$true
    large_file_assessment='32,067,932-byte (30.58 MiB) PDF; unusually large because its 197 pages contain aerial imagery, detailed maps, facility diagrams, alternatives, tables, and capital plans. No smaller authoritative version was identified. Optimization could reduce map or image fidelity and is not proposed. The unchanged original is below the 100,000,000-byte approval threshold.'
  }
  [pscustomobject][ordered]@{
    id='src-63d212f6733be409'; title='Development Process Manual Chapter 17: Drainage and Transportation Procedures'; date='2018'
    r2_key='development-land-use/development-process/cabq-dpm-drainage-traffic-layout-procedures-2018.pdf'; canonical_page=$development
    source_page='https://documents.cabq.gov/planning/development-process-manual/'
    description='Preserves pre-2020 City procedures for drainage and Traffic Circulation Layout submittals, engineering review, approvals, expiration, construction certification, private storm drains in rights-of-way, and the forms used to coordinate development with public infrastructure.'
  }
  [pscustomobject][ordered]@{
    id='src-75935732f3f11f34'; title='Development Process Manual Intersection Design Final-Review Draft'; date='2017'
    r2_key='transportation/design-references/cabq-dpm-intersection-design-final-review-draft-2017.pdf'; canonical_page=$design
    source_page='https://documents.cabq.gov/planning/development-process-manual/'
    description='Preserves a 2017 draft predecessor to current City intersection standards, addressing signals, stop and yield control, roundabouts, channelized turns, spacing, sight distance, accessibility, pedestrian crossings, bicycle lanes, and development responsibilities.'
    implementation_locations=@($design,$development); cross_listing_approved=$true
  }
  [pscustomobject][ordered]@{
    id='src-82eb4064df12e83a'; title='Tingley Beach Metropolitan Redevelopment Area Designation Resolution R-305'; date='1983-04'
    r2_key='development-land-use/redevelopment-plans/cabq-tingley-beach-mra-designation-resolution-r-305-1983.pdf'; canonical_page=$redevelopment
    source_page='https://documents.cabq.gov/planning/UDD/MRA/'
    description='Designates the Tingley Beach Metropolitan Redevelopment Area, records findings concerning the former Beach Motel property along Central Avenue, maps the area, and directs preparation of the redevelopment plan adopted later in 1983.'
  }
  [pscustomobject][ordered]@{
    id='src-83a50a7b1723e768'; title='Erosion and Sediment Control Plan Standard Notes'; date='2026-02-02'
    r2_key='public-works/stormwater-drainage/cabq-erosion-sediment-control-plan-standard-notes-2026.pdf'; canonical_page=$stormwater
    source_page='https://documents.cabq.gov/planning/DevelopmentReviewServices/'
    description="Sets the City's 2026 standard erosion and sediment control plan notes for construction BMPs, inspections, stabilization, ownership transfers, off-site support areas, right-of-way work, professional certification, and stormwater controls near major drainage facilities."
    implementation_locations=@($stormwater,$design); cross_listing_approved=$true
  }
)

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
foreach ($decision in $decisions) {
  $words = @($decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { throw "$($decision.id) description has $words words." }
  $candidate = @($inventory.candidates | Where-Object id -eq $decision.id)
  if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for '$($decision.id)'; found $($candidate.Count)." }
  $candidate = $candidate[0]
  if (-not $candidate.local_path -or -not (Test-Path -LiteralPath $candidate.local_path)) { throw "Missing local file for '$($decision.id)'." }
  $candidate.status = 'parsed'
  $candidate.title = $decision.title
  $candidate.date = $decision.date
  $candidate.provenance_status = 'official government source page and authoritative file URL recorded'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Representative first, midpoint, and final pages visually inspected; PDF rendered successfully.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  $decision | Add-Member -NotePropertyName provenance_status -NotePropertyValue 'official government source page and authoritative file URL recorded'
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative government file preserved without modification.',
    'Description reviewed against extracted text and representative visual inspection.'
  )
}

$duplicates = @(
  [pscustomobject]@{id='src-603f2f46d2ec1f3b'; canonical='src-d311dfa1ad0a2915'; reason='Duplicate City Address Report discovery pathway for the same official interactive tool.'}
  [pscustomobject]@{id='src-51d5f0b8ea9585e1'; canonical='src-0b9dc46fbf32cfb7'; reason='Duplicate preserved-file representation of the same byte-identical June 2020 Development Process Manual.'}
)
foreach ($item in $duplicates) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)[0]
  $candidate.status = 'duplicate'
  $candidate.exclusion_reason = "$($item.reason) Canonical inventory record: $($item.canonical)."
  $candidate.validation_status = 'duplicate source pathway reconciled'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Reviewed in the GIS, DMD, and historical-records batch; duplicate pathway will not be implemented again.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$superseded = @(
  [pscustomobject]@{id='src-2022f9b1333dbd14'; canonical='src-4ccef0c6ec25aac8'; reason='July 2008 working version of the Uptown Sector Development Plan; the later adopted and amended plan is already archived and validated.'}
  [pscustomobject]@{id='src-62b8404d07720179'; canonical='src-4ccef0c6ec25aac8'; reason='Revised July 2008 working version of the Uptown Sector Development Plan; the later adopted and amended plan is already archived and validated.'}
  [pscustomobject]@{id='src-762c178489f05d25'; canonical='src-4ccef0c6ec25aac8'; reason='November 2008 final-review version of the Uptown Sector Development Plan; the later adopted and amended plan is already archived and validated.'}
  [pscustomobject]@{id='src-2cdb21bc19db1fb9'; canonical='src-7b6cb9849a434271'; reason='Draft FY2025 Albuquerque MS4 annual report; the authoritative final December 2025 report is already archived and validated.'}
)
foreach ($item in $superseded) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)[0]
  $candidate.status = 'superseded'
  $candidate.exclusion_reason = "$($item.reason) Canonical final record: $($item.canonical)."
  $candidate.validation_status = 'superseded by later final authoritative record'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Reviewed in the GIS, DMD, and historical-records batch; superseded working record will not be uploaded.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$exclusions = @(
  [pscustomobject]@{id='src-12983ac0cdc3d74b'; reason='Fillable operations-and-maintenance analysis form used for individual development submissions; it is an administrative intake artifact rather than durable public planning guidance.'}
  [pscustomobject]@{id='src-1773631d805ccd03'; reason='Single private lease floor plan for the Acropolis property; it has no broader planning analysis, adopted policy, public-infrastructure record, or durable citywide informational value.'}
  [pscustomobject]@{id='src-2b3232bda5576ddc'; reason='Blank drainage and transportation information intake sheet for individual development applications; it provides no substantive standards or explanatory planning content.'}
  [pscustomobject]@{id='src-497dfbd2555ab1f0'; reason='Administrative Traffic Circulation Layout application checklist; the current Development Process Manual and substantive design standards provide the durable requirements useful to ABQInfo readers.'}
  [pscustomobject]@{id='src-614c3f337bc345c4'; reason='Administrative site-plan application checklist; it contains no project analysis, adopted policy, map, dataset, or durable planning history.'}
  [pscustomobject]@{id='src-70a95b24db4b5435'; reason="Short procedural guide for renewing a business license; it is outside ABQInfo's development, land-use, transportation, public-works, maps, and public-finance scope."}
  [pscustomobject]@{id='src-a5761edb8f2e9b08'; reason='Blank traffic-scoping form used for individual development applications; it is an intake artifact rather than substantive transportation guidance or planning history.'}
  [pscustomobject]@{id='src-bb3134286c47d666'; reason='City Attorney employee-evaluation advisory letter; it is unrelated to ABQInfo transportation, development, public works, mapping, public finance, or durable civic-data scope.'}
  [pscustomobject]@{id='src-120f42c228f04310'; reason='San Ysidro municipal comprehensive plan outside Albuquerque and the materially relevant metropolitan transportation system.'}
  [pscustomobject]@{id='src-1a2b5858deeb1774'; reason='Cuba municipal comprehensive plan outside Albuquerque and the materially relevant metropolitan transportation system.'}
  [pscustomobject]@{id='src-301a1254092298da'; reason='Moriarty municipal comprehensive plan outside Albuquerque and the materially relevant metropolitan transportation system.'}
  [pscustomobject]@{id='src-5d82af5aab2fcdac'; reason='Encino municipal comprehensive plan outside Albuquerque and the materially relevant metropolitan transportation system.'}
  [pscustomobject]@{id='src-711d18aba1ceb299'; reason='Jemez Springs municipal comprehensive plan outside Albuquerque and the materially relevant metropolitan transportation system.'}
  [pscustomobject]@{id='src-726d6d017433a0d4'; reason='Willard municipal comprehensive plan outside Albuquerque and the materially relevant metropolitan transportation system.'}
  [pscustomobject]@{id='src-7def24524b990fe5'; reason='Earlier San Ysidro municipal comprehensive plan outside Albuquerque and the materially relevant metropolitan transportation system.'}
  [pscustomobject]@{id='src-a34d9eff17d32025'; reason='Torrance County comprehensive plan outside Albuquerque and the materially relevant metropolitan transportation system.'}
  [pscustomobject]@{id='src-c22f58e8eccce805'; reason='Mountainair municipal comprehensive plan outside Albuquerque and the materially relevant metropolitan transportation system.'}
  [pscustomobject]@{id='src-c2463a6cf2a29e42'; reason='Earlier Encino municipal comprehensive plan outside Albuquerque and the materially relevant metropolitan transportation system.'}
)
foreach ($item in $exclusions) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)[0]
  $candidate.status = 'excluded'
  $candidate.exclusion_reason = $item.reason
  $candidate.validation_status = 'excluded after relevance, durability, and informational-value review'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Reviewed in the GIS, DMD, and historical-records batch; excluded under ABQInfo relevance and durability criteria.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$review = @($inventory.candidates | Where-Object id -eq 'src-5f9bf5a35bdb196e')[0]
$review.status = 'requires human review'
$review.exclusion_reason = "The authoritative FY2018 Albuquerque MS4 annual report is 106,231,387 bytes (101.31 MiB), exceeding the project's 100,000,000-byte production-upload approval threshold. It remains valuable stormwater history but requires explicit approval before unchanged archival."
$review.validation_status = 'requires explicit human approval before production upload because the authoritative file exceeds 100,000,000 bytes'
$review.processing_notes = @(@($review.processing_notes) + @(
  'Exact authoritative file size: 106,231,387 bytes (101.31 MiB); PDF.',
  'The unusually large annual regulatory report likely includes extensive forms, tables, maps, exhibits, and appendices.',
  'No smaller authoritative version has been identified. Optimization might reduce scanned-image or map fidelity and is not proposed without approval.',
  'Projected R2 total if approved after this batch: 7,520,452,547 bytes, below the 8,000,000,000-byte project stop point.'
) | Sort-Object -Unique)
$review.updated_at = (Get-Date).ToUniversalTime().ToString('o')

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

[ordered]@{schema_version=1;batch_id='gis-dmd-history-86';decisions=$decisions} |
  ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;Duplicates=$duplicates.Count;Superseded=$superseded.Count;Exclusions=$exclusions.Count;RequiresHumanReview=1;OutputPath=$OutputPath}|ConvertTo-Json -Compress
