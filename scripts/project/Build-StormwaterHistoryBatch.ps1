[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/stormwater-history-batch-decisions-2026-09-09.json',
  [string]$PlanPath = 'project-state/discovery/stormwater-history-batch-r2-archive-plan-2026-09-09.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$stormwater = 'content/public-works/stormwater-drainage.md'
$capital = 'content/city-data/capital-spending.md'
$development = 'content/development-land-use/development-process.md'
$items = @(
  [ordered]@{id='src-02ea7ef3e62f8a24';title='Antibiotic Resistance Analysis of Contamination in Stormwater — Figures';date='2002-06';key='public-works/stormwater-drainage/cabq-stormwater-antibiotic-resistance-analysis-figures-2002.pdf';page=$stormwater;locations=@($stormwater);description='Supplies the ten mapped sampling-area figures referenced by the 2002 final report, locating monitored arroyos, channels, rain gauges, land uses, and contamination-source results across Albuquerque.';note='Official June 2002 companion figure volume; preserve and present only with the canonical final report src-11da795efc34f4f3.'}
  [ordered]@{id='src-ce078e834d05b947';title='Antibiotic Resistance Analysis of Contamination in Stormwater — Appendices';date='2002-06';key='public-works/stormwater-drainage/cabq-stormwater-antibiotic-resistance-analysis-appendices-2002.pdf';page=$stormwater;locations=@($stormwater);description='Preserves the 2002 final report''s supporting classification tables, sample and isolate summaries, study-area map, and site photographs, completing the City''s separately published technical record.';note='Official June 2002 companion appendix volume; preserve and present only with the canonical final report src-11da795efc34f4f3.'}
  [ordered]@{id='src-676d9afa33a1fdcf';title='MS4 Stormwater-Quality Sampling Fact Sheet';date='2003-01';key='public-works/stormwater-drainage/usgs-cabq-ms4-stormwater-quality-sampling-fact-sheet-2003.pdf';page=$stormwater;locations=@($stormwater);description='Summarizes the City and USGS cooperative stormwater-quality program, describing sampling locations, land uses, channel conditions, runoff loads, and regulatory monitoring across Albuquerque.';note='Official City-hosted USGS fact sheet; extracted text and metadata reviewed.'}
  [ordered]@{id='src-850bc7367355b085';title='Albuquerque Municipal Separate Storm Sewer System Permit';date='2005-10';key='public-works/stormwater-drainage/cabq-municipal-separate-storm-sewer-system-permit-2005.pdf';page=$stormwater;locations=@($stormwater);description='Sets the 2005 federal municipal-storm-sewer permit requirements for Albuquerque, covering authorized discharges, pollution prevention, monitoring, reporting, implementation schedules, enforcement, and interagency responsibilities.';note='Official City-hosted permit; 66-page text and metadata reviewed.'}
  [ordered]@{id='src-90604f46a9ff3c1e';title='City Storm Drainage Library Index';date='2010-05-19';key='public-works/stormwater-drainage/cabq-storm-drainage-library-index-2010.pdf';page=$stormwater;locations=@($stormwater);description='Indexes the City''s historical hydrology and drainage library, identifying capital-program, arroyo, channel, pond, study, design, construction, and close-out records available as of May 2010.';note='Official City library index; extracted text and metadata reviewed.'}
  [ordered]@{id='src-516ebc4bf5dbe6e9';title='Arroyo Maintenance Facility Stormwater Pollution Prevention Plan';date='2021-05';key='public-works/stormwater-drainage/cabq-arroyo-maintenance-facility-stormwater-pollution-prevention-plan-2021.pdf';page=$stormwater;locations=@($stormwater);description='Documents pollution-prevention controls for the City''s Arroyo Maintenance Facility, including operations, potential pollutants, spill response, inspections, training, monitoring, site maps, and environmental compliance.';note='Official City facility plan; 150-page text and representative rendered pages reviewed.'}
  [ordered]@{id='src-75f0dcf6be426005';title='Albuquerque MS4 Notice of Intent';date='2015-05-19';key='public-works/stormwater-drainage/cabq-ms4-notice-of-intent-2015.pdf';page=$stormwater;locations=@($stormwater);description='Records Albuquerque''s 2015 notice of intent for municipal stormwater permit coverage, documenting the transition to the watershed-based MS4 program and related compliance commitments.';note='Official City-hosted scanned notice of intent; 40 pages visually reviewed.'}
  [ordered]@{id='src-e87ebbf853413338';title='Drainage Pond Slope Stabilization and Seeding Requirements';date='2022-03-25';key='public-works/stormwater-drainage/cabq-drainage-pond-slope-stabilization-seeding-requirements-2022.pdf';page=$stormwater;locations=@($stormwater);description='Establishes City interim requirements for stabilizing and seeding subdivision drainage ponds, controlling erosion, reducing maintenance, using native plants and aggregate, and documenting erosion-control plan compliance.';note='Official City Planning guidance; extracted text and metadata reviewed.'}
  [ordered]@{id='src-edd2380f46aacc71';title='Development Process Manual Chapter 22: Drainage, Flood Control, and Erosion Control';date='2015-02';key='development-land-use/development-process/cabq-development-process-manual-chapter-22-drainage-flood-control-erosion-control-2015.pdf';page=$development;locations=@($development,$stormwater);description='Preserves the 2015 City drainage chapter governing grading, floodplains, erosion control, stormwater pollution prevention, detention, drainage reports, facilities, and development-review obligations before the later manual revision.';note='Historical City Development Process Manual chapter; extracted text and metadata reviewed.'}
  [ordered]@{id='src-0c7c3af1438a8349';title='Use of NOAA Atlas 14 With AHYMO Type 1 and 2 Rainfall Distributions';date='2011-09-05';key='public-works/stormwater-drainage/ahymo-noaa-atlas-14-rainfall-distributions-2011.pdf';page=$stormwater;locations=@($stormwater);description='Explains how Albuquerque''s AHYMO hydrologic model applies NOAA Atlas 14 rainfall distributions and adjusts older software inputs for accurate urban-stormwater peak-flow calculations.';note='City-hosted AHYMO technical application note; extracted text and metadata reviewed.'}
  [ordered]@{id='src-e28f489ec0fba72f';title='2003 Storm Sewer System General Obligation Bond Project Scopes';date='2003';key='city-data/capital-spending/cabq-2003-storm-sewer-system-go-bond-project-scopes.pdf';page=$capital;locations=@($capital,$stormwater);description='Details $11.576 million in 2003 storm-sewer bond scopes for drainage rehabilitation, monitoring, pumps, channels, collectors, crossings, planning, rights-of-way, and public art.';note='Official 2003 City bond-scope table; extracted text and metadata reviewed.'}
  [ordered]@{id='src-5e610a27e456abd8';title='2007 Storm Sewer System General Obligation Bond Project Scopes';date='2007';key='city-data/capital-spending/cabq-2007-storm-sewer-system-go-bond-project-scopes.pdf';page=$capital;locations=@($capital,$stormwater);description='Details $10.403 million in 2007 storm-sewer bond scopes for District 3, water-quality monitoring, hydrologic planning, collectors, rehabilitation, pump stations, and public art.';note='Official 2007 City bond-scope table; extracted text and metadata reviewed.'}
)

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
foreach ($item in $items) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for '$($item.id)'." }
  $candidate = $candidate[0]
  if ($candidate.status -notin @('downloaded','parsed')) { throw "Candidate '$($item.id)' is not ready: $($candidate.status)." }
  $candidate.status = 'placement assigned'
  $candidate.title = $item.title
  $candidate.date = $item.date
  $candidate.r2_key = $item.key
  $candidate.r2_url = "https://files.abqinfo.com/$($item.key)"
  $candidate.proposed_canonical_page = $item.page
  $candidate.description = $item.description
  $candidate.description_word_count = @($item.description -split '\s+' | Where-Object { $_ }).Count
  $candidate.implementation_locations = @($item.locations)
  $candidate.cross_listing_approved = $item.locations.Count -gt 1
  $candidate.provenance_status = 'official City-hosted source and direct government file reviewed'
  $candidate.validation_status = 'source, exact size, SHA-256, extracted content or rendered pages, and description reviewed; R2 upload pending'
  $candidate.processing_notes = @($candidate.processing_notes | Where-Object { $_ }) + $item.note | Sort-Object -Unique
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$inventory.next_pending_id = 'src-02ea7ef3e62f8a24'
$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$tempPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($tempPath, $json, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $tempPath -Destination $fullPath -Force

$r2 = Get-Content -Raw -Encoding UTF8 -LiteralPath 'project-state/r2-inventory.json' | ConvertFrom-Json
$bytes = [int64](@($items | ForEach-Object { (@($inventory.candidates | Where-Object id -eq $_.id)[0].size_bytes) } | Measure-Object -Sum).Sum)
$planItems = @($items | ForEach-Object {
  $candidate = @($inventory.candidates | Where-Object id -eq $_.id)[0]
  [ordered]@{id=$_.id;source_url=$candidate.source_url;direct_file_url=$candidate.direct_file_url;parent_url=$candidate.parent_url;agency=$candidate.agency;title=$_.title;date=$_.date;file_type=$candidate.file_type;size_bytes=[int64]$candidate.size_bytes;checksum_sha256=$candidate.checksum_sha256;r2_key=$_.key;proposed_canonical_page=$_.page;implementation_locations=@($_.locations);description=$_.description;provenance_status=$candidate.provenance_status;processing_notes=$_.note;size_warning_over_25mb=([int64]$candidate.size_bytes -gt 25MB);already_present=$false}
})
[ordered]@{schema_version=1;created_at=(Get-Date).ToUniversalTime().ToString('o');batch_id='stormwater-history-batch-2026-09-09';current_r2_bytes=[int64]$r2.total_bytes;maximum_object_bytes=100000000;maximum_projected_r2_bytes=10000000000;batch_bytes=$bytes;added_bytes=$bytes;projected_r2_bytes=([int64]$r2.total_bytes+$bytes);items=$planItems} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $PlanPath -Encoding utf8
[ordered]@{batch_id='stormwater-history-batch-2026-09-09';visible_additions=15;decisions=@($planItems | ForEach-Object { [ordered]@{id=$_.id;title=$_.title;date=$_.date;r2_key=$_.r2_key;canonical_page=$_.proposed_canonical_page;implementation_locations=$_.implementation_locations;description=$_.description;decision='approved for addition';provenance_status=$_.provenance_status;processing_notes=$_.processing_notes} })} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $DecisionPath -Encoding utf8
[pscustomobject]@{Items=$items.Count;VisibleAdditions=15;BatchBytes=$bytes;PlanPath=$PlanPath;DecisionPath=$DecisionPath}|ConvertTo-Json -Compress
