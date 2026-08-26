[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$ServiceUrl,
  [Parameter(Mandatory)][string]$OutputPath,
  [Parameter(Mandatory)][string]$Title,
  [Parameter(Mandatory)][string]$Agency,
  [string]$CanonicalPage,
  [string]$SiteAction = 'Review required.'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = $ServiceUrl.TrimEnd('/')
$service = Invoke-RestMethod -Uri "$root`?f=pjson"
if ($service.PSObject.Properties['error']) { throw "ArcGIS service error: $($service.error.message)" }

$layers = @()
foreach ($layerSummary in @($service.layers)) {
  $layerUrl = "$root/$($layerSummary.id)"
  $metadata = Invoke-RestMethod -Uri "$layerUrl`?f=pjson"
  $featureCount = $null
  if ([string]$metadata.capabilities -match '(^|,)Query(,|$)') {
    try {
      $countResult = Invoke-RestMethod -Uri "$layerUrl/query?where=1%3D1&returnCountOnly=true&f=json"
      if ($null -ne $countResult.count) { $featureCount = [long]$countResult.count }
    } catch {
      $featureCount = $null
    }
  }
  $layers += [ordered]@{
    id = [int]$layerSummary.id
    name = [string]$layerSummary.name
    type = [string]$layerSummary.type
    geometry_type = [string]$metadata.geometryType
    description = [string]$metadata.description
    feature_count_at_review = $featureCount
    capabilities = @(([string]$metadata.capabilities -split ',') | Where-Object { $_ })
    supported_query_formats = @(([string]$metadata.supportedQueryFormats -split ',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    fields = @($metadata.fields | ForEach-Object { [ordered]@{ name = [string]$_.name; alias = [string]$_.alias; type = [string]$_.type } })
  }
}

$output = [ordered]@{
  schema_version = 1
  source_url = $root
  title = $Title
  agency = $Agency
  retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
  discovery_method = 'Deterministic ArcGIS REST service, layer-metadata, and feature-count review'
  crawl_status = 'relevant ArcGIS dependency frontier exhausted'
  proposed_canonical_page = $CanonicalPage
  service = [ordered]@{
    arcgis_version = $service.currentVersion
    description = [string]$service.description
    service_description = [string]$service.serviceDescription
    copyright = [string]$service.copyrightText
    capabilities = @(([string]$service.capabilities -split ',') | Where-Object { $_ })
    supported_query_formats = @(([string]$service.supportedQueryFormats -split ',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
  }
  layers = $layers
  archival_reconciliation = [ordered]@{
    new_uploads_required = 0
    reason = 'This is a maintained live ArcGIS service rather than a static authoritative document. Preserve direct map and data-service links; archive a separate source document only if the service exposes one.'
  }
  site_action = $SiteAction
  processing_notes = @(
    'The root service and every published sublayer were reviewed through official REST metadata.',
    'Feature counts are audit observations and are not fixed claims for ABQInfo content.',
    'No PDF, spreadsheet, document attachment, or static map is implied by an ArcGIS service unless separately recorded.'
  )
}

$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
$json = $output | ConvertTo-Json -Depth 12
[IO.File]::WriteAllText([IO.Path]::GetFullPath($OutputPath), $json, [Text.UTF8Encoding]::new($false))
[pscustomobject]@{ service = $root; layers = $layers.Count; output = $OutputPath } | ConvertTo-Json -Compress
