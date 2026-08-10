[CmdletBinding()]
param(
  [string]$CatalogPath = 'research/discovery/dmd-arcgis-hub-links.json',
  [string]$ReviewPath = 'project-state/discovery/dmd-arcgis-hub-overrides.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/discovery/dmd-arcgis-hub-batch-report.json',
  [switch]$CheckLinks
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-HumanSize([long]$Bytes) {
  if ($Bytes -ge 1GB) { return '{0:N2} GiB' -f ($Bytes / 1GB) }
  if ($Bytes -ge 1MB) { return '{0:N2} MiB' -f ($Bytes / 1MB) }
  if ($Bytes -ge 1KB) { return '{0:N2} KiB' -f ($Bytes / 1KB) }
  return "$Bytes bytes"
}

function Assert-Batch([bool]$Condition, [string]$Message) {
  if (-not $Condition) { throw $Message }
}

$catalog = Get-Content -Raw -LiteralPath $CatalogPath | ConvertFrom-Json
$review = @(Get-Content -Raw -LiteralPath $ReviewPath | ConvertFrom-Json)
$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json

Assert-Batch ($catalog.catalog_total -le $catalog.limits.max_records) 'Catalog record cap was exceeded.'
Assert-Batch ($catalog.reviewed_count -le $catalog.limits.review_limit) 'Review cap was exceeded.'
Assert-Batch (@($catalog.candidates).Count -eq $catalog.catalog_total) 'Catalog count does not match candidate records.'
Assert-Batch ($review.Count -eq $catalog.reviewed_count) 'Durable review decisions do not match the selected review count.'

$inventoryMatches = @()
foreach ($candidate in @($catalog.candidates)) {
  $url = ([string]$candidate.url).TrimEnd('/')
  $matches = @($inventory.candidates | Where-Object {
    @($_.source_url,$_.direct_file_url) | Where-Object { $_ -and ([string]$_).TrimEnd('/') -eq $url }
  })
  Assert-Batch ($matches.Count -eq 1) "Expected one inventory record for $url; found $($matches.Count)."
  $inventoryMatches += $matches[0]
}

$reviewedUrls = @($catalog.candidates | Where-Object review_selected | ForEach-Object { ([string]$_.url).TrimEnd('/') })
$overrideUrls = @($review.match_url | ForEach-Object { ([string]$_).TrimEnd('/') })
Assert-Batch (-not @($reviewedUrls | Where-Object { $_ -notin $overrideUrls }).Count) 'A selected review candidate lacks a durable decision.'
Assert-Batch (-not @($overrideUrls | Where-Object { $_ -notin $reviewedUrls }).Count) 'A review decision was recorded outside the 25-item selection.'

$statusCounts = [ordered]@{}
foreach ($group in @($inventoryMatches | Group-Object status | Sort-Object Name)) { $statusCounts[$group.Name] = $group.Count }
Assert-Batch ($statusCounts['validated'] -eq 15) 'Expected exactly 15 implemented and validated Hub candidates.'
Assert-Batch ($statusCounts['approved for addition'] -eq 5) 'Expected exactly five deferred approved candidates.'
Assert-Batch ($statusCounts['duplicate'] -eq 4) 'Expected exactly four duplicate candidates.'
Assert-Batch ($statusCounts['excluded'] -eq 1) 'Expected exactly one excluded candidate.'
Assert-Batch ($statusCounts['pending review'] -eq 9) 'Expected exactly nine cataloged but unreviewed candidates.'

$descriptionFailures = @($inventoryMatches | Where-Object {
  $_.status -in @('validated','approved for addition') -and
  ($_.description_word_count -lt 20 -or $_.description_word_count -gt 50)
})
Assert-Batch (-not $descriptionFailures.Count) 'One or more reviewed descriptions are outside the 20-50 word range.'

$placementFailures = @()
foreach ($candidate in @($inventoryMatches | Where-Object status -eq 'validated')) {
  foreach ($location in @($candidate.implementation_locations)) {
    if (-not (Test-Path -LiteralPath $location)) {
      $placementFailures += [pscustomobject]@{ id=$candidate.id; location=$location; reason='file missing' }
      continue
    }
    $content = Get-Content -Raw -LiteralPath $location
    if (-not $content.Contains([string]$candidate.source_url)) {
      $placementFailures += [pscustomobject]@{ id=$candidate.id; location=$location; reason='source URL not present' }
    }
  }
  if (@($candidate.implementation_locations).Count -gt 1 -and -not $candidate.cross_listing_approved) {
    $placementFailures += [pscustomobject]@{ id=$candidate.id; location=(@($candidate.implementation_locations) -join ', '); reason='cross-listing not approved' }
  }
}
Assert-Batch (-not $placementFailures.Count) 'One or more implemented placements failed validation.'

$fileCandidates = @($catalog.candidates | Where-Object file_type -in @('PDF','Image') | ForEach-Object {
  Assert-Batch ($null -ne $_.size_bytes) "File candidate $($_.arcgis_item_id) lacks an exact byte size."
  [pscustomobject]@{
    arcgis_item_id = $_.arcgis_item_id
    title = $_.anchor_text
    file_type = $_.file_type
    size_bytes = [long]$_.size_bytes
    human_size = Get-HumanSize ([long]$_.size_bytes)
    over_100_mb = [long]$_.size_bytes -gt 100MB
    proposed_for_upload = $false
  }
})

$oversizedServices = @($catalog.candidates | Where-Object {
  $_.file_type -notin @('PDF','Image') -and $null -ne $_.size_bytes -and [long]$_.size_bytes -gt 100MB
} | ForEach-Object {
  [pscustomobject]@{
    arcgis_item_id = $_.arcgis_item_id
    title = $_.anchor_text
    file_type = $_.file_type
    size_bytes = [long]$_.size_bytes
    human_size = Get-HumanSize ([long]$_.size_bytes)
    note = 'ArcGIS service storage metric, not an individual source file and not proposed for R2 upload.'
  }
})

$linkResults = @()
if ($CheckLinks) {
  foreach ($candidate in @($inventoryMatches | Where-Object status -eq 'validated')) {
    try {
      $response = Invoke-WebRequest -Uri $candidate.source_url -Method Head -UseBasicParsing -TimeoutSec 30
    } catch {
      $response = Invoke-WebRequest -Uri $candidate.source_url -Method Get -UseBasicParsing -TimeoutSec 60
    }
    $linkResults += [pscustomobject]@{ id=$candidate.id; url=$candidate.source_url; status=[int]$response.StatusCode }
  }
  Assert-Batch (-not @($linkResults | Where-Object status -ge 400).Count) 'One or more implemented Hub links failed HTTP validation.'
}

$report = [ordered]@{
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  source_url = $catalog.source_url
  catalog_records = $catalog.catalog_total
  reviewed_records = $catalog.reviewed_count
  status_counts = $statusCounts
  descriptions_20_to_50_words = $true
  placement_validation = 'passed'
  external_links_checked = [bool]$CheckLinks
  external_link_results = $linkResults
  candidate_files = $fileCandidates
  files_over_100_mb = @($fileCandidates | Where-Object over_100_mb).Count
  oversized_non_file_services = $oversizedServices
  r2_uploads = 0
  r2_storage_added_bytes = 0
}

$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$report | ConvertTo-Json -Depth 10
