[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$crossListings = @(
  [pscustomobject]@{id='src-0b9dc46fbf32cfb7'; locations=@('content/development-land-use/development-process.md','content/transportation/transportation-plans.md')}
  [pscustomobject]@{id='src-2cf447cc8b453482'; locations=@('content/transportation/transportation-plans.md','content/public-works/city-facilities.md')}
  [pscustomobject]@{id='src-75935732f3f11f34'; locations=@('content/transportation/design-references.md','content/development-land-use/development-process.md')}
  [pscustomobject]@{id='src-83a50a7b1723e768'; locations=@('content/public-works/stormwater-drainage.md','content/transportation/design-references.md')}
)

foreach ($item in $crossListings) {
  foreach ($page in $item.locations) {
    if (-not (Test-Path -LiteralPath $page)) { throw "Missing cross-list page '$page'." }
  }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $item.id -Set @{
    implementation_location = [string]$item.locations[0]
    implementation_locations = @($item.locations)
    cross_listing_approved = $true
  } -InventoryPath $InventoryPath | Out-Null
}

$id = 'src-d311dfa1ad0a2915'
$pagePath = 'content/maps/dashboards.md'
$sourceUrl = 'https://www.cabq.gov/gis/address-report'
$liveUrl = 'https://geocortexweb.cabq.gov/vertigisstudio/web/?app=eeffb6977e0c467f8439b0c97d34eaaa'
$description = 'Creates printable reports for Albuquerque addresses combining Bernalillo County property ownership, City services, political boundaries, and trash-collection schedules in one searchable location.'
$page = Get-Content -Raw -Encoding UTF8 -LiteralPath $pagePath
if ($page -notlike "*$sourceUrl*" -or $page -notlike "*$liveUrl*" -or $page -notlike "*$description*") {
  throw 'Address Report implementation is missing its direct tool, official source, or reviewed description.'
}
$wordCount = @($description -split '\s+' | Where-Object { $_ }).Count
if ($wordCount -lt 20 -or $wordCount -gt 50) { throw "Address Report description has $wordCount words." }
& "$PSScriptRoot/Update-Candidate.ps1" -Id $id -Set @{
  status = 'validated'
  title = 'Albuquerque Address Report'
  source_url = $sourceUrl
  direct_file_url = $liveUrl
  agency = 'City of Albuquerque'
  proposed_canonical_page = $pagePath
  description = $description
  implementation_location = $pagePath
  implementation_locations = @($pagePath)
  provenance_status = 'official government source page and live City application recorded'
  validation_status = 'passed: live City tool, official City source page, 20–50-word description, and page placement validated'
  processing_notes = @(
    'Direct live application is the primary user-facing link; the official City explanatory page is retained for provenance.',
    'Web-only interactive tool; no static R2 archival object is applicable.'
  )
  exclusion_reason = $null
} -InventoryPath $InventoryPath | Out-Null

[pscustomobject]@{CrossListings=$crossListings.Count;WebRecords=1;Status='validated'} | ConvertTo-Json -Compress
