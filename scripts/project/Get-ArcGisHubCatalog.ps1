[CmdletBinding()]
param(
  [string]$HubUrl = 'https://dmd-public-cabq.hub.arcgis.com/',
  [ValidateRange(1,100)][int]$MaxRecords = 100,
  [ValidateRange(1,25)][int]$ReviewLimit = 25,
  [string]$OutputPath = 'research/discovery/dmd-arcgis-hub-links.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-JsonRequest([string]$Uri) {
  for ($attempt = 1; $attempt -le 4; $attempt++) {
    try { return Invoke-RestMethod -Uri $Uri -TimeoutSec 60 }
    catch {
      if ($attempt -eq 4) { throw }
      Start-Sleep -Milliseconds (250 * $attempt)
    }
  }
}

function Convert-ArcGisDate($Milliseconds) {
  if ($null -eq $Milliseconds -or [long]$Milliseconds -le 0) { return $null }
  return [DateTimeOffset]::FromUnixTimeMilliseconds([long]$Milliseconds).UtcDateTime.ToString('o')
}

function Get-PlainText([AllowNull()][string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { return $null }
  $text = [Net.WebUtility]::HtmlDecode($Value)
  $text = $text -replace '<[^>]+>', ' '
  return ($text -replace '\s+', ' ').Trim()
}

function Get-LiveUrl($Item) {
  if (-not [string]::IsNullOrWhiteSpace([string]$Item.url)) { return [string]$Item.url }
  switch ([string]$Item.type) {
    'Dashboard' { return "https://www.arcgis.com/apps/dashboards/$($Item.id)" }
    default { return "https://www.arcgis.com/home/item.html?id=$($Item.id)" }
  }
}

function Get-ReviewScore($Item) {
  $value = (([string]$Item.title) + ' ' + ([string]$Item.snippet) + ' ' + (@($Item.tags) -join ' ')).ToLowerInvariant()
  $score = 0
  foreach ($term in @('project','bikeway','bicycle','trail','street','traffic','vision zero','maintenance','school crossing','drainage','arroyo','parking','moratorium','speed limit','pedestrian')) {
    if ($value.Contains($term)) { $score += 3 }
  }
  if ([string]$Item.type -in @('Web Experience','Web Mapping Application','Dashboard','StoryMap')) { $score += 4 }
  if ([string]$Item.type -eq 'Feature Service') { $score += 1 }
  foreach ($term in @('world_basemap','current city limits','public restroom','survey monument','map menu','request process flowchart','council district poster')) {
    if ($value.Contains($term)) { $score -= 20 }
  }
  return $score
}

$hubResponse = Invoke-WebRequest -Uri $HubUrl -UseBasicParsing -TimeoutSec 60
$siteIdMatch = [regex]::Match($hubResponse.Content, 'siteId["'']?\s*:\s*["''](?<id>[0-9a-f]{32})', 'IgnoreCase')
if (-not $siteIdMatch.Success) { throw "Could not identify an ArcGIS Hub site ID at $HubUrl" }
$siteId = $siteIdMatch.Groups['id'].Value

$siteItem = Invoke-JsonRequest "https://www.arcgis.com/sharing/rest/content/items/${siteId}?f=json"
$siteData = Invoke-JsonRequest "https://www.arcgis.com/sharing/rest/content/items/${siteId}/data?f=json"
$groupIds = @($siteData.catalog.groups | Where-Object { $_ } | Sort-Object -Unique)
if (-not $groupIds.Count) { throw "The Hub site metadata contains no public catalog group." }

$groupRecords = @()
$searchItems = @()
foreach ($groupId in $groupIds) {
  $groupRecords += Invoke-JsonRequest "https://www.arcgis.com/sharing/rest/community/groups/${groupId}?f=json"
  $remaining = $MaxRecords - $searchItems.Count
  if ($remaining -le 0) { break }
  $search = Invoke-JsonRequest "https://www.arcgis.com/sharing/rest/search?q=group%3A${groupId}&num=${remaining}&sortField=modified&sortOrder=desc&f=json"
  $searchItems += @($search.results)
}
$searchItems = @($searchItems | Group-Object id | ForEach-Object { $_.Group[0] } | Select-Object -First $MaxRecords)

$ranked = @($searchItems | ForEach-Object {
  [pscustomobject]@{ item = $_; score = Get-ReviewScore $_ }
} | Sort-Object @{Expression='score';Descending=$true}, @{Expression={ [long]$_.item.modified };Descending=$true}, @{Expression={ [string]$_.item.title };Descending=$false})
$selectedIds = @($ranked | Select-Object -First ([Math]::Min($ReviewLimit,$ranked.Count)) | ForEach-Object { [string]$_.item.id })

$candidates = @()
foreach ($entry in $ranked) {
  $summary = $entry.item
  $item = Invoke-JsonRequest "https://www.arcgis.com/sharing/rest/content/items/$($summary.id)?f=json"
  $selected = [string]$item.id -in $selectedIds
  $relatedIds = @()
  if ($selected) {
    try {
      $data = Invoke-JsonRequest "https://www.arcgis.com/sharing/rest/content/items/$($item.id)/data?f=json"
      $dataText = $data | ConvertTo-Json -Depth 50 -Compress
      $relatedIds = @([regex]::Matches($dataText, '(?i)(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])') | ForEach-Object { $_.Value.ToLowerInvariant() } | Where-Object { $_ -ne ([string]$item.id).ToLowerInvariant() } | Sort-Object -Unique)
    } catch {
      $relatedIds = @()
    }
  }

  $liveUrl = Get-LiveUrl $item
  $itemPageUrl = "https://www.arcgis.com/home/item.html?id=$($item.id)"
  $directFileUrl = if ([string]$item.type -in @('PDF','Image')) { "https://www.arcgis.com/sharing/rest/content/items/$($item.id)/data" } else { $null }
  $notes = @(
    "ArcGIS item ID $($item.id); owner $($item.owner); organization $($item.orgId).",
    "Created $(Convert-ArcGisDate $item.created); modified $(Convert-ArcGisDate $item.modified)."
  )
  if (-not $selected) { $notes += 'Cataloged but not substantively reviewed in this bounded 25-item batch.' }

  $candidates += [ordered]@{
    url = $liveUrl
    anchor_text = [string]$item.title
    agency = 'City of Albuquerque'
    arcgis_item_id = [string]$item.id
    arcgis_item_page_url = $itemPageUrl
    direct_file_url = $directFileUrl
    file_type = [string]$item.type
    size_bytes = if ($null -ne $item.size) { [long]$item.size } else { $null }
    owner = [string]$item.owner
    organization_id = [string]$item.orgId
    created_at = Convert-ArcGisDate $item.created
    modified_at = Convert-ArcGisDate $item.modified
    snippet = Get-PlainText ([string]$item.snippet)
    source_description = Get-PlainText ([string]$item.description)
    tags = @($item.tags)
    review_score = [int]$entry.score
    review_selected = $selected
    related_item_ids = $relatedIds
    parent_url = $HubUrl
    referring_urls = @($HubUrl,$itemPageUrl)
    discovery_path = @(
      'https://www.cabq.gov/municipaldevelopment/maps',
      'https://www.cabq.gov/municipaldevelopment/',
      $HubUrl,
      $itemPageUrl
    )
    discovery_method = 'authoritative City outbound link followed by ArcGIS Hub content-group REST query'
    discovery_depth = 3
    provenance_status = 'CABQ-owned ArcGIS item recovered through the official DMD Hub catalog'
    processing_notes = $notes
  }
}

$output = [ordered]@{
  schema_version = 1
  agency = 'cabq'
  source_url = $HubUrl
  scope = 'Official Department of Municipal Development ArcGIS Hub content group'
  retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
  limits = [ordered]@{ max_records = $MaxRecords; review_limit = $ReviewLimit }
  site = [ordered]@{
    id = [string]$siteItem.id
    title = [string]$siteItem.title
    owner = [string]$siteItem.owner
    organization_id = [string]$siteItem.orgId
    modified_at = Convert-ArcGisDate $siteItem.modified
  }
  groups = @($groupRecords | ForEach-Object { [ordered]@{ id=[string]$_.id; title=[string]$_.title; owner=[string]$_.owner; organization_id=[string]$_.orgId; access=[string]$_.access } })
  catalog_total = $searchItems.Count
  reviewed_count = @($candidates | Where-Object review_selected).Count
  pending_count = @($candidates | Where-Object { -not $_.review_selected }).Count
  candidates = $candidates
}

$parent = Split-Path -Parent $OutputPath
if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
$output | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{
  source_url = $output.source_url
  retrieved_at = $output.retrieved_at
  catalog_total = $output.catalog_total
  reviewed_count = $output.reviewed_count
  pending_count = $output.pending_count
} | ConvertTo-Json
