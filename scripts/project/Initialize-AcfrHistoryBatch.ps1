[CmdletBinding()]
param(
  [string]$CrawlPath = 'research/discovery/cabq-acfr-history-audit-2026-08-24.json',
  [string]$DownloadDirectory = 'research/staging/acfr-history',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$parentUrl = 'https://www.cabq.gov/dfa/treasury/investor-information/annual-comprehensive-financial-reports'
if (-not (Test-Path -LiteralPath $CrawlPath)) {
  & "$PSScriptRoot/Invoke-SourceCrawl.ps1" -Agency cabq -StartUrl $parentUrl -OutputPath $CrawlPath -MainOnly | Out-Null
}
$crawl = Get-Content -Raw -Encoding UTF8 -LiteralPath $CrawlPath | ConvertFrom-Json
$links = @($crawl.candidates | Where-Object { $_.anchor_text -match '^Download the (?<year>\d{4}) Annual Comprehensive Financial Report$' })
if ($links.Count -ne 23) { throw "Expected 23 ACFR documents; found $($links.Count)." }

$results = foreach ($link in $links) {
  $null = $link.anchor_text -match '^Download the (?<year>\d{4}) Annual Comprehensive Financial Report$'
  $year = [int]$Matches.year
  $candidate = & "$PSScriptRoot/Add-InventoryCandidate.ps1" `
    -SourceUrl ([string]$link.url) -DirectFileUrl ([string]$link.url) `
    -Agency 'City of Albuquerque' -Title "City of Albuquerque Annual Comprehensive Financial Report, Fiscal Year $year" `
    -Date "FY $year" -FileType PDF -ParentUrl $parentUrl `
    -DiscoveryMethod 'authored ACFR archive document link' -CrawlDepth 1 -InventoryPath $InventoryPath | ConvertFrom-Json
  if ($candidate.status -notin @('downloaded','parsed','description drafted','placement assigned','implemented','validated','duplicate','superseded','excluded')) {
    $candidate = & "$PSScriptRoot/Download-Candidate.ps1" -Id $candidate.id -InventoryPath $InventoryPath -DownloadDirectory $DownloadDirectory | ConvertFrom-Json
  }
  [pscustomobject]@{id=$candidate.id;status=$candidate.status;title=$candidate.title;size_bytes=$candidate.size_bytes;checksum_sha256=$candidate.checksum_sha256;local_path=$candidate.local_path}
}
$results | Sort-Object title | ConvertTo-Json -Depth 5
