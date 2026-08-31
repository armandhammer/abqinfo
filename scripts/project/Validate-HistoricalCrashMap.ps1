[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/discovery/historical-crash-map-validation.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$id = 'src-89bcf717950c6b15'
$itemId = 'ec395f5587744d778832207af7d86f93'
$appUrl = "https://mrmpo.maps.arcgis.com/apps/MapSeries/index.html?appid=$itemId"
$metadataUrl = "https://www.arcgis.com/sharing/rest/content/items/$itemId`?f=json"
$pagePath = 'content/transportation/bicycling/safety-crash-data.md'

$item = Invoke-RestMethod -Uri $metadataUrl -TimeoutSec 60
$app = Invoke-WebRequest -Uri $appUrl -UseBasicParsing -MaximumRedirection 10 -TimeoutSec 60
if ([string]$item.id -ne $itemId) { throw 'ArcGIS item identifier mismatch.' }
if ([string]$item.type -ne 'Web Mapping Application') { throw "Unexpected ArcGIS item type: $($item.type)" }
if ([string]$item.owner -ne 'MRMPO_GIS' -or [string]$item.access -ne 'public') { throw 'ArcGIS item is not the expected public MRMPO application.' }
if ([int]$app.StatusCode -ne 200) { throw "Historical crash application returned HTTP $($app.StatusCode)." }
$page = Get-Content -Raw -Encoding UTF8 -LiteralPath $pagePath
if ($page -notlike "*$appUrl*") { throw 'Historical crash application is missing from its ABQInfo implementation page.' }

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$candidate = @($inventory.candidates | Where-Object id -eq $id)
if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for '$id'." }
$description = "Opens MRMPO’s interactive historical crash report for the Albuquerque Metropolitan Planning Area, with mapped and summarized crash patterns covering the 2015–2019 period."
$candidate[0].status = 'validated'
$candidate[0].agency = 'MRCOG'
$candidate[0].title = '2015–2019 Albuquerque Metropolitan Online Crash Report'
$candidate[0].date = '2015–2019'
$candidate[0].file_type = 'Web Mapping Application'
$candidate[0].provenance_status = 'official MRCOG archive page and public MRMPO ArcGIS item metadata recorded'
$candidate[0].proposed_canonical_page = $pagePath
$candidate[0].description = $description
$candidate[0].description_word_count = @($description -split '\s+' | Where-Object { $_ }).Count
$candidate[0].implementation_location = $pagePath
$candidate[0].implementation_locations = @($pagePath)
$candidate[0].validation_status = 'passed: official MRCOG referral, public MRMPO ArcGIS ownership and item metadata, HTTP 200 application response, and page placement validated'
$candidate[0].processing_notes = @($candidate[0].processing_notes) + @('Validated direct map application rather than substituting its ArcGIS REST or metadata page.') | Sort-Object -Unique
$candidate[0].updated_at = (Get-Date).ToUniversalTime().ToString('o')

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$json = $inventory | ConvertTo-Json -Depth 12
$inventoryFull = [IO.Path]::GetFullPath($InventoryPath)
$inventoryTemporary = "$inventoryFull.tmp-$PID"
[IO.File]::WriteAllText($inventoryTemporary,$json,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $inventoryTemporary -Destination $inventoryFull -Force

$validation = [ordered]@{
  schema_version = 1
  verified_at = (Get-Date).ToUniversalTime().ToString('o')
  candidate_id = $id
  arcgis_item_id = $itemId
  title = [string]$item.title
  type = [string]$item.type
  owner = [string]$item.owner
  access = [string]$item.access
  modified = [int64]$item.modified
  application_url = $appUrl
  application_http_status = [int]$app.StatusCode
  implementation_location = $pagePath
  passed = $true
}
$validation | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$validation | ConvertTo-Json -Compress
