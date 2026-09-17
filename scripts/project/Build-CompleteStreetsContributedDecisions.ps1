[CmdletBinding()]
param(
  [string]$CatalogPath = 'project-state/contributed-complete-streets-review-2026-09-11.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/contributed-complete-streets-decisions-2026-09-11.json',
  [string]$ArchivePlanPath = 'project-state/discovery/contributed-complete-streets-r2-archive-plan-2026-09-11.json'
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

function New-InventoryRecord([string]$Id) {
  $now = (Get-Date).ToUniversalTime().ToString('o')
  return [pscustomobject][ordered]@{
    id = $Id; status = 'pending review'; source_url = $null; direct_file_url = $null
    r2_url = $null; r2_key = $null; r2_etag = $null; r2_last_modified = $null
    agency = 'City of Albuquerque'; title = $null; date = $null; file_type = 'PDF'
    size_bytes = $null; checksum_sha256 = $null; parent_url = $null
    referring_urls = @(); discovery_path = @(); discovery_method = 'User-contributed official document review'
    crawl_depth = $null; cited_predecessors = @(); cited_successors = @(); provenance_status = $null
    proposed_canonical_page = $null; description = $null; description_word_count = 0
    processing_notes = @(); implementation_location = $null; implementation_locations = @()
    cross_listing_approved = $false; validation_status = 'not run'; exclusion_reason = $null
    local_path = $null; discovered_at = $now; updated_at = $now
  }
}

$catalog = Get-Content -Raw -Encoding UTF8 -LiteralPath $CatalogPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$r2 = Get-Content -Raw -Encoding UTF8 -LiteralPath $R2InventoryPath | ConvertFrom-Json
$programUrl = 'https://www.cabq.gov/vision-zero/what-are-we-doing'

$definitions = @(
  [ordered]@{
    filename = '4th Street Complete Streets Review - August 2025 - Final.pdf'
    title = '4th Street Complete Streets Review: Menaul Boulevard to Candelaria Road (August 2025)'
    date = '2025-08'
    r2_key = 'transportation/roadway-projects/studies/cabq-4th-street-complete-streets-review-2025.pdf'
    description = 'Evaluates 4th Street from Menaul to Candelaria for maintenance-era restriping, comparing existing dimensions and bikeway alternatives, explaining policy and design constraints, and identifying planning priorities without presenting a final engineered design.'
    notes = @(
      'Twenty-page City of Albuquerque review prepared by Toole Design Group; cover, substantive text, maps, and representative pages were visually reviewed.',
      'The report expressly identifies itself as planning-level analysis rather than final design.',
      'No current authoritative direct-file URL was located; the maintained City program page corroborates the Annual Complete Streets Maintenance Program.'
    )
  },
  [ordered]@{
    filename = 'FY25 Complete Streets Package 1_Updates.pdf'
    title = 'FY 2025 Complete Streets Package 1 Updates'
    date = '2024-05-07'
    r2_key = 'transportation/roadway-projects/studies/cabq-fy2025-complete-streets-package-1-updates.pdf'
    description = 'Preserves City restriping concept sheets for Chappell Drive, Hanover Road, and Indian School Road, showing proposed lane, parking, bicycle, bus-stop, curb-paint, and intersection changes over aerial basemaps and surveyed roadway dimensions.'
    notes = @(
      'Eighteen City of Albuquerque Department of Municipal Development engineering sheets dated May 7, 2024; all pages and representative title blocks were visually reviewed.',
      'The 31,832,318-byte original exceeds 25 MiB because it preserves full-resolution aerial engineering sheets; it is below the 100 MiB archive limit and is retained without modification.',
      'No current authoritative direct-file URL was located; City title blocks establish authorship and the maintained City program page corroborates the Annual Complete Streets Maintenance Program.'
    )
  },
  [ordered]@{
    filename = 'FY26-27 COA Complete Streets_Final Signed_5.29.2026.pdf'
    title = 'FY 2026–2027 City of Albuquerque Complete Streets Package (Final Signed, May 29, 2026)'
    date = '2026-05-29'
    r2_key = 'transportation/roadway-projects/studies/cabq-fy2026-2027-complete-streets-package-final-signed.pdf'
    description = 'Combines signed City restriping plans for eight Albuquerque corridors with WSP existing-conditions memoranda for Five Points/Goff, Gonzales, San Mateo, and Wyoming, documenting proposed multimodal layouts, field conditions, traffic, crashes, transit, and implementation constraints.'
    notes = @(
      'Eighty-one-page final package: 60 City engineering sheets plus four WSP existing-conditions memoranda; all pages and representative title blocks were visually reviewed.',
      'Plan sets cover Benavides, Girard, Ladera, Menaul, Montaño, Pennsylvania, University/Randolph, and Unser and carry the seal of New Mexico professional engineer Risa Lujan.',
      'The 82,437,210-byte original exceeds 25 MiB because it preserves full-resolution signed aerial engineering sheets and technical memoranda; it is below the 100 MiB archive limit and is retained without modification.',
      'No current authoritative direct-file URL was located; City title blocks, signatures, and seals establish authorship and the maintained City program page corroborates the Annual Complete Streets Maintenance Program.'
    )
  }
)

$r2ByKey = @{}
foreach ($object in @($r2.objects)) { $r2ByKey[[string]$object.key] = $object }

$decisions = @()
foreach ($definition in $definitions) {
  $item = @($catalog.items | Where-Object filename -eq $definition.filename)
  if ($item.Count -ne 1) { throw "Expected one catalog item named '$($definition.filename)'; found $($item.Count)." }
  $item = $item[0]
  $seed = "user-contributed:$($definition.filename):$($item.checksum_sha256)"
  $id = Get-StableId $seed
  $record = @($inventory.candidates | Where-Object id -eq $id)
  if ($record.Count -gt 1) { throw "Duplicate inventory id '$id'." }
  if (-not $record.Count) {
    $record = @(New-InventoryRecord $id)
    $inventory.candidates += $record[0]
  }
  $record = $record[0]
  $wordCount = Get-WordCount $definition.description
  if ($wordCount -lt 20 -or $wordCount -gt 50) { throw "Description for '$id' has $wordCount words." }
  $record.status = 'placement assigned'
  $record.source_url = $programUrl
  $record.direct_file_url = $null
  $record.r2_url = 'https://files.abqinfo.com/' + $definition.r2_key
  $record.r2_key = $definition.r2_key
  $record.agency = 'City of Albuquerque'
  $record.title = $definition.title
  $record.date = $definition.date
  $record.file_type = 'PDF'
  $record.size_bytes = [int64]$item.size_bytes
  $record.checksum_sha256 = [string]$item.checksum_sha256
  $record.parent_url = $programUrl
  $record.referring_urls = @($programUrl)
  $record.discovery_path = @($programUrl, "user-contributed:$($definition.filename)")
  $record.discovery_method = 'User-contributed official document review with maintained City program-page corroboration'
  $record.provenance_status = 'City-branded original verified from internal title pages, Department of Municipal Development title blocks, and where applicable signatures and professional-engineer seals; maintained City program page corroborates the program; no current direct-file URL located'
  $record.proposed_canonical_page = 'content/transportation/roadway-projects/studies.md'
  $record.description = $definition.description
  $record.description_word_count = $wordCount
  $record.processing_notes = @($definition.notes)
  $record.validation_status = 'local PDF structure, extracted text, visual rendering, exact size, and SHA-256 verified; R2 upload pending'
  $record.exclusion_reason = $null
  $record.local_path = $item.local_path
  $record.updated_at = (Get-Date).ToUniversalTime().ToString('o')

  $decisions += [pscustomobject][ordered]@{
    id = $id; filename = $definition.filename; decision = 'approved for archival and addition'
    agency = 'City of Albuquerque'; title = $definition.title; date = $definition.date; file_type = 'PDF'
    pages = [int]$item.pages; size_bytes = [int64]$item.size_bytes; size_human = [string]$item.size_human
    exceeds_25_mib = [bool]$item.exceeds_25_mib; exceeds_100_mib = [bool]$item.exceeds_100_mib
    checksum_sha256 = [string]$item.checksum_sha256; source_url = $programUrl; direct_file_url = $null
    parent_url = $programUrl; proposed_canonical_page = 'content/transportation/roadway-projects/studies.md'
    implementation_locations = @('content/transportation/roadway-projects/studies.md')
    r2_key = $definition.r2_key; r2_url = 'https://files.abqinfo.com/' + $definition.r2_key
    description = $definition.description; description_word_count = $wordCount
    provenance_status = $record.provenance_status; processing_notes = @($definition.notes)
    already_present = $r2ByKey.ContainsKey([string]$definition.r2_key)
  }
}

$addedBytes = [int64](($decisions | Measure-Object -Property size_bytes -Sum).Sum)
$alreadyPresentBytes = [int64](($decisions | Where-Object already_present | Measure-Object -Property size_bytes -Sum).Sum)
$preBatchR2Bytes = [int64]$r2.total_bytes - $alreadyPresentBytes
$decisionDocument = [ordered]@{
  schema_version = 1; generated_at = (Get-Date).ToUniversalTime().ToString('o')
  reviewed_file_count = [int]$catalog.file_count; additions = $decisions; duplicates = @()
  added_bytes = $addedBytes; current_r2_bytes = $preBatchR2Bytes
  projected_r2_bytes = $preBatchR2Bytes + $addedBytes
  exact_next_action = 'Upload and publicly verify the three originals, add them under City Corridor and Neighborhood Studies, and run the full validation suite.'
}
$decisionDocument | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $DecisionPath -Encoding utf8

$archivePlan = [ordered]@{
  schema_version = 1; generated_at = (Get-Date).ToUniversalTime().ToString('o')
  bucket = [string]$r2.bucket; current_r2_bytes = $preBatchR2Bytes; added_bytes = $addedBytes
  projected_r2_bytes = $preBatchR2Bytes + $addedBytes
  maximum_object_bytes = [int64](100MB); maximum_projected_r2_bytes = [int64](10GB); items = $decisions
}
$archivePlan | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ArchivePlanPath -Encoding utf8

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$inventory | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $InventoryPath -Encoding utf8

[pscustomobject]@{ Reviewed = $catalog.file_count; Additions = $decisions.Count; AddedBytes = $addedBytes; ProjectedR2Bytes = $preBatchR2Bytes + $addedBytes; DecisionPath = $DecisionPath; ArchivePlanPath = $ArchivePlanPath }
