[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$resolved = @()

foreach ($candidate in @($inventory.candidates | Where-Object {
  $_.status -eq 'pending review' -and $_.source_url -match '(?i)(arcgis\.com|mrcogmaps\.org)' -and $_.source_url -match '(?i)(?:appid=|[?&]id=)([a-f0-9]{32})'
})) {
  $itemId = [regex]::Match($candidate.source_url, '(?i)(?:appid=|[?&]id=)([a-f0-9]{32})').Groups[1].Value
  $metadataRoot = if ($candidate.source_url -match '(?i)mrcogmaps\.org') { 'https://mrcogmaps.org/portal' } else { 'https://www.arcgis.com' }
  $metadataUrl = "$metadataRoot/sharing/rest/content/items/$itemId`?f=json"
  $metadata = Invoke-RestMethod -Uri $metadataUrl -Method Get
  if (-not $metadata.PSObject.Properties['title'] -or -not $metadata.title) {
    $message = if ($metadata.PSObject.Properties['error']) { [string]$metadata.error.message } else { 'item metadata unavailable' }
    $notes = @($candidate.processing_notes) + "ArcGIS metadata lookup failed for item $itemId`: $message."
    & "$PSScriptRoot/Update-Candidate.ps1" -Id $candidate.id -InventoryPath $InventoryPath -Set @{ processing_notes = $notes } | Out-Null
    continue
  }

  $date = $null
  if ($metadata.PSObject.Properties['modified'] -and $metadata.modified) {
    $date = [DateTimeOffset]::FromUnixTimeMilliseconds([int64]$metadata.modified).UtcDateTime.ToString('yyyy-MM-dd')
  }
  $notes = @($candidate.processing_notes | Where-Object { $_ -notmatch '^ArcGIS metadata:' })
  $notes += "ArcGIS metadata: item $itemId, type '$($metadata.type)', owner '$($metadata.owner)', last modified $date."
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $candidate.id -InventoryPath $InventoryPath -Set @{
    title = [string]$metadata.title
    agency = 'MRCOG ArcGIS'
    date = $date
    processing_notes = $notes
  } | Out-Null
  $resolved += [pscustomobject]@{ id=$candidate.id; title=$metadata.title; item_id=$itemId; type=$metadata.type; modified=$date }
}

@($resolved) | ConvertTo-Json -Depth 4
