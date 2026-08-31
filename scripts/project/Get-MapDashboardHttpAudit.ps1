[CmdletBinding()]
param(
  [string]$QueuePath = 'project-state/discovery/map-dashboard-interactive-audit-queue.json',
  [string]$OutputPath = 'project-state/discovery/map-dashboard-http-audit-2026-08-30.json',
  [int]$ThrottleLimit = 8
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 or newer is required.' }

$queue = Get-Content -Raw -Encoding UTF8 -LiteralPath $QueuePath | ConvertFrom-Json
$results = @($queue.items) | ForEach-Object -Parallel {
  $item = $_
  $record = [ordered]@{
    id = [string]$item.id
    url = [string]$item.url
    http_status = $null
    final_url = $null
    content_type = $null
    response_title = $null
    response_bytes = $null
    arcgis_item_id = $null
    arcgis_item_title = $null
    arcgis_item_type = $null
    arcgis_owner = $null
    arcgis_access = $null
    arcgis_error = $null
    shell_warning = $null
    request_error = $null
  }
  try {
    $response = Invoke-WebRequest -Uri $item.url -UseBasicParsing -MaximumRedirection 10 -TimeoutSec 45
    $record.http_status = [int]$response.StatusCode
    $record.final_url = [string]$response.BaseResponse.RequestMessage.RequestUri.AbsoluteUri
    $record.content_type = [string]$response.Headers.'Content-Type'
    $record.response_bytes = [int64]$response.RawContentLength
    if ([string]$response.Content -match '(?is)<title[^>]*>(.*?)</title>') {
      $record.response_title = [Net.WebUtility]::HtmlDecode($Matches[1]).Trim()
    }
    $signals = @('Item Replacement','Replacement not available','has been retired','Page Not Found','404 Not Found','Sign in')
    foreach ($signal in $signals) {
      if ([string]$response.Content -like "*$signal*" -or [string]$record.response_title -like "*$signal*") { $record.shell_warning = $signal; break }
    }
  } catch {
    $record.request_error = $_.Exception.Message
    if ($_.Exception.Response.StatusCode) { $record.http_status = [int]$_.Exception.Response.StatusCode }
  }

  $uri = [uri]$item.url
  $query = [Web.HttpUtility]::ParseQueryString($uri.Query)
  $arcgisId = if ($query['appid']) { $query['appid'] } elseif ($query['id']) { $query['id'] } elseif ($uri.AbsolutePath -match '/items/([0-9a-f]{32})') { $Matches[1] } else { $null }
  if ($arcgisId -and $arcgisId -match '^[0-9a-fA-F]{32}$') {
    $record.arcgis_item_id = $arcgisId.ToLowerInvariant()
    try {
      $metadata = Invoke-RestMethod -Uri "https://www.arcgis.com/sharing/rest/content/items/$arcgisId`?f=json" -TimeoutSec 45
      if ($metadata.error) { $record.arcgis_error = "ArcGIS $($metadata.error.code): $($metadata.error.message)" }
      else {
        $record.arcgis_item_title = [string]$metadata.title
        $record.arcgis_item_type = [string]$metadata.type
        $record.arcgis_owner = [string]$metadata.owner
        $record.arcgis_access = [string]$metadata.access
      }
    } catch { $record.arcgis_error = $_.Exception.Message }
  }
  [pscustomobject]$record
} -ThrottleLimit $ThrottleLimit

$output = [ordered]@{
  schema_version = 1
  checked_at = (Get-Date).ToUniversalTime().ToString('o')
  input_count = @($queue.items).Count
  result_count = @($results).Count
  results = @($results | Sort-Object id)
}
$json = $output | ConvertTo-Json -Depth 8
$full = [IO.Path]::GetFullPath($OutputPath)
$temporary = "$full.tmp-$PID"
[IO.File]::WriteAllText($temporary,$json,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $full -Force
[pscustomobject]@{
  Checked = @($results).Count
  HttpErrors = @($results | Where-Object { $_.request_error -or ($_.http_status -and $_.http_status -ge 400) }).Count
  ShellWarnings = @($results | Where-Object shell_warning).Count
  ArcGisErrors = @($results | Where-Object arcgis_error).Count
  OutputPath = $OutputPath
} | ConvertTo-Json -Compress
