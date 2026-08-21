[CmdletBinding()]
param(
  [string]$OutputPath = 'project-state/discovery/crawler-regression-report.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/Discovery.Common.ps1"

$allowedHosts = @('www.cabq.gov','documents.cabq.gov')
$publishingHosts = @(Get-DefaultRecognizedPublishingHosts)
$relevantPattern = Get-DefaultDiscoveryRelevantPattern
$documentPattern = '(?i)\.(pdf|docx?|xlsx?|csv|zip|kml|kmz|shp)(?:/view)?(?:$|[?#])'
$errors = [Collections.Generic.List[string]]::new()
$checkCount = 0

function Assert-Regression([bool]$Condition,[string]$Message) {
  $script:checkCount++
  if (-not $Condition) { $errors.Add($Message) }
}

$ancestors = @(Get-DiscoverySeedAncestorUrls -Url 'https://www.cabq.gov/municipaldevelopment/maps')
Assert-Regression ($ancestors -contains 'https://www.cabq.gov/municipaldevelopment/') 'A DMD child seed did not produce the DMD section root ancestor.'
Assert-Regression ($ancestors -notcontains 'https://www.cabq.gov/') 'Seed ancestor traversal escaped to the CABQ site root.'

$hubPolicy = Get-DiscoveryLinkPolicy `
  -Url 'https://dmd-public-cabq.hub.arcgis.com/' `
  -AnchorText 'Project Maps GIS maps and apps' `
  -AllowedHosts $allowedHosts `
  -RecognizedPublishingHosts $publishingHosts `
  -RelevantPattern $relevantPattern `
  -DocumentPattern $documentPattern
Assert-Regression $hubPolicy.capture 'The DMD Project Maps link was not captured as a candidate.'
Assert-Regression (-not $hubPolicy.recursive) 'The external ArcGIS Hub was recursively queued without explicit host authorization.'
Assert-Regression ($hubPolicy.host_classification -eq 'recognized official publishing platform') 'The ArcGIS Hub hostname was not recognized as an official publishing platform.'

$internalPolicy = Get-DiscoveryLinkPolicy `
  -Url 'https://www.cabq.gov/municipaldevelopment/maps' `
  -AnchorText 'Project Maps' `
  -AllowedHosts $allowedHosts `
  -RecognizedPublishingHosts $publishingHosts `
  -RelevantPattern $relevantPattern `
  -DocumentPattern $documentPattern
Assert-Regression ($internalPolicy.capture -and $internalPolicy.recursive) 'A relevant internal DMD map page was not recursively eligible.'

$pdfPolicy = Get-DiscoveryLinkPolicy `
  -Url 'https://external.example.gov/technical-standards.pdf' `
  -AnchorText 'Download' `
  -AllowedHosts $allowedHosts `
  -RecognizedPublishingHosts $publishingHosts `
  -RelevantPattern $relevantPattern `
  -DocumentPattern $documentPattern
Assert-Regression ($pdfPolicy.capture -and -not $pdfPolicy.recursive) 'An externally hosted document was not captured without recursive expansion.'

$irrelevantPolicy = Get-DiscoveryLinkPolicy `
  -Url 'https://example.com/about-us' `
  -AnchorText 'About our company' `
  -AllowedHosts $allowedHosts `
  -RecognizedPublishingHosts $publishingHosts `
  -RelevantPattern $relevantPattern `
  -DocumentPattern $documentPattern
Assert-Regression (-not $irrelevantPolicy.capture) 'An irrelevant external navigation link was captured.'

foreach ($crawler in @('Invoke-UnknownDocumentDiscovery.ps1','Invoke-ScopedSectionCrawl.ps1')) {
  $source = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $PSScriptRoot $crawler)
  Assert-Regression ($source -match 'Get-DiscoverySeedAncestorUrls') "$crawler does not use shared seed-ancestor traversal."
  Assert-Regression ($source -match 'Get-DiscoveryLinkPolicy') "$crawler does not use shared outbound-link policy."
}
$unknownSource = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $PSScriptRoot 'Invoke-UnknownDocumentDiscovery.ps1')
Assert-Regression ($unknownSource -match 'relevant-page ancestor traversal') 'The general crawler does not ascend from relevant discovered child pages.'
Assert-Regression ($unknownSource -match 'pageInDiscoveryContext') 'Generic ancestor pages cannot expose collection links in discovery context.'
Assert-Regression ($unknownSource -match 'isExplicitDiscoveryRoot') 'Explicitly retained source pages are not treated as document-discovery roots.'
Assert-Regression ($unknownSource -match 'requires rendered-browser review') 'Access-controlled pages can still be silently treated as exhausted.'
Assert-Regression ($unknownSource -match '-not \$isDiscoveryAncestor -or \$linkContext -match \$RelevantPattern') 'Generic ancestor pages can enqueue unrelated global collection navigation.'
Assert-Regression ($relevantPattern -match 'vision\.zero') 'Vision Zero and school-safety source pages are absent from the shared relevance policy.'

$result = [ordered]@{
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  regression = 'document-graph discovery, retained-source expansion, and outbound-host capture'
  passed = ($errors.Count -eq 0)
  checks = $checkCount
  errors = @($errors)
}
$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$result | ConvertTo-Json -Depth 5 -Compress
if ($errors.Count) { exit 1 }
