[CmdletBinding()]
param(
  [string]$CatalogPath = 'project-state/contributed-document-review-2026-08-14.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json',
  [string]$DecisionPath = 'project-state/contributed-document-decisions-2026-08-14.json',
  [string]$ArchivePlanPath = 'project-state/contributed-document-archive-plan-2026-08-14.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-StableId([string]$Value) {
  $bytes = [Text.Encoding]::UTF8.GetBytes($Value.Trim().ToLowerInvariant())
  $sha = [Security.Cryptography.SHA256]::Create()
  try { $hash = $sha.ComputeHash($bytes) } finally { $sha.Dispose() }
  return 'src-' + (-join ($hash | ForEach-Object { $_.ToString('x2') })).Substring(0,16)
}

function Get-WordCount([string]$Value) {
  return @($Value -split '\s+' | Where-Object { $_ }).Count
}

function Get-CatalogItem([string]$Filename) {
  $item = @($catalog.items | Where-Object filename -eq $Filename)
  if ($item.Count -ne 1) { throw "Expected one catalog item named '$Filename'; found $($item.Count)." }
  return $item[0]
}

function New-InventoryRecord([string]$Id) {
  $now = (Get-Date).ToUniversalTime().ToString('o')
  return [pscustomobject][ordered]@{
    id = $Id
    status = 'pending review'
    source_url = $null
    direct_file_url = $null
    r2_url = $null
    r2_key = $null
    r2_etag = $null
    r2_last_modified = $null
    agency = 'City of Albuquerque'
    title = $null
    date = $null
    file_type = 'PDF'
    size_bytes = $null
    checksum_sha256 = $null
    parent_url = $null
    referring_urls = @()
    discovery_path = @()
    discovery_method = 'User-contributed document review with graph-crawl provenance reconciliation'
    crawl_depth = $null
    cited_predecessors = @()
    cited_successors = @()
    provenance_status = $null
    proposed_canonical_page = $null
    description = $null
    description_word_count = 0
    processing_notes = @()
    implementation_location = $null
    implementation_locations = @()
    cross_listing_approved = $false
    validation_status = 'not run'
    exclusion_reason = $null
    local_path = $null
    discovered_at = $now
    updated_at = $now
  }
}

$catalog = Get-Content -Raw -LiteralPath $CatalogPath | ConvertFrom-Json
$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$r2 = Get-Content -Raw -LiteralPath $R2InventoryPath | ConvertFrom-Json

$definitions = @(
  [ordered]@{
    filename = 'Bike Boulevard Silver R-28Enacted.pdf'
    id_seed = 'https://codelibrary.amlegal.com/codes/albuquerque/latest/albuquerque_nm_reslist/0-0-0-16727#r-2020-079'
    title = 'City Council Resolution R-2020-079: Silver Avenue Bike Boulevard Review'
    date = '2020-08-17'
    source_url = 'https://codelibrary.amlegal.com/codes/albuquerque/latest/albuquerque_nm_reslist/0-0-0-16727#R-2020-079'
    direct_file_url = $null
    parent_url = 'https://www.cabq.gov/council/documents/silver-ave-blvd-blvd-review-final-dec-2019.pdf'
    referring_urls = @('https://www.cabq.gov/council/documents/silver-ave-blvd-blvd-review-final-dec-2019.pdf')
    discovery_path = @('user-contributed:Bike Boulevard Silver R-28Enacted.pdf','official-legislation-index:R-2020-079')
    provenance_status = 'City-branded enacted resolution; enactment number, title, and passage date corroborated by the official Albuquerque resolution index; exact PDF source URL is no longer available'
    page = 'content/transportation/bicycling/projects/_index.md'
    r2_key = 'transportation/bicycling/projects/cabq-silver-avenue-bike-boulevard-review-resolution-r-2020-079.pdf'
    description = 'Adopts the Silver Avenue Bike Boulevard Review as City policy priorities for the corridor between Yale Boulevard and the Paseo del Bosque Trail and directs implementation, funding, coordination, and incorporation into future bicycle planning.'
    notes = @('Four-page scanned enacted resolution. City Council bill R-20-28; enactment R-2020-079.','No current direct City PDF was recovered; the official legislation index corroborates the enacted record.')
  },
  [ordered]@{
    filename = 'CABQ Vision Zero Action Plan 2021.pdf'
    id_seed = 'https://www.cabq.gov/vision-zero/documents/abq-vzactionplan-2021-final.pdf'
    title = 'Albuquerque Vision Zero Action Plan (2021)'
    date = '2021'
    source_url = 'https://www.cabq.gov/vision-zero/vision-zero'
    direct_file_url = 'https://www.cabq.gov/vision-zero/documents/abq-vzactionplan-2021-final.pdf'
    parent_url = 'https://www.cabq.gov/vision-zero/vision-zero'
    referring_urls = @('https://www.cabq.gov/bikes/city-plans-docs-support-bike-friendly-community','https://www.cabq.gov/municipaldevelopment/news/mayor-tim-keller-city-leaders-unveil-vision-zero-abq-2040-action-plan-at-bike-to-wherever-event')
    discovery_path = @('https://www.cabq.gov/bikes/city-plans-docs-support-bike-friendly-community','https://www.cabq.gov/vision-zero','official-retired-file:abq-vzactionplan-2021-final.pdf','user-contributed:CABQ Vision Zero Action Plan 2021.pdf')
    provenance_status = 'Official City program and release pages identify the 2021 plan; retired City PDF path and City-branded local copy reconcile the document, though the original download now returns 404'
    page = 'content/transportation/bicycling/safety-crash-data.md'
    r2_key = 'transportation/bicycling/safety-crash-data/cabq-vision-zero-action-plan-2021.pdf'
    description = "Sets Albuquerque’s original 2040 Vision Zero framework across street design, safe speeds, policy, education, walking and rolling, data, and accountability. The City’s 2023 Year-in-Review later replaced it for implementation, but this plan preserves the program’s baseline."
    notes = @('Fifty-two-page City plan released in 2021.','The maintained Vision Zero page states that the 2023 Year-in-Review replaced this plan for implementation; the 2021 plan remains historically important.')
  },
  [ordered]@{
    filename = 'crosswalk-report.pdf'
    existing_id = 'src-1231cfe4a3029341'
    title = 'City of Albuquerque Elementary & Middle School Crossing Evaluation (2019)'
    date = '2019'
    source_url = 'https://www.cabq.gov/municipaldevelopment/documents/crosswalk-report.pdf/view'
    direct_file_url = 'https://www.cabq.gov/municipaldevelopment/documents/crosswalk-report.pdf'
    parent_url = 'https://www.cabq.gov/municipaldevelopment/documents'
    referring_urls = @('https://www.cabq.gov/municipaldevelopment/documents/crosswalk-report.pdf/view','https://www.cabq.gov/municipaldevelopment/documents')
    discovery_path = @('https://www.cabq.gov/municipaldevelopment/documents','https://www.cabq.gov/municipaldevelopment/documents/crosswalk-report.pdf/view','https://www.cabq.gov/municipaldevelopment/documents/crosswalk-report.pdf','user-contributed:crosswalk-report.pdf')
    provenance_status = 'Authoritative City collection path and former PDF URL were recovered by the graph crawl; the City-branded contributed copy restores the now-unavailable file'
    page = 'content/maps/dashboards.md'
    r2_key = 'maps/dashboards/cabq-school-crossing-evaluation-2019.pdf'
    description = 'Explains how DMD evaluated more than 350 elementary and middle school crossings, defines the six dashboard ratings, documents the two-step scoring method, and identifies locations prioritized or monitored for funding with recommended remedies and costs.'
    notes = @('One-hundred-nine-page City study created in October 2019.','The report defines “Meets Minimum Standards” and “Exceeds Minimum Standards” and documents the dashboard scoring method.','The former City PDF and view URLs now return 404; this contributed file closes the previously blocked provenance-backed archive gap.')
  },
  [ordered]@{
    filename = 'east-central-ave-safety-study-final-draft-10-2-2020.pdf'
    id_seed = 'https://www.cabq.gov/municipaldevelopment/our-department/engineering/greater-albuquerque-active-transportation-committee/documents/east-central-ave-safety-study-final-draft-10-2-2020.pdf'
    title = 'East Central Avenue Safety Study (2020)'
    date = '2020-10-02'
    source_url = 'https://www.bernco.gov/public-works/blog/2025/02/12/east-central-pedestrian-safety-project'
    direct_file_url = 'https://www.cabq.gov/municipaldevelopment/our-department/engineering/greater-albuquerque-active-transportation-committee/documents/east-central-ave-safety-study-final-draft-10-2-2020.pdf'
    parent_url = 'https://www.cabq.gov/municipaldevelopment/our-department/engineering/greater-albuquerque-active-transportation-committee'
    referring_urls = @('https://www.bernco.gov/public-works/blog/2025/02/12/east-central-pedestrian-safety-project')
    discovery_path = @('user-contributed:east-central-ave-safety-study-final-draft-10-2-2020.pdf','official-City-GAATC-document-path','https://www.bernco.gov/public-works/blog/2025/02/12/east-central-pedestrian-safety-project')
    provenance_status = 'City-branded study with a recovered official CABQ document URL and a maintained Bernalillo County successor project page; former City download now returns 404'
    page = 'content/transportation/roadway-projects/studies.md'
    r2_key = 'transportation/roadway-projects/studies/cabq-east-central-avenue-safety-study-2020.pdf'
    description = 'Analyzes pedestrian and bicycle safety on Central Avenue from Louisiana to Eubank using crashes, speeds, crossings, lighting, sidewalks, demographics, and policy context, then recommends near-term treatments, a conditional temporary road diet, and a permanent long-term road diet.'
    notes = @('Fifty-nine-page joint City and County corridor safety study.','The file is labeled final draft and dated October 2, 2020; the County now maintains the related East Central Pedestrian Safety Project page.')
  },
  [ordered]@{
    filename = 'Girard Streetscape FINAL - Annotated.pdf'
    existing_id = 'src-0a69860a80fbe98a'
    title = 'Girard Streetscape Annotated Schematic Design (2022)'
    date = '2022-09-02'
    source_url = 'https://www.cabq.gov/council/find-your-councilor/district-7/district-7-projects/traffic-street-improvements/girard_streetscape_2025'
    direct_file_url = $null
    parent_url = 'https://www.cabq.gov/council/find-your-councilor/district-7/district-7-projects/traffic-street-improvements/girard_streetscape_2025'
    referring_urls = @('https://documents.cabq.gov/planning/environmental-planning-commission/Nov10_2022/Agenda%202_NH%20CPA_Assessment_Report-FIN.pdf')
    discovery_path = @('https://www.cabq.gov/council/find-your-councilor/district-7/district-7-projects/traffic-street-improvements/girard_streetscape_2025','Near Heights CPA Assessment description of 2022 schematic design and cost estimate','user-contributed:Girard Streetscape FINAL - Annotated.pdf')
    provenance_status = 'Official City pages corroborate the 2022 Girard schematic-design project, but the exact annotated PDF is user-contributed and no authoritative direct file URL has been recovered'
    page = 'content/transportation/roadway-projects/studies.md'
    r2_key = 'transportation/roadway-projects/studies/cabq-girard-streetscape-annotated-schematic-design-2022.pdf'
    description = "Preserves the City’s annotated 2022 schematic design for Girard between Indian School and Hannett, showing pedestrian, bicycle, sidewalk, streetscape, tree, parking, intersection, and cost concepts. Red review notes indicate this is a working design record, not an adopted final plan."
    notes = @('Ten-page schematic design updated September 2, 2022.','Visible red review annotations alter lane, signage, cost, lighting, patio, and implementation details; the site entry must label this as an annotated working record.','Exact-file provenance remains unresolved, so the inventory status remains requires human review after archival and site validation.')
  },
  [ordered]@{
    filename = 'i-25-bike-study-summary-memo-september-2020.pdf'
    id_seed = 'https://www.cabq.gov/municipaldevelopment/documents/i-25-bike-study-summary-memo-september-2020.pdf'
    title = 'I-25 Bicycle Accessibility Study Summary (2020; Updated 2021)'
    date = '2021'
    source_url = 'https://www.cabq.gov/bikes/city-plans-docs-support-bike-friendly-community'
    direct_file_url = 'https://www.cabq.gov/municipaldevelopment/documents/i-25-bike-study-summary-memo-september-2020.pdf'
    parent_url = 'https://www.cabq.gov/bikes/city-plans-docs-support-bike-friendly-community'
    referring_urls = @('https://www.cabq.gov/planning/documents/2024-bikeway-and-trail-facilities-plan.pdf')
    discovery_path = @('https://www.cabq.gov/planning/documents/2024-bikeway-and-trail-facilities-plan.pdf','pdf-lineage:I-25 Bicycle Accessibility Study (2020; updated 2021)','official-retired-file:i-25-bike-study-summary-memo-september-2020.pdf','user-contributed:i-25-bike-study-summary-memo-september-2020.pdf')
    provenance_status = 'The adopted 2024 bicycle plan identifies the study and a recovered official City PDF URL matches the contributed filename and text; former download now returns 404'
    page = 'content/transportation/bicycling/projects/_index.md'
    r2_key = 'transportation/bicycling/projects/cabq-i25-bicycle-accessibility-study-summary-2021.pdf'
    description = "Summarizes the 2019–2020 study of bicycle access across northern Albuquerque’s I-25 crossings, recommending corridor, trail, lane, signage, and network improvements while identifying San Francisco Street and San Diego Avenue as potential future bicycle-pedestrian crossings."
    notes = @('Six-page summary memo generated in October 2021 for a study completed in 2019 and early 2020.','The adopted 2024 Bikeway and Trail Facilities Plan describes this study as updated in 2021.')
  },
  [ordered]@{
    filename = 'Silver Ave Blvd Blvd Review - Final - Dec 2019.pdf'
    id_seed = 'https://www.cabq.gov/council/documents/silver-ave-blvd-blvd-review-final-dec-2019.pdf'
    title = 'Silver Avenue Bike Boulevard Review (2019)'
    date = '2019-12'
    source_url = 'https://www.cabq.gov/council/documents/silver-ave-blvd-blvd-review-final-dec-2019.pdf'
    direct_file_url = 'https://www.cabq.gov/council/documents/silver-ave-blvd-blvd-review-final-dec-2019.pdf'
    parent_url = 'https://www.cabq.gov/bikes/city-plans-docs-support-bike-friendly-community'
    referring_urls = @('https://codelibrary.amlegal.com/codes/albuquerque/latest/albuquerque_nm_reslist/0-0-0-16727#R-2020-079')
    discovery_path = @('user-contributed:Silver Ave Blvd Blvd Review - Final - Dec 2019.pdf','official-City-Council-document:silver-ave-blvd-blvd-review-final-dec-2019.pdf','official-legislation-index:R-2020-079')
    provenance_status = 'Exact local file is byte-identical to the currently downloadable official City Council PDF; adoption is corroborated by official resolution R-2020-079'
    page = 'content/transportation/bicycling/projects/_index.md'
    r2_key = 'transportation/bicycling/projects/cabq-silver-avenue-bike-boulevard-review-2019.pdf'
    description = 'Evaluates the Silver Avenue and 14th Street bike boulevards from Yale to the Bosque, documenting traffic, crashes, public input, I-25 and railroad crossing alternatives, route treatments, costs, and recommended improvements, with a qualitative review of Mountain Road.'
    notes = @('Ninety-eight-page, map- and image-heavy City study; exact official source match verified.','At 26,597,978 bytes (25.37 MiB), this is the only contributed file over 25 MiB. The size reflects full-resolution maps, diagrams, photographs, and appendices.','No smaller authoritative City edition was found. Optimization is technically possible but would alter the authoritative source or reduce map fidelity, so the original is preserved without modification.')
  }
)

$decisions = @()
$archiveItems = @()
foreach ($definition in $definitions) {
  $item = Get-CatalogItem $definition.filename
  $id = if ($definition.Contains('existing_id')) { [string]$definition.existing_id } else { Get-StableId ([string]$definition.id_seed) }
  $record = @($inventory.candidates | Where-Object id -eq $id)
  if ($record.Count -gt 1) { throw "Duplicate inventory id '$id'." }
  if (-not $record.Count) {
    $record = @(New-InventoryRecord $id)
    $inventory.candidates += $record[0]
  }
  $record = $record[0]
  $record.status = if ($id -eq 'src-0a69860a80fbe98a') { 'requires human review' } else { 'placement assigned' }
  $record.source_url = $definition.source_url
  $record.direct_file_url = $definition.direct_file_url
  $record.r2_url = 'https://files.abqinfo.com/' + $definition.r2_key
  $record.r2_key = $definition.r2_key
  $record.agency = 'City of Albuquerque'
  $record.title = $definition.title
  $record.date = $definition.date
  $record.file_type = 'PDF'
  $record.size_bytes = [int64]$item.size_bytes
  $record.checksum_sha256 = [string]$item.checksum_sha256
  $record.parent_url = $definition.parent_url
  $record.referring_urls = @($definition.referring_urls)
  $record.discovery_path = @($definition.discovery_path)
  $record.discovery_method = 'User-contributed document review with graph-crawl provenance reconciliation'
  $record.provenance_status = $definition.provenance_status
  $record.proposed_canonical_page = $definition.page
  $record.description = $definition.description
  $record.description_word_count = Get-WordCount $definition.description
  if ($record.description_word_count -lt 20 -or $record.description_word_count -gt 50) { throw "Description for '$id' has $($record.description_word_count) words." }
  $record.processing_notes = @($definition.notes)
  $record.validation_status = 'local PDF text and representative pages reviewed; exact size and SHA-256 recorded; R2 upload pending'
  $record.exclusion_reason = $null
  $record.local_path = $item.local_path
  $record.updated_at = (Get-Date).ToUniversalTime().ToString('o')

  $decision = [pscustomobject][ordered]@{
    id = $id
    filename = $definition.filename
    decision = if ($id -eq 'src-0a69860a80fbe98a') { 'include with provenance warning; requires human review' } else { 'approved for addition' }
    agency = 'City of Albuquerque'
    title = $definition.title
    date = $definition.date
    file_type = 'PDF'
    pages = [int]$item.pages
    size_bytes = [int64]$item.size_bytes
    size_human = [string]$item.size_human
    exceeds_25_mib = [bool]$item.exceeds_25_mib
    exceeds_100_mib = [bool]$item.exceeds_100_mib
    checksum_sha256 = [string]$item.checksum_sha256
    source_url = $definition.source_url
    direct_file_url = $definition.direct_file_url
    parent_url = $definition.parent_url
    proposed_canonical_page = $definition.page
    r2_key = $definition.r2_key
    r2_url = 'https://files.abqinfo.com/' + $definition.r2_key
    description = $definition.description
    description_word_count = Get-WordCount $definition.description
    provenance_status = $definition.provenance_status
    processing_notes = @($definition.notes)
  }
  $decisions += $decision
  $archiveItems += $decision
}

# Reconcile the contributed 2007 resolution to its byte-identical existing R2 object.
$general = Get-CatalogItem 'Bike Boulevard General R-268fsfinal.pdf'
$generalRecord = @($inventory.candidates | Where-Object id -eq 'src-4cb190564a688d42')[0]
$generalRecord.size_bytes = [int64]$general.size_bytes
$generalRecord.checksum_sha256 = [string]$general.checksum_sha256
$generalRecord.local_path = $general.local_path
$generalRecord.validation_status = 'existing public R2 object verified byte-identical to the contributed file by exact size and SHA-256'
$generalNote = 'User-contributed source file is byte-identical to the existing R2 object (86,484 bytes; SHA-256 8ab53b1618bb0dcda93f43d7ae9d79dd6822d1f6fcc1b9868dd03d37aca9d83a).'
$generalRecord.processing_notes = @(@($generalRecord.processing_notes) + $generalNote | Where-Object { $_ } | Sort-Object -Unique)
$generalRecord.updated_at = (Get-Date).ToUniversalTime().ToString('o')

$duplicateDecisions = @($catalog.items | Where-Object matching_inventory_id | ForEach-Object {
  [pscustomobject][ordered]@{id=$_.id;filename=$_.filename;decision='duplicate';matching_inventory_id=$_.matching_inventory_id;size_bytes=$_.size_bytes;size_human=$_.size_human;checksum_sha256=$_.checksum_sha256}
}) + @([pscustomobject][ordered]@{id=$general.id;filename=$general.filename;decision='duplicate';matching_inventory_id='src-4cb190564a688d42';size_bytes=$general.size_bytes;size_human=$general.size_human;checksum_sha256=$general.checksum_sha256})

$totalAdded = [int64](($archiveItems | ForEach-Object { [int64]$_.size_bytes } | Measure-Object -Sum).Sum)
$decisionDocument = [ordered]@{
  schema_version = 1
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  reviewed_file_count = [int]$catalog.file_count
  additions = $decisions
  duplicates = $duplicateDecisions
  added_bytes = $totalAdded
  current_r2_bytes = [int64]$r2.total_bytes
  projected_r2_bytes = [int64]$r2.total_bytes + $totalAdded
  exact_next_action = 'Upload and verify the seven archive-plan objects, add their links and descriptions to the assigned Hugo pages, then run full project validation.'
}
$decisionDocument | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $DecisionPath -Encoding utf8

$archivePlan = [ordered]@{
  schema_version = 1
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  bucket = [string]$r2.bucket
  pricing_source = 'https://developers.cloudflare.com/r2/pricing/'
  pricing_verified_at = (Get-Date).ToUniversalTime().ToString('o')
  standard_free_storage_gb_month = 10
  current_r2_bytes = [int64]$r2.total_bytes
  added_bytes = $totalAdded
  projected_r2_bytes = [int64]$r2.total_bytes + $totalAdded
  maximum_object_bytes = [int64](100MB)
  maximum_projected_r2_bytes = [int64](8GB)
  items = $archiveItems
}
$archivePlan | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ArchivePlanPath -Encoding utf8

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$inventory | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $InventoryPath -Encoding utf8

[pscustomobject]@{
  Reviewed = [int]$catalog.file_count
  Additions = $decisions.Count
  Duplicates = $duplicateDecisions.Count
  AddedBytes = $totalAdded
  ProjectedR2Bytes = [int64]$r2.total_bytes + $totalAdded
  DecisionPath = $DecisionPath
  ArchivePlanPath = $ArchivePlanPath
}
