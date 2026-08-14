[CmdletBinding()]
param(
  [string]$PlanPath = 'project-state/dmd-library-expansion-archive-plan-2026-08-14.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json',
  [string]$OutputPath = 'project-state/discovery/dmd-library-expansion-overrides.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plan = Get-Content -Raw -LiteralPath $PlanPath | ConvertFrom-Json
$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$r2 = Get-Content -Raw -LiteralPath $R2InventoryPath | ConvertFrom-Json
$overrides = [System.Collections.Generic.List[object]]::new()

foreach ($item in @($plan.items)) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for '$($item.id)'." }
  $object = @($r2.objects | Where-Object key -eq $item.r2_key)
  if ($object.Count -ne 1) { throw "Expected one R2 object for '$($item.r2_key)'." }
  $candidate = $candidate[0]
  $overrides.Add([pscustomobject][ordered]@{
    id = [string]$item.id
    match_url = "https://files.abqinfo.com/$($item.r2_key)"
    status = 'validated'
    source_url = [string]$item.source_url
    direct_file_url = [string]$item.direct_file_url
    r2_key = [string]$item.r2_key
    r2_etag = [string]$object[0].etag
    r2_last_modified = [string]$object[0].last_modified
    agency = [string]$item.agency
    title = [string]$item.title
    date = [string]$item.date
    file_type = [string]$item.file_type
    size_bytes = [int64]$item.size_bytes
    checksum_sha256 = [string]$item.checksum_sha256
    parent_url = [string]$item.parent_url
    referring_urls = @($candidate.referring_urls)
    proposed_canonical_page = [string]$item.proposed_canonical_page
    description = [string]$item.description
    processing_notes = @($item.processing_notes) + @('Original authoritative file uploaded without modification; public R2 download matched exact size and SHA-256.')
    implementation_location = [string]$item.proposed_canonical_page
    implementation_locations = @([string]$item.proposed_canonical_page)
    cross_listing_approved = $false
    validation_status = 'passed: authoritative provenance, public byte-identical R2 download, description, and placement validated'
    provenance_status = 'official government source page and byte-identical official file recorded'
  })
}

$crossingId = 'src-14839f6b5ae5f9f1'
$crossing = @($inventory.candidates | Where-Object id -eq $crossingId)[0]
$crossingKey = 'transportation/bicycling/bike-plans/2024-albuquerque-bike-plan-coa-bicycle-and-trail-crossings-guide.pdf'
$crossingObject = @($r2.objects | Where-Object key -eq $crossingKey)[0]
$crossingDescription = 'Provides design guidance for bicycle and trail crossings, helping practitioners select treatments that improve visibility, clarify priority, and reduce conflicts at roadway intersections.'
$overrides.Add([pscustomobject][ordered]@{
  id = $crossingId
  match_url = "https://files.abqinfo.com/$crossingKey"
  status = 'validated'
  source_url = [string]$crossing.source_url
  direct_file_url = [string]$crossing.direct_file_url
  r2_key = $crossingKey
  r2_etag = [string]$crossingObject.etag
  r2_last_modified = [string]$crossingObject.last_modified
  agency = 'City of Albuquerque'
  title = 'Bicycle and Trail Crossings Guide'
  date = '2024'
  file_type = 'PDF'
  size_bytes = [int64]$crossing.size_bytes
  checksum_sha256 = [string]$crossing.checksum_sha256
  parent_url = [string]$crossing.parent_url
  referring_urls = @($crossing.referring_urls)
  proposed_canonical_page = 'content/transportation/bicycling/bike-plans.md'
  description = $crossingDescription
  processing_notes = @($crossing.processing_notes) + @('Existing public R2 object matched the newly recovered authoritative DMD source byte-for-byte, resolving prior provenance uncertainty.')
  implementation_location = 'content/transportation/bicycling/bike-plans.md'
  implementation_locations = @('content/transportation/bicycling/bike-plans.md')
  cross_listing_approved = $false
  validation_status = 'passed: authoritative DMD provenance and public byte-identical R2 copy validated'
  provenance_status = 'official City DMD source and byte-identical archived file recorded'
})

foreach ($record in @(
  @{id='src-64dcaac3f80477e6';status='duplicate';title='Bicycle and Trail Crossings Guide';reason='R2-only display-link alias reconciled to authoritative DMD candidate src-14839f6b5ae5f9f1.'},
  @{id='src-350f1b4d381f1b7e';status='excluded';title='Mountain Road Bike Boulevard Crossing at San Pedro Drive';reason='The 36,723-byte official object is a malformed PDF that cannot be parsed or rendered; the complete 2015 GABAC presentation is archived under src-438b3ebcc3f671e2.'},
  @{id='src-48483555b0d1b8bf';status='excluded';title='12th Street Great Streets Improvements Project Public Meeting Notice';reason='One-page 2015 meeting notice supplies only event logistics and a short project boundary; it does not contain a plan, study, design, or substantive project record.'},
  @{id='src-7405cfc41e5500c4';status='excluded';title='2003 General Obligation Bond Summary';reason='One-page pie chart gives only broad bond-purpose percentages and dollar totals, without project lists, locations, schedules, or other capital-program detail.'},
  @{id='src-ff46ff46ba925573';status='excluded';title='National Pollutant Discharge Elimination System Stormwater Program Form';reason='Generic, partially completed six-page annual-report form is lower-information than the complete FY 2022, FY 2024, and FY 2025 reports archived in this batch.'}
)) {
  $overrides.Add([pscustomobject][ordered]@{
    id = $record.id
    status = $record.status
    title = $record.title
    exclusion_reason = $record.reason
    validation_status = if ($record.status -eq 'duplicate') { 'duplicate reconciled to authoritative source candidate' } else { 'reviewed and excluded with reason' }
    processing_notes = @($record.reason)
  })
}

foreach ($alias in @(
  @{id='src-665d53bf27d05210';title='Two-Stage Bike Box at MLK Avenue and Broadway Boulevard — Image';canonical='src-380ba25628c0ee5c'},
  @{id='src-da5e1983716179b9';title='2025–2034 Decade Plan Funding Allocation Workbook';canonical='src-00e4a0dfe5460a1d'}
)) {
  $overrides.Add([pscustomobject][ordered]@{
    id = $alias.id
    status = 'duplicate'
    title = $alias.title
    exclusion_reason = "Content-link alias reconciled to canonical authoritative candidate $($alias.canonical)."
    validation_status = 'duplicate content-link record reconciled to authoritative source candidate'
  })
}

$overrides.Add([pscustomobject][ordered]@{
  id = 'src-6981a0204fb7ffe2'
  status = 'validated'
  source_url = 'https://www.cabq.gov/automated-speed-enforcement'
  agency = 'City of Albuquerque'
  title = 'City Automated Speed Enforcement Program'
  file_type = 'Web page or live service'
  proposed_canonical_page = 'content/transportation/roadway-projects/speed-management.md'
  description = 'Provides the current City source for camera locations, program rules, citation payment and review, community service, hearings, speed studies, and automated-enforcement updates.'
  implementation_location = 'content/transportation/roadway-projects/speed-management.md'
  implementation_locations = @('content/transportation/roadway-projects/speed-management.md')
  cross_listing_approved = $false
  validation_status = 'passed: authoritative City page returned HTTP 200 and content was reviewed'
  provenance_status = 'authoritative government source recorded'
})

$overrides | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{OutputPath=$OutputPath;Validated=@($overrides|Where-Object status -eq 'validated').Count;Excluded=@($overrides|Where-Object status -eq 'excluded').Count;Duplicate=@($overrides|Where-Object status -eq 'duplicate').Count} | ConvertTo-Json -Compress
