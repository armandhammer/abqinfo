[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/discovery/historical-crash-map-validation.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 or newer is required to preserve canonical inventory formatting.' }
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
$responseTitle = [regex]::Match([string]$app.Content,'<title>(.*?)</title>','IgnoreCase').Groups[1].Value.Trim()
$replacementShell = $responseTitle -eq 'Item Replacement'
if (-not $replacementShell) { throw "Expected retired Item Replacement shell, received '$responseTitle'. Recheck the application interactively." }
$page = Get-Content -Raw -Encoding UTF8 -LiteralPath $pagePath
if ($page -like "*$appUrl*") { throw 'Retired historical crash application is still linked from its former ABQInfo implementation page.' }

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$candidate = @($inventory.candidates | Where-Object id -eq $id)
if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for '$id'." }
$candidate[0].status = 'excluded'
$candidate[0].agency = 'MRCOG'
$candidate[0].title = '2015–2019 Albuquerque Metropolitan Online Crash Report'
$candidate[0].date = '2015–2019'
$candidate[0].file_type = 'Web Mapping Application'
$candidate[0].provenance_status = 'official MRCOG archive page and public MRMPO ArcGIS item metadata recorded; application retirement confirmed in a rendered browser'
$candidate[0].proposed_canonical_page = $pagePath
$candidate[0].description = $null
$candidate[0].description_word_count = 0
$candidate[0].implementation_location = $null
$candidate[0].implementation_locations = @()
$candidate[0].validation_status = 'failed interactive validation: ArcGIS renders an Item Replacement dialog stating the application has been retired and no replacement is available'
$candidate[0].exclusion_reason = 'Retired ArcGIS application; the visible user interface states “Replacement not available,” so HTTP 200 and public item metadata do not constitute a working map.'
$candidate[0].processing_notes = @($candidate[0].processing_notes) + @(
  'The prior HTTP-and-metadata-only validation was a false positive and was corrected after rendered-browser review.',
  'Do not reintroduce unless a functioning authoritative replacement is found and interactively validated.'
) | Sort-Object -Unique
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
  response_title = $responseTitle
  replacement_shell_detected = $replacementShell
  rendered_browser_observation = 'Item Replacement dialog: MRCOG Roadway Safety and Crash Report (2015-2019) has been retired; Replacement not available.'
  implementation_location = $null
  exclusion_reason = [string]$candidate[0].exclusion_reason
  passed = $false
}
$validation | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$validation | ConvertTo-Json -Compress
